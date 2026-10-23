"""Synthetic spike populations with planted stimulus codes.

Spikes are generated at 1 ms resolution over a 250 ms window, then binned to
5 ms (T = 50). Each code type plants stimulus information at a known temporal
scale, so a correct multiscale tokenizer should reveal it at a known level.

Level bin widths (ms): L1 250, L2 125, L3 50, L4 25, L5 10, L6 5.

Code types
----------
rate
    Stimulus changes each unit's spike count. Time profile is flat and shared.
    Information is available at level 1.
timing (precision p)
    Equal expected counts and identical coarse PSTHs across stimuli. Each unit
    has a few "events" whose base times sit on a boundary of the width-p bin
    grid but never on a boundary of any coarser grid. Each stimulus shifts each
    event by +p/2 or -p/2, so the spike lands on one side of that boundary or the
    other. Bins of width p (or finer) see the shift. Coarser bins do not.
    p = 125 ms is the "response shape" code (early vs late in the window).
control (p = 2 ms)
    Same construction with shifts of +-1 ms around times that are not 5 ms
    boundaries. No level can resolve it.
mixed
    A weak rate code plus a 10 ms timing code.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

WINDOW_MS = 250
BIN_MS = 5
T = WINDOW_MS // BIN_MS  # 50
LEVEL_LENGTHS = (1, 2, 5, 10, 25, 50)
LEVEL_WIDTHS_MS = tuple(WINDOW_MS // L for L in LEVEL_LENGTHS)  # 250,125,50,25,10,5


@dataclass
class SynthConfig:
    code: str = "rate"  # rate | timing | control | mixed
    precision_ms: int = 10  # used by timing
    n_units: int = 60
    n_stimuli: int = 16
    trials_per_stim: int = 100
    background_hz: float = 8.0
    event_prob: float = 0.7  # chance an event emits a spike on a given trial
    jitter_frac: float = 0.15  # event jitter sd as a fraction of p (timing codes)
    events_per_unit: int = 3
    rate_gain_sd: float = 0.35  # log-normal sd of per-stimulus gain (rate code)
    seed: int = 0


def _valid_event_times(p_ms: int, jitter_frac: float = 0.15) -> np.ndarray:
    """Times (ms) on the width-p grid whose whole shift-plus-jitter range avoids coarser boundaries.

    An event at t is shifted to t +- p/2 and jittered with sd = jitter_frac * p.
    If any boundary of a coarser level's grid falls inside that range, the
    coarser level could see the shift, so such times are rejected.
    """
    coarser = [w for w in LEVEL_WIDTHS_MS if w > p_ms]
    reach = p_ms / 2 + 3 * jitter_frac * p_ms
    times = []
    for t in range(p_ms, WINDOW_MS, p_ms):
        lo, hi = t - reach, t + reach
        if lo < 0 or hi > WINDOW_MS:
            continue
        hits_coarser = any(
            lo < b < hi for w in coarser for b in range(w, WINDOW_MS, w)
        )
        if not hits_coarser:
            times.append(t)
    return np.array(times, dtype=float)


def _control_event_times() -> np.ndarray:
    """Times midway between 5 ms boundaries, so a +-1 ms shift never crosses one."""
    return np.arange(2.5, WINDOW_MS, BIN_MS)[2:-2]


def _poisson_background(rng, n_trials, n_units, rate_hz, gain=None):
    lam = rate_hz / 1000.0  # per ms
    if gain is None:
        lam_arr = np.full((n_trials, n_units, WINDOW_MS), lam)
    else:
        lam_arr = (lam * gain)[:, :, None] * np.ones((1, 1, WINDOW_MS))
    return rng.poisson(lam_arr)


def _add_events(rng, spikes_ms, base_times, shifts, cfg, sd_ms):
    """Add one spike per event with probability event_prob, jittered by sd_ms.

    spikes_ms: (trials, units, 250) int array, modified in place.
    base_times: (units, events) ms.
    shifts: (trials, units, events) ms, already resolved per trial's stimulus.
    """
    n_trials, n_units, _ = spikes_ms.shape
    n_events = base_times.shape[1]
    emit = rng.random((n_trials, n_units, n_events)) < cfg.event_prob
    times = base_times[None] + shifts + rng.normal(0, sd_ms, (n_trials, n_units, n_events))
    times = np.clip(np.floor(times).astype(int), 0, WINDOW_MS - 1)
    tr, un, ev = np.nonzero(emit)
    np.add.at(spikes_ms, (tr, un, times[tr, un, ev]), 1)


def generate(cfg: SynthConfig, return_ms: bool = False):
    """Return counts (trials, units, T) at 5 ms bins and stimulus labels (trials,).

    With return_ms=True, also return the 1 ms spike counts (trials, units, 250),
    which the jitter control needs.
    """
    rng = np.random.default_rng(cfg.seed)
    labels = np.repeat(np.arange(cfg.n_stimuli), cfg.trials_per_stim)
    n_trials = labels.size

    if cfg.code == "rate":
        gain_su = np.exp(rng.normal(0, cfg.rate_gain_sd, (cfg.n_stimuli, cfg.n_units)))
        gain = gain_su[labels]
        spikes = _poisson_background(rng, n_trials, cfg.n_units, cfg.background_hz * 2.5, gain)

    elif cfg.code in ("timing", "control", "mixed"):
        if cfg.code == "control":
            grid = _control_event_times()
            half_shift = 1.0
            sd = 0.3
        else:
            p = 10 if cfg.code == "mixed" else cfg.precision_ms
            grid = _valid_event_times(p)
            half_shift = p / 2.0
            sd = cfg.jitter_frac * p
        if grid.size == 0:
            raise ValueError(f"no valid event times for precision {cfg.precision_ms}")
        k = min(cfg.events_per_unit, grid.size)
        base = np.stack([rng.choice(grid, size=k, replace=False) for _ in range(cfg.n_units)])
        sign_su = rng.choice([-1.0, 1.0], size=(cfg.n_stimuli, cfg.n_units, k))
        shifts = half_shift * sign_su[labels]

        gain = None
        if cfg.code == "mixed":
            gain_su = np.exp(rng.normal(0, cfg.rate_gain_sd * 0.4, (cfg.n_stimuli, cfg.n_units)))
            gain = gain_su[labels]
        spikes = _poisson_background(rng, n_trials, cfg.n_units, cfg.background_hz, gain)
        _add_events(rng, spikes, base, shifts, cfg, sd)
    else:
        raise ValueError(f"unknown code {cfg.code}")

    counts = spikes.reshape(n_trials, cfg.n_units, T, BIN_MS).sum(-1).astype(np.float32)
    if return_ms:
        return counts, labels, spikes.astype(np.int16)
    return counts, labels


def suite() -> list[SynthConfig]:
    """The E2 condition set from the plan."""
    out = [SynthConfig(code="rate")]
    for p in (125, 50, 25, 10, 5):
        out.append(SynthConfig(code="timing", precision_ms=p))
    out.append(SynthConfig(code="mixed"))
    out.append(SynthConfig(code="control", precision_ms=2))
    return out


def expected_level(cfg: SynthConfig) -> int | None:
    """1-indexed level whose bin width matches the planted precision (None for control)."""
    if cfg.code == "rate":
        return 1
    if cfg.code == "control":
        return None
    p = 10 if cfg.code == "mixed" else cfg.precision_ms
    return LEVEL_WIDTHS_MS.index(p) + 1
