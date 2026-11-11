"""How much of the 125 and 50 ms detail information is onset latency?

The level-2 detail of a unit is its second-half minus first-half count and
the level-3 detail is its 50 ms profile with the half-window means removed,
so both are dominated by when in the window the unit's response rises.
Image information in first-spike latency is well known (Gollisch and Meister
2008). This script asks whether the per-scale details carry anything beyond
an explicit per-unit timing summary, from both directions:

  1. Decode the image from the timing summaries alone and together with the
     whole-window count, then add the details and see whether accuracy rises.
  2. Regress the level-2 and level-3 details on the timing summaries (fit on
     training trials, as in the rate regression of residual_levels.py) and
     decode what remains.

Per-unit timing summaries, from the 1 ms spike array:

  first   time of the first spike in the window (fraction of 250 ms;
          1.0 when the unit is silent)
  miss    1 when the unit is silent in the window
  com     mean spike time (fraction of 250 ms; 0.5 when silent)

Readouts (one nested-C logistic each, time-blocked split):

  rate              L1 detail (sqrt whole-window count); the reference
  latency           first + miss
  com               com + miss
  timing            first + com + miss
  rate_timing       rate + timing
  rate_timing_d23   rate + timing + level-2 and level-3 details (does shape
                    add anything to count and timing?)
  detail2, detail3  each detail alone (as residual_levels.py)
  detail2_unitlat   detail regressed on the unit's own rate (L1 coefficient
  detail3_unitlat   and sqrt count) and timing summaries
  detail2_poplat    detail regressed on every unit's rate and timing
  detail3_poplat    summaries (the stronger control)
  d23_poplat        both details, population-regressed, together
  pyr1, pyr3        the E3 pyramid readout (cumulative log pooled counts) at
                    L1 and L3, the coordinates in which the per-level gain is
                    measured in the rest of the results
  pyr1_timing       pyr1 + timing: does the timing summary recover the L1 to
  pyr3_timing       L3 gain of the pyramid? pyr3 + timing for the ceiling

Population-level timing (--readouts ... --tag pop): per trial, the first
spike of the population, the centre of mass of the population count over
time, and the time at which the population's cumulative count reaches half,
each a fraction of the window.

  poptiming         the three population summaries alone
  pyr1_timing_pop   pyr1 + unit timing + population timing
  pyr3_timing_pop   pyr3 + the same
  detail2_popall    detail regressed on every unit's rate and timing plus
  detail3_popall    the population timing
  d23_popall        both details, so regressed, together

Behavioural state (--readouts ... --tag state; needs data/allen_<session>_state.npz
from scripts/load_allen_state.py): per-trial running speed and pupil area,
z-scored on the training trials, with a missing indicator for pupil.

  state             running and pupil alone (should be near chance)
  rate_state        L1 detail + state
  pyr3_state        pyramid L3 + state
  detail2_popstate  detail regressed on every unit's rate (L1 coefficient and
  detail3_popstate  sqrt count) plus the state covariates
  d23_popstate      both details, so regressed, together
  run_pyr<k>        pyramid level k decoded within running trials only
  still_pyr<k>      (speed above 5 cm/s) and within stationary trials only,
                    the larger set subsampled to the smaller's size; NaN when
                    the smaller state has under 8 repeats of some image

    PYTHONPATH=. python scripts/latency_readout.py --data data/allen_<id>_VISp.npz --n-units 60 --repeats 5
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parent))
from residual_levels import detail_bases, detail_feats, regress_out, subsample  # noqa: E402
from spikescale.decode import blocked_split, fit_clf_nested, pool_counts, score  # noqa: E402
from spikescale.jitter import bin_ms  # noqa: E402
from spikescale.synth import SynthConfig, generate  # noqa: E402

READOUTS = ("rate", "latency", "com", "timing", "rate_timing", "rate_timing_d23",
            "detail2", "detail3", "detail2_unitlat", "detail3_unitlat",
            "detail2_poplat", "detail3_poplat", "d23_poplat",
            "pyr1", "pyr3", "pyr1_timing", "pyr3_timing",
            "poptiming", "pyr1_timing_pop", "pyr3_timing_pop", "detail2_popall", "detail3_popall", "d23_popall",
            "state", "rate_state", "pyr3_state", "detail2_popstate", "detail3_popstate", "d23_popstate",
            *[f"{st}_pyr{k}" for st in ("run", "still") for k in range(1, 7)])
RUN_CMS = 5.0


def timing_summaries(spikes_ms):
    """(trials, units, 3): first-spike time, silent indicator, centre of mass, each in [0, 1]."""
    n, u, t = spikes_ms.shape
    any_spike = spikes_ms.sum(-1) > 0
    first = np.argmax(spikes_ms > 0, axis=-1) / t
    first[~any_spike] = 1.0
    times = np.arange(t) / t
    com = (spikes_ms * times).sum(-1) / np.maximum(spikes_ms.sum(-1), 1)
    com[~any_spike] = 0.5
    return np.stack([first, (~any_spike).astype(float), com], axis=-1)


def population_timing(spikes_ms):
    """(trials, 3): population first spike, centre of mass and half-count time, fractions of the window."""
    pop = spikes_ms.sum(1)  # (trials, t)
    n, t = pop.shape
    any_spike = pop.sum(-1) > 0
    first = np.argmax(pop > 0, axis=-1) / t
    first[~any_spike] = 1.0
    times = np.arange(t) / t
    com = (pop * times).sum(-1) / np.maximum(pop.sum(-1), 1)
    com[~any_spike] = 0.5
    cum = np.cumsum(pop, axis=-1)
    half = np.argmax(cum >= cum[:, -1:] / 2, axis=-1) / t
    half[~any_spike] = 0.5
    return np.stack([first, com, half], axis=-1)


def state_feats(state, tr):
    """(trials, 2 or 3): running and pupil z-scored on the training trials, NaN to 0 plus an indicator."""
    cols = []
    for name in ("running", "pupil"):
        v = state[name].astype(float)
        ok = np.isfinite(v)
        if ok[tr].sum() < 2:
            continue
        z = (v - np.nanmean(v[tr])) / (np.nanstd(v[tr]) + 1e-9)
        cols.append(np.where(ok, z, 0.0))
        if not ok.all():
            cols.append((~ok).astype(float))
    return np.stack(cols, axis=1)


def pyramid(counts, k):
    n = len(counts)
    return np.concatenate([np.log1p(pool_counts(counts, L)).reshape(n, -1) for L in (1, 2, 5, 10, 25, 50)[:k]], axis=1)


def features(readout, counts, spikes_ms, bases, tr, state=None):
    n, u, _ = counts.shape
    if readout == "state":
        return state_feats(state, tr)
    if readout.endswith("_state"):
        st = state_feats(state, tr)
        base = detail_feats(counts, bases)[0] if readout == "rate_state" else pyramid(counts, 3)
        return np.concatenate([base, st], axis=1)
    if readout.endswith("_popstate"):
        feats = detail_feats(counts, bases)
        cov = np.stack([feats[0], np.sqrt(counts.sum(-1))], axis=-1)
        reg = regress_out(feats, cov, tr, "pop", extra=state_feats(state, tr))
        if readout == "d23_popstate":
            return np.concatenate([reg[1], reg[2]], axis=1)
        return reg[int(readout[6]) - 1]
    feats = detail_feats(counts, bases)
    tim = timing_summaries(spikes_ms)
    ptim = population_timing(spikes_ms)
    rate = feats[0]
    cov = np.concatenate([feats[0][:, :, None], np.sqrt(counts.sum(-1))[:, :, None], tim], axis=-1)
    if readout == "rate":
        return rate
    if readout == "latency":
        return tim[:, :, [0, 1]].reshape(n, -1)
    if readout == "com":
        return tim[:, :, [2, 1]].reshape(n, -1)
    if readout == "timing":
        return tim.reshape(n, -1)
    if readout == "rate_timing":
        return np.concatenate([rate, tim.reshape(n, -1)], axis=1)
    if readout == "rate_timing_d23":
        return np.concatenate([rate, tim.reshape(n, -1), feats[1], feats[2]], axis=1)
    if readout == "poptiming":
        return ptim
    if readout.startswith("pyr"):
        k = int(readout[3])
        pyr = np.concatenate([np.log1p(pool_counts(counts, L)).reshape(n, -1) for L in (1, 2, 5)[:k]], axis=1)
        if readout.endswith("_timing_pop"):
            return np.concatenate([pyr, tim.reshape(n, -1), ptim], axis=1)
        return np.concatenate([pyr, tim.reshape(n, -1)], axis=1) if readout.endswith("_timing") else pyr
    if readout.endswith("_popall"):
        reg = regress_out(feats, cov, tr, "pop", extra=ptim)
        if readout == "d23_popall":
            return np.concatenate([reg[1], reg[2]], axis=1)
        return reg[int(readout[6]) - 1]
    if readout in ("detail2", "detail3"):
        return feats[int(readout[-1]) - 1]
    if readout.endswith("_unitlat"):
        return regress_out(feats, cov, tr, "unit")[int(readout[6]) - 1]
    if readout.endswith("_poplat"):
        reg = regress_out(feats, cov, tr, "pop")
        if readout == "d23_poplat":
            return np.concatenate([reg[1], reg[2]], axis=1)
        return reg[int(readout[6]) - 1]
    raise ValueError(readout)


def state_subset(labels, state, which, seed):
    """Trial indices of one state, the larger state subsampled to the smaller's size; None if too few repeats."""
    running = state["running"] > RUN_CMS
    sets = {"run": np.nonzero(running)[0], "still": np.nonzero(~running)[0]}
    small = min(sets.values(), key=len)
    if np.bincount(labels[small], minlength=labels.max() + 1).min() < 8:
        return None
    idx = sets[which]
    if len(idx) > len(small):
        idx = np.sort(np.random.default_rng(100 + seed).choice(idx, len(small), replace=False))
    return idx


def one(counts, spikes_ms, labels, readout, bases, state=None, seed=0):
    if readout.startswith(("run_pyr", "still_pyr")):
        which, k = readout.split("_pyr")
        idx = state_subset(labels, state, which, seed)
        if idx is None:
            return float("nan"), None
        counts, labels = counts[idx], labels[idx]
        tr, te = blocked_split(len(labels), labels)
        x = pyramid(counts, int(k))
    else:
        tr, te = blocked_split(len(labels), labels)
        x = features(readout, counts, spikes_ms, bases, tr, state)
    clf, c = fit_clf_nested(x[tr], labels[tr])
    return score(clf, x[te], labels[te]), c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data")
    ap.add_argument("--synthetic")
    ap.add_argument("--n-units", type=int, default=0)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--out", default="results")
    ap.add_argument("--readouts", default=",".join(READOUTS[:17]))
    ap.add_argument("--tag", default="", help="suffix for the output file, e.g. pop")
    args = ap.parse_args()
    readouts = tuple(args.readouts.split(","))
    bad = set(readouts) - set(READOUTS)
    if bad:
        ap.error(f"unknown readouts {sorted(bad)}")

    state = None
    if args.synthetic:
        name = args.synthetic
        cfg = (SynthConfig(code="timing", precision_ms=int(name.split("p")[1]))
               if name.startswith("timing_p") else SynthConfig(code=name))
        _, labels, spikes_all = generate(cfg, return_ms=True)
        counts_all = bin_ms(spikes_all)
    else:
        d = np.load(args.data)
        counts_all, spikes_all, labels = d["counts"], d["spikes_ms"], d["labels"]
        name = Path(args.data).stem
        sp = Path(args.data).with_name(f"allen_{name.split('_')[1]}_state.npz")
        if sp.exists():
            st = np.load(sp)
            assert np.allclose(st["start_time"], d["start_time"])
            state = {"running": st["running"], "pupil": st["pupil"]}
            print(f"state: {np.mean(state['running'] > RUN_CMS):.2f} of trials running, pupil on "
                  f"{np.isfinite(state['pupil']).mean():.2f}", flush=True)
    if any(ro == "state" or ro.endswith(("_state", "_popstate")) or ro.startswith(("run_", "still_")) for ro in readouts) and state is None:
        ap.error("state readouts need data/allen_<session>_state.npz (scripts/load_allen_state.py)")
    counts_all = counts_all.astype(np.float64)
    spikes_all = spikes_all.astype(np.int16)  # kept small: each worker receives a copy of its subset
    bases = detail_bases(t=counts_all.shape[2])
    print(f"{name}: {len(labels)} trials, {counts_all.shape[1]} units, "
          f"{(spikes_all.sum(-1) == 0).mean():.2f} of trial-unit pairs silent", flush=True)

    jobs = [(seed, ro) for seed in range(args.repeats) for ro in readouts]

    def sub(seed):
        rng = np.random.default_rng(seed)
        u = counts_all.shape[1]
        if args.n_units and args.n_units < u:
            idx = np.sort(rng.choice(u, args.n_units, replace=False))
            return counts_all[:, idx], spikes_all[:, idx]
        return counts_all, spikes_all

    assert np.array_equal(sub(0)[0], subsample(counts_all, args.n_units, 0))  # same subsets as run_e3
    t0 = time.time()
    res = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(one)(*sub(seed), labels, ro, bases, state, seed) for seed, ro in jobs)
    print(f"{len(jobs)} fits in {time.time() - t0:.0f}s", flush=True)

    result = {"name": name, "chance": 1 / len(np.unique(labels)), "n_units": args.n_units or counts_all.shape[1],
              "readouts": list(readouts), "runs": {}}
    for (seed, ro), (acc, c) in zip(jobs, res):
        result["runs"].setdefault(f"seed{seed}", {})[ro] = {"acc": acc, "c": c}
    result["mean"] = {ro: float(np.nanmean([r[ro]["acc"] for r in result["runs"].values()])) for ro in readouts}
    result["std"] = {ro: float(np.nanstd([r[ro]["acc"] for r in result["runs"].values()])) for ro in readouts}
    for ro in readouts:
        print(f"{ro:17s} {result['mean'][ro]:.3f} +- {result['std'][ro]:.3f}")
    out = Path(args.out) / f"latency_{name}{'_' + args.tag if args.tag else ''}.json"
    out.write_text(json.dumps(result, indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
