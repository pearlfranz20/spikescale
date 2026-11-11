"""Decode from each level's orthogonal detail alone: is the information at a scale unique to it?

The cumulative pyramid readout at level k contains levels 1 to k, so a gain
from level k-1 to k means the finer bins add decodable information, but it
cannot say whether that information is unique to scale k or a re-expression of
coarser structure. This script splits the 5 ms count vector of each unit into
orthogonal pieces, one per level: V_k is the space of functions constant on
level k's bins, and the level-k detail is the component of V_1 + ... + V_k
orthogonal to V_1 + ... + V_{k-1}. Level lengths 1, 2, 5, 10, 25, 50 do not
all nest (2 does not divide 5, 10 does not divide 25), so the details are
built by Gram-Schmidt on the pooling bases rather than as Haar differences.
Detail dimensions per unit come to 1, 1, 4, 4, 20, 20 (sum 50).

Three readouts per level, each through the E3 primary decoder (nested-C
cumulative logistic on sqrt counts):

  detail       level-k detail alone
  detail_cum   details 1 to k concatenated (equals the cumulative pyramid up to
               a rotation and the sqrt transform; a check)
  shuffled     level-k detail alone after the 5 ms bins of every trial and unit
               are permuted. This keeps each unit's count and destroys all
               timing, so it measures how much "detail" decoding comes from
               the size of the fluctuations rather than their shape. The
               unique information at scale k is detail minus shuffled.

Rate-regressed readouts (--readouts detail_unitrate,detail_poprate,shuffled_unitrate
--tag rate) address the caveat that a detail can be decodable because its
shape covaries with firing rate across images. Before decoding, every detail
feature is regressed on whole-window rate, with the regression fit on the
training trials only and applied to both splits:

  detail_unitrate   each unit's level-k detail regressed on that unit's own rate
                    (its L1 coefficient and the sqrt of its whole-window count)
  detail_poprate    each detail feature regressed on the rates of all units
                    (the whole population rate vector), the stronger control:
                    what remains is temporal shape not linearly predictable from
                    any unit's rate
  shuffled_unitrate the shuffled control after the same per-unit regression; the
                    size of the fluctuations is a function of the count, so this
                    should fall to chance

At L1 these readouts decode the rate itself (there is nothing to regress out)
and so repeat the detail row.

    PYTHONPATH=. python scripts/residual_levels.py --data data/allen_<id>_VISp.npz --n-units 60 --repeats 5 --all-units
    PYTHONPATH=. python scripts/residual_levels.py --data data/allen_<id>_VISp.npz --n-units 60 --repeats 5 --all-units         --readouts detail_unitrate,detail_poprate,shuffled_unitrate --tag rate
    PYTHONPATH=. python scripts/residual_levels.py --synthetic timing_p25
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

from spikescale.decode import blocked_split, fit_clf_nested, score
from spikescale.jitter import bin_ms
from spikescale.synth import LEVEL_LENGTHS, SynthConfig, generate

READOUTS = ("detail", "detail_cum", "shuffled")
ALL_READOUTS = READOUTS + ("detail_unitrate", "detail_poprate", "shuffled_unitrate")


def detail_bases(lengths=LEVEL_LENGTHS, t=50):
    """Orthonormal basis (t, d_k) of the level-k detail space, for each level."""
    prev = np.zeros((t, 0))
    out = []
    for L in lengths:
        b = np.repeat(np.eye(L), t // L, axis=0) / np.sqrt(t // L)  # pooling basis of V_L
        r = b - prev @ (prev.T @ b)
        u, s, _ = np.linalg.svd(r, full_matrices=False)
        q = u[:, s > 1e-8]
        out.append(q)
        prev = np.concatenate([prev, q], axis=1)
    return out


def detail_feats(counts, bases):
    s = np.sqrt(counts)  # (trials, units, t)
    return [np.einsum("nut,td->nud", s, q).reshape(len(s), -1) for q in bases]


def shuffle_time(counts, rng):
    """Permute the time bins independently within every trial and unit."""
    n, u, t = counts.shape
    perm = np.argsort(rng.random((n, u, t)), axis=-1)
    return np.take_along_axis(counts, perm, axis=-1)


def rate_covariates(counts, feats):
    """(trials, units, 2): each unit's L1 coefficient and the sqrt of its whole-window count."""
    return np.stack([feats[0], np.sqrt(counts.sum(-1))], axis=-1)


def regress_out(feats, cov, tr, mode, extra=None):
    """Remove from every detail (levels 2 on) the part linearly predictable from rate.

    The regression is fit on the training trials tr and applied to all trials.
    mode "unit": unit u's detail on unit u's own covariates. mode "pop": every
    detail feature on the covariates of all units. Level 1 is returned as is.
    cov may hold any number of covariates per unit (scripts/latency_readout.py
    adds first-spike latency and spike-time centre of mass). extra (n, e) are
    population-level covariates appended in mode "pop" only.
    """
    n, u, _ = cov.shape
    out = [feats[0]]
    for f in feats[1:]:
        if mode == "unit":
            d = f.shape[1] // u
            f3 = f.reshape(n, u, d)
            x = np.concatenate([np.ones((n, u, 1)), cov], axis=-1)  # (n, u, 3)
            xt = x[tr]
            gram = np.einsum("nup,nuq->upq", xt, xt) + 1e-8 * np.eye(x.shape[-1])
            xty = np.einsum("nup,nud->upd", xt, f3[tr])
            beta = np.linalg.solve(gram, xty)  # (u, 3, d)
            out.append((f3 - np.einsum("nup,upd->nud", x, beta)).reshape(n, -1))
        elif mode == "pop":
            x = np.concatenate([np.ones((n, 1)), cov.reshape(n, -1)] + ([extra] if extra is not None else []), axis=1)
            beta, *_ = np.linalg.lstsq(x[tr], f[tr], rcond=None)
            out.append(f - x @ beta)
        else:
            raise ValueError(mode)
    return out


def one(counts, labels, readout, level, seed, bases):
    tr, te = blocked_split(len(labels), labels)
    clean = counts
    if readout.startswith("shuffled"):
        counts = shuffle_time(counts, np.random.default_rng(1000 + seed))
    feats = detail_feats(counts, bases)
    if readout.endswith("_unitrate"):
        feats = regress_out(feats, rate_covariates(clean, detail_feats(clean, bases)), tr, "unit")
    elif readout.endswith("_poprate"):
        feats = regress_out(feats, rate_covariates(clean, detail_feats(clean, bases)), tr, "pop")
    x = np.concatenate(feats[:level + 1], axis=1) if readout == "detail_cum" else feats[level]
    clf, c = fit_clf_nested(x[tr], labels[tr])
    return score(clf, x[te], labels[te]), c


def subsample(counts, n_units, seed):
    """Same unit subset as scripts/run_e3.py for the same seed."""
    rng = np.random.default_rng(seed)
    if n_units and n_units < counts.shape[1]:
        counts = counts[:, np.sort(rng.choice(counts.shape[1], n_units, replace=False))]
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data")
    ap.add_argument("--synthetic")
    ap.add_argument("--n-units", type=int, default=0)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--all-units", action="store_true", help="add one run on every unit (seed 0)")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--out", default="results")
    ap.add_argument("--readouts", default=",".join(READOUTS),
                    help="comma-separated subset of " + ",".join(ALL_READOUTS))
    ap.add_argument("--tag", default="", help="suffix for the output file, e.g. rate")
    args = ap.parse_args()
    readouts = tuple(args.readouts.split(","))
    bad = set(readouts) - set(ALL_READOUTS)
    if bad:
        ap.error(f"unknown readouts {sorted(bad)}")

    if args.synthetic:
        name = args.synthetic
        cfg = (SynthConfig(code="timing", precision_ms=int(name.split("p")[1]))
               if name.startswith("timing_p") else SynthConfig(code=name))
        _, labels, spikes_ms = generate(cfg, return_ms=True)
        counts_all = bin_ms(spikes_ms)
    else:
        d = np.load(args.data)
        counts_all, labels = d["counts"], d["labels"]
        name = Path(args.data).stem
    counts_all = counts_all.astype(np.float64)
    bases = detail_bases(t=counts_all.shape[2])
    print(f"{name}: {len(labels)} trials, {counts_all.shape[1]} units, detail dims "
          f"{[q.shape[1] for q in bases]}", flush=True)

    runs = [(args.n_units, s) for s in range(args.repeats)]
    if args.all_units:
        runs.append((0, 0))
    jobs = [(nu, seed, ro, k) for nu, seed in runs for ro in readouts for k in range(len(LEVEL_LENGTHS))]
    t0 = time.time()
    res = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(one)(subsample(counts_all, nu, seed), labels, ro, k, seed, bases) for nu, seed, ro, k in jobs)
    print(f"{len(jobs)} fits in {time.time() - t0:.0f}s", flush=True)

    result = {"name": name, "chance": 1 / len(np.unique(labels)), "levels": list(LEVEL_LENGTHS),
              "detail_dims": [int(q.shape[1]) for q in bases], "readouts": list(readouts), "runs": {}}
    for (nu, seed, ro, k), (acc, c) in zip(jobs, res):
        key = f"n{nu or counts_all.shape[1]}/seed{seed}"
        r = result["runs"].setdefault(key, {ro: {"acc": [None] * 6, "c": [None] * 6} for ro in readouts})
        r[ro]["acc"][k], r[ro]["c"][k] = acc, c
    by_n = {}
    for key, r in result["runs"].items():
        by_n.setdefault(key.split("/")[0], []).append(r)
    result["mean"] = {n: {ro: np.mean([r[ro]["acc"] for r in rs], axis=0).tolist() for ro in readouts}
                      for n, rs in by_n.items()}
    result["std"] = {n: {ro: np.std([r[ro]["acc"] for r in rs], axis=0).tolist() for ro in readouts}
                     for n, rs in by_n.items()}
    for n, m in result["mean"].items():
        for ro in readouts:
            print(f"{n:6s} {ro:17s} " + " ".join(f"{a:.3f}" for a in m[ro]) + f"  (seeds {len(by_n[n])})")
    out = Path(args.out) / f"residual_{name}{'_' + args.tag if args.tag else ''}.json"
    out.write_text(json.dumps(result, indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
