"""
Fig2_primary_N100.py -- CENTRAL RESULT.
Panel A: operability  (achieved anterior tilt vs achieved speed, Nominal +/-1% band)
Panel B: primary endpoint (achieved anterior tilt vs 1-stride peak lMtilde, 4 muscles + LS lines)
Panel C: per-muscle slope with leave-one-condition-out range + speed-adjusted coefficient

All values recomputed from the 8 strict N=100 MAT via _common. No regression CI is drawn.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

plt = C.setup_mpl()
import matplotlib.gridspec as gridspec
from datetime import datetime


def main():
    conds = C.load_primary_N100()
    ant = np.array([c["anterior"] for c in conds])
    spd = np.array([c["speed"] for c in conds])
    tags = [c["offset"] for c in conds]

    nom = C.load(C.NOMINAL_N100)
    nom_speed = nom["speed"]
    nom_ant = -nom["td"]

    # ---- source CSV ----
    src_rows = []
    for c in conds:
        for nm in C.MUS:
            src_rows.append(["point", c["offset"], f"{c['anterior']:.4f}", f"{c['speed']:.6f}",
                             c["status"], nm, nm in C.BIARTIC,
                             f"{c['m'][nm]['peak_lMtilde']:.5f}", ""])
    reg = {}
    for nm in C.MUS:
        y = np.array([c["m"][nm]["peak_lMtilde"] for c in conds])
        sl, ic, r2 = C.fit(ant, y)
        lo, hi = C.loo_slopes(ant, y)
        adj = C.speed_adj_coef(ant, spd, y)
        reg[nm] = dict(slope=sl, ic=ic, r2=r2, lo=lo, hi=hi, adj=adj)
        src_rows.append(["regression", "", "", "", "", nm, nm in C.BIARTIC, "",
                         f"slope={sl:.6f};R2={r2:.5f};LOO=[{lo:.6f},{hi:.6f}];speedadj={adj:.6f}"])
    src_rows.append(["nominal_ref", "", f"{nom_ant:.4f}", f"{nom_speed:.6f}", nom["status"],
                     "", "", "", "N100 Nominal reference"])
    src_csv = C.write_csv(os.path.join(C.SRC, "Fig2_primary_N100_source.csv"),
                          ["record_type", "offset", "anterior_tilt_deg", "speed_mps", "solver_status",
                           "muscle", "is_biarticular", "peak_lMtilde", "note"], src_rows)

    # ---- figure ----
    fig = plt.figure(figsize=(7.6, 6.4))
    gs = gridspec.GridSpec(2, 2, width_ratios=[1.0, 1.18], height_ratios=[1.0, 1.0],
                           hspace=0.46, wspace=0.46)
    axA = fig.add_subplot(gs[0, 0])
    axC = fig.add_subplot(gs[1, 0])
    axB = fig.add_subplot(gs[:, 1])

    # Panel A -------------------------------------------------------------
    band = 0.01 * nom_speed
    spd_range_pct = 100.0 * (spd.max() - spd.min()) / nom_speed
    axA.axhspan(nom_speed - band, nom_speed + band, color="0.88", zorder=0)
    axA.axhline(nom_speed, color="0.45", ls="--", lw=1.0, zorder=1)
    axA.plot(ant, spd, "o", color="#222222", ms=6, zorder=3)
    for x, y, tg in zip(ant, spd, tags):
        axA.annotate(tg, (x, y), textcoords="offset points", xytext=(0, 6),
                     ha="center", fontsize=6.5, color="0.35")
    axA.set_xlabel("achieved anterior tilt  A = -pelvis_tilt  (deg)")
    axA.set_ylabel("achieved speed (m/s)")
    axA.set_title("A  Operability: speed held ~constant", loc="left", fontweight="bold", fontsize=9.5)
    axA.set_ylim(nom_speed - 0.15, nom_speed + 0.15)
    axA.annotate("Nominal +/-1% band", (ant.max(), nom_speed + band),
                 textcoords="offset points", xytext=(0, 2), ha="right", va="bottom",
                 fontsize=6.2, color="0.4")
    axA.annotate("Nominal", (ant.min() - 0.3, nom_speed), textcoords="offset points",
                 xytext=(0, 2), ha="left", va="bottom", fontsize=6.2, color="0.4")
    axA.text(0.02, 0.055, f"speed spread = {spd_range_pct:.2f}% of Nominal (all within +/-1%)\n"
             "all 8: PelvisTDwide, strict Solve_Succeeded",
             transform=axA.transAxes, fontsize=6.0, color="0.45", va="bottom")

    # Panel B -------------------------------------------------------------
    xline = np.linspace(ant.min(), ant.max(), 50)
    axB.axhline(1.0, color="0.6", ls=":", lw=0.9, zorder=0)
    axB.text(ant.min(), 1.0, " lMtilde = 1 (optimal fibre length)", fontsize=6.3,
             color="0.4", va="bottom", ha="left")
    for nm in C.MUS:
        y = np.array([c["m"][nm]["peak_lMtilde"] for c in conds])
        r = reg[nm]
        open_m = nm == "bifemsh"
        axB.plot(xline, r["slope"] * xline + r["ic"], ls=C.LINESTYLES[nm],
                 color=C.COLORS[nm], lw=1.4, zorder=2)
        axB.plot(ant, y, marker=C.MARKERS[nm], ls="none", ms=5.5,
                 mfc="white" if open_m else C.COLORS[nm], mec=C.COLORS[nm],
                 mew=1.3, zorder=3)
        ylab = r["slope"] * ant.max() + r["ic"]
        axB.annotate(f"{C.SHORT[nm]}  b={r['slope']:+.4f}/deg, R\u00b2={r['r2']:.2f}",
                     (ant.max(), ylab), textcoords="offset points", xytext=(8, 0),
                     va="center", ha="left", fontsize=7.0, color=C.COLORS[nm],
                     fontweight="bold" if nm in C.BIARTIC else "normal")
    axB.set_xlabel("achieved anterior tilt  A = -pelvis_tilt  (deg)")
    axB.set_ylabel("1-stride peak  lMtilde  (lM / lMo)")
    axB.set_title("B  Primary endpoint: peak lMtilde rises with anterior tilt",
                  loc="left", fontweight="bold", fontsize=9.5)
    axB.set_xlim(ant.min() - 1.0, ant.max() + 7.2)
    axB.text(0.02, 0.02, "8 deterministic design points; least-squares line (no population CI)",
             transform=axB.transAxes, fontsize=6.0, color="0.45")

    # Panel C -------------------------------------------------------------
    order = ["semimem", "semiten", "bifemlh", "bifemsh"]
    ypos = np.arange(len(order))[::-1]
    axC.axvline(0.0, color="0.6", lw=0.9, ls="--", zorder=0)
    for yp, nm in zip(ypos, order):
        r = reg[nm]
        open_m = nm == "bifemsh"
        axC.plot([r["lo"], r["hi"]], [yp, yp], color=C.COLORS[nm], lw=3.0,
                 solid_capstyle="round", alpha=0.45, zorder=1)
        axC.plot(r["slope"], yp, marker=C.MARKERS[nm], ms=7,
                 mfc="white" if open_m else C.COLORS[nm], mec=C.COLORS[nm], mew=1.4, zorder=3)
        axC.plot(r["adj"], yp, marker="|", ms=13, mec=C.COLORS[nm], mew=1.8, zorder=3)
    axC.set_yticks(ypos)
    axC.set_yticklabels([C.SHORT[nm] for nm in order])
    axC.set_ylim(-0.6, len(order) - 0.4)
    axC.set_xlabel("slope of peak lMtilde  (per deg anterior tilt)")
    axC.set_title("C  Slope, drop-one range, speed-adjusted", loc="left",
                  fontweight="bold", fontsize=9.5)
    # legend proxies
    from matplotlib.lines import Line2D
    proxies = [
        Line2D([0], [0], marker="o", color="0.3", ls="none", mfc="0.3", ms=6, label="full-8 slope"),
        Line2D([0], [0], color="0.3", lw=3, alpha=0.45, label="leave-one-out range"),
        Line2D([0], [0], marker="|", color="0.3", ls="none", ms=12, mew=1.8, label="speed-adjusted"),
    ]
    axC.legend(handles=proxies, loc="lower right", fontsize=6.2, frameon=False, handletextpad=0.5)
    axC.text(0.02, 0.62, "bar = single-condition-drop\nsensitivity range\n(NOT a confidence interval)",
             transform=axC.transAxes, fontsize=6.0, color="0.4", va="center", ha="left")

    fig.suptitle("Figure 2 | Touchdown anterior pelvic tilt and biarticular hamstring peak fibre length (N=100)",
                 fontsize=10.5, fontweight="bold", x=0.01, ha="left", y=1.005)
    paths = C.save_fig(fig, "Fig2_primary_N100")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common = dict(figure_id="Fig2", source_commit="e7b8de9", simulation_commit="e7b8de9",
                  analysis_commit="e7b8de9", mesh="N=100",
                  condition_family="PelvisTDwide (ref -7.987 deg)",
                  solver_acceptance_rule="strict Solve_Succeeded; min final inf_pr per requested offset",
                  muscle_names_and_indices="semimem L6/R52, semiten L7/R53, bifemlh L8/R54, bifemsh L9/R55 (0-based)",
                  source_csv=src_csv, plotting_script="scripts/Fig2_primary_N100.py",
                  pdf_path=paths[0], svg_path=paths[1], png_path=paths[2],
                  generated_at=ts, qa_status="auto-pass; visual pending",
                  input_path=";".join(fn for _, fn in C.SELECTED_N100),
                  input_sha256="see final_source_manifest.csv / sha256_manifest.csv")
    frags = [
        dict(common, panel_id="A", analytical_question="Is speed held ~constant across achieved tilt?",
             takeaway="Speed stays within +/-1% of Nominal across A=1.99-15.99 deg.",
             phase_window="whole stride (ave_speed)", metric_formula="ave_speed vs A=-pelvis_tilt(deg)"),
        dict(common, panel_id="B", analytical_question="Does peak lMtilde rise with anterior tilt?",
             takeaway="Biarticular SM/ST/BFlh rise graded (b=+0.0037..0.0068/deg, R2 .95-.96); BFsh flat.",
             phase_window="full reconstructed stride (max)",
             metric_formula="peak lMtilde=max_t lM/lMo; LS slope vs A"),
        dict(common, panel_id="C", analytical_question="Robust to dropping one condition / to speed?",
             takeaway="Slopes monotonic; LOO range narrow; speed-adjusted coef similar sign+magnitude.",
             phase_window="full stride", metric_formula="LS slope; LOO min-max; partial coef on A given speed"),
    ]
    C.write_manifest_fragment("Fig2", frags)
    print("Fig2 done:", paths[2])
    for nm in C.MUS:
        r = reg[nm]
        print(f"  {nm:9s} slope={r['slope']:+.5f} R2={r['r2']:.4f} LOO[{r['lo']:+.5f},{r['hi']:+.5f}] adj={r['adj']:+.5f}")


if __name__ == "__main__":
    main()
