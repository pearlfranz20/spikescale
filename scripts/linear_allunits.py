"""The linear baseline for the cross-session decoder: every unit of a population, one decoder per recording.

Same readout as everywhere (cumulative log1p pyramid, nested-C L2 logistic),
same time-blocked test set, but all units of the population instead of
60-unit subsets, because the cross-session decoder (spike_transformer.py)
reads all units. One run per recording; there is no unit subsampling, so
no seeds.

    PYTHONPATH=. python scripts/linear_allunits.py --jobs 8
Output: results/linear_allunits.json  {recording: [accuracy at L1..L6 = 250..5 ms]}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spikescale.decode import blocked_split, fit_clf_nested, pool_counts, score  # noqa: E402

LENGTHS = (1, 2, 5, 10, 25, 50)


def run(path):
    d = np.load(path)
    sp, y = d["spikes_ms"], d["labels"]
    c5 = sp.reshape(len(y), sp.shape[1], 50, 5).sum(-1).astype(np.float64)
    tr, te = blocked_split(len(y), y)
    accs = []
    for k in range(len(LENGTHS)):
        x = np.concatenate([np.log1p(pool_counts(c5, L)).reshape(len(y), -1) for L in LENGTHS[:k + 1]], 1)
        clf, _ = fit_clf_nested(x[tr], y[tr])
        accs.append(score(clf, x[te], y[te]))
    print(Path(path).stem, " ".join(f"{a:.3f}" for a in accs), flush=True)
    return Path(path).stem.replace("allen_", ""), accs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()
    files = sorted(str(f) for f in Path("data").glob("allen_*_*.npz")
                   if len(f.stem.split("_")) == 3 and f.stem.split("_")[2] != "state")
    res = Parallel(n_jobs=args.jobs)(delayed(run)(f) for f in files)
    Path("results/linear_allunits.json").write_text(json.dumps(dict(res), indent=1))
    print("wrote results/linear_allunits.json")


if __name__ == "__main__":
    main()
