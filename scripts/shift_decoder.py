"""Is fine timing masked by trial-to-trial latency shifts? A shift-invariant template decoder.

Every fixed-bin decoder compares spikes in the same absolute bins on every
trial. If the whole population responds a few ms earlier on one trial than
on another, information in 5 to 10 ms structure is smeared out for such a
decoder, however much data it has. This decoder searches over one common
time shift per trial and image instead:

    score_k(x) = max over d of  log N(x shifted by d ; mu_k, diag var) + log prior(d)

where mu_k is image k's mean response (on training trials aligned to their
own image's template, three rounds) and the variance is the pooled residual
variance per unit and bin. The same decoder with d fixed at 0 is a Gaussian
naive Bayes, the control. Window: 200 ms starting at 25 ms (so shifts of up
to 20 ms stay inside the recorded 0 to 250 ms), log1p counts in bins of
--width ms.

    PYTHONPATH=. python scripts/shift_decoder.py --jobs 8
Output: results/shift_decoder.json  {recording: {width: {"fixed": acc, "shift": acc, "sd_shift": ms}}}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spikescale.decode import blocked_split  # noqa: E402

W0, T = 25, 200
WIDTHS = (50, 25, 10, 5)


def windows(sp, shifts, width):
    """log1p binned counts for every shift: (n_shift, trials, units * T / width)."""
    cs = np.concatenate([np.zeros(sp.shape[:2] + (1,), np.int32), np.cumsum(sp, 2, dtype=np.int32)], 2)
    edges = np.arange(0, T + 1, width)
    out = []
    for d in shifts:
        e = cs[:, :, W0 + d + edges]
        out.append(np.log1p(np.diff(e, axis=2)).reshape(len(sp), -1).astype(np.float32))
    return np.stack(out)


def fit(xs, y, shifts, n_cls, align):
    """Templates and variance from training windows xs (n_shift, n, f); optionally align each trial to its template."""
    i0 = list(shifts).index(0)
    d_idx = np.full(len(y), i0)
    for _ in range(3 if align else 1):
        x = xs[d_idx, np.arange(len(y))]
        mu = np.stack([x[y == c].mean(0) for c in range(n_cls)])
        var = ((x - mu[y]) ** 2).mean(0) + 1e-3
        if not align:
            break
        ll = -0.5 * (((xs - mu[y][None]) ** 2) / var).sum(-1)  # (n_shift, n)
        ll = ll - 1e-6 * np.abs(np.asarray(shifts))[:, None]  # ties (e.g. trials without spikes) go to no shift
        d_idx = ll.argmax(0)
    sd = float(np.std(np.asarray(shifts)[d_idx]))
    return mu, var, sd


def scores(xs, mu, var, logprior):
    """max over shifts of the diagonal Gaussian log likelihood, per trial and image."""
    iv = 1 / var
    best = None
    for s in range(len(xs)):
        x = xs[s]
        ll = -0.5 * (((x ** 2) @ iv)[:, None] - 2 * x @ (mu * iv).T + ((mu ** 2) @ iv)[None]) + logprior[s]
        best = ll if best is None else np.maximum(best, ll)
    return best


def run(path, max_shift):
    d = np.load(path)
    sp, y = d["spikes_ms"], d["labels"]
    tr, te = blocked_split(len(y), y)
    shifts = np.arange(-max_shift, max_shift + 1)
    out = {}
    for w in WIDTHS:
        xs = windows(sp, shifts, w)
        i0 = list(shifts).index(0)
        mu, var, _ = fit(xs[:, tr], y[tr], shifts, 118, align=False)
        fixed = float((scores(xs[i0:i0 + 1, te], mu, var, [0.0]).argmax(1) == y[te]).mean())
        mu, var, sd = fit(xs[:, tr], y[tr], shifts, 118, align=True)
        logprior = -0.5 * (shifts / max(sd, 1.0)) ** 2
        shift = float((scores(xs[:, te], mu, var, logprior).argmax(1) == y[te]).mean())
        out[w] = {"fixed": fixed, "shift": shift, "sd_shift": sd}
    name = Path(path).stem.replace("allen_", "")
    print(name, " ".join(f"{w}:{o['fixed']:.3f}->{o['shift']:.3f}(sd{o['sd_shift']:.1f})" for w, o in out.items()), flush=True)
    return name, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--max-shift", type=int, default=20)
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    files = sorted(str(f) for f in Path("data").glob("allen_*_*.npz")
                   if len(f.stem.split("_")) == 3 and f.stem.split("_")[2] != "state")
    if args.only:
        files = [f for f in files if any(o in f for o in args.only.split(","))]
    res = Parallel(n_jobs=args.jobs)(delayed(run)(f, args.max_shift) for f in files)
    if not args.only:
        Path("results/shift_decoder.json").write_text(json.dumps(dict(res), indent=1))
        print("wrote results/shift_decoder.json")


if __name__ == "__main__":
    main()
