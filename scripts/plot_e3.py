"""Plot E3 and E3b: per-level accuracy on one Allen session.

    python scripts/plot_e3.py results/e3_allen_732592105_VISp_n60.json results/e3_allen_732592105_VISp_n60.png

Four panels. A: the four readouts on the clean test set under the primary
(nested-C cumulative) decoder, with seed std. B: the continuous pyramid under
all four decoders. C and D: the pyramid and the codes under jitter and the
PSTH-matched surrogate.
"""
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

WIDTHS_MS = [250, 125, 50, 25, 10, 5]
PRIMARY = "cum_nested_logreg"
BLUE, ORANGE, AQUA, YELLOW, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#6b7280"
BLUES = ["#0d366b", "#2a78d6", "#5598e7", "#9ec5f4"]  # clean, then jitter 5, 10, 25 ms

READOUTS = [
    ("codes", "Tokenizer codes", BLUE, "-"),
    ("recon", "Tokenizer reconstruction", AQUA, "-"),
    ("qpyramid", "Quantized pyramid (matched bits)", ORANGE, "-"),
    ("pyramid", "Continuous pyramid (ceiling)", GRAY, "--"),
]
DECODERS = [
    ("cum_nested_logreg", "cumulative, nested C (primary)", BLUE, "-"),
    ("cum_pca100_logreg", "cumulative, PCA-100, C = 0.1", AQUA, "-"),
    ("logreg", "level k only, C = 0.1", ORANGE, "-"),
    ("pca100_logreg", "level k only, PCA-100, C = 0.1", YELLOW, "-"),
]
TEST_SETS = [
    ("clean", "clean", BLUES[0], "-"),
    ("jitter_5ms", "jitter 5 ms", BLUES[1], "-"),
    ("jitter_10ms", "jitter 10 ms", BLUES[2], "-"),
    ("jitter_25ms", "jitter 25 ms", BLUES[3], "-"),
    ("psth_surrogate", "PSTH-matched surrogate", ORANGE, "--"),
]


def seed_std(runs, feat, dec, test):
    return np.std([r[feat][dec][test] for r in runs], axis=0)


def style(ax, title, chance, ymax, **legend):
    xs = range(1, len(WIDTHS_MS) + 1)
    ax.axhline(chance, color="#9ca3af", lw=0.8, ls=":")
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"L{i}\n{w} ms" for i, w in zip(xs, WIDTHS_MS)], fontsize=8)
    ax.set_ylim(0, ymax)
    ax.grid(axis="y", color="#e5e7eb", lw=0.6)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=7.5, frameon=False, **({"loc": "upper left"} | legend))


def main(path_in, path_out):
    res = json.load(open(path_in))
    mean, runs, chance = res["mean"], res["runs"], res["chance"]
    xs = np.arange(1, len(WIDTHS_MS) + 1)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    (a, b), (c, d) = axes

    for feat, label, color, ls in READOUTS:
        y = np.array(mean[feat][PRIMARY]["clean"])
        a.errorbar(xs, y, yerr=seed_std(runs, feat, PRIMARY, "clean"), ls=ls, color=color,
                   marker="o", ms=4, lw=1.8, capsize=2, label=label)
    style(a, "A  Clean test set, nested-C cumulative decoder (bars: seed std)", chance, 0.55,
          loc="center left", bbox_to_anchor=(0.0, 0.6))
    a.set_ylabel("Held-out top-1 accuracy (118 images)")

    for dec, label, color, ls in DECODERS:
        b.plot(xs, mean["pyramid"][dec]["clean"], ls, color=color, marker="o", ms=4, lw=1.8, label=label)
    style(b, "B  Continuous pyramid, four decoders", chance, 0.55)

    for ax, feat, title, ymax, loc in ((c, "pyramid", "C  Continuous pyramid, E3b test sets", 0.55, "lower left"),
                                       (d, "codes", "D  Tokenizer codes, E3b test sets", 0.30, "upper left")):
        for test, label, color, ls in TEST_SETS:
            ax.plot(xs, mean[feat][PRIMARY][test], ls, color=color, marker="o", ms=4, lw=1.8, label=label)
        style(ax, title, chance, ymax, loc=loc)
    c.set_ylabel("Held-out top-1 accuracy (118 images)")

    fig.suptitle(f"E3 and E3b: Allen {res['name'].split('_')[2]} {res['name'].split('_')[1]}, {res['n_units']} units, "
                 f"{res['repeats']} seeds, time-blocked holdout (dotted: chance)", fontsize=11)
    fig.tight_layout()
    fig.savefig(path_out, dpi=150)
    print("wrote", path_out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
