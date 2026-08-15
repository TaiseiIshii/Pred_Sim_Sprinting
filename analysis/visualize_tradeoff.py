"""
visualize_tradeoff.py
Figure 6: the Experiment-2 speed <-> injury-related-loading trade-off for the
Nominal athlete (the "free-lunch" curve). x = sprint speed, twin y-axes show
peak fascicle strain surrogate and peak eccentric contractile force (both
relative to the untreated w=0 technique). The near-vertical initial segment is
the free-lunch region: large loading reduction for negligible speed cost.
Reads Results/HamPareto_Study/individual_force.csv (saved data only).
"""
import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "..", "Results", "HamPareto_Study")
CSV = os.path.join(OUTDIR, "individual_force.csv")


def load(athlete="Nom"):
    rows = [r for r in csv.DictReader(open(CSV, encoding="utf-8"))
            if r["athlete"] == athlete]
    for r in rows:
        for k in ("weight", "speed", "peakLM", "eccPeakFceNorm", "eccWorkJ",
                  "peakFceNorm"):
            r[k] = float(r[k])
    rows.sort(key=lambda r: r["weight"])
    return rows


def main():
    rows = load("Nom")
    s0 = rows[0]["speed"]
    l0 = rows[0]["peakLM"]
    e0 = rows[0]["eccPeakFceNorm"]
    dspeed = [100 * (s0 - r["speed"]) / s0 for r in rows]
    dstrain = [100 * (l0 - r["peakLM"]) / l0 for r in rows]
    decc = [100 * (e0 - r["eccPeakFceNorm"]) / e0 for r in rows]
    speed = [r["speed"] for r in rows]

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    ax.plot(dspeed, dstrain, "o-", color="#d62728", label="peak fascicle strain reduction")
    ax.plot(dspeed, decc, "s-", color="#1f77b4", label="peak eccentric force reduction")
    for i, r in enumerate(rows):
        ax.annotate(f"w={r['weight']:g}", (dspeed[i], dstrain[i]),
                    textcoords="offset points", xytext=(5, -9), fontsize=7,
                    color="#d62728")
    # free-lunch band: speed cost < 0.5%
    ax.axvspan(0, 0.5, color="green", alpha=0.08)
    ax.text(0.25, ax.get_ylim()[1] * 0.05, "free-lunch\n(<0.5% speed)", fontsize=8,
            ha="center", color="green")
    ax.set_xlabel("sprint speed cost (% vs untreated technique)")
    ax.set_ylabel("injury-related loading reduction (%)")
    ax.set_title("Figure 6  Speed<->safety trade-off (Nominal athlete)\n"
                 "steep initial slope = large loading cut for tiny speed cost")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9, loc="lower right")
    fig.tight_layout()
    p = os.path.join(OUTDIR, "fig6_speed_safety_tradeoff.png")
    fig.savefig(p, dpi=150)
    print("wrote", os.path.relpath(p, HERE))
    # print the knee (max reduction per unit speed cost)
    eff = [(dstrain[i] / dspeed[i]) if dspeed[i] > 1e-6 else np.inf
           for i in range(len(rows))]
    cand = [(rows[i]["weight"], dstrain[i], dspeed[i], eff[i])
            for i in range(1, len(rows)) if np.isfinite(eff[i])]
    if cand:
        knee = max(cand, key=lambda z: z[3])
        print(f"knee: w={knee[0]:g}  strain -{knee[1]:.1f}%  speed -{knee[2]:.2f}%  "
              f"efficiency {knee[3]:.1f}% strain per %speed")


if __name__ == "__main__":
    main()
