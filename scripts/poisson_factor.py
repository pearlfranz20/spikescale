"""Poisson factor decoder: low-rank image templates plus shared per-trial latent factors.

    log rate[n, u, t] = b[u, t] + sum_r a[y_n, u, r] phi[u, r, t] + sum_j z[n, j] L[u, t, j],   z_n ~ N(0, I)

The image part is the low-rank template of tensor_decoder.py: each unit has
an image-independent time course b and R temporal shapes phi, and images
differ only in how strongly they drive each shape. The latent part models
trial-to-trial variability shared across units and bins (gain, state,
correlated noise) with J factors L. All parameters and the training trials'
z are fitted jointly by MAP (Adam, L2 on a, phi and L, unit Gaussian prior
on z) on the Poisson likelihood of the counts.

Decoding: for each test trial and image k, z is found by Newton's method,
and the image is scored by the Laplace approximation to the marginal
likelihood, log p(x | k) ~ log p(x | z*, k) + log p(z*) - 0.5 log det H.
Images have equal priors.

R and J are chosen on the inner time-blocked split (last 25% of each image's
training repeats), the model is refitted on all training trials and scored
once on the test trials (last 20% of each image's repeats), as for every
other decoder here. Bins of --widths ms over 0 to 250 ms; spike counts, not
log counts.

    .venv-gpu/Scripts/python.exe scripts/poisson_factor.py
Output: results/poisson_factor.json  {recording: {width: {"acc", "R", "J", "val": {"R,J": acc}}}}
written after every recording; recordings already in the file are skipped.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spikescale.decode import blocked_split  # noqa: E402

DEV = torch.device("cuda")
K = 118


def fit(x, y, R, J, l2=1e-2, steps=1500, seed=0):
    """MAP fit on trials x (n, U, T) with labels y. Returns image log rates (K, U, T) and loadings (U, T, J) or None."""
    g = torch.Generator(device=DEV).manual_seed(seed)
    n, U, T = x.shape
    R = min(R, T)
    b = x.mean(0).clamp_min(1e-3).log().clone().requires_grad_(True)
    a = (0.1 * torch.randn(K, U, R, device=DEV, generator=g)).requires_grad_(True)
    phi = (0.1 * torch.randn(U, R, T, device=DEV, generator=g)).requires_grad_(True)
    params = [b, a, phi]
    if J:
        L = (0.01 * torch.randn(U, T, J, device=DEV, generator=g)).requires_grad_(True)
        z = torch.zeros(n, J, device=DEV, requires_grad=True)
        params += [L, z]
    opt = torch.optim.Adam(params, lr=0.03)
    for _ in range(steps):
        eta = b + torch.einsum("kur,urt->kut", a, phi)[y]
        if J:
            eta = eta + torch.einsum("nj,utj->nut", z, L)
        loss = ((eta.exp() - x * eta).sum() / n + l2 * (a.pow(2).sum() / K + phi.pow(2).sum() / T))
        if J:
            loss = loss + 0.5 * z.pow(2).sum() / n + l2 * L.pow(2).sum()
        opt.zero_grad()
        loss.backward()
        opt.step()
    with torch.no_grad():
        return (b + torch.einsum("kur,urt->kut", a, phi)).detach(), (L.detach() if J else None)


def loglik(x, eta, L, chunk=40, iters=8):
    """(n, K) Laplace log marginal likelihood of each trial under each image, up to constants."""
    n = len(x)
    xf, ef = x.reshape(n, -1), eta.reshape(K, -1)
    if L is None:
        return xf @ ef.T - ef.exp().sum(1)[None]
    Lf = L.reshape(-1, L.shape[-1])
    J = Lf.shape[1]
    eye = torch.eye(J, device=DEV)
    out = torch.empty(n, K, device=DEV)
    for i in range(0, n, chunk):
        xc = xf[i:i + chunk]
        z = torch.zeros(len(xc), K, J, device=DEV)
        for _ in range(iters):
            lam = (ef[None] + z @ Lf.T).exp()
            grad = (xc[:, None] - lam) @ Lf - z
            H = torch.einsum("ckd,dj,di->ckji", lam, Lf, Lf) + eye
            z = z + torch.linalg.solve(H, grad.unsqueeze(-1)).squeeze(-1)
        e = ef[None] + z @ Lf.T
        lam = e.exp()
        H = torch.einsum("ckd,dj,di->ckji", lam, Lf, Lf) + eye
        out[i:i + chunk] = (xc[:, None] * e).sum(-1) - lam.sum(-1) - 0.5 * z.pow(2).sum(-1) - 0.5 * torch.logdet(H)
    return out


def acc(x, y, eta, L):
    return float((loglik(x, eta, L).argmax(1) == y).float().mean())


def run(path, widths, ranks, factors):
    d = np.load(path)
    sp, yn = d["spikes_ms"], d["labels"].astype(np.int64)
    n, U, _ = sp.shape
    tr, te = blocked_split(n, yn)
    tri = np.nonzero(tr)[0]
    itr, iva = blocked_split(len(tri), yn[tri], test_frac=0.25)
    y = torch.as_tensor(yn, device=DEV)
    idx = {k: torch.as_tensor(v, device=DEV) for k, v in
           {"tr": np.nonzero(tr)[0], "te": np.nonzero(te)[0], "itr": tri[itr], "iva": tri[iva]}.items()}
    out = {}
    for w in widths:
        x = torch.as_tensor(sp.reshape(n, U, 250 // w, w).sum(-1), dtype=torch.float32, device=DEV)
        val = {}
        for R in sorted({min(r, 250 // w) for r in ranks}):
            for J in factors:
                val[f"{R},{J}"] = acc(x[idx["iva"]], y[idx["iva"]], *fit(x[idx["itr"]], y[idx["itr"]], R, J))
        R, J = (int(v) for v in max(val, key=val.get).split(","))
        a = acc(x[idx["te"]], y[idx["te"]], *fit(x[idx["tr"]], y[idx["tr"]], R, J))
        out[w] = {"acc": a, "R": R, "J": J, "val": val}
        print(f"  {Path(path).stem} {w} ms: {a:.3f} (R {R}, J {J})", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--widths", default="250,125,50,25,10,5")
    ap.add_argument("--ranks", default="2,3")
    ap.add_argument("--factors", default="4,8,16,32")
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default="results/poisson_factor.json")
    args = ap.parse_args()
    widths = [int(v) for v in args.widths.split(",")]
    ranks = [int(v) for v in args.ranks.split(",")]
    factors = [int(v) for v in args.factors.split(",")]
    files = sorted(str(f) for f in Path("data").glob("allen_*_*.npz")
                   if len(f.stem.split("_")) == 3 and f.stem.split("_")[2] != "state")
    if args.only:
        files = [f for f in files if any(o in f for o in args.only.split(","))]
    out_path = Path(args.out)
    res = json.loads(out_path.read_text()) if out_path.exists() else {}
    for f in files:
        name = Path(f).stem.replace("allen_", "")
        if name in res:
            continue
        t0 = time.time()
        res[name] = run(f, widths, ranks, factors)
        out_path.write_text(json.dumps(res, indent=1))
        print(f"{name} done in {time.time() - t0:.0f}s ({len(res)}/{len(files)})", flush=True)


if __name__ == "__main__":
    main()
