"""A kernel decoder against the linear one: does a nonlinear readout find more at fine bins?

The linear decoder (nested-C L2 logistic on log pooled counts) reads little
below 25 ms. To ask whether that is a limit of the readout, this script
decodes the same trials with a Gaussian-kernel SVM on the same cumulative
pyramid features (standardized log1p counts of every level down to the given
bin width), with C and the kernel width chosen on the same inner time-blocked
split as the logistic's C (C in 1, 10, 100; gamma = g / n_features with g in
0.03, 0.1, 0.3, 1, 3), then refit on all training trials and scored once on
the held-out block. Same 60-unit subsets (residual_levels.subsample) and
held-out set as every other analysis.

(A temporal convolutional network, with and without a linear path, was tried
first on 732592105 VISp, seed 0, with weight decay and early stopping chosen
the same way: 0.37 to 0.40 at 50 ms and 0.20 to 0.31 at 5 ms, against 0.45
and 0.35 for the linear decoder. With about 32 training trials per image it
overfits within a few epochs; see results/RESULTS.md.)

    PYTHONPATH=. python scripts/nonlinear_svm.py --scenes data/allen_<id>_<area>.npz --seeds 0,1,2 --widths 50,5
Output: results/nonlinear_svm_allen_<id>_<area>.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

sys.path.insert(0, str(Path(__file__).resolve().parent))
from residual_levels import subsample  # noqa: E402
from spikescale.decode import blocked_split, pool_counts  # noqa: E402

LENGTHS = (1, 2, 5, 10, 25, 50)  # 250 ms window: 250, 125, 50, 25, 10, 5 ms bins
GRID = [(C, g) for C in (1, 10, 100) for g in (0.03, 0.1, 0.3, 1.0, 3.0)]


def features(c5, width):
    n = len(c5)
    return np.concatenate([np.log1p(pool_counts(c5, L)).reshape(n, -1) for L in LENGTHS if 250 // L >= width], 1)


def fit_score(xtr, ytr, xte, yte, C, g):
    sc = StandardScaler().fit(xtr)
    m = SVC(C=C, gamma=g / xtr.shape[1], kernel="rbf").fit(sc.transform(xtr), ytr)
    return float(m.score(sc.transform(xte), yte))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", required=True)
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--widths", default="50,5")
    ap.add_argument("--n-units", type=int, default=60)
    ap.add_argument("--jobs", type=int, default=15)
    args = ap.parse_args()
    s = np.load(args.scenes)
    y = s["labels"]
    name = Path(args.scenes).stem
    tr, te = blocked_split(len(y), y)
    tri = np.nonzero(tr)[0]
    itr, iva = blocked_split(len(tri), y[tri], test_frac=0.25)
    out = {"scenes": args.scenes, "grid": GRID, "runs": {}, "mean": {}}
    t0 = time.time()
    for seed in [int(v) for v in args.seeds.split(",")]:
        sp = subsample(s["spikes_ms"], args.n_units, seed)
        c5 = sp.reshape(len(y), sp.shape[1], 50, 5).sum(-1).astype(np.float32)
        for w in [int(v) for v in args.widths.split(",")]:
            x = features(c5, w)
            xt = x[tri]
            inner = Parallel(n_jobs=args.jobs)(delayed(fit_score)(xt[itr], y[tri][itr], xt[iva], y[tri][iva], C, g)
                                               for C, g in GRID)
            C, g = GRID[int(np.argmax(inner))]
            acc = fit_score(x[tr], y[tr], x[te], y[te], C, g)
            out["runs"].setdefault(f"seed{seed}", {})[f"width{w}"] = {"acc": acc, "C": C, "g": g, "inner_best": max(inner)}
            print(f"seed {seed} width {w}: {acc:.3f} (C {C}, g {g}) {time.time() - t0:.0f}s", flush=True)
    for w in args.widths.split(","):
        out["mean"][f"width{w}"] = float(np.mean([r[f"width{w}"]["acc"] for r in out["runs"].values()]))
    path = Path("results") / f"nonlinear_svm_{name}.json"
    path.write_text(json.dumps(out, indent=1))
    print(out["mean"], f"wrote {path}")


if __name__ == "__main__":
    main()
