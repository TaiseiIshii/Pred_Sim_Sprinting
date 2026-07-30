"""Quick pre-flight: list all Nominal solutions with their mesh N and status,
so we can confirm a valid N=100 Nominal exists for the N=100 TDPT warm-start."""
import glob
import os

import numpy as np
from scipy.io import loadmat

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "Results")


def _get(o, *names):
    for n in names:
        o = getattr(o, n) if hasattr(o, n) else o[n]
    return o


for p in sorted(glob.glob(os.path.join(RESULTS, "pred_sprinting_data_*Nominal.mat")),
                key=os.path.getmtime):
    try:
        m = loadmat(p, struct_as_record=False, squeeze_me=True)
        o = m["optimumOutput"]
        N = int(np.asarray(_get(o, "options", "N")).ravel()[0])
        try:
            status = str(_get(o, "stats", "return_status"))
        except Exception:
            status = "?"
        q = np.asarray(_get(o, "optVars_nsc", "q"), dtype=float)
        td = np.degrees(q[0, 0])
        print(f"N={N:4d}  {status:<18s}  TDtilt={td:7.3f}deg  ncol={q.shape[1]:4d}  {os.path.basename(p)}")
    except Exception as e:
        print("  <error>", os.path.basename(p), e)
