"""A nonlinear decoder on spike timing: is "nothing below 25 ms" a limit of the linear decoder?

Every result so far reads image identity with an L2 logistic regression on log
pooled counts. A linear readout can miss information that sits in the
conjunction or the relative timing of spikes across units and bins, so the
small amounts found below 25 ms may be what a linear decoder can reach rather
than what the spikes carry. This script trains a small temporal convolutional
network on the same trials, units and split, in two families of conditions:

  width <w>   input pooled to w ms bins (250, 125, 50, 25, 10, 5), log1p, then
              repeated back to 5 ms resolution so that the network is the same
              in every condition; the nonlinear analogue of the pyramid
              (each input contains every coarser one, so it is cumulative)
  jitter <j>  every spike moved by uniform noise in [-j, +j] ms (j = 5, 10, 25,
              reflecting at the window edges), in training and test trials
              alike, then 5 ms bins: what is left when timing finer than about
              j ms is destroyed. width 5 minus jitter j is the information the
              network finds in timing below j.

Network: units as input channels, two 1-D convolutions over 5 ms bins
(kernel 5, i.e. 25 ms, 64 channels, GELU, dropout), the time axis kept and
flattened into a linear layer over the classes. Inputs standardized with
training statistics. Adam, batch 128. The weight decay (1e-3, 1e-2) and the
number of epochs (early stopping, patience 15, at most 150) are chosen on an
inner time-blocked split of the training set (the last 25% of every image's
training repeats), and the network is then retrained on all training trials
with those settings and scored once on the held-out block: the same nesting
as the linear decoder's C.

Same 60-unit subsets per seed as every other analysis (residual_levels.subsample),
same time-blocked held-out set (last 20% of every image's repeats), 5 seeds.

    PYTHONPATH=. python scripts/nonlinear_timing.py --scenes data/allen_<id>_<area>.npz --jobs 8
Output: results/nonlinear_allen_<id>_<area>.json
  runs[seed<k>][<condition>] = {acc, wd, epochs}; mean[<condition>] over seeds
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parent))
from residual_levels import subsample  # noqa: E402
from spikescale.decode import blocked_split, pool_counts  # noqa: E402
from spikescale.jitter import jitter_spikes  # noqa: E402

BIN_MS = 5
WIDTHS = (250, 125, 50, 25, 10, 5)
JITTERS = (5, 10, 25)
WD_GRID = (1e-3, 1e-2)
MAX_EPOCHS, PATIENCE, BATCH, LR = 150, 15, 128, 1e-3


def features(spikes_ms, cond, seed):
    """(trials, units, T5) float32 input at 5 ms resolution for one condition."""
    w = spikes_ms.shape[2]
    if cond.startswith("jitter"):
        spikes_ms = jitter_spikes(spikes_ms, float(cond[6:]), np.random.default_rng(4000 + seed))
    n, u = spikes_ms.shape[:2]
    c5 = spikes_ms.reshape(n, u, w // BIN_MS, BIN_MS).sum(-1).astype(np.float32)
    if cond.startswith("width"):
        width = int(cond[5:])
        L = w // width
        pooled = np.log1p(pool_counts(c5, L).astype(np.float32))
        return np.repeat(pooled, c5.shape[2] // L, axis=2)
    return np.log1p(c5)


ARCH = "lincnn"
CH = 16


def make_net(n_units, t, n_classes, torch):
    nn = torch.nn
    if ARCH == "cnn":
        return nn.Sequential(
            nn.Conv1d(n_units, 64, 5, padding=2), nn.GELU(), nn.Dropout(0.3),
            nn.Conv1d(64, 64, 5, padding=2), nn.GELU(), nn.Dropout(0.3),
            nn.Flatten(), nn.Dropout(0.5), nn.Linear(64 * t, n_classes))

    class LinCNN(nn.Module):
        """Logits = a linear readout of the input (the logistic model) + a convolutional branch,
        so the network contains the linear decoder and can only add nonlinear structure to it."""

        def __init__(self):
            super().__init__()
            self.lin = nn.Sequential(nn.Flatten(), nn.Dropout(0.2), nn.Linear(n_units * t, n_classes))
            self.conv = nn.Sequential(
                nn.Conv1d(n_units, CH, 5, padding=2), nn.GELU(), nn.Dropout(0.3),
                nn.Conv1d(CH, CH, 5, padding=2), nn.GELU(),
                nn.Flatten(), nn.Dropout(0.5), nn.Linear(CH * t, n_classes))

        def forward(self, x):
            return self.lin(x) + self.conv(x)

    return LinCNN()


def train(xtr, ytr, xva, yva, wd, epochs, seed, torch):
    """Train; with validation data, early-stop and return (best val acc, best epoch count);
    without, train for `epochs` and return the model."""
    torch.manual_seed(seed)
    net = make_net(xtr.shape[1], xtr.shape[2], int(ytr.max()) + 1, torch)
    opt = torch.optim.AdamW(net.parameters(), lr=LR, weight_decay=wd)
    lossf = torch.nn.CrossEntropyLoss()
    xt, yt = torch.from_numpy(xtr), torch.from_numpy(ytr)
    g = torch.Generator().manual_seed(seed)
    best, best_ep, bad = -1.0, 0, 0
    for ep in range(1, (epochs or MAX_EPOCHS) + 1):
        net.train()
        for idx in torch.randperm(len(xt), generator=g).split(BATCH):
            opt.zero_grad()
            lossf(net(xt[idx]), yt[idx]).backward()
            opt.step()
        if xva is None:
            continue
        acc = evaluate(net, xva, yva, torch)
        if acc > best:
            best, best_ep, bad = acc, ep, 0
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    return (best, best_ep) if xva is not None else net


def evaluate(net, x, y, torch):
    net.eval()
    with torch.no_grad():
        pred = torch.cat([net(b).argmax(1) for b in torch.from_numpy(x).split(1024)])
    return float((pred.numpy() == y).mean())


def one(spikes_ms, labels, cond, seed, threads, cfg):
    import torch
    global ARCH, WD_GRID, CH
    ARCH, WD_GRID, CH = cfg  # worker processes do not see main()'s settings
    torch.set_num_threads(threads)
    x = features(spikes_ms, cond, seed)
    tr, te = blocked_split(len(labels), labels)
    tr_idx = np.nonzero(tr)[0]
    itr, iva = blocked_split(len(tr_idx), labels[tr_idx], test_frac=0.25)
    mu, sd = x[tr].mean(0, keepdims=True), x[tr].std(0, keepdims=True) + 1e-3
    x = ((x - mu) / sd).astype(np.float32)
    y = labels.astype(np.int64)
    xtr, ytr = x[tr_idx], y[tr_idx]
    inner = {wd: train(xtr[itr], ytr[itr], xtr[iva], ytr[iva], wd, None, seed, torch) for wd in WD_GRID}
    wd = max(WD_GRID, key=lambda w: inner[w][0])
    ep = inner[wd][1]
    net = train(xtr, ytr, None, None, wd, ep, seed, torch)
    return {"acc": evaluate(net, x[te], y[te], torch), "wd": wd, "epochs": ep, "inner_val": inner[wd][0]}


def main():
    global ARCH, WD_GRID, CH
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", required=True, help="data/allen_<id>_<area>.npz")
    ap.add_argument("--n-units", type=int, default=60)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--threads", type=int, default=2, help="torch threads per job")
    ap.add_argument("--conds", default=",".join([f"width{w}" for w in WIDTHS] + [f"jitter{j}" for j in JITTERS]))
    ap.add_argument("--out", default="results")
    ap.add_argument("--tag", default="")
    ap.add_argument("--arch", default=ARCH, choices=("cnn", "lincnn"))
    ap.add_argument("--wd", default=",".join(str(w) for w in WD_GRID))
    ap.add_argument("--ch", type=int, default=CH)
    args = ap.parse_args()
    ARCH, CH = args.arch, args.ch
    WD_GRID = tuple(float(w) for w in args.wd.split(","))
    conds = args.conds.split(",")

    s = np.load(args.scenes)
    spikes, labels = s["spikes_ms"].astype(np.int16), s["labels"]
    name = Path(args.scenes).stem
    print(f"{name}: {len(labels)} trials, {spikes.shape[1]} units, {len(np.unique(labels))} images", flush=True)
    jobs = [(seed, c) for seed in range(args.repeats) for c in conds]
    t0 = time.time()
    res = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(one)(subsample(spikes, args.n_units, seed), labels, c, seed, args.threads, (ARCH, WD_GRID, CH))
        for seed, c in jobs)
    print(f"{len(jobs)} jobs in {time.time() - t0:.0f}s", flush=True)
    out = {"scenes": args.scenes, "n_units": args.n_units, "repeats": args.repeats, "chance": 1 / len(np.unique(labels)),
           "arch": ARCH, "wd_grid": list(WD_GRID), "channels": CH,
           "conds": conds, "runs": {}, "mean": {}}
    for (seed, c), r in zip(jobs, res):
        out["runs"].setdefault(f"seed{seed}", {})[c] = r
    for c in conds:
        out["mean"][c] = float(np.mean([out["runs"][f"seed{k}"][c]["acc"] for k in range(args.repeats)]))
    path = Path(args.out) / f"nonlinear_{name}{args.tag}.json"
    path.write_text(json.dumps(out, indent=1))
    for c in conds:
        accs = [out["runs"][f"seed{k}"][c]["acc"] for k in range(args.repeats)]
        eps = [out["runs"][f"seed{k}"][c]["epochs"] for k in range(args.repeats)]
        print(f"  {c:9s} {np.mean(accs):.3f} (seeds {min(accs):.3f} to {max(accs):.3f}; epochs {min(eps)} to {max(eps)})")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
