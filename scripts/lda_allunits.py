"""Shrinkage LDA on the cumulative pyramid, all units, one decoder per recording.

A generative readout: one mean response per image and one pooled noise
covariance, shrunk toward its diagonal by a factor chosen on the same inner
time-blocked split as the logistic's C. Compared against the logistic
decoder of linear_allunits.py on the same trials.

    PYTHONPATH=. python scripts/lda_allunits.py --jobs 8
Output: results/lda_allunits.json  {recording: {"acc": [L1..L6], "shrink": [L1..L6]}}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spikescale.decode import blocked_split, pool_counts  # noqa: E402

LENGTHS = (1, 2, 5, 10, 25, 50)
SHRINK = (0.05, 0.1, 0.2, 0.35, 0.5, 0.7, 0.85, 0.95, 1.0)


def lda_fit(x, y, a, n_cls=118):
    mu = np.stack([x[y == c].mean(0) for c in range(n_cls)])
    res = x - mu[y]
    S = res.T @ res / len(x)
    d = np.diag(S).copy()
    S = (1 - a) * S + a * np.diag(d) + 1e-4 * d.mean() * np.eye(len(S))
    W = np.linalg.solve(S, mu.T).T
    return W, -0.5 * (W * mu).sum(1)


def lda_acc(W, b, x, y):
    return float(((x @ W.T + b).argmax(1) == y).mean())


def run(path):
    d = np.load(path)
    sp, y = d["spikes_ms"], d["labels"]
    c5 = sp.reshape(len(y), sp.shape[1], 50, 5).sum(-1).astype(np.float64)
    tr, te = blocked_split(len(y), y)
    tri = np.nonzero(tr)[0]
    itr, iva = blocked_split(len(tri), y[tri], test_frac=0.25)
    accs, shr = [], []
    for k in range(len(LENGTHS)):
        x = np.concatenate([np.log1p(pool_counts(c5, L)).reshape(len(y), -1) for L in LENGTHS[:k + 1]], 1)
        xa, ya = x[tri[itr]], y[tri[itr]]
        xv, yv = x[tri[iva]], y[tri[iva]]
        val = [lda_acc(*lda_fit(xa, ya, a), xv, yv) for a in SHRINK]
        a = SHRINK[int(np.argmax(val))]
        accs.append(lda_acc(*lda_fit(x[tr], y[tr], a), x[te], y[te]))
        shr.append(a)
    name = Path(path).stem.replace("allen_", "")
    print(name, " ".join(f"{v:.3f}" for v in accs), flush=True)
    return name, {"acc": accs, "shrink": shr}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()
    files = sorted(str(f) for f in Path("data").glob("allen_*_*.npz")
                   if len(f.stem.split("_")) == 3 and f.stem.split("_")[2] != "state")
    res = Parallel(n_jobs=args.jobs)(delayed(run)(f) for f in files)
    Path("results/lda_allunits.json").write_text(json.dumps(dict(res), indent=1))
    print("wrote results/lda_allunits.json")


if __name__ == "__main__":
    main()
