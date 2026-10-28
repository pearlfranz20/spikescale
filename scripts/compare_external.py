"""External comparison: continuous pyramid decoding under the splits used in the literature.

Published natural-scene decoding on Allen Neuropixels (e.g. arXiv 2510.09451,
Table I: VISp, SVM, 10-fold CV, all units) uses random cross-validation and
every unit in the area. E3 uses a time-blocked holdout and 60 units. This script
runs the continuous pyramid (log1p counts pooled to each level length) under
both protocols, with both unit counts and with the same three decoders as E3,
so the two can be set side by side.

    PYTHONPATH=. python scripts/compare_external.py --data data/allen_<id>_VISp.npz
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from sklearn.model_selection import StratifiedKFold

from spikescale.decode import blocked_split, fit_decode, pool_counts
from spikescale.synth import LEVEL_LENGTHS

DECODERS = {"logreg": (0, False), "pca100_logreg": (100, False), "cum_pca100_logreg": (100, True)}


def splits(labels, n_folds, seed):
    tr, te = blocked_split(len(labels), labels)
    out = {"blocked": [(np.nonzero(tr)[0], np.nonzero(te)[0])]}
    skf = StratifiedKFold(n_folds, shuffle=True, random_state=seed)
    out[f"random_{n_folds}fold"] = list(skf.split(np.zeros(len(labels)), labels))
    return out


def one(feats, labels, tr, te, c, n_pca):
    return fit_decode(feats[tr], labels[tr], feats[te], labels[te], c, n_pca)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--n-units", type=int, nargs="+", default=[60, 0], help="0 means all units")
    ap.add_argument("--folds", type=int, default=10)
    ap.add_argument("--c", type=float, default=0.1)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    d = np.load(args.data)
    counts_all, labels = d["counts"], d["labels"]
    name = Path(args.data).stem
    rng = np.random.default_rng(0)
    result = {"name": name, "chance": 1 / len(np.unique(labels)), "c": args.c,
              "levels": list(LEVEL_LENGTHS), "runs": {}}
    for n_units in args.n_units:
        counts = counts_all
        if n_units and n_units < counts.shape[1]:
            counts = counts[:, np.sort(rng.choice(counts.shape[1], n_units, replace=False))]
        nu = counts.shape[1]
        level_feats = [np.log1p(pool_counts(counts, L)).reshape(len(counts), -1) for L in LEVEL_LENGTHS]
        cum_feats = [np.concatenate(level_feats[:k + 1], axis=1) for k in range(len(LEVEL_LENGTHS))]
        for split_name, folds in splits(labels, args.folds, 0).items():
            for dec_name, (n_pca, cum) in DECODERS.items():
                feats = cum_feats if cum else level_feats
                t0 = time.time()
                jobs = [(k, tr, te) for k in range(len(LEVEL_LENGTHS)) for tr, te in folds]
                accs = Parallel(n_jobs=args.jobs)(
                    delayed(one)(feats[k], labels, tr, te, args.c, n_pca) for k, tr, te in jobs)
                per_level = np.array(accs).reshape(len(LEVEL_LENGTHS), len(folds))
                key = f"n{nu}/{split_name}/{dec_name}"
                result["runs"][key] = {"mean": per_level.mean(1).tolist(),
                                       "std": per_level.std(1).tolist(),
                                       "n_folds": len(folds)}
                print(f"{key:35s} " + " ".join(f"{a:.3f}" for a in per_level.mean(1))
                      + f"   ({time.time() - t0:.0f}s)", flush=True)
    out = Path(args.out) / f"external_{name}.json"
    out.write_text(json.dumps(result, indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
