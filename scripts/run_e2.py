"""E2: synthetic level attribution.

For each planted code, train the tokenizer on training trials, then decode the
stimulus from (a) the codes of levels 1..k, (b) reconstructed log-rates after
levels 1..k (secondary), and (c) the no-learning binning pyramid at each level
length. Writes results/e2.json and results/e2.png.

Gate 1 (from the plan): code-based accuracy reaches 90% of its final value at
the level whose bin width matches the planted precision, plus or minus one
level, and the 2 ms control stays unresolved.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from spikescale.decode import (blocked_split, fit_decode, pyramid_curve,
                               quantized_pyramid_features)
from spikescale.synth import LEVEL_LENGTHS, LEVEL_WIDTHS_MS, expected_level, generate, suite
from spikescale.tokenizer import TokenizerConfig, cumulative_bits, train_tokenizer


def cond_name(cfg) -> str:
    return f"timing_p{cfg.precision_ms}" if cfg.code == "timing" else cfg.code


def recon_features(model, counts):
    """Secondary readout: decoded log-rates after levels 1..k, pooled to L_k."""
    model.eval()
    with torch.no_grad():
        z = model.encode(counts)
        cumulative, _, _, _ = model.quantize(z)
        out = []
        for k, zh in enumerate(cumulative):
            lr = model.decode(zh)
            out.append(F.adaptive_avg_pool1d(lr, LEVEL_LENGTHS[k]).flatten(1).numpy())
    return out


def gate_level(accs, chance, min_signal=0.1):
    """First level reaching 90% of the final accuracy, or None if there is no signal."""
    final = accs[-1]
    if final - chance < min_signal:
        return None
    target = 0.9 * final
    for k, a in enumerate(accs):
        if a >= target:
            return k + 1
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--c", type=float, default=0.1)
    ap.add_argument("--out", default="results")
    ap.add_argument("--d", type=int, default=32)
    ap.add_argument("--codebook-scale", type=int, default=1)
    args = ap.parse_args()
    torch.set_num_threads(2)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base_sizes = (32, 64, 64, 128, 128, 128)
    sizes = tuple(v * args.codebook_scale for v in base_sizes)
    results = {"level_widths_ms": LEVEL_WIDTHS_MS, "codebook_sizes": sizes, "d": args.d,
               "epochs": args.epochs, "conditions": []}

    for cfg0 in suite():
        rows = []
        for seed in range(args.seeds):
            cfg = type(cfg0)(**{**cfg0.__dict__, "seed": seed})
            X, y = generate(cfg)
            tr, te = blocked_split(len(y), y)
            t0 = time.time()
            tc = TokenizerConfig(n_units=X.shape[1], d=args.d, codebook_sizes=sizes)
            model = train_tokenizer(X[tr], tc, epochs=args.epochs, seed=seed)
            Xt = torch.as_tensor(X)
            codes = [fit_decode(f.numpy()[tr], y[tr], f.numpy()[te], y[te], args.c)
                     for f in model.level_features(Xt)]
            recon = [fit_decode(f[tr], y[tr], f[te], y[te], args.c)
                     for f in recon_features(model, Xt)]
            pyr = pyramid_curve(X, y, tr, te, args.c)
            qpyr = [fit_decode(f[tr], y[tr], f[te], y[te], args.c)
                    for f in quantized_pyramid_features(X, tr, sizes, seed)]
            rows.append({
                "seed": seed, "codes": codes, "recon": recon, "pyramid": pyr, "qpyramid": qpyr,
                "nll_test": model.level_nll(Xt[te]),
                "usage": model.code_usage(Xt[tr]),
                "seconds": round(time.time() - t0, 1),
            })
            print(f"{cond_name(cfg):12s} seed {seed}  codes " + " ".join(f"{a:.2f}" for a in codes)
                  + "  |  qpyr " + " ".join(f"{a:.2f}" for a in qpyr)
                  + "  |  pyr " + " ".join(f"{a:.2f}" for a in pyr), flush=True)

        chance = 1.0 / cfg0.n_stimuli
        mean = lambda key: np.mean([r[key] for r in rows], axis=0).tolist()
        codes_m, pyr_m = mean("codes"), mean("pyramid")
        exp = expected_level(cfg0)
        got = gate_level(codes_m, chance)
        if cfg0.code == "control":
            passed = max(codes_m) - chance < 0.1
        elif cfg0.code == "mixed":
            passed = None  # descriptive only
        else:
            passed = got is not None and abs(got - exp) <= 1
        results["conditions"].append({
            "name": cond_name(cfg0), "expected_level": exp, "gate_level_codes": got,
            "gate_level_pyramid": gate_level(pyr_m, chance), "passed": passed,
            "chance": chance, "codes_mean": codes_m, "recon_mean": mean("recon"),
            "pyramid_mean": pyr_m, "qpyramid_mean": mean("qpyramid"),
            "gate_level_qpyramid": gate_level(mean("qpyramid"), chance),
            "nll_test_mean": mean("nll_test"), "runs": rows,
        })

    results["bits"] = cumulative_bits(TokenizerConfig(n_units=1, codebook_sizes=sizes))
    (out / "e2.json").write_text(json.dumps(results, indent=1))
    print("\nGATE 1 SUMMARY")
    for c in results["conditions"]:
        print(f"  {c['name']:12s} expected L{c['expected_level']}  codes L{c['gate_level_codes']}"
              f"  qpyramid L{c['gate_level_qpyramid']}  pyramid L{c['gate_level_pyramid']}"
              f"  pass={c['passed']}")


if __name__ == "__main__":
    main()
