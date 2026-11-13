"""A cross-session spike-token decoder: does more training data find image information below 25 ms?

Every within-session decoder tried (linear, kernel SVM, convolutional
networks) has about 40 training trials per image, and none reads anything
below 25 ms beyond a trace. All 39 extracted populations saw the same 118
images, so one decoder trained on all of them at once has about 180,000
training trials. This script trains such a decoder on individual spikes,
after POYO (Azabou et al. 2023), and asks how its accuracy depends on the
time resolution it is given.

Input: every spike of a trial, 0 to 250 ms, as a token: a learned embedding
of its unit (units are never shared between recordings) plus an encoding of
its time, and one extra token for the recording. --res W rounds every spike
time to the centre of its W ms bin before the model sees it, so the model
can use timing down to W ms and no finer; W = 250 leaves only which units
fired how often. Models trained at W = 1, 10, 25, 50 and 250 ms are compared
on the same held-out trials: the gain from 25 to 1 ms is the image
information in timing below 25 ms that this decoder can reach.

Model: a Perceiver (32 learned latents cross-attend to the spike tokens,
then 4 self-attention blocks, width 128, 4 heads), the latents averaged into
one shared 118-way classifier for every recording. Training: AdamW, cosine
schedule, bf16, random unit dropout (each unit of each trial dropped with
probability --unit-drop; timing untouched). Phase 1 trains on the training
trials and picks the epoch with the best validation accuracy (the last 25%
of each image's training repeats, as in the nested C of the linear
decoder); phase 2 retrains on training and validation trials with the same
schedule for that many epochs and scores the held-out test trials once.

    .venv-gpu/Scripts/python.exe scripts/spike_transformer.py --res 1 --seed 0
Output: results/spiketf_res<W>_seed<S>.json  per-recording test accuracy, validation curve
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

MAX_TOK = 1024


class Data:
    def __init__(self, path, device):
        d = np.load(path)
        self.unit = torch.from_numpy(d["tok_unit"].astype(np.int64)).to(device)
        self.time = torch.from_numpy(d["tok_time"].astype(np.float32)).to(device)
        self.start = torch.from_numpy(d["trial_start"]).to(device)
        self.rec = torch.from_numpy(d["trial_rec"].astype(np.int64)).to(device)
        self.label = torch.from_numpy(d["trial_label"].astype(np.int64)).to(device)
        self.split = d["trial_split"]
        self.names = list(d["rec_names"])
        self.tissue = d["rec_tissue"]
        self.n_units = int(d["rec_unit_start"][-1])
        self.device = device

    def batch(self, idx, res, unit_drop, gen):
        """Padded tokens for trials idx: units (B, L), times (B, L), mask (B, L) True where padding."""
        s, e = self.start[idx], self.start[idx + 1]
        n = (e - s).clamp(max=MAX_TOK)
        L = int(n.max().item()) if len(idx) else 1
        pos = s[:, None] + torch.arange(max(L, 1), device=self.device)[None]
        pad = torch.arange(max(L, 1), device=self.device)[None] >= n[:, None]
        pos = torch.where(pad, s[:, None], pos)
        u, t = self.unit[pos], self.time[pos]
        if res > 1:
            t = torch.floor(t / res) * res + (res - 1) / 2
        if unit_drop > 0:
            keep = torch.rand(len(idx), self.n_units, device=self.device, generator=gen) >= unit_drop
            pad = pad | ~keep.gather(1, u)
        return u, t, pad


class TimeEnc(nn.Module):
    def __init__(self, dim):
        super().__init__()
        periods = torch.tensor([2.0, 4, 8, 16, 32, 64, 128, 256, 512, 1024])
        self.register_buffer("freq", 2 * math.pi / periods)
        self.proj = nn.Linear(2 * len(periods), dim)

    def forward(self, t):
        a = t[..., None] * self.freq
        return self.proj(torch.cat([a.sin(), a.cos()], -1))


class SpikePerceiver(nn.Module):
    def __init__(self, n_units, n_rec, n_classes=118, dim=128, n_latent=32, depth=4, heads=4, drop=0.1):
        super().__init__()
        self.unit = nn.Embedding(n_units, dim)
        self.rec = nn.Embedding(n_rec, dim)
        self.time = TimeEnc(dim)
        self.latents = nn.Parameter(torch.randn(n_latent, dim) * 0.02)
        self.norm_q, self.norm_kv = nn.LayerNorm(dim), nn.LayerNorm(dim)
        self.cross = nn.MultiheadAttention(dim, heads, dropout=drop, batch_first=True)
        self.ff = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, 4 * dim), nn.GELU(), nn.Dropout(drop), nn.Linear(4 * dim, dim))
        layer = nn.TransformerEncoderLayer(dim, heads, 4 * dim, drop, activation="gelu", batch_first=True, norm_first=True)
        self.blocks = nn.TransformerEncoder(layer, depth)
        self.head = nn.Sequential(nn.LayerNorm(dim), nn.Dropout(drop), nn.Linear(dim, n_classes))

    def forward(self, u, t, pad, rec):
        x = self.unit(u) + self.time(t)
        x = torch.cat([self.rec(rec)[:, None], x], 1)  # the recording token is never padding
        pad = torch.cat([torch.zeros_like(pad[:, :1]), pad], 1)
        q = self.latents[None].expand(len(u), -1, -1)
        kv = self.norm_kv(x)
        z = q + self.cross(self.norm_q(q), kv, kv, key_padding_mask=pad, need_weights=False)[0]
        z = z + self.ff(z)
        z = self.blocks(z)
        return self.head(z.mean(1))


def evaluate(model, data, idx, res, bs=1024):
    model.eval()
    correct = torch.zeros(len(idx), dtype=torch.bool, device=data.device)
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
        for i in range(0, len(idx), bs):
            b = idx[i:i + bs]
            u, t, pad = data.batch(b, res, 0.0, None)
            correct[i:i + bs] = model(u, t, pad, data.rec[b]).argmax(1) == data.label[b]
    return correct


def train(data, train_idx, val_idx, args, epochs, total_epochs, log):
    torch.manual_seed(args.seed)
    gen = torch.Generator(device=data.device).manual_seed(args.seed)
    model = SpikePerceiver(data.n_units, len(data.names)).to(data.device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.wd)
    steps_per = math.ceil(len(train_idx) / args.batch)
    total = total_epochs * steps_per
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / steps_per) * 0.5 * (1 + math.cos(math.pi * min(s, total) / total)))
    curve, best, best_ep = [], -1.0, 0
    for ep in range(1, epochs + 1):
        model.train()
        t0 = time.time()
        perm = train_idx[torch.randperm(len(train_idx), device=data.device, generator=gen)]
        loss_sum = 0.0
        for i in range(0, len(perm), args.batch):
            b = perm[i:i + args.batch]
            u, t, pad = data.batch(b, args.res, args.unit_drop, gen)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                loss = F.cross_entropy(model(u, t, pad, data.rec[b]), data.label[b], label_smoothing=0.1)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            loss_sum += loss.item() * len(b)
        msg = f"epoch {ep} loss {loss_sum / len(perm):.3f} {time.time() - t0:.0f}s"
        if val_idx is not None:
            acc = evaluate(model, data, val_idx, args.res).float().mean().item()
            curve.append(acc)
            if acc > best:
                best, best_ep = acc, ep
            msg += f" val {acc:.4f}"
        log(msg)
    return model, curve, best_ep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/packed_scenes.npz")
    ap.add_argument("--res", type=int, default=1, help="time resolution in ms given to the model")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--wd", type=float, default=0.05)
    ap.add_argument("--unit-drop", type=float, default=0.1)
    ap.add_argument("--phase1-only", action="store_true", help="stop after the validation run (for tuning)")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    dev = torch.device("cuda")
    data = Data(args.data, dev)
    sp = torch.from_numpy(data.split).to(dev)
    tr = torch.nonzero(sp == 0).squeeze(1)
    va = torch.nonzero(sp == 1).squeeze(1)
    te = torch.nonzero(sp == 2).squeeze(1)
    out_path = Path("results") / f"spiketf_res{args.res}_seed{args.seed}{args.tag}.json"
    log_lines = []

    def log(m):
        print(m, flush=True)
        log_lines.append(m)

    log(f"res {args.res} ms, seed {args.seed}: {len(tr)} train, {len(va)} val, {len(te)} test trials, "
        f"{len(data.names)} recordings, {data.n_units} units")
    _, curve, best_ep = train(data, tr, va, args, args.epochs, args.epochs, log)
    log(f"phase 1: best validation {max(curve):.4f} at epoch {best_ep}")
    out = {"args": vars(args), "val_curve": curve, "best_epoch": best_ep}
    if not args.phase1_only:
        model, _, _ = train(data, torch.cat([tr, va]), None, args, best_ep, args.epochs, log)
        correct = evaluate(model, data, te, args.res).cpu().numpy()
        rec = data.rec[te].cpu().numpy()
        out["test"] = {n: float(correct[rec == r].mean()) for r, n in enumerate(data.names)}
        out["test_mean"] = float(correct.mean())
        log(f"phase 2: test accuracy {correct.mean():.4f} over all trials")
    out["log"] = log_lines
    out_path.write_text(json.dumps(out, indent=1))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
