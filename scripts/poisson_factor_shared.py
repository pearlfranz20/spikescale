"""Cross-session Poisson factor decoder: one image embedding shared by all 39 recordings.

The per-recording decoder (poisson_factor.py) gives every unit its own
weights a[k, u, r] for every image k, fitted from that recording's 40
training trials per image. Here the image weights factor through an
embedding shared across all recordings:

    a[k, u, r] = sum_m E[k, m] W[u, r, m]
    log rate[n, u, t] = b[u, t] + sum_r a[y_n, u, r] phi[u, r, t] + sum_j z[n, j] L[u, t, j]

E (118 x M) is fitted from all recordings' training trials at once (about
1,600 per image); W, b, phi, L and the trials' z stay per recording (no unit
is shared between recordings). With a free E this is the per-recording
model with the image weights constrained to an M-dimensional space common
to all populations. Everything is fitted jointly by MAP, the sum of the
per-recording objectives of poisson_factor.py (Adam, the same steps and
L2), and each recording is decoded exactly as there (Laplace marginal over
z for each image).

R = 2 (1 at 250 ms). J per recording and width is the one the per-recording
run chose on its inner split (results/poisson_factor.json). M is chosen
on the inner split by mean validation accuracy over recordings, the model is
refitted on all training trials and each recording's test trials are scored
once. The split is the usual time-blocked one.

    .venv-gpu/Scripts/python.exe scripts/poisson_factor_shared.py
Output: results/poisson_factor_shared.json  {width: {"M", "val": {M: mean acc}, "acc": {recording: acc}}},
written after every width; widths already in the file are skipped.
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from poisson_factor import DEV, K, loglik  # noqa: E402
from spikescale.decode import blocked_split  # noqa: E402


def load(files, w):
    """Binned counts (uint8, on the GPU), labels and split indices per recording."""
    recs = []
    for f in files:
        d = np.load(f)
        sp, y = d["spikes_ms"], d["labels"].astype(np.int64)
        n, U, _ = sp.shape
        x = sp.reshape(n, U, 250 // w, w).sum(-1, dtype=np.int64).clip(0, 255).astype(np.uint8)
        tr, te = blocked_split(n, y)
        tri = np.nonzero(tr)[0]
        itr, iva = blocked_split(len(tri), y[tri], test_frac=0.25)
        idx = {"tr": np.nonzero(tr)[0], "te": np.nonzero(te)[0], "itr": tri[itr], "iva": tri[iva]}
        recs.append(dict(name=Path(f).stem.replace("allen_", ""), x=torch.as_tensor(x, device=DEV),
                         y=torch.as_tensor(y, device=DEV), idx={k: torch.as_tensor(v, device=DEV) for k, v in idx.items()}))
    return recs


def fit(recs, part, Js, M, R, l2=1e-2, l2_emb=1e-3, steps=1500, seed=0):
    """Joint MAP fit on the trials recs[i]["idx"][part]. Returns per recording (image log rates, loadings)."""
    g = torch.Generator(device=DEV).manual_seed(seed)
    E = (0.1 * torch.randn(K, M, device=DEV, generator=g)).requires_grad_(True)
    params, per = [E], []
    for r, J in zip(recs, Js):
        i = r["idx"][part]
        x = r["x"][i].float()
        n, U, T = x.shape
        p = dict(x=x, y=r["y"][i], n=n,
                 b=x.mean(0).clamp_min(1e-3).log().clone().requires_grad_(True),
                 W=(0.3 * torch.randn(U, R, M, device=DEV, generator=g)).requires_grad_(True),
                 phi=(0.1 * torch.randn(U, R, T, device=DEV, generator=g)).requires_grad_(True),
                 L=(0.01 * torch.randn(U, T, J, device=DEV, generator=g)).requires_grad_(True),
                 z=torch.zeros(n, J, device=DEV, requires_grad=True))
        params += [p["b"], p["W"], p["phi"], p["L"], p["z"]]
        per.append(p)
    opt = torch.optim.Adam(params, lr=0.03)
    for _ in range(steps):
        opt.zero_grad()
        for p in per:
            a = torch.einsum("km,urm->kur", E, p["W"])
            T = p["phi"].shape[-1]
            eta = p["b"] + torch.einsum("kur,urt->kut", a, p["phi"])[p["y"]] + torch.einsum("nj,utj->nut", p["z"], p["L"])
            loss = ((eta.exp() - p["x"] * eta).sum() / p["n"] + l2 * (a.pow(2).sum() / K + p["phi"].pow(2).sum() / T)
                    + 0.5 * p["z"].pow(2).sum() / p["n"] + l2 * p["L"].pow(2).sum() + l2_emb * p["W"].pow(2).sum())
            loss.backward()
        (l2_emb * E.pow(2).sum()).backward()
        opt.step()
    with torch.no_grad():
        return [(p["b"] + torch.einsum("kur,urt->kut", torch.einsum("km,urm->kur", E, p["W"]), p["phi"]), p["L"].detach())
                for p in per]


def accs(recs, part, models):
    out = []
    for r, (eta, L) in zip(recs, models):
        i = r["idx"][part]
        out.append(float((loglik(r["x"][i].float(), eta, L).argmax(1) == r["y"][i]).float().mean()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--widths", default="50,25,10,5,125,250")
    ap.add_argument("--dims", default="8,16,32,64")
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--out", default="results/poisson_factor_shared.json")
    args = ap.parse_args()
    files = sorted(str(f) for f in Path("data").glob("allen_*_*.npz")
                   if len(f.stem.split("_")) == 3 and f.stem.split("_")[2] != "state")
    single = json.loads(Path("results/poisson_factor.json").read_text())
    out_path = Path(args.out)
    res = json.loads(out_path.read_text()) if out_path.exists() else {}
    for w in (int(v) for v in args.widths.split(",")):
        if str(w) in res:
            continue
        t0 = time.time()
        recs = load(files, w)
        Js = [single[r["name"]][str(w)]["J"] for r in recs]
        R = min(2, 250 // w)
        val = {}
        for M in (int(v) for v in args.dims.split(",")):
            val[M] = float(np.mean(accs(recs, "iva", fit(recs, "itr", Js, M, R, steps=args.steps))))
            print(f"  {w} ms M {M}: val {val[M]:.3f} ({time.time() - t0:.0f}s)", flush=True)
        M = max(val, key=val.get)
        a = accs(recs, "te", fit(recs, "tr", Js, M, R, steps=args.steps))
        res[str(w)] = {"M": M, "val": val, "acc": {r["name"]: v for r, v in zip(recs, a)}}
        out_path.write_text(json.dumps(res, indent=1))
        own = np.mean([single[r["name"]][str(w)]["acc"] for r in recs])
        print(f"{w} ms: shared {np.mean(a):.3f} (M {M}) against per-recording {own:.3f}, {time.time() - t0:.0f}s", flush=True)
        del recs
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
