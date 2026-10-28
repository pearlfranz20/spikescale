"""Trial-averaged PCA (projection fit on class means, not single trials) + logistic, nested C."""
import sys
import numpy as np
from joblib import Parallel, delayed
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from spikescale.decode import blocked_split, pool_counts
from spikescale.synth import LEVEL_LENGTHS

d = np.load(sys.argv[1] if len(sys.argv) > 1 else "data/allen_732592105_VISp.npz")
counts_all, labels = d["counts"], d["labels"]
tr, te = blocked_split(len(labels), labels)
tr_idx = np.nonzero(tr)[0]
itr, ite = blocked_split(len(tr_idx), labels[tr_idx], test_frac=0.25)
C_GRID = [0.003, 0.01, 0.03, 0.1, 0.3, 1.0]


def tapca_fit(x, y, n_comp):
    sc = StandardScaler().fit(x)
    z = sc.transform(x)
    means = np.stack([z[y == c].mean(0) for c in np.unique(y)])
    means -= means.mean(0)
    _, _, vt = np.linalg.svd(means, full_matrices=False)
    W = vt[:n_comp].T
    return sc, W


def fit_score(xtr, ytr, xte, yte, n_comp, c):
    sc, W = tapca_fit(xtr, ytr, n_comp)
    m = LogisticRegression(C=c, max_iter=3000).fit(sc.transform(xtr) @ W, ytr)
    return m.score(sc.transform(xte) @ W, yte)


def nested(xtr, ytr, xte, yte, n_comp):
    best = max(C_GRID, key=lambda c: fit_score(xtr[itr], ytr[itr], xtr[ite], ytr[ite], n_comp, c))
    return fit_score(xtr, ytr, xte, yte, n_comp, best), best


def main(n_units):
    rng = np.random.default_rng(0)
    counts = counts_all
    if n_units < counts.shape[1]:
        counts = counts[:, np.sort(rng.choice(counts.shape[1], n_units, replace=False))]
    n = len(counts)
    lvl = [np.log1p(pool_counts(counts, L)).reshape(n, -1) for L in LEVEL_LENGTHS]
    cum = [np.concatenate(lvl[:k + 1], 1) for k in range(6)]
    jobs = [(fam, k, n_comp) for fam in ("level", "cum") for k in range(6) for n_comp in (50, 117)]
    F = {"level": lvl, "cum": cum}
    res = Parallel(n_jobs=12)(delayed(nested)(F[fam][k][tr], labels[tr], F[fam][k][te], labels[te], nc)
                              for fam, k, nc in jobs)
    print(f"\n=== {counts.shape[1]} units, time-blocked, taPCA + nested logistic ===")
    for fam in ("level", "cum"):
        for nc in (50, 117):
            row = [(a, c) for (f, k, n), (a, c) in zip(jobs, res) if f == fam and n == nc]
            print(f"{fam}/tapca{nc}_nested_logreg".ljust(28) + " ".join(f"{a:.3f}" for a, _ in row)
                  + "   C=" + ",".join(str(c) for _, c in row))


for nu in (60, 113):
    main(nu)
