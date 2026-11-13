"""Figure for the stimuli beyond the scenes, and the tissue test.

  A  the natural movie in 250 ms segments: accuracy relative to the 50 ms level
  B  the natural movie in 1000 ms segments: accuracy relative to the best level
  C  drifting gratings, 40 conditions, 2 s window: accuracy relative to the count
  D  the scenes test metric (10 ms level / 50 ms level) per sample, by animal,
     with the stratified and pooled p values of scripts/stats_tissue.py

    PYTHONPATH=. python scripts/plot_stimuli.py
Output: results/summary_stimuli.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stats_tissue import MOVIE, THAL, scenes_metrics  # noqa: E402

BLUE, ORANGE, AQUA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#6b7280"
RES = Path("results")


def color(area):
    return ORANGE if area == "LGd" else AQUA if area == "LP" else BLUE


def axes_common(ax, title):
    ax.set_title(title, loc="left", fontsize=10.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e7eb", lw=0.8)
    ax.set_axisbelow(True)


def curves(ax, key, rel, title, ylabel, tag, labels=True):
    for sid, area in MOVIE:
        f = RES / f"gratings_allen_{sid}_{area}{tag}.json"
        r = json.load(open(f))
        p = np.array(r["mean"][key])
        w = key.split("/")[1]
        lv = r["levels"][w]
        if p.max() < 3 * r["chance"].get(f"seg_{w}", r["chance"].get("cond", 0)):
            continue
        ref = {"best": p.max(), "count": p[0], "l50": p[lv.index(50)]}[rel]
        lw = 1.8 if area in ("VISp", "LGd", "LP") else 1.2
        al = 1.0 if area in ("VISp", "LGd", "LP") else 0.55
        ax.plot(range(len(lv)), p - ref, "-o", color=color(area), lw=lw, alpha=al, ms=3.5)
        if labels:
            ax.annotate(f"{area} {sid[-3:]}", (len(lv) - 1, p[-1] - ref), xytext=(4, 0), textcoords="offset points",
                        fontsize=7, color="#4b5563", va="center")
    ax.set_xticks(range(len(lv)))
    ax.set_xticklabels([str(x) for x in lv[:-1]] + [f"{lv[-1]} ms"])
    ax.set_xlabel("bin width")
    ax.set_ylabel(ylabel)
    ax.axhline(0, color=GRAY, lw=0.8, ls=":")
    axes_common(ax, title)


def tissue_panel(ax):
    rows = scenes_metrics()
    st = json.load(open(RES / "stats_tissue.json"))["results"]["scenes_10_50"]
    # animals ordered by the thalamus-minus-cortex difference, cortex-only animals first
    def gap(a):
        th = [r["scenes_10_50"] for r in rows if r["sid"] == a and r["area"] in THAL]
        cx = [r["scenes_10_50"] for r in rows if r["sid"] == a and r["area"] not in THAL]
        return np.mean(th) - np.mean(cx) if th and cx else -1
    animals = sorted({r["sid"] for r in rows}, key=gap)
    for i, a in enumerate(animals):
        for r in rows:
            if r["sid"] != a:
                continue
            th = r["area"] in THAL
            x = i + (0.12 if th else -0.12)
            ax.scatter(x, r["scenes_10_50"], s=36, color=color(r["area"]), edgecolor="white", lw=1.5, zorder=3)
    ax.set_xticks(range(len(animals)))
    ax.set_xticklabels([a[-3:] for a in animals], fontsize=8)
    ax.set_xlabel("animal (session id, last three digits), ordered by thalamus minus cortex")
    ax.set_ylabel("scenes: accuracy at 10 ms / at 50 ms")
    ax.set_ylim(0.72, 1.03)
    ax.text(0.98, 0.04, f"thalamus {st['thal_mean']:.2f}, cortex {st['ctx_mean']:.2f}; thalamus higher in "
                        f"{sum(gap(a) > 0 for a in animals)} of {st['n_animals_both']} animals with both\n"
                        f"p = {st['p_stratified']:.4f} within animals (Holm {st['p_stratified_holm']:.4f}); "
                        f"{st['thal_inside_ctx_range']} of {st['n_thal']} thalamic samples (all LP) in the cortical range",
            transform=ax.transAxes, fontsize=7.5, color="#374151", ha="right")
    ax.scatter([], [], color=BLUE, s=30, label="cortex")
    ax.scatter([], [], color=ORANGE, s=30, label="LGd")
    ax.scatter([], [], color=AQUA, s=30, label="LP")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    axes_common(ax, "D  Thalamus against cortex on the scenes, per animal")


def main():
    fig, axs = plt.subplots(2, 2, figsize=(13, 9))
    curves(axs[0, 0], "movie/w250/seg/pyramid", "l50", "A  Natural movie, 250 ms segments (120 labels): no onsets",
           "accuracy minus accuracy at 50 ms", "_movie", labels=False)
    curves(axs[0, 1], "movie/w1000/seg/pyramid", "best", "B  Natural movie, 1000 ms segments (30 labels)",
           "accuracy minus best level", "_movie", labels=False)
    curves(axs[1, 0], "dg/w2000/cond/pyramid", "count", "C  Drifting gratings, 40 conditions, 2 s window",
           "accuracy minus whole-window count", "", labels=False)
    tissue_panel(axs[1, 1])
    for ax in axs.flat[:3]:
        ax.plot([], [], color=BLUE, label="cortex")
        ax.plot([], [], color=ORANGE, label="LGd")
        ax.plot([], [], color=AQUA, label="LP")
        ax.legend(frameon=False, fontsize=8, loc="upper left" if ax is axs[1, 0] else "lower left")
    fig.suptitle(f"Beyond the scenes: natural movie and drifting gratings in {len({s for s, _ in MOVIE})} animals "
                 "(60 units, 5 seeds, time-blocked); "
                 "cortex blue, LGd orange, LP aqua", fontsize=11, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(RES / "summary_stimuli.png", dpi=130)
    print("wrote results/summary_stimuli.png")


if __name__ == "__main__":
    main()
