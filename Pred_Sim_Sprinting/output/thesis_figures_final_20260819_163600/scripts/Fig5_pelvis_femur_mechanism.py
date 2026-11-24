"""
Fig5_pelvis_femur_mechanism.py  (base python) -- render Figure 5 from the OpenSim
waveforms produced by Fig5_compute_mtu.py.

Panel A : schematic of the 3 geometric boundary conditions (tree-rigid / femur-fixed /
          adaptive) -- pelvis axis, femur axis, hip relative angle.
Panels B-E: dMTU length waveforms vs Nominal (mm) per muscle, 3 series, TS shaded.
Panel F : terminal-swing peak dMTU, femur-fixed vs adaptive (biarticular), with fixed/adaptive %.

A (tree-rigid) and B (femur-fixed) are GEOMETRIC counterfactuals, not dynamically feasible
running; only C (adaptive) satisfies the model constraints.  fixed/adaptive % is a peak
RATIO, NOT a statistical mediation fraction or an independent-contribution share of tilt.
"""
import csv
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

plt = C.setup_mpl()
import matplotlib.gridspec as gridspec
from matplotlib.patches import Arc
from datetime import datetime

WAVES = os.path.join(C.SRC, "Fig5_mtu_waveforms_source.csv")
PEAKS = os.path.join(C.SRC, "Fig5_mtu_peaks_source.csv")
SERIES = [("tree_rigid", "tree-rigid", "#8c8c8c", ":"),
          ("femur_fixed", "femur-fixed", "#e08214", "--"),
          ("adaptive", "adaptive", "#000000", "-")]
MUSMAP = {"semimem_l": "semimem", "semiten_l": "semiten",
          "bifemlh_l": "bifemlh", "bifemsh_l": "bifemsh"}
TS_PCT = 85.0


def load_waves():
    w = {}
    for r in csv.DictReader(open(WAVES, encoding="utf-8")):
        w.setdefault(r["muscle"], {}).setdefault(r["series"], ([], []))
        w[r["muscle"]][r["series"]][0].append(float(r["phase_pct"]))
        w[r["muscle"]][r["series"]][1].append(float(r["dMTU_mm"]))
    return w


def draw_cfg(ax, cx, ptilt, fang, ghost=None, label="", sublabel=""):
    """Schematic: pelvis segment + femur segment at a hip pivot (deg; not to scale)."""
    hy = 0.52
    Lp, Lf = 0.30, 0.34
    def pelvis_pts(a):
        rad = math.radians(a)
        dx, dy = math.cos(rad) * Lp / 2, math.sin(rad) * Lp / 2
        return [cx - dx, cx + dx], [hy - dy, hy + dy]
    def femur_pts(f):
        rad = math.radians(f)
        return [cx, cx + Lf * math.sin(rad)], [hy, hy - Lf * math.cos(rad)]
    if ghost is not None:
        gp, gf = ghost
        xp, yp = pelvis_pts(gp); ax.plot(xp, yp, color="0.75", lw=3, solid_capstyle="round", zorder=1)
        xf, yf = femur_pts(gf); ax.plot(xf, yf, color="0.8", lw=2, zorder=1)
    xp, yp = pelvis_pts(ptilt); ax.plot(xp, yp, color="#2166ac", lw=4, solid_capstyle="round", zorder=3)
    xf, yf = femur_pts(fang); ax.plot(xf, yf, color="#b2182b", lw=2.6, zorder=3)
    ax.plot(cx, hy, "o", color="black", ms=4, zorder=4)
    # hip relative angle arc between pelvis-normal (downward) and femur
    pnorm = ptilt - 90.0
    a0 = min(pnorm, -90.0 + fang if False else (-90.0 + fang))
    ax.add_patch(Arc((cx, hy), 0.20, 0.20, angle=0, theta1=min(pnorm, fang - 90),
                     theta2=max(pnorm, fang - 90), color="0.35", lw=1.0))
    ax.text(cx, 0.90, label, ha="center", va="center", fontsize=8, fontweight="bold")
    ax.text(cx, 0.06, sublabel, ha="center", va="center", fontsize=6.0, color="0.35")


def main():
    waves = load_waves()
    peaks = {r["muscle"]: r for r in csv.DictReader(open(PEAKS, encoding="utf-8"))}
    delta = float(next(iter(peaks.values()))["delta_pelvis_deg"])

    fig = plt.figure(figsize=(8.8, 8.4))
    gs = gridspec.GridSpec(3, 3, height_ratios=[0.85, 1.0, 1.0], hspace=0.5, wspace=0.32)
    axA = fig.add_subplot(gs[0, :])
    axB = fig.add_subplot(gs[1, 0]); axC = fig.add_subplot(gs[1, 1]); axD = fig.add_subplot(gs[1, 2])
    axE = fig.add_subplot(gs[2, 0]); axF = fig.add_subplot(gs[2, 1:])

    # Panel A schematic --------------------------------------------------
    axA.set_xlim(0, 3); axA.set_ylim(0, 1.0); axA.axis("off")
    axA.set_title(f"A  Boundary-condition schematic \u2014 anterior tilt {-delta:+.0f} deg at touchdown "
                  "(pelvis blue, femur red; not to scale)",
                  loc="left", fontweight="bold", fontsize=9.2)
    p0, f0 = 12.0, 18.0            # nominal pelvis tilt / femur angle (schematic)
    dv = 14.0                      # visual exaggeration of the anterior-tilt increment
    draw_cfg(axA, 0.5, p0 + dv, f0 + dv, ghost=(p0, f0), label="tree-rigid",
             sublabel="pelvis & femur co-rotate\nhip angle preserved -> dMTU ~ 0")
    draw_cfg(axA, 1.5, p0 + dv, f0, ghost=(p0, f0), label="femur-fixed",
             sublabel="femur world pose held\nhip angle changes")
    draw_cfg(axA, 2.5, p0 + dv, f0 + dv * 0.35, ghost=(p0, f0), label="adaptive",
             sublabel="whole body re-optimized\n(only feasible solution)")

    # Panels B-E waveforms ----------------------------------------------
    allv = []
    for mm in waves:
        for s, _, _, _ in SERIES:
            if s in waves[mm]:
                allv += waves[mm][s][1]
    ylo, yhi = min(allv) - 0.6, max(allv) + 0.8
    for ax, mkey in zip((axB, axC, axD, axE), ["semimem_l", "semiten_l", "bifemlh_l", "bifemsh_l"]):
        ax.axvspan(TS_PCT, 100, color="0.90", zorder=0)
        ax.axhline(0, color="0.6", lw=0.8, zorder=1)
        for s, lab, col, ls in SERIES:
            if s in waves[mkey]:
                ph, v = waves[mkey][s]
                ax.plot(ph, v, color=col, ls=ls, lw=1.6, label=lab, zorder=2)
        nm = MUSMAP[mkey]
        ax.set_title(f"{C.SHORT[nm]}  ({C.LABELS_EN[nm]})", loc="left", fontsize=8.6,
                     color=C.COLORS[nm], fontweight="bold")
        ax.set_xlim(0, 100); ax.set_ylim(ylo, yhi)
        ax.set_xlabel("% phase"); ax.set_ylabel("dMTU from Nominal (mm)")
    axB.legend(loc="upper left", fontsize=6.0, frameon=False)

    # Panel F bars -------------------------------------------------------
    biartic = ["semimem_l", "semiten_l", "bifemlh_l"]
    x = np.arange(len(biartic))
    Bpk = [float(peaks[m]["B_femur_fixed_TSpeak_mm"]) for m in biartic]
    Cpk = [float(peaks[m]["C_adaptive_TSpeak_mm"]) for m in biartic]
    ratio = [float(peaks[m]["fixed_over_adaptive_pct"]) for m in biartic]
    axF.bar(x - 0.19, Cpk, 0.36, color="#4a4a4a", label="adaptive (feasible)")
    axF.bar(x + 0.19, Bpk, 0.36, color="#e08214", label="femur-fixed (counterfactual)")
    for xi, (b, c, r) in enumerate(zip(Bpk, Cpk, ratio)):
        axF.text(xi, max(b, c) + 0.15, f"{r:.0f}%", ha="center", fontsize=7.5, fontweight="bold")
    axF.set_xticks(x); axF.set_xticklabels([C.SHORT[MUSMAP[m]] for m in biartic])
    axF.set_ylabel("terminal-swing peak dMTU (mm)")
    axF.set_title("F  Femur-fixed vs adaptive terminal-swing peak", loc="left", fontweight="bold", fontsize=8.8)
    axF.legend(loc="upper right", fontsize=6.6, frameon=False)
    axF.set_ylim(0, max(Cpk) + 1.6)
    axF.text(0.02, 0.97, "% = femur-fixed / adaptive peak ratio\n(NOT a mediation fraction or an\nindependent tilt-contribution share)",
             transform=axF.transAxes, fontsize=6.0, color="0.4", va="top")

    fig.suptitle("Figure 5 | Pelvis-femur coordination decomposition of biarticular hamstring MTU stretch",
                 fontsize=10.3, fontweight="bold", x=0.01, ha="left", y=1.0)
    fig.text(0.01, -0.01,
             "Terminal swing = last 15% of phase (boundary-analysis window). Tree-rigid & femur-fixed are geometric "
             "counterfactuals (not runnable); adaptive is the re-optimized N=100 max-tilt solution. MTU length from "
             "OpenSim 4.4 exact geometry, phase-normalized.", fontsize=6.2, color="0.35", ha="left")
    paths = C.save_fig(fig, "Fig5_pelvis_femur_mechanism")

    # copy the source CSVs' provenance into the manifest fragment
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common = dict(figure_id="Fig5", source_commit="e7b8de9", simulation_commit="e7b8de9",
                  analysis_commit="e7b8de9", mesh="N=100 (adaptive) + geometric counterfactuals",
                  condition_family="Nominal N=100 vs PelvisTDwide_m8 (adaptive); tree-rigid/femur-fixed",
                  solver_acceptance_rule="adaptive strict Solve_Succeeded",
                  muscle_names_and_indices="semimem_l/semiten_l/bifemlh_l/bifemsh_l (OpenSim MTU)",
                  source_csv="source_data/Fig5_mtu_waveforms_source.csv ; source_data/Fig5_mtu_peaks_source.csv",
                  plotting_script="scripts/Fig5_compute_mtu.py (opencap) + scripts/Fig5_pelvis_femur_mechanism.py",
                  pdf_path=paths[0], svg_path=paths[1], png_path=paths[2],
                  generated_at=ts, qa_status="auto-pass (cross-checked vs audit); visual pending",
                  input_path="Scaled_FullBody_HamnerModel...osim; Nominal.mot; PelvisTDwide_m8.mot",
                  input_sha256="see sha256_manifest.csv")
    frags = [
        dict(common, panel_id="A", analytical_question="What are the 3 boundary conditions?",
             takeaway="tree-rigid co-rotates (hip preserved); femur-fixed holds femur; adaptive re-optimizes.",
             phase_window="schematic", metric_formula="conceptual pelvis/femur/hip diagram"),
        dict(common, panel_id="B-E", analytical_question="Is hamstring stretch explained by pelvis absolute angle or pelvis-femur configuration?",
             takeaway="tree-rigid dMTU~0; femur-fixed reproduces most of adaptive terminal-swing MTU rise.",
             phase_window="full phase; TS = last 15%", metric_formula="dMTU=10*(MTU-Nominal) mm, phase-normalized"),
        dict(common, panel_id="F", analytical_question="How much of adaptive terminal-swing stretch does femur-fixed explain?",
             takeaway="femur-fixed / adaptive TS peak = 89.6-95.8% for the 3 biarticular muscles.",
             phase_window="TS (last 15%)", metric_formula="100*B_peak/C_peak (ratio, not mediation)"),
    ]
    C.write_manifest_fragment("Fig5", frags)
    print("Fig5 done:", paths[2], "| y[%.2f,%.2f] delta=%+.0f" % (ylo, yhi, delta))


if __name__ == "__main__":
    main()
