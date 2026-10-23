"""Per-level decoding: one fixed decoder for every level and every feature set."""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .synth import LEVEL_LENGTHS


def blocked_split(n_trials: int, labels: np.ndarray, test_frac: float = 0.2, seed: int = 0):
    """Hold out a contiguous block of repeats per stimulus.

    Trials are assumed ordered in time within each stimulus. The last
    test_frac of each stimulus's repeats form the test set, so every test
    block contains every stimulus.
    """
    test = np.zeros(n_trials, dtype=bool)
    for s in np.unique(labels):
        idx = np.nonzero(labels == s)[0]
        n_test = max(1, int(round(test_frac * idx.size)))
        test[idx[-n_test:]] = True
    return ~test, test


def pool_counts(counts: np.ndarray, length: int) -> np.ndarray:
    """Sum counts (trials, units, T) into `length` equal bins."""
    n, u, t = counts.shape
    return counts.reshape(n, u, length, t // length).sum(-1)


def fit_clf(x_train, y_train, c: float = 1.0):
    clf = make_pipeline(
        StandardScaler(),
        LogisticRegression(C=c, max_iter=3000),
    )
    clf.fit(x_train.reshape(len(x_train), -1), y_train)
    return clf


def score(clf, x, y) -> float:
    return float(clf.score(x.reshape(len(x), -1), y))


def fit_decode(x_train, y_train, x_test, y_test, c: float = 1.0) -> float:
    return score(fit_clf(x_train, y_train, c), x_test, y_test)


def quantized_pyramid_features(counts, train, codebook_sizes, seed: int = 0):
    """Matched-bits, no-learning baseline: residual k-means on pooled log-counts.

    Same level lengths and codebook sizes as the tokenizer, but the "encoder"
    is the identity on log1p counts and each codebook is plain k-means fit on
    training trials. Returns, for each level k, the cumulative reconstruction
    pooled to L_k (trials, units * L_k).
    """
    from sklearn.cluster import MiniBatchKMeans

    x = np.log1p(counts).astype(np.float32)  # (trials, units, T)
    n, u, t = x.shape
    recon = np.zeros_like(x)
    feats = []
    for L, V in zip(LEVEL_LENGTHS, codebook_sizes):
        resid = x - recon
        pooled = resid.reshape(n, u, L, t // L).mean(-1)  # (n, u, L)
        vecs = pooled.transpose(0, 2, 1).reshape(n * L, u)
        train_vecs = vecs.reshape(n, L, u)[train].reshape(-1, u)
        km = MiniBatchKMeans(n_clusters=V, random_state=seed, n_init=3, batch_size=2048)
        km.fit(train_vecs)
        q = km.cluster_centers_[km.predict(vecs)].reshape(n, L, u).transpose(0, 2, 1)
        recon = recon + np.repeat(q, t // L, axis=2)
        feats.append(recon.reshape(n, u, L, t // L).mean(-1).reshape(n, -1))
    return feats


def pyramid_curve(counts, labels, train, test, c: float = 1.0) -> list[float]:
    """Binning-pyramid baseline: counts pooled to each level length, same decoder."""
    accs = []
    for length in LEVEL_LENGTHS:
        feats = np.log1p(pool_counts(counts, length))
        accs.append(fit_decode(feats[train], labels[train], feats[test], labels[test], c))
    return accs
