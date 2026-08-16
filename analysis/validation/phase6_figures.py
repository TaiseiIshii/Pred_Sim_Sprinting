"""
phase6_figures.py -- Figure 1 (formulation/counterfactual schematic) and Figure 5 (baseline vs
near-matched-speed candidate motion), for the thesis/conference figure set (Phase 6.4).

Figure 5 uses the N=50 Nominal Pareto w=0 (baseline) vs w=0.1 (candidate). It is marked DRAFT and
will be refreshed from the N=100 multi-start solution when run_ham_pareto_N100 completes.

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" analysis/validation/phase6_figures.py
"""
from __future__ import annotations

import glob
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

import ham_load_metrics as H

OUTDIR = os.path.join(H.RESULTS, "Validation_Master")
HIP_R = 6           # 0-based q row: hip_flexion_r (from fair_opt_comparison.py)
BIARTIC = ["semimem", "semiten", "bifemlh"]
COLORS = {"semimem": "#1b7837", "semiten": "#762a83", "bifemlh": "#2166ac", "bifemsh": "#b2182b"}


def latest(token):
    fs = sorted(glob.glob(os.path.join(H.RESULTS, f"pred_sprinting_data_*{token}.mat")),
                key=os.path.getmtime, reverse=True)
    return fs[0] if fs else None


def fig1_schematic():
    fig, ax = plt.subplots(figsize=(11, 5.2)); ax.axis("off")
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)

    def box(x, y, w, h, text, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2",
                                    fc=fc, ec="#333", lw=1.2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5, wrap=True)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                                     lw=1.4, color="#333"))

    box(2, 72, 30, 20, "Performance objective\n(max speed + regularization)\n+ biarticular-ham\noverstretch penalty w", "#dbe9f6")
    box(2, 40, 30, 20, "Predictive optimization\n(CasADi/IPOPT, direct\ncollocation, matched speed)", "#dbe9f6")
    box(38, 40, 26, 52, "Adaptive re-optimized\nmotion\n(dynamically feasible:\nmuscle equilibrium,\nGRF/contact,\nperiodicity)", "#d7f0d7")
    box(70, 72, 28, 20, "Kinematic counterfactuals\n(GEOMETRIC only)\ntree-rigid / femur-fixed", "#f6e6c9")
    box(70, 44, 28, 18, "Coordination:\npelvis / hip / knee / trunk\n(hip flexion mediates tilt)", "#eee")
    box(70, 20, 28, 18, "Fiber length & velocity\n-> active / passive / tendon\nforce, negative work\n(load SURROGATES)", "#f7d9d9")
    box(38, 8, 26, 22, "Terminal-swing vs\nearly-stance per-muscle\nload; speed-load Pareto\ncandidate", "#f7d9d9")

    arrow(17, 72, 17, 60); arrow(32, 50, 38, 50)
    arrow(64, 66, 70, 62); arrow(64, 55, 70, 53); arrow(84, 72, 84, 62)
    arrow(84, 44, 84, 38); arrow(70, 29, 64, 22); arrow(51, 40, 51, 30)
    ax.text(50, 97, "Figure 1  Study formulation and counterfactual comparison",
            ha="center", fontsize=12, weight="bold")
    ax.text(50, 2, "Only the adaptive branch is dynamically feasible; tree-rigid/femur-fixed are "
            "geometric kinematic counterfactuals (see OPT_ON_OFF_INTERPRETATION.md).",
            ha="center", fontsize=7.5, color="#444")
    fig.savefig(os.path.join(OUTDIR, "fig_1_formulation.png"), dpi=150, bbox_inches="tight")
    plt.close(fig); print("wrote fig_1_formulation.png")


def fig5_candidate():
    pb = latest("HamPareto_Nom_w0000"); pc = latest("HamPareto_Nom_w0100")
    if not pb or not pc:
        print("SKIP fig5: need w0000 & w0100 MATs"); return
    b = H.load_optimum(pb); c = H.load_optimum(pc)
    mb = H.condition_metrics(pb); mc = H.condition_metrics(pc)

    fig, axs = plt.subplots(1, 3, figsize=(14, 4.4))
    # Panel A: pelvis tilt & hip flexion over the step (baseline vs candidate)
    for d, style, lab in [(b, "-", "baseline w0"), (c, "--", "candidate w0.1")]:
        q = d["q"]; x = np.linspace(0, 100, q.shape[1])
        axs[0].plot(x, np.degrees(q[0]), style, color="#2166ac", label=f"pelvis tilt {lab}")
        axs[0].plot(x, np.degrees(q[HIP_R]), style, color="#b2182b", label=f"hip flexion {lab}")
    axs[0].set_xlabel("% step"); axs[0].set_ylabel("angle (deg)")
    axs[0].set_title("kinematics: pelvis tilt & hip flexion"); axs[0].grid(alpha=0.3)
    axs[0].legend(fontsize=6.5, ncol=1)

    # Panel B: biarticular peak lMtilde per muscle (baseline vs candidate)
    xs = np.arange(len(BIARTIC)); w = 0.35
    axs[1].bar(xs - w / 2, [mb[f"{m}_peak_lMtilde"] for m in BIARTIC], w, color="#888", label="baseline w0")
    axs[1].bar(xs + w / 2, [mc[f"{m}_peak_lMtilde"] for m in BIARTIC], w,
               color=[COLORS[m] for m in BIARTIC], label="candidate w0.1")
    axs[1].set_xticks(xs); axs[1].set_xticklabels(BIARTIC); axs[1].axhline(1.0, color="k", lw=0.8, ls=":")
    axs[1].set_ylabel("peak normalized fiber length"); axs[1].set_ylim(0.9, None)
    axs[1].set_title("biarticular peak fiber length"); axs[1].legend(fontsize=7)

    # Panel C: surrogate % change baseline -> candidate
    def biartic_mean(m, key):
        return float(np.mean([m[f"{n}_{key}"] for n in BIARTIC]))
    labels = ["speed", "TS peak\nlMtilde", "passive\nforce", "neg\nwork"]
    base = [b["speed"], biartic_mean(mb, "TS_peak_lMtilde"), biartic_mean(mb, "peak_passive_force_N"),
            biartic_mean(mb, "neg_fiber_work_J")]
    cand = [c["speed"], biartic_mean(mc, "TS_peak_lMtilde"), biartic_mean(mc, "peak_passive_force_N"),
            biartic_mean(mc, "neg_fiber_work_J")]
    pct = [100.0 * (cd - bs) / bs for bs, cd in zip(base, cand)]
    cols = ["#2166ac" if p <= 0 else "#b2182b" for p in pct]
    axs[2].bar(labels, pct, color=cols)
    axs[2].axhline(0, color="k", lw=0.8)
    for i, p in enumerate(pct):
        axs[2].text(i, p + (0.1 if p >= 0 else -0.1), f"{p:+.2f}%", ha="center",
                    va="bottom" if p >= 0 else "top", fontsize=8)
    axs[2].set_ylabel("% change (candidate vs baseline)")
    axs[2].set_title("surrogate change (near-matched speed)")

    fig.suptitle(f"Figure 5 (N={b['N']})  Baseline (w=0) vs near-matched-speed candidate (w=0.1)", y=1.02)
    fig.text(0.5, -0.02, f"speed {b['speed']:.3f}->{c['speed']:.3f} m/s ({pct[0]:+.2f}%); "
             "mechanical-load surrogates, not injury; baseline w0 and candidate w0.1 at the same mesh.",
             ha="center", fontsize=7.5, color="#444")
    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    fig.savefig(os.path.join(OUTDIR, "fig_5_candidate_motion.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote fig_5_candidate_motion.png (speed {b['speed']:.4f}->{c['speed']:.4f}, "
          f"TS lMtilde {pct[1]:+.2f}%, passive {pct[2]:+.2f}%, negwork {pct[3]:+.2f}%)")


if __name__ == "__main__":
    fig1_schematic()
    fig5_candidate()
