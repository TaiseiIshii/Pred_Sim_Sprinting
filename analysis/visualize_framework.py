"""
visualize_framework.py
Figure 1: the research framework / logical chain of the thesis, drawn as a flow
diagram so the causal claims and their evidential status are explicit:
  imposed pelvic tilt -> [opt-OFF: no effect] vs [opt-ON: hip flexion -> fascicle
  length -> force/eccentric -> mechanical loading surrogate] -> optimisation
  (same speed, lower loading) -> individualised strategy, with an explicit
  boundary that the loading surrogate is NOT the injury risk itself.
All numbers shown were verified in this session's analyses.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "..", "Results", "PelvicShift_Study")


def box(ax, x, y, w, h, text, fc, ec="#333333", fs=9, tc="black"):
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                       boxstyle="round,pad=0.02,rounding_size=0.02",
                       linewidth=1.4, edgecolor=ec, facecolor=fc, zorder=2)
    ax.add_patch(p)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc,
            zorder=3, wrap=True)


def arrow(ax, x0, y0, x1, y1, color="#333333", style="-|>", lw=1.6, ls="-"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style,
                                 mutation_scale=16, linewidth=lw, color=color,
                                 linestyle=ls, zorder=1))


def main():
    fig, ax = plt.subplots(figsize=(11, 8.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    G = "#e8e8e8"      # grey (opt-off / no effect)
    B = "#d6e6f5"      # blue (kinematics)
    R = "#f6d6d6"      # red (loading)
    Gr = "#d7ede0"     # green (optimisation win)
    Y = "#fdf2c8"      # yellow (intervention)

    box(ax, 5, 9.4, 5.6, 0.8,
        "Imposed anterior pelvic tilt at touchdown\n(predictive optimal-control constraint)",
        "#cfe0f0", fs=10)

    # two branches
    arrow(ax, 3.8, 9.0, 2.4, 8.2)
    arrow(ax, 6.2, 9.0, 7.6, 8.2)

    box(ax, 2.2, 7.8, 3.6, 1.0,
        "opt-OFF: change tilt only,\nhold Nominal hip & knee",
        G, fs=9)
    box(ax, 7.8, 7.8, 3.6, 1.0,
        "opt-ON: re-optimise the\nwhole sprint (pelvis pinned)",
        B, fs=9)

    arrow(ax, 2.2, 7.3, 2.2, 6.6, color="#888")
    box(ax, 2.2, 6.1, 3.6, 1.0,
        "Hamstring MTU length\nUNCHANGED (0.000 mm)\n→ direct tilt effect = 0",
        G, fs=9)

    arrow(ax, 7.8, 7.3, 7.8, 6.9)
    box(ax, 7.8, 6.4, 3.6, 0.9, "Hip flexion ↑  (tilt→hip r = −1.00)", B, fs=9)
    arrow(ax, 7.8, 5.95, 7.8, 5.6)
    box(ax, 7.8, 5.1, 3.6, 0.9,
        "Biarticular fascicle length ↑\n(R² > 0.99; mono bifemsh flat)", B, fs=9)
    arrow(ax, 7.8, 4.65, 7.8, 4.3)
    box(ax, 7.8, 3.8, 3.6, 1.0,
        "Contractile & eccentric force ↑\n(semimem R²0.97; BFlh force flat)", R, fs=9)

    # merge to loading surrogate
    arrow(ax, 2.2, 5.6, 2.2, 3.0, color="#888", ls="--")
    ax.text(2.2, 4.3, "no change\n(reference)", ha="center", va="center",
            fontsize=8, color="#888")
    arrow(ax, 7.8, 3.3, 5.2, 2.7)

    box(ax, 3.6, 2.4, 4.6, 0.9,
        "Mechanical loading surrogate\n(peak fascicle strain, eccentric force)",
        R, fs=9)

    # optimisation intervention
    arrow(ax, 5.0, 6.4, 6.0, 6.4, color="#c78a00", lw=1.4)
    box(ax, 5.0, 6.4, 2.2, 1.5,
        "Add fascicle-\noverstretch\npenalty &\nre-optimise", Y, fs=8.5)
    arrow(ax, 5.0, 5.65, 5.0, 3.0, color="#c78a00", ls=":")

    box(ax, 3.6, 1.15, 4.6, 0.8,
        "Same speed (−0.24%), lower loading (−3.9%)\n→ individualised (Nom free-lunch / Short needs training)",
        Gr, fs=8.5)
    arrow(ax, 3.6, 1.95, 3.6, 1.55, color="#2a7")

    # epistemic boundary box (dashed)
    b = FancyBboxPatch((6.2 - 0.02, 0.55), 3.6, 1.5,
                       boxstyle="round,pad=0.03", linewidth=1.6,
                       edgecolor="#b00", facecolor="#fff", linestyle="--", zorder=2)
    ax.add_patch(b)
    ax.text(8.0, 1.3,
            "EVIDENTIAL BOUNDARY\nloading surrogate ≠ injury risk\n"
            "(NOT tested here; epidemiology:\nBFlh most injured, PMID 32443515)",
            ha="center", va="center", fontsize=8, color="#b00", zorder=3)
    arrow(ax, 5.9, 2.2, 6.2, 1.6, color="#b00", ls="--", style="-|>")

    ax.text(5, 0.15, "Figure 1  Research framework and evidential status of each link "
            "(all numbers verified from saved simulations)",
            ha="center", va="center", fontsize=10, fontweight="bold")
    fig.tight_layout()
    p = os.path.join(OUTDIR, "fig1_framework.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print("wrote", os.path.relpath(p, HERE))


if __name__ == "__main__":
    main()
