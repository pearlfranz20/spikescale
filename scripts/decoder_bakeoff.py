"""Decoder bake-off on the continuous pyramid, Allen VISp 732592105.

Question: which decoder gives a per-level curve that measures information and
not capacity, and which gives the highest accuracy? Time-blocked split, 60 and
113 units, levels L1..L6.
"""
import sys, time, json
import numpy as np
from joblib import Parallel, delayed
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from spikescale.decode import blocked_split, pool_counts
from spikescale.synth import LEVEL_LENGTHS

d = np.load(sys.argv[2] if len(sys.argv) > 2 else "data/allen_732592105_VISp.npz")
counts_all, labels = d["counts"], d["labels"]
tr, te = blocked_split(len(labels), labels)
# inner blocked split of the training set for nested CV (last 10 of the 40 training repeats)
tr_idx = np.nonzero(tr)[0]
itr_mask, ite_mask = blocked_split(len(tr_idx), labels[tr_idx], test_frac=0.25)
C_GRID = [0.003, 0.01, 0.03, 0.1, 0.3, 1.0]


def multiscale_basis(T=50):
    """Orthonormal basis of R^T whose first L_k vectors span the level-k block indicators."""
    vecs = []
    for L in LEVEL_LENGTHS:
        w = T // L
        for j in range(L):
            v = np.zeros(T); v[j * w:(j + 1) * w] = 1.0
            vecs.append(v)
    B = []
    for v in vecs:
        for b in B:
            v = v - (v @ b) * b
        n = np.linalg.norm(v)
        if n > 1e-8:
            B.append(v / n)
    B = np.stack(B, 1)
    assert B.shape == (T, T)
    return B


B = multiscale_basis()


def feats_for(counts):
    n = len(counts)
    lvl = [np.log1p(pool_counts(counts, L)).reshape(n, -1) for L in LEVEL_LENGTHS]
    cum = [np.concatenate(lvl[:k + 1], 1) for k in range(6)]
    raw = [pool_counts(counts, L).reshape(n, -1) for L in LEVEL_LENGTHS]  # for Poisson NB
    sq = np.sqrt(counts.astype(float)) @ B  # (n, u, T) variance-stabilised, multiscale coords
    haar = [sq[:, :, :L].reshape(n, -1) for L in LEVEL_LENGTHS]
    return lvl, cum, raw, haar


def poisson_nb(xtr, ytr, xte, alpha=0.5):
    classes = np.unique(ytr)
    rates = np.stack([(xtr[ytr == c].sum(0) + alpha) / ((ytr == c).sum() + alpha) for c in classes])  # (C, F)
    ll = xte @ np.log(rates).T - rates.sum(1)[None, :]
    return classes[ll.argmax(1)]


def template_corr(xtr, ytr, xte):
    classes = np.unique(ytr)
    mu, sd = xtr.mean(0), xtr.std(0) + 1e-6
    ztr, zte = (xtr - mu) / sd, (xte - mu) / sd
    T = np.stack([ztr[ytr == c].mean(0) for c in classes])
    Tn = T / (np.linalg.norm(T, axis=1, keepdims=True) + 1e-9)
    zn = zte / (np.linalg.norm(zte, axis=1, keepdims=True) + 1e-9)
    return classes[(zn @ Tn.T).argmax(1)]


def acc(pred, y):
    return float((pred == y).mean())


def run(full, k, xtr, ytr, xte, yte):
    t0 = time.time()
    fam, name = full.split("/")
    if name == "logreg_C0.1":
        m = make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=3000)).fit(xtr, ytr)
        a = m.score(xte, yte)
    elif name == "pca100_logreg":
        m = make_pipeline(StandardScaler(), PCA(min(100, xtr.shape[1], len(xtr) - 1), random_state=0),
                          LogisticRegression(C=0.1, max_iter=3000)).fit(xtr, ytr)
        a = m.score(xte, yte)
    elif name == "nested_logreg":
        # choose C on an inner blocked split of the training set, refit on all training trials
        best, bestc = -1, None
        for c in C_GRID:
            m = make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=3000)).fit(xtr[itr_mask], ytr[itr_mask])
            s = m.score(xtr[ite_mask], ytr[ite_mask])
            if s > best:
                best, bestc = s, c
        m = make_pipeline(StandardScaler(), LogisticRegression(C=bestc, max_iter=3000)).fit(xtr, ytr)
        a = m.score(xte, yte)
        name = f"{name}(C={bestc})"
    elif name == "lda_shrink":
        m = make_pipeline(StandardScaler(), LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")).fit(xtr, ytr)
        a = m.score(xte, yte)
    elif name == "pca100_lda_shrink":
        m = make_pipeline(StandardScaler(), PCA(min(100, xtr.shape[1], len(xtr) - 1), random_state=0),
                          LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")).fit(xtr, ytr)
        a = m.score(xte, yte)
    elif name == "gauss_nb":
        m = make_pipeline(StandardScaler(), GaussianNB(var_smoothing=1e-2)).fit(xtr, ytr)
        a = m.score(xte, yte)
    elif name == "poisson_nb":
        a = acc(poisson_nb(xtr, ytr, xte), yte)
    elif name == "template_corr":
        a = acc(template_corr(xtr, ytr, xte), yte)
    elif name == "pls50_lda":
        sc = StandardScaler().fit(xtr)
        Y = np.eye(118)[ytr]
        pls = PLSRegression(n_components=min(50, xtr.shape[1]), scale=False).fit(sc.transform(xtr), Y)
        ztr, zte = pls.transform(sc.transform(xtr)), pls.transform(sc.transform(xte))
        m = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto").fit(ztr, ytr)
        a = m.score(zte, yte)
    else:
        raise ValueError(name)
    return f"{fam}/{name}", k, a, time.time() - t0


def main(n_units):
    rng = np.random.default_rng(0)
    counts = counts_all
    if n_units < counts.shape[1]:
        counts = counts[:, np.sort(rng.choice(counts.shape[1], n_units, replace=False))]
    lvl, cum, raw, haar = feats_for(counts)
    jobs = []
    for k in range(6):
        for fam, F in (("level", lvl), ("cum", cum), ("haar", haar)):
            for dec in ("logreg_C0.1", "pca100_logreg", "nested_logreg", "lda_shrink", "pca100_lda_shrink",
                        "gauss_nb", "template_corr", "pls50_lda"):
                if fam == "haar" and dec not in ("logreg_C0.1", "nested_logreg", "lda_shrink", "pca100_logreg"):
                    continue
                jobs.append((f"{fam}/{dec}", k, F[k]))
        jobs.append(("level/poisson_nb", k, raw[k]))
    res = Parallel(n_jobs=16)(delayed(run)(nm, k, F[tr], labels[tr], F[te], labels[te]) for nm, k, F in jobs)
    table = {}
    for nm, k, a, dt in res:
        base = nm.split("(")[0]
        table.setdefault(base, [None] * 6)[k] = (a, nm, dt)
    print(f"\n=== {counts.shape[1]} units, time-blocked, L1..L6 ===")
    for nm, row in sorted(table.items(), key=lambda kv: -max(x[0] for x in kv[1] if x)):
        accs = " ".join(f"{x[0]:.3f}" if x else "  -  " for x in row)
        extra = ""
        if "nested" in nm:
            extra = "  C=" + ",".join(x[1].split("C=")[1].rstrip(")") if x else "-" for x in row)
        tsum = sum(x[2] for x in row if x)
        print(f"{nm:28s} {accs}   ({tsum:.0f}s){extra}")
    return table


if __name__ == "__main__":
    out = {}
    for nu in (60, 113):
        t = main(nu)
        out[nu] = {k: [x[0] if x else None for x in v] for k, v in t.items()}
    json.dump(out, open(sys.argv[1], "w"), indent=1)
