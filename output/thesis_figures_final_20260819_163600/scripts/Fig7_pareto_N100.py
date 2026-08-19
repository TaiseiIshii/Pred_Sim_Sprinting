"""
Fig7_pareto_N100.py -- N=100 speed vs load-surrogate Pareto, regenerated from the
raw HamPareto_N100 MAT (checkpoint.csv provenance), recomputed via _common.

Panel A: Pareto plane (dSpeed% vs biartic terminal-swing-window peak lMtilde mean change%),
         weight labels, warm-start path markers, pre-registered target region shaded.
Panel B: representative lMtilde waveforms (3 biarticular) w=0 vs w=0.1, TS shaded.
Panel C: kinematic differences (w=0.1 - w=0) for pelvis tilt, hip flexion, knee angle.

The 3 w=0.1 solves are 3 DETERMINISTIC warm-start paths (forward / from-Nominal /
backward), NOT independent restarts.  The optimiser directly penalises a smooth
integrated overstretch term; the reported terminal-swing peak is a post-hoc readout.
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

CKPT = os.path.join(C.RESULTS, "HamPareto_N100", "checkpoint.csv")
GRID = np.linspace(0.0, 100.0, 201)
PATH_MARK = {"forward": "^", "nominal": "o", "backward": "s"}


def path_of(init):
    if "backward" in init:
        return "backward"
    if init == "from_NominalN100":
        return "nominal"
    return "forward"


def coords_for(datafile):
    """Map a ...data_<stamp>___<cond>.mat to its coords .mot, with a minute-prefix fallback."""
    import glob
    direct = datafile.replace("pred_sprinting_data_", "pred_sprinting_coords_").replace(".mat", ".mot")
    p = os.path.join(C.RESULTS, direct)
    if os.path.isfile(p):
        return p
    stamp = datafile.split("pred_sprinting_data_")[1].rsplit("___", 1)[0][:-3]  # drop seconds
    cond = datafile.rsplit("___", 1)[1].replace(".mat", "")
    hits = glob.glob(os.path.join(C.RESULTS, f"pred_sprinting_coords_{stamp}*___{cond}.mot"))
    if not hits:
        raise FileNotFoundError(f"no coords .mot for {datafile}")
    return hits[0]


def mot_stride_deg(motpath, coord):
    """Right-then-left reconstructed full-stride waveform (deg) for a coordinate, on GRID."""
    cols, data = C.read_mot(motpath)
    t = data[:, 0]
    T = float(t[-1] - t[0])
    idx = {c: i for i, c in enumerate(cols)}
    if coord == "pelvis_tilt":
        seg = np.concatenate([data[:, idx["pelvis_tilt"]], data[:, idx["pelvis_tilt"]]])
    else:
        seg = np.concatenate([data[:, idx[coord + "_r"]], data[:, idx[coord + "_l"]]])
    ts = np.concatenate([t - t[0], (t - t[0]) + T])
    pct = 100.0 * ts / (2.0 * T)
    return np.interp(GRID, pct, seg)


def main():
    rows = list(csv.DictReader(open(CKPT, encoding="utf-8")))
    for r in rows:
        r["w"] = float(r["condition"].split("_w")[-1]) / 1000.0
        r["path"] = path_of(r["init_method"])
    base = next(r for r in rows if r["w"] == 0.0)
    db = C.load(base["out_file"]); cb, _, _ = C.contact_s(db)
    base_speed = db["speed"]
    base_surro = float(np.mean([C.metrics(db, nm, cb)["TS_peak_lMtilde"] for nm in C.BIARTIC]))

    pts = []
    for r in rows:
        d = C.load(r["out_file"]); c, _, _ = C.contact_s(d)
        surro = float(np.mean([C.metrics(d, nm, c)["TS_peak_lMtilde"] for nm in C.BIARTIC]))
        pts.append(dict(tag=r["tag"], w=r["w"], path=r["path"], init=r["init_method"],
                        status=d["status"], speed=d["speed"], surro=surro,
                        dSpeed=100.0 * (d["speed"] - base_speed) / base_speed,
                        dSurro=100.0 * (surro - base_surro) / base_surro,
                        tilt=-d["td"], out_file=r["out_file"]))

    # ---- source CSV (points) ----
    prows = [[p["tag"], f"{p['w']:.2f}", p["path"], p["init"], p["status"],
              f"{p['speed']:.6f}", f"{p['surro']:.5f}", f"{p['dSpeed']:+.4f}",
              f"{p['dSurro']:+.4f}", f"{p['tilt']:.4f}", p["out_file"]] for p in pts]
    src_csv = C.write_csv(os.path.join(C.SRC, "Fig7_pareto_N100_source.csv"),
                          ["tag", "weight", "warmstart_path", "init_method", "solver_status",
                           "speed_mps", "TS_peak_biartic_mean", "dSpeed_pct", "dSurro_pct",
                           "achieved_anterior_tilt_deg", "out_file"], prows)

    # representative w=0.1 (from-Nominal path) + baseline waveforms
    rep = next(p for p in pts if p["w"] == 0.1 and p["path"] == "nominal")
    d0 = db
    d1 = C.load(rep["out_file"]); c1, _, _ = C.contact_s(d1)
    strideT0 = 2.0 * d0["totalTime"]; strideT1 = 2.0 * d1["totalTime"]
    tsw0 = np.mean([C.metrics(d0, nm, cb)["tsw_start_pct"] for nm in C.BIARTIC])
    wave_rows = []
    waves0, waves1 = {}, {}
    for nm in C.BIARTIC:
        waves0[nm] = C.stride_waveform(d0, nm, GRID)["lMtilde"]
        waves1[nm] = C.stride_waveform(d1, nm, GRID)["lMtilde"]
        for p, v0, v1 in zip(GRID, waves0[nm], waves1[nm]):
            wave_rows.append([nm, f"{p:.1f}", f"{v0:.5f}", f"{v1:.5f}"])
    C.write_csv(os.path.join(C.SRC, "Fig7_waveforms_source.csv"),
                ["muscle", "pct_stride", "lMtilde_w0", "lMtilde_w0.1"], wave_rows)

    # kinematics diff (from exported coords .mot, phase-normalized)
    mot0 = coords_for(base["out_file"]); mot1 = coords_for(rep["out_file"])
    kin = {}
    kin_rows = []
    for nm in ("pelvis_tilt", "hip_flexion", "knee_angle"):
        a0 = mot_stride_deg(mot0, nm)
        a1 = mot_stride_deg(mot1, nm)
        kin[nm] = a1 - a0
        for p, dv in zip(GRID, kin[nm]):
            kin_rows.append([nm, f"{p:.1f}", f"{dv:+.4f}"])
    C.write_csv(os.path.join(C.SRC, "Fig7_kinematics_source.csv"),
                ["coordinate", "pct_stride", "delta_deg_w0.1_minus_w0"], kin_rows)

    # ---- figure ----
    fig = plt.figure(figsize=(7.8, 6.6))
    gs = gridspec.GridSpec(2, 2, hspace=0.42, wspace=0.30, height_ratios=[1.05, 1.0])
    axA = fig.add_subplot(gs[0, :])
    axB = fig.add_subplot(gs[1, 0])
    axC = fig.add_subplot(gs[1, 1])

    # Panel A ------------------------------------------------------------
    # pre-registered target region: dSpeed >= -0.5 AND dSurro <= -3
    axA.add_patch(plt.Rectangle((-0.5, -9.0), 0.55, 6.0, facecolor="#c7e9c0",
                                edgecolor="none", alpha=0.6, zorder=0))
    axA.axvline(-0.5, color="#4a7f4a", ls=":", lw=0.9)
    axA.axhline(-3.0, color="#4a7f4a", ls=":", lw=0.9)
    axA.axhline(0, color="0.7", lw=0.8); axA.axvline(0, color="0.7", lw=0.8)
    seen, labeled_w = set(), set()
    for p in pts:
        mk = PATH_MARK[p["path"]]
        lbl = {"forward": "forward continuation", "nominal": "from Nominal",
               "backward": "backward continuation"}[p["path"]]
        axA.plot(p["dSpeed"], p["dSurro"], marker=mk, ms=8, mfc="#2166ac",
                 mec="black", mew=0.7, ls="none",
                 label=lbl if p["path"] not in seen else None, zorder=3)
        seen.add(p["path"])
        if p["w"] not in labeled_w:
            axA.annotate(f"w={p['w']:g}", (p["dSpeed"], p["dSurro"]), textcoords="offset points",
                         xytext=(8, 3), fontsize=6.8, color="0.2")
            labeled_w.add(p["w"])
    axA.set_xlabel("speed change from w=0  (%)")
    axA.set_ylabel("biartic TS-window peak lMtilde\nmean change from w=0  (%)")
    axA.set_title("A  Speed vs load-surrogate Pareto (N=100)", loc="left", fontweight="bold", fontsize=9.5)
    axA.set_xlim(-0.85, 0.10); axA.set_ylim(-9.0, 0.9)
    axA.legend(loc="lower right", fontsize=6.6, frameon=False)
    axA.text(-0.485, -6.0, "pre-registered target:\nspeed loss <=0.5% AND surrogate <=-3%",
             fontsize=6.0, color="#3a6b3a", va="top")
    axA.text(0.02, 0.96, "all strict Solve_Succeeded", transform=axA.transAxes,
             fontsize=6.0, color="0.45", ha="left", va="top")

    # Panel B ------------------------------------------------------------
    axB.axvspan(tsw0, 100, color="0.90", zorder=0)
    axB.axhline(1.0, color="0.7", ls=":", lw=0.8)
    for nm in C.BIARTIC:
        axB.plot(GRID, waves0[nm], color=C.COLORS[nm], lw=1.5, ls="-", zorder=2)
        axB.plot(GRID, waves1[nm], color=C.COLORS[nm], lw=1.5, ls="--", zorder=2)
    axB.set_xlabel("% stride")
    axB.set_ylabel("lMtilde")
    axB.set_title("B  Waveforms: w=0 (solid) vs w=0.1 (dashed)", loc="left", fontweight="bold", fontsize=9.3)
    axB.set_xlim(0, 100)
    from matplotlib.lines import Line2D
    legB = [Line2D([0], [0], color=C.COLORS[nm], label=C.SHORT[nm], lw=1.5) for nm in C.BIARTIC]
    legB += [Line2D([0], [0], color="0.3", ls="-", label="w=0"),
             Line2D([0], [0], color="0.3", ls="--", label="w=0.1")]
    axB.legend(handles=legB, loc="lower right", fontsize=5.8, frameon=False, ncol=1,
               labelspacing=0.25, handlelength=1.6)

    # Panel C ------------------------------------------------------------
    axC.axvspan(tsw0, 100, color="0.90", zorder=0)
    axC.axhline(0, color="0.6", lw=0.9)
    KC = {"pelvis_tilt": ("#000000", "\u0394 pelvis tilt"),
          "hip_flexion": ("#2166ac", "\u0394 hip flexion"),
          "knee_angle": ("#d73027", "\u0394 knee angle")}
    for nm, (col, lab) in KC.items():
        axC.plot(GRID, kin[nm], color=col, lw=1.5, label=lab)
    axC.set_xlabel("% stride")
    axC.set_ylabel("angle difference w=0.1 - w=0  (deg)")
    axC.set_title("C  Kinematic differences", loc="left", fontweight="bold", fontsize=9.3)
    axC.set_xlim(0, 100)
    axC.legend(loc="lower left", fontsize=6.2, frameon=False)

    fig.suptitle("Figure 7 | Speed vs hamstring load-surrogate trade-off (N=100, 3 warm-start paths)",
                 fontsize=10.3, fontweight="bold", x=0.01, ha="left", y=1.0)
    fig.text(0.01, -0.02,
             "3 w=0.1 solves = 3 deterministic warm-start paths (not independent restarts). Optimiser penalises a "
             "smooth integrated overstretch term; TS-window peak is a post-hoc readout. Candidate solutions do NOT "
             "prove runnability or injury reduction.", fontsize=6.2, color="0.35", ha="left")
    paths = C.save_fig(fig, "Fig7_pareto_N100")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common = dict(figure_id="Fig7", source_commit="e7b8de9", simulation_commit="e7b8de9",
                  analysis_commit="e7b8de9", mesh="N=100",
                  condition_family="HamPareto_Nom (w=0,0.05,0.1,0.2), 3 warm-start paths",
                  solver_acceptance_rule="strict Solve_Succeeded",
                  muscle_names_and_indices="biarticular semimem/semiten/bifemlh (L6-8/R52-54)",
                  source_csv=src_csv, plotting_script="scripts/Fig7_pareto_N100.py",
                  pdf_path=paths[0], svg_path=paths[1], png_path=paths[2],
                  generated_at=ts, qa_status="auto-pass; visual pending",
                  input_path="HamPareto_N100/checkpoint.csv + referenced MAT",
                  input_sha256="see pareto_checkpoint_audit.csv / sha256_manifest.csv")
    frags = [
        dict(common, panel_id="A", analytical_question="Can we compute candidates with low surrogate at small speed loss?",
             takeaway="w=0.05/0.1 meet the pre-registered target; w=0.2 exceeds the speed-loss budget.",
             phase_window="whole stride (speed); terminal-swing window (surrogate)",
             metric_formula="dSpeed=100*(v-v0)/v0; dSurro on biartic TS-window peak lMtilde mean"),
        dict(common, panel_id="B", analytical_question="How does the surrogate reduction appear in the waveform?",
             takeaway="w=0.1 lowers the terminal-swing lMtilde peak of all 3 biarticular muscles.",
             phase_window="full stride; TS shaded", metric_formula="lMtilde=lM/lMo"),
        dict(common, panel_id="C", analytical_question="What kinematics change between w=0 and w=0.1?",
             takeaway="Reduced terminal-swing hip flexion / posture shift, not an absolute-angle claim.",
             phase_window="full stride", metric_formula="q(w0.1)-q(w0) per coordinate, phase-normalized"),
    ]
    C.write_manifest_fragment("Fig7", frags)
    print("Fig7 done:", paths[2])
    print(f"  base speed={base_speed:.5f} surro={base_surro:.5f}")
    for p in sorted(pts, key=lambda z: (z["w"], z["tag"])):
        print(f"  {p['tag']:8s} w={p['w']:.2f} {p['path']:9s} dSpeed={p['dSpeed']:+.3f}% dSurro={p['dSurro']:+.3f}% {p['status']}")


if __name__ == "__main__":
    main()
