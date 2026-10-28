"""Per-level decoding: one fixed decoder for every level and every feature set."""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA
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


def fit_clf(x_train, y_train, c: float = 1.0, n_pca: int = 0):
    """Standardize, optionally project to n_pca components, then L2 logistic.

    n_pca caps decoder capacity at fine levels, where the raw feature count
    (units * L_k) can exceed the number of training trials per class many
    times over. The PCA is fit on training trials only.
    """
    x = x_train.reshape(len(x_train), -1)
    steps = [StandardScaler()]
    if n_pca:
        steps.append(PCA(n_components=min(n_pca, x.shape[1], len(x) - 1), random_state=0))
    steps.append(LogisticRegression(C=c, max_iter=3000))
    clf = make_pipeline(*steps)
    clf.fit(x, y_train)
    return clf


C_GRID = (0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0)


def fit_clf_nested(x_train, y_train, c_grid=C_GRID, n_pca: int = 0, inner_frac: float = 0.25,
                   n_jobs: int = 1):
    """fit_clf with C chosen per call on an inner time-blocked split of the training set.

    The last inner_frac of each stimulus's training repeats are held out, every
    C in c_grid is scored on them, and the best C is refit on all training
    trials. With the per-level feature count varying 50-fold across levels, a
    fixed C under- or over-regularizes somewhere; choosing it per level makes
    the per-level curve capacity-matched by construction (notes/decoder_bakeoff.md).
    Returns (clf, chosen_c).
    """
    from joblib import Parallel, delayed

    itr, ite = blocked_split(len(y_train), y_train, test_frac=inner_frac)
    scores = Parallel(n_jobs=n_jobs)(
        delayed(fit_decode)(x_train[itr], y_train[itr], x_train[ite], y_train[ite], c, n_pca)
        for c in c_grid)
    best = c_grid[int(np.argmax(scores))]
    return fit_clf(x_train, y_train, best, n_pca), best


def score(clf, x, y) -> float:
    return float(clf.score(x.reshape(len(x), -1), y))


def fit_decode(x_train, y_train, x_test, y_test, c: float = 1.0, n_pca: int = 0) -> float:
    return score(fit_clf(x_train, y_train, c, n_pca), x_test, y_test)


class QuantizedPyramid:
    """Matched-bits, no-learning baseline: residual k-means on pooled log-counts.

    Same level lengths and codebook sizes as the tokenizer, but the "encoder"
    is the identity on log1p counts and each codebook is plain k-means fit on
    training trials. `transform` returns, for each level k, the cumulative
    reconstruction pooled to L_k (trials, units * L_k), the same readout as
    the tokenizer's code features.
    """

    def __init__(self, codebook_sizes, seed: int = 0):
        self.codebook_sizes = tuple(codebook_sizes)
        self.seed = seed
        self.kms = []

    def _residual_levels(self, counts, fit: bool):
        from sklearn.cluster import MiniBatchKMeans

        x = np.log1p(counts).astype(np.float32)  # (trials, units, T)
        n, u, t = x.shape
        recon = np.zeros_like(x)
        feats = []
        for k, (L, V) in enumerate(zip(LEVEL_LENGTHS, self.codebook_sizes)):
            resid = x - recon
            pooled = resid.reshape(n, u, L, t // L).mean(-1)  # (n, u, L)
            vecs = pooled.transpose(0, 2, 1).reshape(n * L, u)
            if fit:
                km = MiniBatchKMeans(n_clusters=V, random_state=self.seed, n_init=3, batch_size=2048)
                km.fit(vecs)
                self.kms.append(km)
            km = self.kms[k]
            q = km.cluster_centers_[km.predict(vecs)].reshape(n, L, u).transpose(0, 2, 1)
            recon = recon + np.repeat(q, t // L, axis=2)
            feats.append(recon.reshape(n, u, L, t // L).mean(-1).reshape(n, -1))
        return feats

    def fit(self, counts_train):
        self.kms = []
        self._residual_levels(counts_train, fit=True)
        return self

    def transform(self, counts):
        return self._residual_levels(counts, fit=False)


def quantized_pyramid_features(counts, train, codebook_sizes, seed: int = 0):
    """Fit the quantized pyramid on `train` trials and return features for all trials."""
    return QuantizedPyramid(codebook_sizes, seed).fit(counts[train]).transform(counts)


def pyramid_curve(counts, labels, train, test, c: float = 1.0) -> list[float]:
    """Binning-pyramid baseline: counts pooled to each level length, same decoder."""
    accs = []
    for length in LEVEL_LENGTHS:
        feats = np.log1p(pool_counts(counts, length))
        accs.append(fit_decode(feats[train], labels[train], feats[test], labels[test], c))
    return accs
