"""
FigS1_force_length.py -- force-length operating region of the 3 biarticular hamstrings
at the minimum-tilt (p6) and maximum-tilt (m8) N=100 conditions.

x = lMtilde, y = Fce (contractile-element force INCLUDING the damping term, N).
Terminal-swing portion thickened; 1-stride peak lMtilde marked; lMtilde=1 (optimum) line.
Shows that more anterior tilt shifts the terminal-swing operating point to longer lMtilde.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

plt = C.setup_mpl()
from datetime import datetime

GRID = np.linspace(0.0, 100.0, 201)


def main():
    conds = C.load_primary_N100()
    lo = conds[0]   # p6, min anterior tilt 1.987
    hi = conds[-1]  # m8, max anterior tilt 15.987

    src_rows = []
    fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.5))
    for ax, nm in zip(axes, C.BIARTIC):
        for cond, col, lab in ((lo, "#9ecae1", f"min tilt {lo['anterior']:.1f} deg"),
                               (hi, "#08519c", f"max tilt {hi['anterior']:.1f} deg")):
            w = C.stride_waveform(cond["d"], nm, GRID)
            lM, fce = w["lMtilde"], w["Fce"]
            ts_start = cond["m"][nm]["tsw_start_pct"]
            tsmask = GRID >= ts_start
            ax.plot(lM, fce, color=col, lw=1.0, alpha=0.7, zorder=2)
            ax.plot(lM[tsmask], fce[tsmask], color=col, lw=2.6, zorder=3, label=lab)
            pk = cond["m"][nm]["peak_lMtilde"]
            # Fce at peak-lMtilde node (nearest grid)
            fpk = float(fce[np.argmin(np.abs(lM - pk))])
            ax.plot(pk, fpk, marker="o", ms=5, mfc=col, mec="black", mew=0.5, zorder=4)
            for p, l, f in zip(GRID, lM, fce):
                src_rows.append([nm, cond["offset"], f"{cond['anterior']:.3f}", f"{p:.1f}",
                                 f"{l:.5f}", f"{f:.1f}"])
        ax.axvline(1.0, color="0.6", ls=":", lw=0.9)
        ax.set_title(f"{C.SHORT[nm]}  ({C.LABELS_EN[nm]})", loc="left", fontsize=8.6,
                     color=C.COLORS[nm], fontweight="bold")
        ax.set_xlabel("lMtilde (lM / lMo)")
        ax.legend(loc="upper left", fontsize=6.2, frameon=False)
    axes[0].set_ylabel("Fce  (contractile force incl. damping, N)")
    axes[0].text(1.01, 0.02, "lMtilde=1\n(optimum)", transform=axes[0].get_xaxis_transform(),
                 fontsize=5.8, color="0.5", rotation=90, va="bottom")

    src_csv = C.write_csv(os.path.join(C.SRC, "FigS1_force_length_source.csv"),
                          ["muscle", "offset", "anterior_tilt_deg", "pct_stride", "lMtilde", "Fce_N"], src_rows)
    fig.suptitle("Figure S1 | Force-length operating region (biarticular hamstrings, min vs max tilt, N=100)",
                 fontsize=9.8, fontweight="bold", x=0.01, ha="left", y=1.02)
    fig.text(0.01, -0.04, "Thick segment = terminal swing; marker = 1-stride peak lMtilde. Fce includes the De Groote "
             "2016 damping term (not a pure active force).", fontsize=6.2, color="0.35", ha="left")
    paths = C.save_fig(fig, "FigS1_force_length")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    frag = dict(figure_id="FigS1", panel_id="A-C",
                analytical_question="Where on the length axis do the biarticular hamstrings operate, and how does tilt shift it?",
                takeaway="More anterior tilt shifts the terminal-swing operating point to longer lMtilde at similar/higher Fce.",
                input_path=f"{lo['file']}; {hi['file']}", input_sha256="see sha256_manifest.csv",
                source_commit="e7b8de9", simulation_commit="e7b8de9", analysis_commit="e7b8de9",
                mesh="N=100", condition_family="PelvisTDwide p6 & m8",
                solver_acceptance_rule="strict Solve_Succeeded",
                muscle_names_and_indices="semimem L6/R52, semiten L7/R53, bifemlh L8/R54",
                phase_window="full stride; TS thickened", metric_formula="Fce vs lMtilde parametric over stride",
                source_csv=src_csv, plotting_script="scripts/FigS1_force_length.py",
                pdf_path=paths[0], svg_path=paths[1], png_path=paths[2],
                generated_at=ts, qa_status="auto-pass; visual pending")
    C.write_manifest_fragment("FigS1", [frag])
    print("FigS1 done:", paths[2])


if __name__ == "__main__":
    main()
