"""
FigS2_muscle_metric_heatmap.py -- percent change of each load-surrogate metric from the
minimum-tilt (p6) to the maximum-tilt (m8) N=100 condition, per muscle.

Rows = 4 muscles; columns = peak lMtilde, peak Fce, peak Fpass, peak tendon force,
peak lengthening velocity, negative fibre work.  Colour = % change (diverging, centred 0).
Cell text = % change; peak lMtilde also shows the absolute lMtilde difference (small denominator).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

plt = C.setup_mpl()
import matplotlib.colors as mcolors
from datetime import datetime

METRICS = [("peak_lMtilde", "peak\nlMtilde"), ("peak_Fce_N", "peak\nFce"),
           ("peak_Fpass_N", "peak\nFpass"), ("peak_FT_N", "peak\ntendon F"),
           ("peak_leng_vel_mps", "peak\nlength. vel"), ("neg_fiber_work_J", "neg fibre\nwork")]


def main():
    conds = C.load_primary_N100()
    lo, hi = conds[0], conds[-1]      # p6 min tilt, m8 max tilt
    order = ["semimem", "semiten", "bifemlh", "bifemsh"]

    pct = np.zeros((len(order), len(METRICS)))
    absd = np.zeros_like(pct)
    src_rows = []
    for i, nm in enumerate(order):
        for j, (mk, _) in enumerate(METRICS):
            a = lo["m"][nm][mk]
            b = hi["m"][nm][mk]
            pct[i, j] = 100.0 * (b - a) / abs(a) if a != 0 else np.nan
            absd[i, j] = b - a
            src_rows.append([nm, mk, f"{a:.5f}", f"{b:.5f}", f"{pct[i,j]:+.3f}", f"{absd[i,j]:+.5f}"])
    src_csv = C.write_csv(os.path.join(C.SRC, "FigS2_muscle_metric_source.csv"),
                          ["muscle", "metric", "value_min_tilt_p6", "value_max_tilt_m8",
                           "pct_change", "abs_change"], src_rows)

    vmax = np.nanmax(np.abs(pct))
    norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    im = ax.imshow(pct, cmap="RdBu_r", norm=norm, aspect="auto")
    ax.set_xticks(range(len(METRICS)))
    ax.set_xticklabels([lab for _, lab in METRICS], fontsize=7.5)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([f"{C.SHORT[nm]}\n{C.LABELS_EN[nm]}" for nm in order], fontsize=7.2)
    for i in range(len(order)):
        for j, (mk, _) in enumerate(METRICS):
            txt = f"{pct[i,j]:+.1f}%"
            if mk == "peak_lMtilde":
                txt += f"\n({absd[i,j]:+.3f})"
            ax.text(j, i, txt, ha="center", va="center", fontsize=6.6,
                    color="black" if abs(pct[i, j]) < 0.6 * vmax else "white")
    ax.set_xticks(np.arange(-0.5, len(METRICS), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(order), 1), minor=True)
    ax.grid(which="minor", color="white", lw=1.5)
    ax.tick_params(which="minor", length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("% change  min \u2192 max tilt (p6 \u2192 m8)", fontsize=7.5)

    ax.set_title("Figure S2 | Metric change from minimum to maximum anterior tilt (N=100)",
                 loc="left", fontsize=9.5, fontweight="bold")
    fig.text(0.01, -0.06, "peak lMtilde cell also shows absolute lMtilde difference (small denominator). "
             "Fce includes the damping term. Biarticular rows rise; bifemsh (single-joint) stays near zero.",
             fontsize=6.2, color="0.35", ha="left")
    paths = C.save_fig(fig, "FigS2_muscle_metric_heatmap")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    frag = dict(figure_id="FigS2", panel_id="whole",
                analytical_question="How does each load surrogate change from min to max anterior tilt, per muscle?",
                takeaway="Biarticular peak lMtilde/Fpass/tendon force rise; bifemsh flat; passive force rises most steeply.",
                input_path=f"{lo['file']}; {hi['file']}", input_sha256="see sha256_manifest.csv",
                source_commit="e7b8de9", simulation_commit="e7b8de9", analysis_commit="e7b8de9",
                mesh="N=100", condition_family="PelvisTDwide p6 & m8",
                solver_acceptance_rule="strict Solve_Succeeded",
                muscle_names_and_indices="semimem/semiten/bifemlh/bifemsh L6-9/R52-55",
                phase_window="full stride peaks; neg work integral",
                metric_formula="100*(m8-p6)/|p6| per metric; abs diff for lMtilde",
                source_csv=src_csv, plotting_script="scripts/FigS2_muscle_metric_heatmap.py",
                pdf_path=paths[0], svg_path=paths[1], png_path=paths[2],
                generated_at=ts, qa_status="auto-pass; visual pending")
    C.write_manifest_fragment("FigS2", [frag])
    print("FigS2 done:", paths[2])
    print("  % change min->max tilt:")
    for i, nm in enumerate(order):
        print(f"    {nm:9s} " + "  ".join(f"{mk.split('_')[1][:4]}={pct[i,j]:+.1f}%" for j, (mk, _) in enumerate(METRICS)))


if __name__ == "__main__":
    main()
