"""The pyramid on drifting gratings: is the 50 ms optimum tied to the 250 ms presentation?

Natural scenes play back to back every 250 ms, so the window of every analysis
above ends where the next image begins, and a reader may ask whether the
50 ms optimum is set by that boundary. Drifting gratings are shown for 2 s
after 1 s of gray, 8 directions x 5 temporal frequencies, 15 repeats each.
This script decodes from the pyramid in three windows from grating onset,
250, 1000 and 2000 ms, with bin widths from the whole window down to 5 ms,
and three label sets:

  cond   the 40 direction x frequency conditions (chance 0.025)
  ori    the 8 directions, frequencies pooled (chance 0.125): a static property
         of the stimulus, the analogue of image identity
  tf     the 5 temporal frequencies, directions pooled (chance 0.2): a temporal
         property, the positive control that fine bins are read when the
         stimulus itself has fine temporal structure

Readouts per window, label set and level: the cumulative pyramid (log1p pooled
counts of the levels down to that one), the level's orthogonal detail alone,
the detail after shuffling the 5 ms bins within every trial and unit (control),
and for the pyramid the 10 ms jitter cost. Same nested-C logistic, same
time-blocked split (last 20% of every condition's repeats, the same trials for
all three label sets), same 60-unit subsets per seed as the natural-scenes
analyses of the same area (scripts/residual_levels.subsample).

    PYTHONPATH=. python scripts/gratings_pyramid.py --data data/allen_<id>_VISp_dg.npz --scenes data/allen_<id>_VISp.npz --n-units 60 --repeats 5 --jobs 8

With --scenes, the same readouts run on the area's natural-scenes trials in
the 250 ms window (label set img, 118 images), on the same unit subsets, so
the two stimuli are compared within one script and one decoder.

Output: results/gratings_allen_<id>_<area>.json with
  runs[seed<k>][<dg|scenes>/w<W>/<labels>/<readout>] = list over levels of held-out accuracy
  mean[...] the same, averaged over seeds; levels[w<W>] the bin widths in ms.
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
from residual_levels import detail_bases, detail_feats, shuffle_time, subsample  # noqa: E402
from spikescale.decode import blocked_split, fit_clf_nested, pool_counts, score  # noqa: E402
from spikescale.jitter import jitter_spikes  # noqa: E402

BIN_MS = 5
# window in ms -> pooling lengths (number of bins); widths are window / length
WINDOWS = {250: (1, 2, 5, 10, 25, 50),
           1000: (1, 2, 4, 8, 20, 40, 100, 200),
           2000: (1, 2, 4, 8, 16, 40, 80, 200, 400)}
LABELS = ("cond", "ori", "tf")
READOUTS = ("pyramid", "detail", "shuffled", "jitter10")


def bin_counts(spikes_ms, window):
    n, u, _ = spikes_ms.shape
    return spikes_ms[:, :, :window].reshape(n, u, window // BIN_MS, BIN_MS).sum(-1).astype(np.float64)


def pyramid(counts, lengths, k):
    n = len(counts)
    return np.concatenate([np.log1p(pool_counts(counts, L)).reshape(n, -1) for L in lengths[:k + 1]], axis=1)


def one(spikes_ms, labels_all, split_labels, window, label_set, readout, seed):
    """Accuracy at every level of `window` for one readout, label set and unit subset."""
    lengths = WINDOWS[window]
    y = labels_all[label_set]
    tr, te = blocked_split(len(y), split_labels)
    if readout == "jitter10":
        spikes_ms = jitter_spikes(spikes_ms, 10.0, np.random.default_rng(2000 + seed))
    counts = bin_counts(spikes_ms, window)
    if readout == "shuffled":
        counts = shuffle_time(counts, np.random.default_rng(1000 + seed))
    if readout in ("detail", "shuffled"):
        feats = detail_feats(counts, detail_bases(lengths, t=counts.shape[2]))
    accs, cs = [], []
    for k in range(len(lengths)):
        x = feats[k] if readout in ("detail", "shuffled") else pyramid(counts, lengths, k)
        clf, c = fit_clf_nested(x[tr], y[tr])
        accs.append(score(clf, x[te], y[te]))
        cs.append(c)
    return accs, cs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="data/allen_<id>_<area>_dg.npz")
    ap.add_argument("--scenes", default="", help="the area's natural-scenes file, for the 250 ms pyramid on the same units")
    ap.add_argument("--n-units", type=int, default=60)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--windows", default="250,1000,2000")
    ap.add_argument("--readouts", default=",".join(READOUTS))
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    windows = [int(w) for w in args.windows.split(",")]
    readouts = args.readouts.split(",")

    d = np.load(args.data)
    spikes_all = d["spikes_ms"].astype(np.int16)
    cond = d["labels"]
    labels_all = {"cond": cond,
                  "ori": np.searchsorted(np.unique(d["ori"]), d["ori"]),
                  "tf": np.searchsorted(np.unique(d["tf"]), d["tf"])}
    name = Path(args.data).stem.replace("_dg", "")
    reps = np.bincount(cond)
    print(f"{name}: {len(cond)} trials, {spikes_all.shape[1]} units, {len(reps)} conditions, "
          f"{reps.min()} to {reps.max()} repeats; mean rate {spikes_all.sum(-1).mean() / spikes_all.shape[2] * 1000:.1f} Hz", flush=True)
    # dataset -> (spikes, label sets, labels for the split, windows, label-set names)
    data = {"dg": (spikes_all, labels_all, cond, windows, LABELS)}
    if args.scenes:
        s = np.load(args.scenes)
        assert np.array_equal(s["unit_ids"], d["unit_ids"]), "scenes file has a different unit set"
        data["scenes"] = (s["spikes_ms"].astype(np.int16), {"img": s["labels"]}, s["labels"], [250], ("img",))
        print(f"scenes: {len(s['labels'])} trials, same {s['spikes_ms'].shape[1]} units", flush=True)

    jobs = [(ds, seed, w, ls, ro) for ds, (_, _, _, ws, lss) in data.items() for seed in range(args.repeats)
            for w in ws for ls in lss for ro in readouts if not (ro == "jitter10" and ls not in ("cond", "img"))]
    t0 = time.time()
    res = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(one)(subsample(data[ds][0], args.n_units, seed), data[ds][1], data[ds][2], w, ls, ro, seed)
        for ds, seed, w, ls, ro in jobs)
    print(f"{len(jobs)} jobs in {time.time() - t0:.0f}s", flush=True)

    out = {"data": args.data, "scenes": args.scenes, "n_units": args.n_units, "repeats": args.repeats,
           "n_trials": int(len(cond)), "repeats_per_condition": [int(reps.min()), int(reps.max())],
           "levels": {f"w{w}": [w // L for L in WINDOWS[w]] for w in set(windows) | {250}},
           "chance": {ls: 1 / len(np.unique(v)) for ls, v in labels_all.items()}, "runs": {}, "mean": {}}
    for (ds, seed, w, ls, ro), (accs, cs) in zip(jobs, res):
        out["runs"].setdefault(f"seed{seed}", {})[f"{ds}/w{w}/{ls}/{ro}"] = {"acc": accs, "c": cs}
    for key in {k for r in out["runs"].values() for k in r}:
        out["mean"][key] = np.mean([r[key]["acc"] for r in out["runs"].values() if key in r], axis=0).tolist()
    path = Path(args.out) / f"gratings_{name}.json"
    path.write_text(json.dumps(out, indent=1))
    for ds, (_, _, _, ws, lss) in data.items():
        for w in ws:
            print(f"{ds}, window {w} ms, widths {out['levels'][f'w{w}']}")
            for ls in lss:
                for ro in readouts:
                    key = f"{ds}/w{w}/{ls}/{ro}"
                    if key in out["mean"]:
                        print(f"  {ls:4s} {ro:8s} " + " ".join(f"{a:.3f}" for a in out["mean"][key]))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
