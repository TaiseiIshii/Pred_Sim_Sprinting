"""Probe v3 (TDPT) pilot results: verify the touchdown-pelvis-tilt manipulation
and check that other joints adapted naturally (re-optimised, not forced).

Loads the saved _PelvisTD_*.mat optimumOutput and prints, per condition:
  - IPOPT return_status
  - realized touchdown pelvis_tilt (deg)   <- should equal nominalTD + offset
  - emergent stride-mean pelvis_tilt (deg) <- NOT imposed
  - touchdown / peak right-hip flexion (deg)
  - achieved speed (m/s) and step length / time if available
  - peak normalized fibre length lMtilde of the biarticular hamstrings (R)

Run (base conda python):
  python analysis/probe_pelvic_td.py
"""
from __future__ import annotations

import glob
import os

import numpy as np
from scipy.io import loadmat

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Results")

# coordinate indices (1-based -> 0-based): 1 pelvis_tilt, 7 hip_flexion_r
PT = 0
HIP_R = 6
# muscleValues.lMtilde rows (1-based) for right biarticular hamstrings
HAM_R = {"semimem_r": 53, "semiten_r": 54, "bifemlh_r": 55, "bifemsh_r": 56}


def _get(o, *names):
    for n in names:
        o = getattr(o, n) if hasattr(o, n) else o[n]
    return o


def latest(pattern):
    files = glob.glob(os.path.join(RESULTS, pattern))
    return max(files, key=os.path.getmtime) if files else None


def probe(path):
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    print(f"\n=== {os.path.basename(path)} ===")
    print("  optimumOutput fields:", [f for f in dir(o) if not f.startswith("_")])
    # status
    try:
        print("  return_status:", _get(o, "stats", "return_status"))
    except Exception as e:
        print("  return_status: <n/a>", e)
    # kinematics
    try:
        q = np.asarray(_get(o, "optVars_nsc", "q"), dtype=float)  # 37 x ncol (rad)
        td_tilt = np.degrees(q[PT, 0])
        mean_tilt = np.degrees(np.mean(q[PT, :]))
        td_hip = np.degrees(q[HIP_R, 0])
        peak_hip = np.degrees(np.max(q[HIP_R, :]))
        print(f"  q shape: {q.shape}")
        print(f"  touchdown pelvis_tilt : {td_tilt:8.3f} deg   (imposed target)")
        print(f"  stride-mean pelvis_tilt: {mean_tilt:8.3f} deg   (EMERGENT)")
        print(f"  touchdown hip_flex_r  : {td_hip:8.3f} deg   (EMERGENT)")
        print(f"  peak hip_flex_r       : {peak_hip:8.3f} deg   (EMERGENT)")
        # displacement / speed if a final time is present
        disp = float(q[3, -1] - q[3, 0])  # pelvis_tx travel
        print(f"  pelvis_tx travel      : {disp:8.3f} m")
    except Exception as e:
        print("  kinematics: <error>", e)
    # speed / time fields (search common names)
    for nm in ("speed", "avgSpeed", "vCOM", "totalTime", "finalTime", "time"):
        try:
            v = _get(o, nm)
            print(f"  optimumOutput.{nm} = {np.asarray(v).ravel()[:3]}")
        except Exception:
            pass
    try:
        tt = float(np.asarray(_get(o, "optVars_nsc", "totalTime")).ravel()[0])
        print(f"  optVars_nsc.totalTime = {tt:.4f} s  -> step speed ~ {disp/tt:.3f} m/s")
    except Exception:
        pass
    # hamstring strain
    try:
        lM = np.asarray(_get(o, "muscleValues", "lMtilde"), dtype=float)
        print(f"  muscleValues.lMtilde shape: {lM.shape}")
        for nm, r in HAM_R.items():
            print(f"  peak lMtilde {nm:10s}: {np.max(lM[r - 1, :]):.4f}")
    except Exception as e:
        print("  muscle lMtilde: <n/a>", e)


def main():
    print("############## STANDARD bound conditions ##############")
    for tag in ("p6", "m6", "p0", "m2", "m4", "p2", "p4"):
        p = latest(f"pred_sprinting_data_*PelvisTD_{tag}.mat")
        if p:
            probe(p)
    print("\n############## WIDE (bound-relaxed) conditions ##############")
    for tag in ("m8", "m6", "m4", "m2", "p0"):
        p = latest(f"pred_sprinting_data_*PelvisTDwide_{tag}.mat")
        if p:
            probe(p)
    # nominal for reference
    nom = latest("pred_sprinting_data_*Nominal.mat")
    if nom:
        probe(nom)


if __name__ == "__main__":
    main()
