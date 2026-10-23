"""E3b controls on 1 ms spike arrays (trials, units, 250).

jitter_spikes
    Move every spike by uniform noise in [-j, +j] ms, reflecting at the window
    edges so no spikes are lost. Destroys timing finer than about j ms and
    keeps counts.
psth_matched_surrogate
    For each unit, shuffle trials within each stimulus. Each unit keeps its
    exact spike trains and so its PSTH per stimulus, but trial-by-trial
    coordination across units is broken.
"""
from __future__ import annotations

import numpy as np

from .synth import BIN_MS, WINDOW_MS


def _reflect(t: np.ndarray, length: int) -> np.ndarray:
    period = 2 * length
    t = np.mod(t, period)
    return np.where(t >= length, period - 1 - t, t)


def jitter_spikes(spikes_ms: np.ndarray, j_ms: float, rng: np.random.Generator) -> np.ndarray:
    if j_ms <= 0:
        return spikes_ms.copy()
    n, u, w = spikes_ms.shape
    tr, un, tt = np.nonzero(spikes_ms)
    reps = spikes_ms[tr, un, tt]
    tr, un, tt = np.repeat(tr, reps), np.repeat(un, reps), np.repeat(tt, reps)
    new_t = tt + rng.uniform(-j_ms, j_ms, size=tt.size)
    new_t = _reflect(np.floor(new_t).astype(int), w)
    out = np.zeros_like(spikes_ms)
    np.add.at(out, (tr, un, new_t), 1)
    return out


def psth_matched_surrogate(spikes_ms: np.ndarray, labels: np.ndarray,
                           rng: np.random.Generator) -> np.ndarray:
    out = np.empty_like(spikes_ms)
    for s in np.unique(labels):
        idx = np.nonzero(labels == s)[0]
        for u in range(spikes_ms.shape[1]):
            out[idx, u] = spikes_ms[rng.permutation(idx), u]
    return out


def bin_ms(spikes_ms: np.ndarray, bin_ms: int = BIN_MS) -> np.ndarray:
    n, u, w = spikes_ms.shape
    assert w == WINDOW_MS
    return spikes_ms.reshape(n, u, w // bin_ms, bin_ms).sum(-1).astype(np.float32)
