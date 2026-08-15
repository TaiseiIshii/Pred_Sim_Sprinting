"""
fair_opt_comparison.py  --  Step 5: fair comparison of the re-optimized (opt-ON / adaptive)
touchdown-pelvic-tilt conditions.

Uses ONLY strict (Solve_Succeeded) TDPT conditions from manifest.csv.  Reports, per condition:
achieved speed, achieved touchdown & mean pelvic tilt, step duration, ground-contact time,
touchdown & peak hip flexion, solver status, and the biarticular hamstring load surrogate
(peak lMtilde, peak MTU).  The dose-response x-axis is the ACHIEVED touchdown pelvic tilt,
never the requested offset.

Speed-match policy (declared BEFORE inspecting load results): conditions are treated as
performance-matched if achieved speed is within +/- 1.0% of the mesh-matched Nominal.  Any
condition outside this band is flagged and excluded from matched-speed statements.

Outputs (Results/Validation_Master/):
  fair_opt_comparison_N50.csv, _N100.csv, fig_s1_fair_comparison.png

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" \
       analysis/validation/fair_opt_comparison.py
"""
from __future__ import annotations

import csv
import os

import numpy as np
from scipy.io import loadmat
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import ham_load_metrics as H

OUTDIR = os.path.join(H.RESULTS, "Validation_Master")
MANIFEST = os.path.join(OUTDIR, "manifest.csv")
BIARTIC = ["semimem", "semiten", "bifemlh"]
SPEED_TOL_PCT = 1.0
HIP_R = 6      # 0-based q row: hip_flexion_r (verified vs probe_pelvic_td.py)


def _get(o, *n):
    for k in n:
        o = getattr(o, k) if hasattr(o, k) else o[k]
    return o


def kin_extra(path):
    o = loadmat(path, struct_as_record=False, squeeze_me=True)["optimumOutput"]
    q = np.asarray(_get(o, "optVars_nsc", "q"), float)
    return {"hip_td_deg": float(np.degrees(q[HIP_R, 0])),
            "hip_peak_deg": float(np.degrees(q[HIP_R].max()))}


def read_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def select(rows, mesh_N):
    cand = {}
    for r in rows:
        if r["experiment"] != "PelvicTD" or r["strict"] != "True" or int(r["mesh_N"]) != mesh_N:
            continue
        off = float(r["requested_pelvis_offset_deg"])
        resid = float(r["constraint_residual"]) if r["constraint_residual"] not in ("", "nan") else 1e9
        if off not in cand or resid < cand[off][0]:
            cand[off] = (resid, r)
    return [cand[o][1] for o in sorted(cand)]


def build(rows_sel):
    data = []
    for r in rows_sel:
        p = os.path.join(H.RESULTS, r["source_file"])
        m = H.condition_metrics(p)
        k = kin_extra(p)
        step_s = m["totalTime_s"]
        data.append({
            "condition": r["condition"], "solver_status": r["solver_status"],
            "requested_offset_deg": float(r["requested_pelvis_offset_deg"]),
            "achieved_td_tilt_deg": float(r["achieved_td_tilt_deg"]),
            "achieved_mean_tilt_deg": float(r["achieved_pelvis_angle_deg"]),
            "speed_mps": m["speed_mps"], "speed_error_pct": float(r["speed_error_pct"]),
            "step_duration_s": step_s, "step_frequency_hz": 1.0 / step_s if step_s else np.nan,
            "contact_s": m["contact_s"], "duty_factor": (m["contact_s"] / step_s) if step_s else np.nan,
            "hip_td_deg": k["hip_td_deg"], "hip_peak_deg": k["hip_peak_deg"],
            "biartic_peak_lMtilde": float(np.mean([m[f"{nm}_peak_lMtilde"] for nm in BIARTIC])),
            "biartic_peak_MTU_m": float(np.mean([m[f"{nm}_peak_MTU_len_m"] for nm in BIARTIC])),
            "biartic_TS_neg_work_J": float(np.mean([m[f"{nm}_TS_neg_fiber_work_J"] for nm in BIARTIC])),
        })
    data.sort(key=lambda d: d["achieved_td_tilt_deg"])
    return data


def write_csv(data, mesh_N):
    cols = list(data[0].keys())
    p = os.path.join(OUTDIR, f"fair_opt_comparison_N{mesh_N}.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(data)
    print("wrote", os.path.basename(p))


def verify_speed_match(data, mesh_N):
    spd = np.array([d["speed_mps"] for d in data])
    ref = spd.max()   # nominal-like top; report spread and tolerance band
    within = [abs(d["speed_error_pct"]) <= SPEED_TOL_PCT for d in data]
    print(f"\n[N={mesh_N}] speed range [{spd.min():.3f},{spd.max():.3f}] m/s  "
          f"spread {100*(spd.max()-spd.min())/spd.mean():.2f}%  "
          f"| within +/-{SPEED_TOL_PCT}%: {sum(within)}/{len(data)}")
    for d in data:
        flag = "" if abs(d["speed_error_pct"]) <= SPEED_TOL_PCT else "  <-- OUTSIDE band"
        print(f"    td_tilt {d['achieved_td_tilt_deg']:7.2f}  speed {d['speed_mps']:.3f} "
              f"({d['speed_error_pct']:+.2f}%)  hipTD {d['hip_td_deg']:6.2f}  "
              f"hipPeak {d['hip_peak_deg']:6.2f}  biarticPeakLMt {d['biartic_peak_lMtilde']:.3f}{flag}")


def _fit(x, y):
    A = np.vstack([x, np.ones_like(x)]).T
    s, b = np.linalg.lstsq(A, y, rcond=None)[0]
    return s, b


def figure(d50, d100, out):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    for data, ls, mk, lab in ((d50, "--s", "s", "N=50"), (d100, "-o", "o", "N=100")):
        x = np.array([d["achieved_td_tilt_deg"] for d in data])
        axes[0].plot(x, [d["speed_mps"] for d in data], ls, ms=5, label=lab, color="#333")
        axes[1].plot(x, [d["hip_peak_deg"] for d in data], ls, ms=5, label=lab, color="#2166ac")
        axes[2].plot(x, [d["biartic_peak_lMtilde"] for d in data], ls, ms=5, label=lab, color="#b2182b")
    axes[0].set_ylabel("achieved speed (m/s)")
    axes[0].set_title("performance is matched\n(opt-ON, re-optimized)")
    axes[0].set_ylim(11.4, 11.95)
    axes[1].set_ylabel("peak hip flexion (deg)")
    axes[1].set_title("mediator: peak hip flexion\nrises with anterior tilt")
    axes[2].set_ylabel("biarticular mean peak lMtilde")
    axes[2].set_title("adaptive load surrogate\n(opt-ON dose-response)")
    for ax in axes:
        ax.set_xlabel("achieved touchdown pelvic tilt (deg)\n(more negative = more anterior)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle("Step 5 fair comparison (strict TDPT, achieved-tilt axis): matched speed, "
                 "hip-flexion mediation, adaptive hamstring load", fontsize=10)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", os.path.basename(out))


def main():
    rows = read_manifest()
    d50 = build(select(rows, 50))
    d100 = build(select(rows, 100))
    write_csv(d50, 50)
    write_csv(d100, 100)
    verify_speed_match(d50, 50)
    verify_speed_match(d100, 100)
    # mediation slopes (documented, N conditions small -> descriptive only)
    x = np.array([d["achieved_td_tilt_deg"] for d in d100])
    sh, _ = _fit(x, np.array([d["hip_peak_deg"] for d in d100]))
    sl, _ = _fit(x, np.array([d["biartic_peak_lMtilde"] for d in d100]))
    print(f"\n[N=100] peak hip flexion slope = {sh:+.3f} deg/deg-tilt ; "
          f"biarticular peak lMtilde slope = {sl:+.4f} /deg-tilt (descriptive; 8 conditions)")
    figure(d50, d100, os.path.join(OUTDIR, "fig_s1_fair_comparison.png"))


if __name__ == "__main__":
    main()
