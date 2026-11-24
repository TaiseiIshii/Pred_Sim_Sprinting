"""Verify fibre-velocity sign convention and force units (audit #5 core check).

Empirically answers:
  1. Does saved normalised velocity vMtilde use vMtilde>0 = LENGTHENING or SHORTENING?
     (compare sign of vMtilde with sign of d(lM)/dt computed on the REAL timeNodes)
  2. Is Fpass (vs Fpetilde) in Newtons?
  3. Magnitude sanity of a PHYSICAL negative-work integral vs the legacy
     Fce*vMtilde*dt "eccWork".

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" \
       analysis/validation/_check_velocity_sign.py
"""
import glob
import os
import numpy as np
from scipy.io import loadmat

RESULTS = os.path.join(os.path.dirname(__file__), "..", "..", "Results")
HAM_L = [6, 7, 8, 9]     # 0-based semimem,semiten,bifemlh,bifemsh (left)
NAMES = ["semimem", "semiten", "bifemlh", "bifemsh"]


def _get(o, *n):
    for k in n:
        o = getattr(o, k) if hasattr(o, k) else o[k]
    return o


def latest(token):
    fs = glob.glob(os.path.join(RESULTS, f"pred_sprinting_data_*{token}.mat"))
    return max(fs, key=os.path.getmtime) if fs else None


def check(token):
    p = latest(token)
    o = loadmat(p, struct_as_record=False, squeeze_me=True)["optimumOutput"]
    mv = _get(o, "muscleValues")
    lM = np.asarray(_get(mv, "lM"), dtype=float)
    vMt = np.asarray(_get(mv, "vMtilde"), dtype=float)
    Fce = np.asarray(_get(mv, "Fce"), dtype=float)
    Fpe_t = np.asarray(_get(mv, "Fpetilde"), dtype=float)
    Fpass = np.asarray(_get(mv, "Fpass"), dtype=float) if hasattr(mv, "Fpass") else None
    vMax = np.asarray(_get(mv, "vMax"), dtype=float) if hasattr(mv, "vMax") else None
    t = np.asarray(_get(o, "timeNodes"), dtype=float).ravel()
    tt = float(_get(o, "optVars_nsc", "totalTime"))
    t_uniform = np.linspace(0.0, tt, lM.shape[1])

    print(f"\n=== {os.path.basename(p)} (N={_get(o,'options','N')}) ===")
    print(f"  timeNodes: len={t.size} start={t[0]:.4f} end={t[-1]:.4f} "
          f"nonuniform_dt=[{np.diff(t).min()*1e3:.3f},{np.diff(t).max()*1e3:.3f}]ms")
    for i, nm in enumerate(NAMES):
        r = HAM_L[i]
        dlmdt = np.gradient(lM[r], t)            # physical m/s on REAL grid
        # correlation of sign between saved vMtilde and computed dlM/dt
        s = np.sign(dlmdt) == np.sign(vMt[r])
        agree = 100.0 * np.mean(s)
        # ratio dlmdt / vMtilde (should be ~ constant = lMo*vMax scale if consistent)
        good = np.abs(vMt[r]) > 0.05
        ratio = np.median(dlmdt[good] / vMt[r][good]) if good.any() else np.nan
        # legacy vs physical negative (eccentric) work
        legacy = float(np.sum(Fce[r] * np.clip(vMt[r], 0, None)) * (t_uniform[1] - t_uniform[0]))
        phys_len = float(np.sum(0.5 * (np.clip(Fce[r] * dlmdt, 0, None)[1:]
                        + np.clip(Fce[r] * dlmdt, 0, None)[:-1]) * np.diff(t)))
        print(f"  {nm:9s} sign(dlMdt)==sign(vMtilde): {agree:5.1f}%  "
              f"ratio dlMdt/vMtilde={ratio:+.4f} m  | legacy(Fce*vMt*dt)={legacy:8.1f}  "
              f"phys ecc-work(J)={phys_len:6.2f}")
    if Fpass is not None:
        print(f"  Fpass range=[{Fpass.min():.3g},{Fpass.max():.3g}] N  "
              f"Fpetilde range=[{Fpe_t.min():.3g},{Fpe_t.max():.3g}]")
    if vMax is not None:
        print(f"  vMax range=[{np.nanmin(vMax):.4g},{np.nanmax(vMax):.4g}] "
              f"(ham semimem_L vMax={vMax.ravel()[HAM_L[0]] if vMax.ndim==1 else vMax[HAM_L[0]].mean():.4g})")


if __name__ == "__main__":
    for tok in ("Nominal", "PelvisTDwide_m8"):
        check(tok)
