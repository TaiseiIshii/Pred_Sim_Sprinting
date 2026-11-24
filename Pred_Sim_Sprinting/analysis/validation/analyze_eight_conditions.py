"""
analyze_eight_conditions.py -- Step 3: corrected muscle tension/stretch analysis of the
strict, speed-matched touchdown-pelvic-tilt (TDPT) 8-condition set, at BOTH meshes.

Uses ham_load_metrics (non-uniform timeNodes, physical units, reconstructed full stride).
Selects conditions from Results/Validation_Master/manifest.csv where experiment==PelvicTD
AND strict==True, one per requested pelvic offset (best constraint residual).

Outputs (Results/Validation_Master/, versioned; existing study files NOT touched):
  eight_condition_metrics_N50.csv, _N100.csv     (machine-readable, unit-suffixed columns)
  eight_condition_status.csv                     (condition x solver status/speed table)
  fig_e1_dose_peakLMtilde.png                    (muscle x achieved tilt, N50 vs N100)
  fig_e2_dose_force_work.png                     (passive force, tendon force, neg work)
  fig_e3_phase_TS_vs_ES.png                      (terminal swing vs early stance)
  fig_e4_velocity_timing.png                     (peak lengthening velocity, peak timing)

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" \
       analysis/validation/analyze_eight_conditions.py
"""
from __future__ import annotations

import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import ham_load_metrics as H

OUTDIR = os.path.join(H.RESULTS, "Validation_Master")
MANIFEST = os.path.join(OUTDIR, "manifest.csv")
MUS = ["semimem", "semiten", "bifemlh", "bifemsh"]
COLORS = {"semimem": "#1b7837", "semiten": "#762a83", "bifemlh": "#2166ac",
          "bifemsh": "#b2182b"}
BIARTIC = ["semimem", "semiten", "bifemlh"]


def read_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def select_conditions(rows, mesh_N):
    """One strict PelvicTD source file per requested offset at the given mesh (best residual)."""
    cand = {}
    for r in rows:
        if r["experiment"] != "PelvicTD" or r["strict"] != "True":
            continue
        if int(r["mesh_N"]) != mesh_N:
            continue
        off = float(r["requested_pelvis_offset_deg"])
        resid = float(r["constraint_residual"]) if r["constraint_residual"] not in ("", "nan") else 1e9
        if off not in cand or resid < cand[off][0]:
            cand[off] = (resid, r)
    return [cand[o][1] for o in sorted(cand)]


def compute(rows_sel):
    out = []
    for r in rows_sel:
        path = os.path.join(H.RESULTS, r["source_file"])
        m = H.condition_metrics(path)
        m["requested_offset_deg"] = float(r["requested_pelvis_offset_deg"])
        m["achieved_td_tilt_deg"] = float(r["achieved_td_tilt_deg"])
        m["achieved_mean_tilt_deg"] = float(r["achieved_pelvis_angle_deg"])
        m["speed_error_pct"] = float(r["speed_error_pct"])
        m["solver_status"] = r["solver_status"]
        m["source_file"] = r["source_file"]
        out.append(m)
    out.sort(key=lambda d: d["achieved_td_tilt_deg"])
    return out


CSV_MUSCLE_METRICS = [
    ("peak_lMtilde", ""), ("peak_MTU_len_m", "m"), ("MTU_excursion_m", "m"),
    ("peak_leng_vel_mps", "m/s"), ("peak_leng_rate_hz", "1/s"),
    ("peak_active_force_N", "N"), ("peak_passive_force_N", "N"),
    ("peak_tendon_force_N", "N"), ("peak_Fpetilde", ""),
    ("peak_act_ecc_power_W", "W"), ("neg_fiber_work_J", "J"),
    ("neg_fiber_work_tot_J", "J"), ("tPeak_lMtilde_pct", "%stride"),
    ("tPeak_Fce_pct", "%stride"), ("leng_at_peak_Fce", "bool"),
    ("cotiming_lMt_Fce_pct", "%stride"),
    ("TS_peak_lMtilde", ""), ("TS_peak_passive_force_N", "N"),
    ("TS_peak_tendon_force_N", "N"), ("TS_peak_leng_vel_mps", "m/s"),
    ("TS_neg_fiber_work_J", "J"),
    ("ES_peak_lMtilde", ""), ("ES_peak_active_force_N", "N"),
    ("ES_peak_tendon_force_N", "N"), ("ES_neg_fiber_work_J", "J"),
]


def write_csv(data, mesh_N):
    base = ["source_file", "solver_status", "requested_offset_deg",
            "achieved_td_tilt_deg", "achieved_mean_tilt_deg", "speed_mps",
            "speed_error_pct", "contact_s"]
    cols = list(base)
    for nm in MUS:
        for metric, _ in CSV_MUSCLE_METRICS:
            cols.append(f"{nm}_{metric}")
    path = os.path.join(OUTDIR, f"eight_condition_metrics_N{mesh_N}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # unit header row (companion to column names)
        units = {c: "" for c in base}
        units["achieved_td_tilt_deg"] = "deg"
        units["achieved_mean_tilt_deg"] = "deg"
        units["speed_mps"] = "m/s"
        units["contact_s"] = "s"
        for nm in MUS:
            for metric, u in CSV_MUSCLE_METRICS:
                units[f"{nm}_{metric}"] = u
        w.writerow(cols)
        w.writerow([units[c] for c in cols])
        for d in data:
            w.writerow([d.get(c, "") for c in cols])
    print(f"wrote {os.path.basename(path)}  ({len(data)} conditions)")
    return path


def _fit(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    A = np.vstack([x, np.ones_like(x)]).T
    slope, inter = np.linalg.lstsq(A, y, rcond=None)[0]
    yh = slope * x + inter
    ss = 1 - np.sum((y - yh) ** 2) / (np.sum((y - y.mean()) ** 2) + 1e-12)
    return slope, inter, ss


def fig_dose(dsets, out):
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.2))
    for ax, nm in zip(axes, MUS):
        for mesh_N, data, ls, mk in dsets:
            x = [d["achieved_td_tilt_deg"] for d in data]
            y = [d[f"{nm}_peak_lMtilde"] for d in data]
            ax.plot(x, y, ls, marker=mk, color=COLORS[nm], ms=5,
                    label=f"N={mesh_N}")
        ax.axhline(1.0, color="grey", lw=0.8, ls=":")
        ax.set_title(nm + ("" if nm in BIARTIC else "  (mono-artic. control)"))
        ax.set_xlabel("achieved touchdown pelvic tilt (deg)\n(more negative = more anterior)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    axes[0].set_ylabel("peak normalized fiber length lMtilde\n(terminal-swing peak)")
    fig.suptitle("TDPT 8-condition dose-response: peak fiber length "
                 "(reconstructed full stride, physical timeNodes)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", os.path.basename(out))


def fig_force_work(dsets, out):
    metrics = [("peak_passive_force_N", "peak passive fiber force (N)"),
               ("peak_tendon_force_N", "peak tendon force (N)"),
               ("neg_fiber_work_J", "negative fiber work per stride (J)")]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    for ax, (metric, ylab) in zip(axes, metrics):
        for nm in MUS:
            for mesh_N, data, ls, mk in dsets:
                if mesh_N != 100:      # keep the panel readable: N=100 lines
                    continue
                x = [d["achieved_td_tilt_deg"] for d in data]
                y = [d[f"{nm}_{metric}"] for d in data]
                ax.plot(x, y, "-", marker=mk, color=COLORS[nm], ms=5, label=nm)
        ax.set_xlabel("achieved touchdown pelvic tilt (deg)")
        ax.set_ylabel(ylab)
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=8)
    fig.suptitle("TDPT 8-condition (N=100): passive force, tendon force, negative work",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", os.path.basename(out))


def fig_phase(data, out):
    """Terminal swing vs early stance for the biarticular hamstrings (N=100)."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    pairs = [("peak_lMtilde", "TS_peak_lMtilde", "ES_peak_lMtilde", "peak lMtilde"),
             ("peak_passive_force_N", "TS_peak_passive_force_N", None,
              "terminal-swing peak passive force (N)"),
             ("neg_fiber_work_J", "TS_neg_fiber_work_J", "ES_neg_fiber_work_J",
              "negative fiber work (J)")]
    x = [d["achieved_td_tilt_deg"] for d in data]
    # panel A: TS vs ES peak lMtilde (biarticular mean)
    ax = axes[0]
    tsy = [np.mean([d[f"{nm}_TS_peak_lMtilde"] for nm in BIARTIC]) for d in data]
    esy = [np.mean([d[f"{nm}_ES_peak_lMtilde"] for nm in BIARTIC]) for d in data]
    ax.plot(x, tsy, "-o", color="#b2182b", label="terminal swing")
    ax.plot(x, esy, "-s", color="#2166ac", label="early stance")
    ax.set_ylabel("biarticular mean peak lMtilde")
    ax.set_title("phase comparison: fiber stretch")
    ax.legend(fontsize=8)
    # panel B: TS passive force per muscle
    ax = axes[1]
    for nm in BIARTIC:
        ax.plot(x, [d[f"{nm}_TS_peak_passive_force_N"] for d in data], "-o",
                color=COLORS[nm], ms=4, label=nm)
    ax.set_ylabel("terminal-swing peak passive force (N)")
    ax.set_title("passive loading in terminal swing")
    ax.legend(fontsize=8)
    # panel C: TS vs ES negative work (biarticular mean)
    ax = axes[2]
    tsw = [np.mean([d[f"{nm}_TS_neg_fiber_work_J"] for nm in BIARTIC]) for d in data]
    esw = [np.mean([d[f"{nm}_ES_neg_fiber_work_J"] for nm in BIARTIC]) for d in data]
    ax.plot(x, tsw, "-o", color="#b2182b", label="terminal swing")
    ax.plot(x, esw, "-s", color="#2166ac", label="early stance")
    ax.set_ylabel("biarticular mean negative fiber work (J)")
    ax.set_title("phase comparison: negative work")
    ax.legend(fontsize=8)
    for ax in axes:
        ax.set_xlabel("achieved touchdown pelvic tilt (deg)")
        ax.grid(alpha=0.3)
    fig.suptitle("TDPT 8-condition (N=100): terminal swing vs early stance", fontsize=11)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", os.path.basename(out))


def fig_vel_timing(data, out):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    x = [d["achieved_td_tilt_deg"] for d in data]
    ax = axes[0]
    for nm in MUS:
        ax.plot(x, [d[f"{nm}_peak_leng_vel_mps"] for d in data], "-o",
                color=COLORS[nm], ms=4, label=nm)
    ax.set_ylabel("peak fiber lengthening velocity (m/s)")
    ax.set_title("lengthening velocity")
    ax.legend(fontsize=8)
    ax = axes[1]
    for nm in MUS:
        ax.plot(x, [d[f"{nm}_tPeak_lMtilde_pct"] for d in data], "-o",
                color=COLORS[nm], ms=4, label=nm)
    ax.set_ylabel("timing of peak lMtilde (% of stride)")
    ax.set_title("peak-strain timing (biarticular ~ terminal swing)")
    ax.axhspan(80, 100, color="#fddbc7", alpha=0.5)
    ax.legend(fontsize=8)
    for ax in axes:
        ax.set_xlabel("achieved touchdown pelvic tilt (deg)")
        ax.grid(alpha=0.3)
    fig.suptitle("TDPT 8-condition (N=100): velocity and peak timing", fontsize=11)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", os.path.basename(out))


def sanity(data100):
    print("\n--- sanity checks (N=100) ---")
    x = np.array([d["achieved_td_tilt_deg"] for d in data100])
    for nm in MUS:
        y = np.array([d[f"{nm}_peak_lMtilde"] for d in data100])
        s, _, r2 = _fit(x, y)
        # x more negative = more anterior; slope sign wrt tilt
        tag = "biarticular" if nm in BIARTIC else "MONO control"
        print(f"  {nm:9s} ({tag:11s}) peak lMtilde slope={s:+.4f}/deg  R2={r2:.2f}  "
              f"range[{y.min():.3f},{y.max():.3f}] span={y.max()-y.min():.3f}")
    spd = np.array([d["speed_mps"] for d in data100])
    print(f"  speed range [{spd.min():.3f},{spd.max():.3f}] m/s  "
          f"(spread {100*(spd.max()-spd.min())/spd.mean():.2f}% -> matched performance)")
    # leng_at_peak_Fce should be True for biarticular (eccentric at peak force)
    for nm in BIARTIC:
        allL = all(d[f"{nm}_leng_at_peak_Fce"] in (True, "True") for d in data100)
        print(f"  {nm}: lengthening at peak active force in ALL conditions = {allL}")


def status_table(rows, meshes):
    path = os.path.join(OUTDIR, "eight_condition_status.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mesh_N", "requested_offset_deg", "condition", "solver_status",
                    "achieved_td_tilt_deg", "achieved_mean_tilt_deg",
                    "achieved_speed_mps", "speed_error_pct", "constraint_residual"])
        for mesh_N in meshes:
            sel = select_conditions(rows, mesh_N)
            for r in sorted(sel, key=lambda r: float(r["requested_pelvis_offset_deg"])):
                w.writerow([mesh_N, r["requested_pelvis_offset_deg"], r["condition"],
                            r["solver_status"], r["achieved_td_tilt_deg"],
                            r["achieved_pelvis_angle_deg"], r["achieved_speed_mps"],
                            r["speed_error_pct"], r["constraint_residual"]])
    print("wrote", os.path.basename(path))


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    rows = read_manifest()
    sel50 = select_conditions(rows, 50)
    sel100 = select_conditions(rows, 100)
    print(f"selected strict PelvicTD conditions: N=50 -> {len(sel50)}, N=100 -> {len(sel100)}")
    data50 = compute(sel50)
    data100 = compute(sel100)
    write_csv(data50, 50)
    write_csv(data100, 100)
    status_table(rows, [50, 100])

    dsets = [(50, data50, "--", "s"), (100, data100, "-", "o")]
    fig_dose(dsets, os.path.join(OUTDIR, "fig_e1_dose_peakLMtilde.png"))
    fig_force_work(dsets, os.path.join(OUTDIR, "fig_e2_dose_force_work.png"))
    fig_phase(data100, os.path.join(OUTDIR, "fig_e3_phase_TS_vs_ES.png"))
    fig_vel_timing(data100, os.path.join(OUTDIR, "fig_e4_velocity_timing.png"))
    sanity(data100)


if __name__ == "__main__":
    main()
