"""Low-rank Poisson template decoder: can fine bins be read once the templates are not noise?

A Bayes decoder needs each image's mean response per unit and time bin. At
5 ms that is 118 x units x 50 rates from about 40 trials per image, mostly
noise, so fine bins look uninformative to any template or linear decoder.
This decoder estimates the rates with low-rank structure instead:

    log rate[k, u, t] = b[u, t] + sum_r a[k, u, r] * phi[u, r, t]

Each unit has its own image-independent time course b and R temporal shapes
phi; images differ only in how strongly they drive each shape. Parameters
per unit: (R + 1) * T + 118 * R instead of 118 * T. Fitted by maximum Poisson
likelihood (L2 on a and phi) from the per-image summed counts, which are
sufficient statistics.

Decoding: argmax_k of the Poisson log likelihood of a test trial's counts.
With --gain the likelihood is profiled over one multiplicative gain per
trial (all units' rates scaled together), which turns it into a multinomial
over units and bins: only the pattern is read, not the overall rate.

Control: full-rank rates shrunk toward each unit's image-independent time
course, rate = (S + alpha * m) / (N + alpha), a Poisson naive Bayes.

R, the L2 weight, alpha and gain on/off are chosen on the inner
time-blocked split, as the logistic's C is; the chosen model is refitted on
all training trials and scored once on the test trials.

    .venv-gpu/Scripts/python.exe scripts/tensor_decoder.py --only 732592105_VISp
Output: results/tensor_decoder.json  {recording: {width: {"lowrank": acc, "fullrank": acc, "choice": ...}}}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spikescale.decode import blocked_split  # noqa: E402

WIDTHS = (250, 125, 50, 25, 10, 5)
RANKS = (1, 2, 3, 5, 8)
L2S = (1e-3, 1e-2)
ALPHAS = (0.5, 1, 2, 5, 10, 20)
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def suff(x, y, n_cls=118):
    """Summed counts per image (K, U, T) and trials per image (K,)."""
    S = torch.zeros((n_cls,) + x.shape[1:], device=DEV).index_add_(0, y, x)
    N = torch.bincount(y, minlength=n_cls).float()
    return S, N


def fit_lowrank(S, N, R, l2, steps=600, seed=0):
    g = torch.Generator(device=DEV).manual_seed(seed)
    K, U, T = S.shape
    m = (S.sum(0) / N.sum()).clamp_min(1e-4)
    b = m.log().clone().requires_grad_(True)
    a = (0.1 * torch.randn(K, U, R, device=DEV, generator=g)).requires_grad_(True)
    phi = (0.1 * torch.randn(U, R, T, device=DEV, generator=g)).requires_grad_(True)
    opt = torch.optim.Adam([b, a, phi], lr=0.05)
    n_tot = N.sum()
    for i in range(steps):
        eta = b + torch.einsum("kur,urt->kut", a, phi)
        nll = (-(S * eta).sum() + (N[:, None, None] * eta.exp()).sum()) / n_tot
        loss = nll + l2 * (a.pow(2).sum() / K + phi.pow(2).sum() / T) / 1.0
        opt.zero_grad()
        loss.backward()
        opt.step()
    with torch.no_grad():
        return b + torch.einsum("kur,urt->kut", a, phi)


def fit_fullrank(S, N, alpha):
    m = S.sum(0) / N.sum()
    return ((S + alpha * m) / (N[:, None, None] + alpha)).clamp_min(1e-6).log()


def loglik(x, eta, gain):
    """Poisson log likelihood (up to terms constant in k): (n, K)."""
    xf = x.reshape(len(x), -1)
    e = eta.reshape(len(eta), -1)
    lin = xf @ e.T
    lam = e.exp().sum(1)
    if gain:  # profile a per-trial gain g: max_g sum x log(g lam) - g Lam  ->  -tot * log Lam (+ const)
        return lin - xf.sum(1, keepdim=True) * lam.log()[None]
    return lin - lam[None]


def acc(x, y, eta, gain):
    return float((loglik(x, eta, gain).argmax(1) == y).float().mean())


def run(path):
    d = np.load(path)
    sp, y_np = d["spikes_ms"], d["labels"].astype(np.int64)
    n, U, _ = sp.shape
    tr, te = blocked_split(n, y_np)
    tri = np.nonzero(tr)[0]
    itr, iva = blocked_split(len(tri), y_np[tri], test_frac=0.25)
    idx = {k: torch.as_tensor(v, device=DEV) for k, v in
           {"tr": np.nonzero(tr)[0], "te": np.nonzero(te)[0], "itr": tri[itr], "iva": tri[iva]}.items()}
    y = torch.as_tensor(y_np, device=DEV)
    out = {}
    for w in WIDTHS:
        x = torch.as_tensor(sp.reshape(n, U, 250 // w, w).sum(-1), dtype=torch.float32, device=DEV)
        Si, Ni = suff(x[idx["itr"]], y[idx["itr"]])
        xv, yv = x[idx["iva"]], y[idx["iva"]]
        # low rank: choose (R, l2, gain) on the inner split
        best = (-1, None)
        for R in RANKS:
            if R > 250 // w:
                continue
            for l2 in L2S:
                eta = fit_lowrank(Si, Ni, R, l2)
                for gain in (False, True):
                    v = acc(xv, yv, eta, gain)
                    if v > best[0]:
                        best = (v, (R, l2, gain))
        R, l2, gain = best[1]
        S, N = suff(x[idx["tr"]], y[idx["tr"]])
        low = acc(x[idx["te"]], y[idx["te"]], fit_lowrank(S, N, R, l2), gain)
        # full rank control
        bestf = (-1, None)
        for al in ALPHAS:
            eta = fit_fullrank(Si, Ni, al)
            for gain_f in (False, True):
                v = acc(xv, yv, eta, gain_f)
                if v > bestf[0]:
                    bestf = (v, (al, gain_f))
        al, gain_f = bestf[1]
        full = acc(x[idx["te"]], y[idx["te"]], fit_fullrank(S, N, al), gain_f)
        out[w] = {"lowrank": low, "fullrank": full, "rank": R, "l2": l2, "gain": gain,
                  "alpha": al, "gain_full": gain_f, "val_lowrank": best[0], "val_fullrank": bestf[0]}
        print(f"  {Path(path).stem} {w} ms: low-rank {low:.3f} (R {R}, l2 {l2}, gain {gain})  "
              f"full-rank {full:.3f} (alpha {al}, gain {gain_f})", flush=True)
    return Path(path).stem.replace("allen_", ""), out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default="results/tensor_decoder.json")
    args = ap.parse_args()
    files = sorted(str(f) for f in Path("data").glob("allen_*_*.npz")
                   if len(f.stem.split("_")) == 3 and f.stem.split("_")[2] != "state")
    if args.only:
        files = [f for f in files if any(o in f for o in args.only.split(","))]
    res = dict(run(f) for f in files)
    Path(args.out).write_text(json.dumps(res, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
