"""
probe_pelvic_shift.py
Quick verification that the _PelvisShift_* manipulation actually moved the
realised mean pelvis_tilt (the v1 PelvisTilt study failed exactly here).
Loads each saved PelvisShift .mat (+ Nominal reference) with scipy and prints
the realised mean/min/max pelvis_tilt, average speed, solver status, and peak
vertical GRF. No MATLAB needed (does not compete with the running sweep).
"""
import glob
import os
import numpy as np
from scipy.io import loadmat

RESULTS = os.path.join(os.path.dirname(__file__), "..", "Results")


def _get(o, *names):
    for n in names:
        try:
            o = getattr(o, n)
        except AttributeError:
            o = o[n]
    return o


def probe(path):
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    q = np.asarray(_get(o, "optVars_nsc", "q"), dtype=float)  # [37 x nCol] rad
    ptilt = np.degrees(q[0, :])
    try:
        spd = float(_get(o, "ave_speed"))
    except Exception:
        spd = np.nan
    try:
        status = str(_get(o, "stats", "return_status"))
    except Exception:
        status = "?"
    try:
        grfR = np.asarray(_get(o, "GRFs", "R"), dtype=float)
        gv = float(np.nanmax(grfR[:, 1]))
    except Exception:
        gv = np.nan
    return dict(mean=ptilt.mean(), lo=ptilt.min(), hi=ptilt.max(),
                spd=spd, status=status, grfv=gv, n=q.shape[1])


def main():
    files = sorted(glob.glob(os.path.join(RESULTS, "pred_sprinting_data_*PelvisShift*.mat")))
    nom = sorted(glob.glob(os.path.join(RESULTS, "pred_sprinting_data_*04-February-2026*Nominal.mat")))
    print(f"{'condition':28s} {'offset':>6s} {'meanTilt':>9s} {'range':>16s} {'speed':>7s} {'GRFv':>7s} status")
    for f in nom:
        r = probe(f)
        print(f"{'Nominal(ref)':28s} {0:6.1f} {r['mean']:9.2f} [{r['lo']:6.2f},{r['hi']:6.2f}] {r['spd']:7.3f} {r['grfv']:7.0f} {r['status']}")
    for f in files:
        base = os.path.basename(f)
        # parse offset token
        import re
        mobj = re.search(r"PelvisShift_([mp])(\d+)", base)
        off = (-1 if mobj.group(1) == "m" else 1) * int(mobj.group(2)) if mobj else np.nan
        r = probe(f)
        tag = base.split("___")[-1].replace(".mat", "")
        flag = ""
        # expected realised mean ~ -7.26 + offset
        exp = -7.26 + off
        if abs(r["mean"] - exp) < 1.0:
            flag = "OK"
        else:
            flag = f"!! exp~{exp:.1f}"
        print(f"{tag:28s} {off:6.1f} {r['mean']:9.2f} [{r['lo']:6.2f},{r['hi']:6.2f}] {r['spd']:7.3f} {r['grfv']:7.0f} {r['status']}  {flag}")


if __name__ == "__main__":
    main()
