"""E3 and E3b on one extracted session (or a synthetic stand-in).

E3   Decode stimulus identity per level from codes (primary), reconstructed
     log-rates (secondary), the continuous binning pyramid (ceiling) and the
     quantized pyramid (residual k-means at the same bits: the decisive
     matched-bits baseline). Every feature set is read out by three decoders:
     plain L2 logistic on the level-k features; PCA to --pca components then
     logistic; and PCA then logistic on the concatenation of the level-1 to
     level-k features (cumulative). The cumulative PCA decoder is the one to
     read per-level curves from: the concatenation keeps the coarse counts
     as explicit features, so a level cannot score below the levels above it
     for reasons of decoder geometry, and the PCA caps capacity.
E3b  Freeze tokenizer and decoders. Re-score on held-out trials whose spikes are
     jittered by 5, 10 and 25 ms, and on PSTH-matched surrogates (trials
     shuffled within stimulus per unit). Timing information at a level is the
     accuracy lost under jitter.

Units are subsampled to --n-units (repeated --repeats times, seeds starting
at --seed) so areas can be compared at matched unit counts. Repeats can be
split over processes with --seed and merged with scripts/merge_e3.py.

    python scripts/run_e3.py --data data/allen_<id>_VISp.npz --n-units 60 --repeats 5
    python scripts/run_e3.py --synthetic timing_p10   # pipeline test
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from spikescale.decode import QuantizedPyramid, blocked_split, fit_clf, pool_counts, score
from spikescale.jitter import bin_ms, jitter_spikes, psth_matched_surrogate
from spikescale.synth import LEVEL_LENGTHS, SynthConfig, generate
from spikescale.tokenizer import TokenizerConfig, cumulative_bits, train_tokenizer

JITTERS_MS = (5, 10, 25)
FEATS = ("codes", "recon", "pyramid", "qpyramid")
TEST_SETS = ("clean",) + tuple(f"jitter_{j}ms" for j in JITTERS_MS) + ("psth_surrogate",)


def load(args):
    if args.synthetic:
        name = args.synthetic
        if name.startswith("timing_p"):
            cfg = SynthConfig(code="timing", precision_ms=int(name.split("p")[1]))
        else:
            cfg = SynthConfig(code=name)
        _, labels, spikes_ms = generate(cfg, return_ms=True)
        return spikes_ms, labels, name
    d = np.load(args.data)
    return d["spikes_ms"], d["labels"], Path(args.data).stem


def code_feats(model, counts):
    return [f.numpy() for f in model.level_features(torch.as_tensor(counts))]


def recon_feats(model, counts):
    x = torch.as_tensor(counts)
    with torch.no_grad():
        cumulative, _, _, _ = model.quantize(model.encode(x))
        return [F.adaptive_avg_pool1d(model.decode(zh), L).flatten(1).numpy()
                for zh, L in zip(cumulative, LEVEL_LENGTHS)]


def pyr_feats(counts):
    return [np.log1p(pool_counts(counts, L)).reshape(len(counts), -1) for L in LEVEL_LENGTHS]


def cumulative(feats):
    """Level-k readout as the concatenation of level-1 to level-k features."""
    return [np.concatenate(feats[:k + 1], axis=1) for k in range(len(feats))]


def run_once(spikes_ms, labels, args, seed):
    rng = np.random.default_rng(seed)
    n_units = spikes_ms.shape[1]
    if args.n_units and args.n_units < n_units:
        keep = np.sort(rng.choice(n_units, args.n_units, replace=False))
        spikes_ms = spikes_ms[:, keep]
    counts = bin_ms(spikes_ms)
    tr, te = blocked_split(len(labels), labels)
    y = labels

    tc = TokenizerConfig(n_units=counts.shape[1], d=args.d)
    model = train_tokenizer(counts[tr], tc, epochs=args.epochs, seed=seed)

    # held-out test sets: clean, jittered, surrogate
    test_sets = {"clean": spikes_ms[te]}
    for j in JITTERS_MS:
        test_sets[f"jitter_{j}ms"] = jitter_spikes(spikes_ms[te], j, rng)
    test_sets["psth_surrogate"] = psth_matched_surrogate(spikes_ms[te], y[te], rng)

    qp = QuantizedPyramid(tc.codebook_sizes, seed).fit(counts[tr])
    decoders = {"logreg": (0, False), f"pca{args.pca}_logreg": (args.pca, False),
                f"cum_pca{args.pca}_logreg": (args.pca, True)}

    out = {}
    for feat_name, fn in (("codes", lambda c: code_feats(model, c)),
                          ("recon", lambda c: recon_feats(model, c)),
                          ("pyramid", pyr_feats),
                          ("qpyramid", qp.transform)):
        train_f = fn(counts[tr])
        test_f = {tname: fn(bin_ms(sp)) for tname, sp in test_sets.items()}
        out[feat_name] = {}
        for dec_name, (n_pca, cum) in decoders.items():
            prep = cumulative if cum else (lambda f: f)
            clfs = [fit_clf(f, y[tr], args.c, n_pca) for f in prep(train_f)]
            out[feat_name][dec_name] = {
                tname: [score(clf, f, y[te]) for clf, f in zip(clfs, prep(test_f[tname]))]
                for tname in test_sets}
    out["nll_test"] = model.level_nll(torch.as_tensor(counts[te]))
    out["usage"] = model.code_usage(torch.as_tensor(counts[tr]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data")
    ap.add_argument("--synthetic")
    ap.add_argument("--n-units", type=int, default=0)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--d", type=int, default=32)
    ap.add_argument("--c", type=float, default=0.1)
    ap.add_argument("--pca", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0, help="first seed; repeats use seed, seed+1, ...")
    ap.add_argument("--tag", default="", help="suffix for the output file name")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    if not (args.data or args.synthetic):
        ap.error("pass --data or --synthetic")
    torch.set_num_threads(2)

    spikes_ms, labels, name = load(args)
    print(f"{name}: {len(labels)} trials, {spikes_ms.shape[1]} units, "
          f"{len(np.unique(labels))} stimuli, chance {1 / len(np.unique(labels)):.3f}")
    runs = []
    for r in range(args.seed, args.seed + args.repeats):
        t0 = time.time()
        runs.append(run_once(spikes_ms, labels, args, seed=r))
        c = runs[-1]
        print(f" seed {r} ({time.time() - t0:.0f}s)", flush=True)
        for feat in FEATS:
            for dec in c[feat]:
                for tname in ("clean", "jitter_25ms", "psth_surrogate"):
                    print(f"   {feat:8s} {dec:13s} {tname:15s} "
                          + " ".join(f"{a:.2f}" for a in c[feat][dec][tname]), flush=True)

    result = {"name": name, "n_units": args.n_units or int(spikes_ms.shape[1]),
              "repeats": args.repeats, "seeds": list(range(args.seed, args.seed + args.repeats)),
              "chance": 1 / len(np.unique(labels)), "pca": args.pca,
              "bits": cumulative_bits(TokenizerConfig(n_units=1)),
              "mean": mean_runs(runs), "runs": runs}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tag = f"_{args.tag}" if args.tag else ""
    path = out / f"e3_{name}_n{result['n_units']}{tag}.json"
    path.write_text(json.dumps(result, indent=1))
    print(f"wrote {path}")


def mean_runs(runs):
    """Mean per-level accuracy over runs: mean[feat][decoder][test_set]."""
    return {feat: {dec: {t: np.mean([r[feat][dec][t] for r in runs], axis=0).tolist()
                         for t in runs[0][feat][dec]}
                   for dec in runs[0][feat]}
            for feat in FEATS}


if __name__ == "__main__":
    main()
