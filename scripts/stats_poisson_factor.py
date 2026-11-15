"""Thalamus against cortex on the Poisson factor decoder's bin-width profile, animals as the unit.

Same test as stats_tissue.py (exact permutation of the tissue labels within
each animal, pooled permutation, hierarchical bootstrap CI), on the Poisson
factor decoder's accuracy at one bin width over its accuracy at 50 ms, all
units of each recording (results/poisson_factor.json). With --thinned the
thalamic recordings are replaced by their rate-matched runs
(results/poisson_factor_thin.json); cortex stays as it is.

A recording enters when its best width decodes at three times chance or more.

    python scripts/stats_poisson_factor.py [--thinned]
Output: results/stats_poisson_factor.json (or _thinned) and a table on stdout.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stats_tissue import THAL, holm, test  # noqa: E402

RES = Path("results")
METRICS = {"pf_25_50": "25", "pf_10_50": "10", "pf_5_50": "5"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thinned", action="store_true")
    args = ap.parse_args()
    pf = json.loads((RES / "poisson_factor.json").read_text())
    if args.thinned:
        pf.update(json.loads((RES / "poisson_factor_thin.json").read_text()))
    rows = []
    for rec, r in sorted(pf.items()):
        sid, area = rec.split("_")
        acc = {w: v["acc"] for w, v in r.items() if w != "keep"}
        if max(acc.values()) < 3 / 118:
            continue
        rows.append(dict(sid=sid, area=area, **{k: acc[w] / acc["50"] for k, w in METRICS.items()}))
    out = {k: test(rows, k) for k in METRICS}
    for k, p in zip(out, holm([out[k]["p_stratified"] for k in out])):
        out[k]["p_stratified_holm"] = p
    print(f"{'metric':10s} {'thal':>6s} {'ctx':>6s} {'diff':>7s}  95% CI            p_within  p_holm  p_pooled  animals(both)")
    for k, s in out.items():
        print(f"{k:10s} {s['thal_mean']:6.3f} {s['ctx_mean']:6.3f} {s['diff']:+7.3f}  [{s['ci95'][0]:+.3f}, {s['ci95'][1]:+.3f}]  "
              f"{s['p_stratified']:8.4f}  {s['p_stratified_holm']:6.4f}  {s['p_pooled']:8.4f}  {s['n_animals']}({s['n_animals_both']}) "
              f"n {s['n_thal']}/{s['n_ctx']}")
    name = "stats_poisson_factor_thinned.json" if args.thinned else "stats_poisson_factor.json"
    (RES / name).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
