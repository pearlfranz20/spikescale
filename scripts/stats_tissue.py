"""Thalamus against cortex: one test per claim, with animals as the grouping unit.

The results describe a thalamic profile that differs from the cortical one in
every sample. This script puts a number on each claim. For every metric it
reports, over the samples of each tissue (seed means, 60 units):

  stratified p   exact permutation of the thalamus/cortex labels within each
                 animal (the label count per animal kept), so differences
                 between animals cannot produce the effect; animals with
                 only one tissue contribute nothing to the null
  pooled p       exact permutation over all samples, ignoring animals
  CI             95% hierarchical bootstrap of the difference in means
                 (animals resampled, then samples within each animal), 10,000 draws
  overlap        how many thalamic samples fall inside the cortical range

Primary metrics (fixed before running, one per claim in RESULTS.md), with a
Holm correction over the four stratified p values:

  scenes_10_50   pyramid accuracy at 10 ms over accuracy at 50 ms (natural scenes)
  scenes_d25     25 ms detail alone as a share of the whole-window count
  movie_10_best  10 ms level over the best level, 250 ms movie segments
  dg_gain2000    best level minus the count, 40 grating conditions, 2 s window

Secondary (reported, not corrected): 5 ms over 50 ms on the scenes, the 50 over
125 ms detail ratio, the 10 ms jitter cost at the 10 ms level, the movie's
1 s best bin width.

A sample enters a stimulus's tests when its best level decodes that stimulus
at three times chance or more (this drops LP of 750749662 from the scenes).

    PYTHONPATH=. python scripts/stats_tissue.py
Output: results/stats_tissue.json and a table on stdout.
"""
from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

import numpy as np

RES = Path("results")
D = "cum_nested_logreg"
THAL = {"LGd", "LP"}
SCENES = [("732592105", "VISp"), ("798911424", "VISp"), ("754829445", "VISp"), ("763673393", "VISp"),
          ("757216464", "VISp"), ("750749662", "VISp"), ("732592105", "VISal"), ("798911424", "VISal"),
          ("798911424", "VISl"), ("732592105", "VISrl"), ("732592105", "VISpm"), ("798911424", "VISam"),
          ("763673393", "VISam"), ("754829445", "LGd"), ("763673393", "LGd"), ("750749662", "LGd"),
          ("754829445", "LP"), ("757216464", "LP"), ("750749662", "LP")]
MAX_EXACT = 200_000  # beyond this many relabellings, draw MAX_EXACT at random instead


def _found(pattern, cut):
    out = []
    for f in sorted(RES.glob(pattern)):
        sid, area = f.stem[len("gratings_allen_"):].replace(cut, "").split("_")[:2]
        out.append((sid, area))
    return out


# samples with gratings and movie runs; scenes samples without the full E3 pipeline are read
# from the gratings run's scenes readouts (same pyramid, decoder, split and units; equal to three
# decimals on the seven samples that have both)
MOVIE = _found("gratings_allen_*_movie.json", "_movie")
SCENES = list(dict.fromkeys(SCENES + [x for x in _found("gratings_allen_*.json", "_movie")
                                       if (RES / f"gratings_allen_{x[0]}_{x[1]}.json").exists()]))
PRIMARY = ("scenes_10_50", "scenes_d25", "movie_10_best", "dg_gain2000")


def scenes_metrics():
    out = []
    for sid, area in SCENES:
        k = f"allen_{sid}_{area}"
        if (RES / f"e3_{k}_n60.json").exists():
            runs = json.load(open(RES / f"e3_{k}_n60.json"))["runs"]
            pyr = np.array([r["pyramid"][D]["clean"] for r in runs]).mean(0)
            j10 = (np.array([r["pyramid"][D]["clean"] for r in runs]) - np.array([r["pyramid"][D]["jitter_10ms"] for r in runs])).mean(0)
            det = np.array(json.load(open(RES / f"residual_{k}.json"))["mean"]["n60"]["detail"])
        else:
            g = json.load(open(RES / f"gratings_{k}.json"))["mean"]
            pyr = np.array(g["scenes/w250/img/pyramid"])
            j10 = pyr - np.array(g["scenes/w250/img/jitter10"])
            det = np.array(g["scenes/w250/img/detail"])
        if pyr.max() < 3 / 118:
            continue
        out.append(dict(sid=sid, area=area, scenes_10_50=pyr[4] / pyr[2], scenes_d25=det[3] / det[0],
                        scenes_5_50=pyr[5] / pyr[2], scenes_d50_d125=det[2] / det[1], scenes_jit10=j10[4]))
    return out


def stim_metrics():
    out = []
    for sid, area in MOVIE:
        m = json.load(open(RES / f"gratings_allen_{sid}_{area}_movie.json"))
        g = json.load(open(RES / f"gratings_allen_{sid}_{area}.json"))
        p = np.array(m["mean"]["movie/w250/seg/pyramid"])
        q = np.array(m["mean"]["movie/w1000/seg/pyramid"])
        c = np.array(g["mean"]["dg/w2000/cond/pyramid"])
        row = dict(sid=sid, area=area)
        if p.max() >= 3 / 120:
            row.update(movie_10_best=p[4] / p.max(), movie_1s_bin=np.log2(m["levels"]["w1000"][int(np.argmax(q))]))
        if c.max() >= 3 / 40:
            row["dg_gain2000"] = c.max() - c[0]
        out.append(row)
    return out


def test(rows, key, n_boot=10000, seed=0):
    rows = [r for r in rows if key in r]
    x = np.array([r[key] for r in rows])
    t = np.array([r["area"] in THAL for r in rows])
    animal = np.array([r["sid"] for r in rows])
    obs = x[t].mean() - x[~t].mean()

    def null(groups, seed=1):
        # every assignment of the thalamic labels that keeps the count per group,
        # or MAX_EXACT random ones (the observed one included) when there are more
        sizes = [float(math.comb(len(g), int(t[g].sum()))) for g in groups]
        if np.prod(sizes) > MAX_EXACT:
            rg = np.random.default_rng(seed)
            stats = [obs]
            for _ in range(MAX_EXACT - 1):
                tt = np.zeros(len(x), dtype=bool)
                for gidx in groups:
                    tt[rg.choice(gidx, int(t[gidx].sum()), replace=False)] = True
                stats.append(x[tt].mean() - x[~tt].mean())
            return np.array(stats), False
        per = []
        for gidx in groups:
            k = t[gidx].sum()
            per.append([gidx[list(c)] for c in itertools.combinations(range(len(gidx)), k)])
        stats = []
        for combo in itertools.product(*per):
            tt = np.zeros(len(x), dtype=bool)
            for c in combo:
                tt[c] = True
            stats.append(x[tt].mean() - x[~tt].mean())
        return np.array(stats), True

    strat, exact_s = null([np.nonzero(animal == a)[0] for a in np.unique(animal)])
    pooled, exact_p = null([np.arange(len(x))])
    p_s = float(np.mean(np.abs(strat) >= abs(obs) - 1e-12))
    p_p = float(np.mean(np.abs(pooled) >= abs(obs) - 1e-12))

    rng = np.random.default_rng(seed)
    animals = np.unique(animal)
    boots = []
    while len(boots) < n_boot:
        pick = rng.choice(animals, len(animals))
        idx = np.concatenate([rng.choice(np.nonzero(animal == a)[0], (animal == a).sum()) for a in pick])
        if t[idx].any() and (~t[idx]).any():
            boots.append(x[idx][t[idx]].mean() - x[idx][~t[idx]].mean())
    lo, hi = np.percentile(boots, [2.5, 97.5])
    ctx = x[~t]
    inside = int(((x[t] >= ctx.min()) & (x[t] <= ctx.max())).sum())
    return dict(n_thal=int(t.sum()), n_ctx=int((~t).sum()), n_animals=len(animals),
                thal_mean=float(x[t].mean()), ctx_mean=float(ctx.mean()),
                thal_range=[float(x[t].min()), float(x[t].max())], ctx_range=[float(ctx.min()), float(ctx.max())],
                diff=float(obs), ci95=[float(lo), float(hi)], p_stratified=p_s, p_pooled=p_p,
                exact_stratified=exact_s, exact_pooled=exact_p,
                n_animals_both=int(sum(t[animal == a].any() and (~t[animal == a]).any() for a in animals)),
                n_perm_stratified=len(strat), n_perm_pooled=len(pooled), thal_inside_ctx_range=inside)


def holm(ps):
    order = np.argsort(ps)
    adj = np.empty(len(ps))
    run = 0.0
    for i, j in enumerate(order):
        run = max(run, (len(ps) - i) * ps[j])
        adj[j] = min(1.0, run)
    return adj


def main():
    sc, st = scenes_metrics(), stim_metrics()
    keys = {"scenes_10_50": sc, "scenes_d25": sc, "movie_10_best": st, "dg_gain2000": st,
            "scenes_5_50": sc, "scenes_d50_d125": sc, "scenes_jit10": sc, "movie_1s_bin": st}
    res = {k: test(rows, k) for k, rows in keys.items()}
    adj = holm(np.array([res[k]["p_stratified"] for k in PRIMARY]))
    for k, a in zip(PRIMARY, adj):
        res[k]["p_stratified_holm"] = float(a)
    out = {"primary": list(PRIMARY), "results": res,
           "samples": {"scenes": [f"{r['area']} {r['sid']}" for r in sc], "movie_gratings": [f"{r['area']} {r['sid']}" for r in st]}}
    (RES / "stats_tissue.json").write_text(json.dumps(out, indent=1))
    print(f"{'metric':16s} {'thal n':>6s} {'ctx n':>5s} {'anim':>4s} {'thal mean':>9s} {'ctx mean':>8s} {'diff':>7s} "
          f"{'95% CI':>16s} {'p strat':>8s} {'(perms)':>7s} {'p pooled':>8s} {'Holm':>6s} {'thal in ctx range':>17s}")
    for k, r in res.items():
        h = f"{r['p_stratified_holm']:.3f}" if "p_stratified_holm" in r else ""
        print(f"{k:16s} {r['n_thal']:6d} {r['n_ctx']:5d} {r['n_animals']:4d} {r['thal_mean']:9.3f} {r['ctx_mean']:8.3f} "
              f"{r['diff']:+7.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] {r['p_stratified']:8.3f} {r['n_perm_stratified']:7d} "
              f"{r['p_pooled']:8.4f} {h:>6s} {r['thal_inside_ctx_range']:>8d} of {r['n_thal']}")
    print("wrote results/stats_tissue.json")


if __name__ == "__main__":
    main()
