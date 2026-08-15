"""
determinants.py  --  Step 7: which kinematic variables track the biarticular hamstring load
surrogate, and the pelvis -> coordination -> fiber-length pathway.

Uses the strict TDPT N=100 set (8 conditions).  Extracts candidate explanatory variables from
the saved kinematics and correlates them (Pearson r, DESCRIPTIVE) with the corrected load
surrogates.  Honesty: N = 8 SIMULATION CONDITIONS (not human subjects); no p-values, no
multiple regression, no over-fitted model.  Interaction terms require the morphology x pelvis
factorial (Step 10) and are not estimated here.

Outputs (Results/Validation_Master/):
  determinants.csv               (per-condition predictors + outcomes)
  determinants_correlations.csv  (predictor x outcome Pearson r)

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" \
       analysis/validation/determinants.py
"""
from __future__ import annotations

import csv
import os

import numpy as np
from scipy.io import loadmat

import ham_load_metrics as H

OUTDIR = os.path.join(H.RESULTS, "Validation_Master")
MANIFEST = os.path.join(OUTDIR, "manifest.csv")
BIARTIC = ["semimem", "semiten", "bifemlh"]

# 0-based q rows (Hamner full-body order; magnitudes sanity-checked at runtime)
Q_PELVIS_TILT = 0
Q_HIP_R = 6
Q_KNEE_R = 9
Q_HIP_L = 13
Q_KNEE_L = 16
Q_LUMBAR_EXT = 20


def _get(o, *n):
    for k in n:
        o = getattr(o, k) if hasattr(o, k) else o[k]
    return o


def predictors(path):
    o = loadmat(path, struct_as_record=False, squeeze_me=True)["optimumOutput"]
    q = np.asarray(_get(o, "optVars_nsc", "q"), float)          # 37 x ncol (rad)
    tt = float(np.asarray(_get(o, "optVars_nsc", "totalTime")).ravel()[0])
    try:
        qdot = np.asarray(_get(o, "optVars_nsc", "qdot"), float)
        pelvic_angvel = float(np.degrees(np.abs(qdot[Q_PELVIS_TILT]).max()))
    except Exception:
        dt = tt / (q.shape[1] - 1)
        pelvic_angvel = float(np.degrees(np.abs(np.gradient(q[Q_PELVIS_TILT], dt)).max()))
    deg = np.degrees
    return {
        "td_tilt_deg": float(deg(q[Q_PELVIS_TILT, 0])),
        "mean_tilt_deg": float(deg(q[Q_PELVIS_TILT].mean())),
        "hipR_td_deg": float(deg(q[Q_HIP_R, 0])),
        "hipR_peak_deg": float(deg(q[Q_HIP_R].max())),
        "hipL_peak_deg": float(deg(q[Q_HIP_L].max())),
        "kneeR_peak_flex_deg": float(deg(np.abs(q[Q_KNEE_R].min()))),   # flexion is negative
        "trunk_lean_mean_deg": float(deg(q[Q_LUMBAR_EXT].mean())),
        "pelvic_tilt_angvel_peak_dps": pelvic_angvel,
        "step_duration_s": tt,
    }


def read_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def select(rows, mesh_N=100):
    cand = {}
    for r in rows:
        if r["experiment"] != "PelvicTD" or r["strict"] != "True" or int(r["mesh_N"]) != mesh_N:
            continue
        off = float(r["requested_pelvis_offset_deg"])
        resid = float(r["constraint_residual"]) if r["constraint_residual"] not in ("", "nan") else 1e9
        if off not in cand or resid < cand[off][0]:
            cand[off] = (resid, r)
    return [cand[o][1] for o in sorted(cand)]


def pearson(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if x.std() < 1e-12 or y.std() < 1e-12:
        return np.nan
    return float(np.corrcoef(x, y)[0, 1])


def main():
    rows = read_manifest()
    sel = select(rows, 100)
    recs = []
    for r in sel:
        p = os.path.join(H.RESULTS, r["source_file"])
        m = H.condition_metrics(p)
        pr = predictors(p)
        pr["contact_s"] = m["contact_s"]
        pr["swing_duration_s"] = pr["step_duration_s"] - m["contact_s"]
        out = {
            "biartic_peak_lMtilde": float(np.mean([m[f"{nm}_peak_lMtilde"] for nm in BIARTIC])),
            "biartic_TS_peak_lMtilde": float(np.mean([m[f"{nm}_TS_peak_lMtilde"] for nm in BIARTIC])),
            "biartic_neg_work_J": float(np.mean([m[f"{nm}_neg_fiber_work_J"] for nm in BIARTIC])),
            "biartic_peak_passive_N": float(np.mean([m[f"{nm}_peak_passive_force_N"] for nm in BIARTIC])),
        }
        rec = {"condition": r["condition"], "speed_mps": m["speed_mps"], **pr, **out}
        recs.append(rec)
    recs.sort(key=lambda d: d["td_tilt_deg"])

    # sanity print of coordinate magnitudes
    print("coordinate sanity (deg): hipR_peak "
          f"[{min(r['hipR_peak_deg'] for r in recs):.1f},{max(r['hipR_peak_deg'] for r in recs):.1f}]  "
          f"hipL_peak [{min(r['hipL_peak_deg'] for r in recs):.1f},{max(r['hipL_peak_deg'] for r in recs):.1f}]  "
          f"kneeR_peak_flex [{min(r['kneeR_peak_flex_deg'] for r in recs):.1f},"
          f"{max(r['kneeR_peak_flex_deg'] for r in recs):.1f}]  "
          f"trunk_lean [{min(r['trunk_lean_mean_deg'] for r in recs):.1f},"
          f"{max(r['trunk_lean_mean_deg'] for r in recs):.1f}]")

    pred_keys = ["td_tilt_deg", "mean_tilt_deg", "hipR_td_deg", "hipR_peak_deg", "hipL_peak_deg",
                 "kneeR_peak_flex_deg", "trunk_lean_mean_deg", "pelvic_tilt_angvel_peak_dps",
                 "contact_s", "swing_duration_s", "speed_mps"]
    out_keys = ["biartic_peak_lMtilde", "biartic_TS_peak_lMtilde", "biartic_neg_work_J",
                "biartic_peak_passive_N"]

    with open(os.path.join(OUTDIR, "determinants.csv"), "w", newline="", encoding="utf-8") as f:
        cols = ["condition", "speed_mps"] + pred_keys[:-1] + out_keys
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(recs)
    print("wrote determinants.csv")

    print("\n--- Pearson r (DESCRIPTIVE, N=8 conditions; not subjects) ---")
    print(f"{'predictor':30s}" + "".join(f"{k.split('_')[1][:7]:>9s}" for k in out_keys))
    corr_rows = []
    for pk in pred_keys:
        x = [r[pk] for r in recs]
        line = f"{pk:30s}"
        crow = {"predictor": pk}
        for ok in out_keys:
            r_ = pearson(x, [r[ok] for r in recs])
            crow[ok] = round(r_, 3)
            line += f"{r_:>9.2f}"
        corr_rows.append(crow)
        print(line)
    with open(os.path.join(OUTDIR, "determinants_correlations.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["predictor"] + out_keys)
        w.writeheader()
        w.writerows(corr_rows)
    print("wrote determinants_correlations.csv")

    # pathway summary (chain correlations)
    tds = [r["td_tilt_deg"] for r in recs]
    hip = [r["hipR_td_deg"] for r in recs]
    lmt = [r["biartic_TS_peak_lMtilde"] for r in recs]
    work = [r["biartic_neg_work_J"] for r in recs]
    print("\n--- pathway (chain correlations) ---")
    print(f"  pelvis td tilt -> hip flexion (td)     r = {pearson(tds, hip):+.3f}")
    print(f"  hip flexion (td) -> TS peak lMtilde    r = {pearson(hip, lmt):+.3f}")
    print(f"  pelvis td tilt -> TS peak lMtilde      r = {pearson(tds, lmt):+.3f}")
    print(f"  TS peak lMtilde -> negative work       r = {pearson(lmt, work):+.3f}")
    print("  (interaction terms require morphology x pelvis factorial -> Step 10 / BLOCKED)")


if __name__ == "__main__":
    main()
