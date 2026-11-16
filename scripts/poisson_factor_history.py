"""Poisson factor decoder with spike history: do a unit's own recent spikes (bursts, refractoriness) help?

Adds to the model of poisson_factor.py a term in each unit's own counts in
the H preceding bins of the same trial (zero before image onset):

    log rate[n, u, t] = b[u, t] + sum_r a[y_n, u, r] phi[u, r, t] + sum_j z[n, j] L[u, t, j]
                        + sum_{h=1..H} beta[u, h] x[n, u, t - h]

As in a point-process GLM, the history term is a known offset at decoding
time (it depends on the observed counts, not the image), and the Laplace
marginal over z is computed with it. Thalamic burst spikes (several spikes
within a few ms after a silence) and refractoriness are what beta can model
at 5 and 10 ms; at 25 ms it is slower adaptation.

H in {0, 1, 2, 4} bins is chosen on the inner split; H = 0 is the model of
poisson_factor.py with the same seed, so the choice includes it. R and J
are those the per-recording run chose for that recording and width
(results/poisson_factor.json). Widths 25, 10 and 5 ms.

    .venv-gpu/Scripts/python.exe scripts/poisson_factor_history.py
Output: results/poisson_factor_history.json  {recording: {width: {"acc", "H", "val": {H: acc}, "acc_H0", "beta1"}}}
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


def history(x, H):
    """(n, U, T, H): the unit's counts h bins earlier, zero before onset."""
    n, U, T = x.shape
    out = torch.zeros(n, U, T, H, device=DEV)
    for h in range(1, H + 1):
        out[:, :, h:, h - 1] = x[:, :, :-h]
    return out


def fit(x, y, R, J, H, l2=1e-2, steps=1500, seed=0):
    g = torch.Generator(device=DEV).manual_seed(seed)
    n, U, T = x.shape
    R = min(R, T)
    b = x.mean(0).clamp_min(1e-3).log().clone().requires_grad_(True)
    a = (0.1 * torch.randn(K, U, R, device=DEV, generator=g)).requires_grad_(True)
    phi = (0.1 * torch.randn(U, R, T, device=DEV, generator=g)).requires_grad_(True)
    L = (0.01 * torch.randn(U, T, J, device=DEV, generator=g)).requires_grad_(True)
    z = torch.zeros(n, J, device=DEV, requires_grad=True)
    params = [b, a, phi, L, z]
    if H:
        hist = history(x, H)
        beta = torch.zeros(U, H, device=DEV, requires_grad=True)
        params.append(beta)
    opt = torch.optim.Adam(params, lr=0.03)
    for _ in range(steps):
        eta = b + torch.einsum("kur,urt->kut", a, phi)[y] + torch.einsum("nj,utj->nut", z, L)
        if H:
            eta = eta + torch.einsum("nuth,uh->nut", hist, beta)
        loss = ((eta.exp() - x * eta).sum() / n + l2 * (a.pow(2).sum() / K + phi.pow(2).sum() / T)
                + 0.5 * z.pow(2).sum() / n + l2 * L.pow(2).sum())
        if H:
            loss = loss + l2 * beta.pow(2).sum()
        opt.zero_grad()
        loss.backward()
        opt.step()
    with torch.no_grad():
        return ((b + torch.einsum("kur,urt->kut", a, phi)).detach(), L.detach(),
                beta.detach() if H else None)


def loglik(x, eta, L, beta, chunk=40, iters=8):
    """(n, K) Laplace log marginal likelihood with the history offset, up to constants."""
    n = len(x)
    xf, ef = x.reshape(n, -1), eta.reshape(K, -1)
    off = (torch.einsum("nuth,uh->nut", history(x, beta.shape[1]), beta).reshape(n, -1)
           if beta is not None else torch.zeros_like(xf))
    Lf = L.reshape(-1, L.shape[-1])
    J = Lf.shape[1]
    eye = torch.eye(J, device=DEV)
    LL = (Lf[:, :, None] * Lf[:, None, :]).reshape(-1, J * J)
    out = torch.empty(n, K, device=DEV)
    for i in range(0, n, chunk):
        xc, oc = xf[i:i + chunk], off[i:i + chunk, None]
        z = torch.zeros(len(xc), K, J, device=DEV)
        for _ in range(iters):
            lam = (ef[None] + oc + z @ Lf.T).exp()
            grad = (xc[:, None] - lam) @ Lf - z
            Hs = (lam @ LL).view(*lam.shape[:2], J, J) + eye
            z = z + torch.linalg.solve(Hs, grad.unsqueeze(-1)).squeeze(-1)
        e = ef[None] + oc + z @ Lf.T
        lam = e.exp()
        Hs = (lam @ LL).view(*lam.shape[:2], J, J) + eye
        out[i:i + chunk] = (xc[:, None] * e).sum(-1) - lam.sum(-1) - 0.5 * z.pow(2).sum(-1) - 0.5 * torch.logdet(Hs)
    return out


def acc(x, y, model):
    return float((loglik(x, *model).argmax(1) == y).float().mean())


def run(path, widths, hs, single):
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
        R, J = single[str(w)]["R"], single[str(w)]["J"]
        val = {H: acc(x[idx["iva"]], y[idx["iva"]], fit(x[idx["itr"]], y[idx["itr"]], R, J, H)) for H in hs}
        H = max(val, key=val.get)
        model = fit(x[idx["tr"]], y[idx["tr"]], R, J, H)
        rec = {"acc": acc(x[idx["te"]], y[idx["te"]], model), "H": H, "val": val}
        rec["acc_H0"] = rec["acc"] if H == 0 else acc(x[idx["te"]], y[idx["te"]], fit(x[idx["tr"]], y[idx["tr"]], R, J, 0))
        if H:
            rec["beta1"] = float(model[2][:, 0].mean())  # mean weight on the previous bin
        out[w] = rec
        print(f"  {Path(path).stem} {w} ms: {rec['acc']:.3f} (H {H}) against H0 {rec['acc_H0']:.3f}", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--widths", default="25,10,5")
    ap.add_argument("--hist", default="0,1,2,4")
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default="results/poisson_factor_history.json")
    args = ap.parse_args()
    widths = [int(v) for v in args.widths.split(",")]
    hs = [int(v) for v in args.hist.split(",")]
    files = sorted(str(f) for f in Path("data").glob("allen_*_*.npz")
                   if len(f.stem.split("_")) == 3 and f.stem.split("_")[2] != "state")
    if args.only:
        files = [f for f in files if any(o in f for o in args.only.split(","))]
    single = json.loads(Path("results/poisson_factor.json").read_text())
    out_path = Path(args.out)
    res = json.loads(out_path.read_text()) if out_path.exists() else {}
    for f in files:
        name = Path(f).stem.replace("allen_", "")
        if name in res:
            continue
        t0 = time.time()
        res[name] = run(f, widths, hs, single[name])
        out_path.write_text(json.dumps(res, indent=1))
        print(f"{name} done in {time.time() - t0:.0f}s ({len(res)}/{len(files)})", flush=True)


if __name__ == "__main__":
    main()
