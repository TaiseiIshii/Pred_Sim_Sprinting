"""
Fig3_lMtilde_waveforms_N100.py -- lMtilde vs % stride for the 8 N=100 conditions,
one small-multiple per muscle, coloured by achieved anterior tilt (darker = larger).

Peaks are read from the NATIVE-node metrics (exact, matches audit); the plotted
waveform is resampled to a common %-stride grid for display only.  Shared y-axis
across the 4 panels so magnitudes are directly comparable.  The muscle-metric
terminal-swing window (last 25% of swing) is shaded; the 1-stride max is marked.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

plt = C.setup_mpl()
import matplotlib.colors as mcolors
from matplotlib.cm import ScalarMappable
from datetime import datetime

GRID = np.linspace(0.0, 100.0, 201)


def main():
    conds = C.load_primary_N100()
    ant = np.array([c["anterior"] for c in conds])
    norm = mcolors.Normalize(vmin=ant.min(), vmax=ant.max())
    base = plt.get_cmap("Blues")
    tcmap = mcolors.LinearSegmentedColormap.from_list(
        "tiltBlues", [base(0.28 + 0.68 * t) for t in np.linspace(0, 1, 256)])

    # mean stance / terminal-swing window across the 8 conditions (visual guide)
    to_pcts, tsw_pcts = [], []
    for c in conds:
        strideT = 2.0 * c["d"]["totalTime"]
        to_pcts.append(100.0 * c["contact"] / strideT)
        tsw_pcts.append(c["m"]["semimem"]["tsw_start_pct"])
    to_pct = float(np.mean(to_pcts))
    tsw_pct = float(np.mean(tsw_pcts))

    # ---- waveforms + source CSV (long format) ----
    src_rows = []
    waves = {nm: [] for nm in C.MUS}
    for c in conds:
        for nm in C.MUS:
            wv = C.stride_waveform(c["d"], nm, GRID)["lMtilde"]
            waves[nm].append(wv)
            for p, v in zip(GRID, wv):
                src_rows.append([nm, c["offset"], f"{c['anterior']:.4f}", f"{p:.1f}", f"{v:.5f}"])
    src_csv = C.write_csv(os.path.join(C.SRC, "Fig3_lMtilde_waveforms_N100_source.csv"),
                          ["muscle", "offset", "anterior_tilt_deg", "pct_stride", "lMtilde"], src_rows)
    pk_rows = []
    for c in conds:
        for nm in C.MUS:
            pk_rows.append([nm, c["offset"], f"{c['anterior']:.4f}",
                            f"{c['m'][nm]['tPeak_pct']:.2f}", f"{c['m'][nm]['peak_lMtilde']:.5f}"])
    C.write_csv(os.path.join(C.SRC, "Fig3_peak_markers_N100_source.csv"),
                ["muscle", "offset", "anterior_tilt_deg", "tPeak_pct_stride", "peak_lMtilde"], pk_rows)

    # global y-range (shared)
    allv = np.concatenate([np.concatenate(waves[nm]) for nm in C.MUS])
    ylo, yhi = float(allv.min()) - 0.01, float(allv.max()) + 0.02

    fig, axes = plt.subplots(2, 2, figsize=(7.6, 6.0), sharex=True, sharey=True)
    axes = axes.ravel()
    order = ["semimem", "semiten", "bifemlh", "bifemsh"]
    for ax, nm in zip(axes, order):
        ax.axvspan(tsw_pct, 100.0, color="0.90", zorder=0)
        ax.axhline(1.0, color="0.7", ls=":", lw=0.8, zorder=1)
        ax.axvline(to_pct, color="0.6", ls="--", lw=0.8, zorder=1)
        for c, wv in zip(conds, waves[nm]):
            ax.plot(GRID, wv, color=tcmap(norm(c["anterior"])), lw=1.3, zorder=2)
        # peak markers (native metrics)
        for c in conds:
            ax.plot(c["m"][nm]["tPeak_pct"], c["m"][nm]["peak_lMtilde"], marker="o",
                    ms=3.6, mfc=tcmap(norm(c["anterior"])), mec="black", mew=0.4, zorder=4)
        ax.set_title(f"{C.SHORT[nm]}  ({C.LABELS_EN[nm]})", loc="left", fontsize=9,
                     color=C.COLORS[nm], fontweight="bold")
        ax.set_ylim(ylo, yhi)
        ax.set_xlim(0, 100)
    axes[0].annotate("toe-off", (to_pct, yhi), textcoords="offset points", xytext=(2, -8),
                     fontsize=6.2, color="0.5")
    axes[0].annotate("terminal swing\n(last 25% of swing)", (tsw_pct, ylo),
                     textcoords="offset points", xytext=(3, 6), fontsize=6.0, color="0.45")
    for ax in axes[2:]:
        ax.set_xlabel("")
    for ax in (axes[0], axes[2]):
        ax.set_ylabel("lMtilde  (lM / lMo)")
    fig.supxlabel("% stride  (0 = touchdown, 100 = next touchdown)  \u2014  shared y-axis",
                  fontsize=8.5, y=0.04)

    sm = ScalarMappable(norm=norm, cmap=tcmap)
    sm.set_array([])
    cb = fig.colorbar(sm, ax=axes, fraction=0.03, pad=0.02, aspect=30)
    cb.set_label("achieved anterior tilt  A (deg)", fontsize=8)
    cb.set_ticks(ant)
    cb.ax.tick_params(labelsize=6.3)

    fig.suptitle("Figure 3 | lMtilde waveforms and peak phase across touchdown anterior tilt (N=100)",
                 fontsize=10.5, fontweight="bold", x=0.01, ha="left", y=1.0)
    fig.text(0.01, -0.02,
             "Primary endpoint = max over the FULL stride (markers). Biarticular peaks fall in terminal swing; "
             "BFsh peaks in early stance. This full-stride max is a DIFFERENT quantity from the Pareto "
             "terminal-swing-window peak (Fig 7).", fontsize=6.3, color="0.35", ha="left")
    paths = C.save_fig(fig, "Fig3_lMtilde_waveforms_N100")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common = dict(figure_id="Fig3", source_commit="e7b8de9", simulation_commit="e7b8de9",
                  analysis_commit="e7b8de9", mesh="N=100",
                  condition_family="PelvisTDwide (ref -7.987 deg)",
                  solver_acceptance_rule="strict Solve_Succeeded; min final inf_pr per requested offset",
                  muscle_names_and_indices="semimem L6/R52, semiten L7/R53, bifemlh L8/R54, bifemsh L9/R55 (0-based)",
                  source_csv=src_csv, plotting_script="scripts/Fig3_lMtilde_waveforms_N100.py",
                  pdf_path=paths[0], svg_path=paths[1], png_path=paths[2],
                  generated_at=ts, qa_status="auto-pass; visual pending",
                  input_path=";".join(fn for _, fn in C.SELECTED_N100),
                  input_sha256="see final_source_manifest.csv")
    frag = dict(common, panel_id="A-D",
                analytical_question="In which phase and how does the 1-stride peak lMtilde respond to anterior tilt?",
                takeaway="Biarticular lMtilde rises graded and peaks in terminal swing (~85-91%); BFsh flat, peaks early stance.",
                phase_window="full stride; TS shading = last 25% of swing (muscle-metric window)",
                metric_formula="lMtilde=lM/lMo resampled to %stride; peak=max over full stride (native nodes)")
    C.write_manifest_fragment("Fig3", [frag])
    print("Fig3 done:", paths[2], "| toe-off%%=%.1f tsw%%=%.1f y[%.3f,%.3f]" % (to_pct, tsw_pct, ylo, yhi))


if __name__ == "__main__":
    main()
