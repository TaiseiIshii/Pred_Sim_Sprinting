"""Focused probe of the N=100 wide TDPT results: return_status, mesh N,
realized touchdown tilt, speed, and biarticular-hamstring peak lMtilde.
Filters by options.N == 100 so it never picks up the N=50 namesakes."""
import glob
import os

import numpy as np
from scipy.io import loadmat

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "Results")
HAM_R = {"semimem_r": 53, "semiten_r": 54, "bifemlh_r": 55, "bifemsh_r": 56}


def _get(o, *names):
    for n in names:
        o = getattr(o, n) if hasattr(o, n) else o[n]
    return o


def latest_n(tag, target_n, prefix="PelvisTDwide"):
    fs = sorted(glob.glob(os.path.join(
        RESULTS, f"pred_sprinting_data_*{prefix}_{tag}.mat")),
        key=os.path.getmtime, reverse=True)
    for p in fs:
        try:
            m = loadmat(p, struct_as_record=False, squeeze_me=True,
                        variable_names=["optimumOutput"])
            if int(np.asarray(_get(m["optimumOutput"], "options", "N")).ravel()[0]) == target_n:
                return p, m["optimumOutput"]
        except Exception:
            pass
    return None, None


for tag in ("m8", "m6", "m4", "m2", "p0", "p2", "p4", "p6"):
    p, o = latest_n(tag, 100)
    if o is None:
        print(f"{tag:>3}  (no N=100 result yet)")
        continue
    try:
        status = str(_get(o, "stats", "return_status"))
    except Exception:
        status = "?"
    q = np.asarray(_get(o, "optVars_nsc", "q"), dtype=float)
    td = np.degrees(q[0, 0])
    try:
        tt = float(np.asarray(_get(o, "optVars_nsc", "totalTime")).ravel()[0])
        speed = (q[3, -1] - q[3, 0]) / tt
    except Exception:
        speed = float("nan")
    lM = np.asarray(_get(o, "muscleValues", "lMtilde"), dtype=float)
    blh = float(np.max(lM[HAM_R["bifemlh_r"] - 1, :]))
    print(f"{tag:>3}  {status:<26s} TD={td:8.3f}deg  v={speed:6.3f}  bifemlh_lM={blh:.3f}  "
          f"{os.path.basename(p)}")
