"""
Fig1_study_logic.py -- research-gap and validation-chain schematic (this study's own).
Editable vector (PDF/SVG); no generative image, no reproduction of published figures.
Message: WHY a single-model predictive manipulation of touchdown pelvic tilt is needed
in addition to observational work, and how the analyses chain together.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

plt = C.setup_mpl()
from matplotlib.patches import FancyBboxPatch
from datetime import datetime


def box(ax, x, y, w, h, text, fc, ec, fs=8.2, weight="normal", tc="#111111"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.012",
                                linewidth=1.2, facecolor=fc, edgecolor=ec, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight=weight, zorder=3, wrap=True)


def arrow(ax, x0, y0, x1, y1, color="#555555"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6, shrinkA=1, shrinkB=1), zorder=1)


def main():
    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    C1, E1 = "#eaf1f8", "#4a7fb5"   # gap
    C2, E2 = "#fdf0e2", "#e08214"   # approach
    C3a, E3a = "#e7f2e7", "#1b7837"  # primary
    C3b, E3b = "#efe7f3", "#762a83"  # mechanism
    C3c, E3c = "#e7eef7", "#2166ac"  # extension

    # Row 1: the gap
    box(ax, 0.02, 0.80, 0.45, 0.15,
        "Observational sprint studies\nlink pelvic motion with hamstring\nstrain and running mechanics",
        C1, E1)
    box(ax, 0.53, 0.80, 0.45, 0.15,
        "Unresolved: individual anatomy and\nco-varying whole-body kinematics\nconfound the pelvis\u2013load relationship",
        C1, E1)
    arrow(ax, 0.47, 0.875, 0.53, 0.875)

    # to approach
    arrow(ax, 0.50, 0.795, 0.50, 0.735)

    # Row 2: the approach (this study)
    box(ax, 0.10, 0.565, 0.80, 0.165,
        "THIS STUDY  \u2014  one predictive musculoskeletal sprinter model\n"
        "constrain ONLY the touchdown pelvis tilt, then re-optimize the whole-body\n"
        "motion for maximum speed (speed held ~constant across conditions)",
        C2, E2, fs=8.6, weight="bold")

    # to analyses
    arrow(ax, 0.30, 0.560, 0.17, 0.475)
    arrow(ax, 0.50, 0.560, 0.50, 0.475)
    arrow(ax, 0.70, 0.560, 0.83, 0.475)

    # Row 3: three analysis arms
    box(ax, 0.02, 0.25, 0.30, 0.21,
        "PRIMARY  (N=100)\n8 deterministic design points\npeak normalized fibre length\nlMtilde vs anterior tilt\n\n\u2192 Fig 2, Fig 3",
        C3a, E3a, fs=7.8)
    box(ax, 0.35, 0.25, 0.30, 0.21,
        "MECHANISM\ntree-rigid / femur-fixed /\nadaptive decomposition\npelvis\u2013femur coordination\n\n\u2192 Fig 5",
        C3b, E3b, fs=7.8)
    box(ax, 0.68, 0.25, 0.30, 0.21,
        "EXTENSION\nspeed vs load-surrogate\nPareto exploration\n(3 warm-start paths)\n\n\u2192 Fig 7",
        C3c, E3c, fs=7.8)

    # baseline validation feeding all arms
    box(ax, 0.16, 0.075, 0.68, 0.10,
        "Baseline face validity: Nominal N=100 vs the subject's own experimental sprint  (\u2192 Fig 4)\n"
        "Numerical operability, solution selection & sensitivity  (\u2192 Fig 6)",
        "#f4f4f4", "#999999", fs=7.6)
    arrow(ax, 0.17, 0.25, 0.30, 0.178)
    arrow(ax, 0.50, 0.25, 0.50, 0.178)
    arrow(ax, 0.83, 0.25, 0.70, 0.178)

    ax.text(0.5, 0.025, "Interpretation stays at correlation / mechanism WITHIN one model \u2014 "
            "not injury causation, not population inference.",
            ha="center", va="center", fontsize=6.8, color="0.4", style="italic")

    fig.suptitle("Figure 1 | Research gap and validation chain",
                 fontsize=10.5, fontweight="bold", x=0.01, ha="left", y=0.99)
    paths = C.save_fig(fig, "Fig1_study_logic")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    frag = dict(figure_id="Fig1", panel_id="whole",
                analytical_question="Why manipulate touchdown pelvic tilt in one predictive model, not only observe?",
                takeaway="Isolates the pelvis-load link from anatomy/kinematic confounds; chains primary/mechanism/extension.",
                input_path="n/a (schematic)", input_sha256="n/a",
                source_commit="e7b8de9", simulation_commit="e7b8de9", analysis_commit="e7b8de9",
                mesh="n/a", condition_family="n/a", solver_acceptance_rule="n/a",
                muscle_names_and_indices="n/a", phase_window="n/a", metric_formula="n/a (conceptual)",
                source_csv="n/a", plotting_script="scripts/Fig1_study_logic.py",
                pdf_path=paths[0], svg_path=paths[1], png_path=paths[2],
                generated_at=ts, qa_status="auto-pass; visual pending")
    C.write_manifest_fragment("Fig1", [frag])
    print("Fig1 done:", paths[2])


if __name__ == "__main__":
    main()
