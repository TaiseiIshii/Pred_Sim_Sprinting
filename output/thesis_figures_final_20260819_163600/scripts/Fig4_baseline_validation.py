"""
Fig4_baseline_validation.py -- how well the Nominal N=100 predictive solution
reproduces the MAJOR EXTERNAL features of the subject's own max-velocity sprint step.

Data reality (honest):
  * Subject own experimental IK: MainFunctions/ExperimentalData/IK_Splined/Splined_100...p02_maxVel_01.mot
  * Nominal N=100 predicted kinematics: pred_sprinting_coords_...Nominal.mot
  * NO subject force-plate GRF and NO subject EMG exist in the repo -> Panels B/C are
    SIMULATION-ONLY (clearly labelled) and GRF/EMG error metrics are 'not available'.
  * pelvis_tilt uses a different offset/convention between raw IK and the model output;
    it is shown with an explicit caveat, not silently aligned.

All angles phase-normalized to % step (touchdown -> next contralateral touchdown).
"""
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

plt = C.setup_mpl()
import matplotlib.gridspec as gridspec
from datetime import datetime

GRID = np.linspace(0.0, 100.0, 101)
KJOINTS = [("pelvis_tilt", "pelvis tilt"), ("hip_flexion_r", "hip flexion (R)"),
           ("knee_angle_r", "knee angle (R)"), ("ankle_angle_r", "ankle angle (R)")]


def mot_pct(motpath, coord):
    cols, data = C.read_mot(motpath)
    t = data[:, 0]
    pct = 100.0 * (t - t[0]) / (t[-1] - t[0])
    idx = {c: i for i, c in enumerate(cols)}
    return np.interp(GRID, pct, data[:, idx[coord]])


def main():
    exp = C.EXP_IK
    sim = os.path.join(C.RESULTS, C.NOMINAL_COORDS)

    # ---- kinematics + RMSE ----
    metrics = []
    kin = {}
    for coord, lab in KJOINTS:
        e = mot_pct(exp, coord)
        s = mot_pct(sim, coord)
        kin[coord] = (e, s)
        rng = float(np.ptp(e)) if np.ptp(e) > 1e-9 else float("nan")
        # for pelvis_tilt also report offset-removed shape agreement
        off = float(np.mean(s - e))
        r = float(np.corrcoef(e, s)[0, 1])
        rmse = float(np.sqrt(np.mean((e - s) ** 2)))
        rmse_shape = float(np.sqrt(np.mean(((s - off) - e) ** 2)))
        metrics.append(dict(coord=coord, label=lab, rmse=rmse, nrmse=100.0 * rmse / rng,
                            corr=r, offset=off, rmse_shape=rmse_shape, exp_range=rng))

    # ---- GRF (simulation only) ----
    dnom = C.load(C.NOMINAL_N100)
    g = dnom["GRF_R"]
    tt = dnom["t"]
    if g.shape[0] != tt.size and g.shape[1] == tt.size:
        g = g.T
    pct_g = 100.0 * (tt - tt[0]) / (tt[-1] - tt[0])
    ap = g[:, 0] / C.BW
    vert = g[:, 1] / C.BW
    contact_mask = vert > 0.05
    contact_end_pct = float(pct_g[contact_mask][-1]) if contact_mask.any() else np.nan
    peak_v = float(vert.max())

    # ---- activations (simulation only), reconstructed over % stride (right->left) ----
    acol, adata = C.read_mot(os.path.join(C.RESULTS, C.NOMINAL_ACTS))
    aidx = {c: i for i, c in enumerate(acol)}
    at = adata[:, 0]
    Ta = float(at[-1] - at[0])
    apct_stride = 100.0 * np.concatenate([at - at[0], (at - at[0]) + Ta]) / (2.0 * Ta)
    acts = {}
    for nm in C.BIARTIC:
        seg = np.concatenate([adata[:, aidx[nm + "_r"]], adata[:, aidx[nm + "_l"]]])
        acts[nm] = np.interp(GRID, apct_stride, seg)

    # ---- source CSVs ----
    krows = []
    for coord, lab in KJOINTS:
        e, s = kin[coord]
        for p, ev, sv in zip(GRID, e, s):
            krows.append([coord, f"{p:.1f}", f"{ev:.4f}", f"{sv:.4f}"])
    for p, a, v in zip(GRID, np.interp(GRID, pct_g, ap), np.interp(GRID, pct_g, vert)):
        krows.append(["GRF_AP_BW_sim", f"{p:.1f}", "", f"{a:.4f}"])
        krows.append(["GRF_vert_BW_sim", f"{p:.1f}", "", f"{v:.4f}"])
    for nm in C.BIARTIC:
        for p, a in zip(GRID, acts[nm]):
            krows.append([f"act_{nm}_sim_stride", f"{p:.1f}", "", f"{a:.4f}"])
    src_csv = C.write_csv(os.path.join(C.SRC, "Fig4_baseline_validation_source.csv"),
                          ["signal", "pct_phase", "experimental", "simulation"], krows)
    mrows = [[m["coord"], m["label"], f"{m['rmse']:.3f}", f"{m['nrmse']:.1f}",
              f"{m['corr']:.3f}", f"{m['offset']:.3f}", f"{m['rmse_shape']:.3f}"] for m in metrics]
    mrows.append(["GRF_vertical", "peak vertical GRF (sim)", f"{peak_v:.2f}BW", "n/a",
                  "n/a", "n/a", "no subject force-plate data -> error not available"])
    mrows.append(["EMG", "muscle activation", "n/a", "n/a", "n/a", "n/a",
                  "no subject EMG data -> onset/offset error not available"])
    met_csv = C.write_csv(os.path.join(C.SRC, "Fig4_baseline_validation_metrics.csv"),
                          ["signal", "label", "RMSE_deg", "NRMSE_pct", "corr_r",
                           "mean_offset_deg", "RMSE_after_offset_removed_deg"], mrows)

    # ---- figure ----
    fig = plt.figure(figsize=(9.8, 6.8))
    gs = gridspec.GridSpec(2, 12, hspace=0.62, wspace=1.5, height_ratios=[1.0, 1.05])
    axk = [fig.add_subplot(gs[0, i * 3:(i + 1) * 3]) for i in range(4)]
    axB = fig.add_subplot(gs[1, 0:4])
    axC = fig.add_subplot(gs[1, 4:8])
    axD = fig.add_subplot(gs[1, 8:12])

    bbox = dict(facecolor="white", edgecolor="none", alpha=0.75, pad=1.0)
    for ax, (coord, lab), m in zip(axk, KJOINTS, metrics):
        e, s = kin[coord]
        ax.plot(GRID, e, color="#1f77b4", lw=1.6, label="experimental IK")
        ax.plot(GRID, s, color="#d62728", lw=1.6, ls="--", label="Nominal N=100")
        ax.set_title(lab, fontsize=8.5, loc="left")
        ax.set_xlim(0, 100)
        if coord == "pelvis_tilt":
            cap = (f"convention/posture offset\nexp TD {e[0]:+.1f}, sim TD {s[0]:+.1f} deg\n"
                   f"shape r={m['corr']:+.2f}, RMSE(off-rem)={m['rmse_shape']:.1f} deg")
        else:
            cap = f"RMSE={m['rmse']:.1f} deg\nr={m['corr']:+.2f}, NRMSE={m['nrmse']:.0f}%"
        ax.text(0.5, 0.03, cap, transform=ax.transAxes, fontsize=5.7, color="0.35",
                ha="center", va="bottom", bbox=bbox)
        ax.set_ylabel("deg", fontsize=7)
        ax.set_xlabel("% step", fontsize=7)
    kh = [plt.Line2D([0], [0], color="#1f77b4", lw=1.8, label="experimental IK (subject p02_maxVel_01)"),
          plt.Line2D([0], [0], color="#d62728", lw=1.8, ls="--", label="Nominal N=100 (predicted)")]
    fig.legend(handles=kh, loc="center", bbox_to_anchor=(0.5, 0.545), ncol=2,
               frameon=False, fontsize=8)

    # Panel B GRF (sim only)
    axB.axvspan(0, contact_end_pct, color="0.92", zorder=0)
    axB.axhline(0, color="0.6", lw=0.8)
    axB.plot(pct_g, vert, color="#2166ac", lw=1.7, label="vertical")
    axB.plot(pct_g, ap, color="#e08214", lw=1.7, label="anterior-posterior")
    axB.set_xlabel("% step"); axB.set_ylabel("GRF (body weight, BW)")
    axB.set_title("B  GRF (simulation only)", loc="left", fontweight="bold", fontsize=8.8)
    axB.set_xlim(0, 100)
    axB.legend(loc="upper right", fontsize=6.2, frameon=False)
    axB.text(0.60, 0.52, "no subject force-plate data;\ncontact-model peak GRF is\ninflated (use shape, not peak).\ngrey = contact interval",
             transform=axB.transAxes, fontsize=5.6, color="0.4", va="top", ha="left")

    # Panel C activation (sim only, reconstructed stride)
    for nm in C.BIARTIC:
        axC.plot(GRID, acts[nm], color=C.COLORS[nm], lw=1.6, label=C.SHORT[nm])
    axC.set_xlabel("% stride"); axC.set_ylabel("activation (0-1)")
    axC.set_title("C  Activation (simulation only)", loc="left", fontweight="bold", fontsize=8.8)
    axC.set_xlim(0, 100); axC.set_ylim(0, 1.08)
    axC.legend(loc="upper right", fontsize=6.2, frameon=False, ncol=3, columnspacing=0.8)
    axC.text(0.5, 0.40, "no subject EMG; shown for\nphase/timing reference only\n(reference-leg stride)",
             transform=axC.transAxes, fontsize=5.6, color="0.4", va="center", ha="center")

    # Panel D metrics
    axD.axis("off")
    axD.set_title("D  Quantitative agreement", loc="left", fontweight="bold", fontsize=8.6)
    lines = ["kinematics (exp IK vs Nominal N=100):", ""]
    for m in metrics:
        if m["coord"] == "pelvis_tilt":
            lines.append(f"  {m['label']:14s} RMSE(shape) {m['rmse_shape']:4.1f} deg  r={m['corr']:+.2f} *")
        else:
            lines.append(f"  {m['label']:14s} RMSE {m['rmse']:4.1f} deg  NRMSE {m['nrmse']:4.0f}%  r={m['corr']:+.2f}")
    lines += ["",
              f"  peak vertical GRF (sim) = {peak_v:.1f} BW",
              "  GRF timing error   : not available",
              "  EMG onset/offset   : not available", "",
              "  * pelvis_tilt convention/posture",
              "    offset removed for shape comparison"]
    axD.text(0.0, 0.92, "\n".join(lines), transform=axD.transAxes, fontsize=6.2,
             va="top", ha="left", family="monospace", color="0.15")

    fig.suptitle("Figure 4 | Baseline (Nominal N=100) reproduction of the subject's own max-velocity sprint step",
                 fontsize=10.0, fontweight="bold", x=0.01, ha="left", y=1.0)
    fig.text(0.01, -0.02,
             "External kinematic / GRF-shape / activation-timing agreement does NOT guarantee validity of internal "
             "fibre length, force or local tissue stress. GRF and activations are simulation-only (no subject force "
             "plate or EMG in the dataset).", fontsize=6.2, color="0.35", ha="left")
    paths = C.save_fig(fig, "Fig4_baseline_validation")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common = dict(figure_id="Fig4", source_commit="e7b8de9", simulation_commit="e7b8de9",
                  analysis_commit="e7b8de9", mesh="N=100 (Nominal) vs experimental IK",
                  condition_family="Nominal N=100 vs subject p02_maxVel_01 IK",
                  solver_acceptance_rule="Nominal strict Solve_Succeeded",
                  muscle_names_and_indices="activations semimem/semiten/bifemlh (_r)",
                  source_csv=src_csv + " ; " + met_csv,
                  plotting_script="scripts/Fig4_baseline_validation.py",
                  pdf_path=paths[0], svg_path=paths[1], png_path=paths[2],
                  generated_at=ts, qa_status="auto-pass; visual pending",
                  input_path=f"{os.path.basename(exp)}; {C.NOMINAL_COORDS}; {C.NOMINAL_N100}; {C.NOMINAL_ACTS}",
                  input_sha256="see sha256_manifest.csv")
    frags = [
        dict(common, panel_id="A", analytical_question="Does Nominal reproduce subject sprint kinematics?",
             takeaway="Hip/knee/ankle match well; pelvis_tilt differs by a convention/posture offset (flagged).",
             phase_window="% step", metric_formula="phase-normalized overlay + RMSE/NRMSE/corr"),
        dict(common, panel_id="B", analytical_question="Is the GRF shape realistic?",
             takeaway="Biphasic AP and unimodal vertical shape; peak magnitude inflated by contact model.",
             phase_window="% step, contact shaded", metric_formula="GRFs.R/BW (simulation only)"),
        dict(common, panel_id="C", analytical_question="Is hamstring activation timing plausible?",
             takeaway="Late-swing/early-stance activation bursts; no subject EMG to compare against.",
             phase_window="% step", metric_formula="activation from Nominal acts.sto (simulation only)"),
        dict(common, panel_id="D", analytical_question="What agreement metrics are computable?",
             takeaway="Kinematic RMSE available; GRF/EMG error not available (no subject data).",
             phase_window="% step", metric_formula="RMSE/NRMSE/corr; unavailable marked"),
    ]
    C.write_manifest_fragment("Fig4", frags)
    print("Fig4 done:", paths[2])
    for m in metrics:
        print(f"  {m['coord']:14s} RMSE={m['rmse']:.2f} NRMSE={m['nrmse']:.1f}% r={m['corr']:+.3f} "
              f"offset={m['offset']:+.2f} RMSE_shape={m['rmse_shape']:.2f}")
    print(f"  peak vGRF(sim)={peak_v:.2f} BW  contact_end={contact_end_pct:.1f}% step")


if __name__ == "__main__":
    main()
