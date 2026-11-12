"""Cross-sample summary figure: eighteen area samples, six animals, one temporal profile per tissue.

Reads the merged E3 JSONs, the detail analyses (plain and rate-regressed) and
the latency readouts, and draws six panels: the pyramid relative to its 50 ms
level, each level's detail as a share of the whole-window count, the 125 and
50 ms details before and after rate and timing regression, the 10 ms jitter
cost, and learned codes against residual k-means.

    PYTHONPATH=. python scripts/plot_summary.py results/summary.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SAMPLES = [("732592105", "VISp"), ("798911424", "VISp"), ("754829445", "VISp"), ("763673393", "VISp"), ("757216464", "VISp"), ("750749662", "VISp"),
           ("732592105", "VISal"), ("798911424", "VISal"), ("798911424", "VISl"), ("732592105", "VISrl"), ("732592105", "VISpm"),
           ("798911424", "VISam"), ("763673393", "VISam"),
           ("754829445", "LGd"), ("763673393", "LGd"), ("750749662", "LGd"), ("754829445", "LP"), ("757216464", "LP")]
BLUE, ORANGE, AQUA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#6b7280"
GROUP = {"LGd": ("LGd", ORANGE), "LP": ("LP", AQUA)}
LEVELS = ["250", "125", "50", "25", "10", "5 ms"]
D = "cum_nested_logreg"


def load(res: Path):
    out = []
    for sid, area in SAMPLES:
        k = f"allen_{sid}_{area}"
        e3 = json.load(open(res / f"e3_{k}_n60.json"))
        runs = e3["runs"]
        pyr = np.array([r["pyramid"][D]["clean"] for r in runs])
        j10 = pyr - np.array([r["pyramid"][D]["jitter_10ms"] for r in runs])
        codes = np.array([r["codes"][D]["clean"] for r in runs])
        qpyr = np.array([r["qpyramid"][D]["clean"] for r in runs])
        rs = json.load(open(res / f"residual_{k}.json"))["mean"]["n60"]
        rr = json.load(open(res / f"residual_{k}_rate.json"))["mean"]["n60"]
        lat = json.load(open(res / f"latency_{k}.json"))["mean"]
        out.append(dict(
            name=f"{area} {sid[-3:]}", area=area, pyr=pyr.mean(0), j10=j10.mean(0), cq=(codes - qpyr).mean(0),
            detail=np.array(rs["detail"]), shuf=np.array(rs["shuffled"]), prate=np.array(rr["detail_poprate"]),
            lat2=lat["detail2_poplat"], lat3=lat["detail3_poplat"]))
    return out


def style(s):
    label, color = GROUP.get(s["area"], ("cortex", BLUE))
    lw = 1.8 if s["area"] in ("VISp", "LGd", "LP") else 1.2
    alpha = 1.0 if s["area"] in ("VISp", "LGd", "LP") else 0.55
    return label, color, lw, alpha


def axes_common(ax, title):
    ax.set_title(title, loc="left", fontsize=10.5)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color="#e5e7eb", lw=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=8.5)


def line_panel(ax, samples, key, title, ylabel, xs=range(6), levels=LEVELS, zero=True):
    axes_common(ax, title)
    seen = set()
    for s in samples:
        label, color, lw, alpha = style(s)
        ax.plot(list(xs), s[key], color=color, lw=lw, alpha=alpha, marker="o", ms=3,
                label=label if label not in seen else None)
        seen.add(label)
    if zero:
        ax.axhline(0, color="#9ca3af", lw=0.8, ls=":")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(levels, fontsize=8.5)
    ax.set_ylabel(ylabel, fontsize=9)


def chain_panel(ax, samples, level, title):
    axes_common(ax, title)
    k = level - 1
    xs = np.arange(len(samples))
    for i, s in enumerate(samples):
        label, color, lw, alpha = style(s)
        ys = [s["detail"][k], s["prate"][k], s["lat2"] if level == 2 else s["lat3"]]
        ax.plot([i, i, i], ys, color=color, lw=1.2, alpha=0.5)
        ax.scatter([i], [ys[0]], color=color, s=22, zorder=3, alpha=alpha)
        ax.scatter([i], [ys[1]], facecolor="white", edgecolor=color, s=22, zorder=3, lw=1.2, alpha=alpha)
        ax.scatter([i], [ys[2]], color=color, marker="_", s=90, zorder=3, lw=1.8, alpha=alpha)
        ax.scatter([i], [s["shuf"][k]], color=GRAY, marker="x", s=14, zorder=3, lw=0.9)
    ax.set_xticks(xs)
    ax.set_xticklabels([s["name"] for s in samples], rotation=60, ha="right", fontsize=7.5)
    ax.set_ylabel("held-out accuracy", fontsize=9)
    ax.set_ylim(0, max(s["detail"][k] for s in samples) * 1.45)
    ax.scatter([], [], color=GRAY, s=22, label="detail alone")
    ax.scatter([], [], facecolor="white", edgecolor=GRAY, s=22, lw=1.2, label="population-rate regressed")
    ax.scatter([], [], color=GRAY, marker="_", s=90, lw=1.8, label="rate and timing regressed")
    ax.scatter([], [], color=GRAY, marker="x", s=14, lw=0.9, label="time-shuffled control")
    ax.legend(fontsize=7.5, frameon=False, loc="upper left", ncol=2)


def main(out: str, res: str = "results"):
    samples = load(Path(res))
    chance = 1 / 118
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.6))
    a, b, c, d, e, f = axes.ravel()

    for s in samples:
        s["rel"] = s["pyr"] - s["pyr"][2]
        s["share"] = s["detail"] / s["detail"][0]
    line_panel(a, samples, "rel", "A  Continuous pyramid, accuracy relative to the 50 ms level",
               "accuracy minus accuracy at 50 ms")
    a.legend(fontsize=8, frameon=False, loc="lower center")
    a.text(5.0, -0.125, "cortex falls", fontsize=8, color="#52514e", va="top", ha="right")

    line_panel(b, samples, "share", "B  Each level's detail alone, as a share of the whole-window count",
               "detail accuracy / count accuracy", zero=False)
    sh = np.array([s["shuf"] / s["detail"][0] for s in samples])
    b.fill_between(range(6), sh.min(0), sh.max(0), color=GRAY, alpha=0.25, lw=0, label="time-shuffled control")
    b.set_ylim(0, 1.05)
    b.legend(fontsize=8, frameon=False, loc="upper right")

    chain_panel(c, samples, 2, "C  125 ms detail: alone, rate-regressed, timing-regressed")
    chain_panel(d, samples, 3, "D  50 ms detail: the same")
    for ax in (c, d):
        ax.axhline(chance, color="#9ca3af", lw=0.8, ls=":")

    line_panel(e, samples, "j10", "E  Cost of 10 ms spike jitter on the pyramid", "clean minus jittered accuracy")
    e.set_ylim(-0.015, 0.035)

    line_panel(f, samples, "cq", "F  Learned codes minus residual k-means at matched bits",
               "codes minus quantized pyramid")
    f.text(0.1, 0.055, "learned codes ahead", fontsize=8, color="#52514e")
    f.text(0.1, -0.085, "k-means ahead", fontsize=8, color="#52514e")
    f.set_ylim(-0.11, 0.09)

    for ax in (a, b, e, f):
        ax.set_xlabel("bin width", fontsize=9)
    fig.suptitle("Eighteen area samples, six mice, 60 units each, time-blocked holdout: cortex (blue, VISp bold), "
                 "LGd (orange), LP (aqua)", fontsize=11, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(out, dpi=150)
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/summary.png")
