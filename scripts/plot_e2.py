"""Plot E2: decoding accuracy by level for every planted code.

    python scripts/plot_e2.py results/e2.json results/e2.png
"""
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SERIES = [
    ("codes_mean", "Tokenizer codes", "#2563eb", "-"),
    ("qpyramid_mean", "Quantized pyramid (matched bits)", "#d97706", "-"),
    ("pyramid_mean", "Continuous pyramid (ceiling)", "#6b7280", "--"),
]
TITLES = {
    "rate": "Rate code", "timing_p125": "Shape, 125 ms", "timing_p50": "Timing, 50 ms",
    "timing_p25": "Timing, 25 ms", "timing_p10": "Timing, 10 ms", "timing_p5": "Timing, 5 ms",
    "mixed": "Mixed (weak rate + 10 ms)", "control": "Control, 2 ms (unresolvable)",
}


def main(path_in, path_out):
    res = json.load(open(path_in))
    widths = res["level_widths_ms"]
    conds = res["conditions"]
    fig, axes = plt.subplots(2, 4, figsize=(15, 7), sharey=True)
    xs = list(range(1, len(widths) + 1))
    for ax, c in zip(axes.flat, conds):
        if c["expected_level"]:
            ax.axvspan(c["expected_level"] - 0.4, c["expected_level"] + 0.4, color="#e5e7eb", zorder=0)
        ax.axhline(c["chance"], color="#9ca3af", lw=0.8, ls=":")
        for key, label, color, ls in SERIES:
            ax.plot(xs, c[key], ls, color=color, marker="o", ms=4, lw=1.8, label=label)
        verdict = {True: "pass", False: "FAIL", None: "descriptive"}[c["passed"]]
        ax.set_title(f"{TITLES.get(c['name'], c['name'])}  [{verdict}]", fontsize=10)
        ax.set_xticks(xs)
        ax.set_xticklabels([f"L{i}\n{w}ms" for i, w in zip(xs, widths)], fontsize=8)
        ax.set_ylim(0, 1.05)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0, 0].set_ylabel("Held-out accuracy")
    axes[1, 0].set_ylabel("Held-out accuracy")
    axes[0, 0].legend(fontsize=8, loc="lower left", frameon=False)
    fig.suptitle("E2: where each planted code appears (shaded = expected level, dotted = chance)",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(path_out, dpi=150)
    print("wrote", path_out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
