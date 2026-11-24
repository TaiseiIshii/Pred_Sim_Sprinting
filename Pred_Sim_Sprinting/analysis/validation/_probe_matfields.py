"""Empirical probe of saved optimumOutput .mat structure (Step 0 audit).

Resolves audit items:
  #4  Is the saved time vector uniform (linspace) or non-uniform (Radau)?
      Which grid do muscleValues live on (timeNodes vs timeGrid vs collocation)?
  #5  Is Fce in Newtons (=> Fce*dlM/dt is Watts) or normalised (=> not Joules)?
  Also: what solver status/stats fields exist, GRF shape, q shape.

Run with base python (numpy/scipy present):
  & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" \
      analysis/validation/_probe_matfields.py
"""
import os
import sys
import glob
import numpy as np
from scipy.io import loadmat

RESULTS = os.path.join(os.path.dirname(__file__), "..", "..", "Results")


def find(token):
    pats = glob.glob(os.path.join(RESULTS, f"pred_sprinting_data_*{token}.mat"))
    if not pats:
        return None
    return max(pats, key=os.path.getmtime)


def walk(o, prefix="", depth=0, maxdepth=2):
    """Print field names + shapes/types for a MATLAB struct object."""
    if depth > maxdepth:
        return
    names = getattr(o, "_fieldnames", None)
    if names is None:
        return
    for n in names:
        try:
            v = getattr(o, n)
        except Exception as e:
            print(f"{prefix}{n}: <err {e}>")
            continue
        if hasattr(v, "_fieldnames"):
            print(f"{prefix}{n}: struct")
            walk(v, prefix + "  ", depth + 1, maxdepth)
        elif isinstance(v, np.ndarray):
            info = f"ndarray shape={v.shape} dtype={v.dtype}"
            if v.size and np.issubdtype(v.dtype, np.number):
                fv = v.astype(float)
                info += f" min={np.nanmin(fv):.4g} max={np.nanmax(fv):.4g}"
            print(f"{prefix}{n}: {info}")
        else:
            s = str(v)
            print(f"{prefix}{n}: {type(v).__name__} = {s[:60]}")


def probe(token):
    p = find(token)
    print("=" * 78)
    print(f"TOKEN {token} -> {os.path.basename(p) if p else None}")
    if not p:
        return
    m = loadmat(p, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    print("--- optimumOutput top-level fields ---")
    print(list(getattr(o, "_fieldnames", [])))

    # stats
    if hasattr(o, "stats"):
        st = o.stats
        print("--- stats fields ---", list(getattr(st, "_fieldnames", [])))
        for f in ("return_status", "success", "iter_count", "t_wall_total"):
            if hasattr(st, f):
                print(f"   stats.{f} = {getattr(st, f)}")

    # time vectors
    for tn in ("timeNodes", "timeGrid", "timeGrid_con"):
        if hasattr(o, tn):
            tv = np.asarray(getattr(o, tn), dtype=float).ravel()
            d = np.diff(tv)
            uniform = np.allclose(d, d[0], rtol=1e-6) if d.size else True
            print(f"--- {tn}: len={tv.size} span=[{tv[0]:.5f},{tv[-1]:.5f}] "
                  f"uniform={uniform} dt_min={d.min():.5g} dt_max={d.max():.5g}"
                  if d.size else f"--- {tn}: len={tv.size}")

    # muscleValues
    mv = o.muscleValues
    print("--- muscleValues fields ---", list(getattr(mv, "_fieldnames", [])))
    for f in ("lM", "lMtilde", "lMTk_lr", "Fce", "Fpetilde", "Fiso", "vMtilde", "FT"):
        if hasattr(mv, f):
            v = np.asarray(getattr(mv, f), dtype=float)
            print(f"   mv.{f}: shape={v.shape} min={np.nanmin(v):.4g} "
                  f"max={np.nanmax(v):.4g} median={np.nanmedian(v):.4g}")

    # Ham rows (0-based) L semimem=6, R semimem=52
    for f in ("Fce", "Fiso", "FT", "lM", "lMtilde"):
        if hasattr(mv, f):
            v = np.asarray(getattr(mv, f), dtype=float)
            if v.ndim == 2 and v.shape[0] > 52:
                print(f"   ham semimem L(row6) {f}: min={v[6].min():.4g} max={v[6].max():.4g}")

    # options / speed / q
    if hasattr(o, "options") and hasattr(o.options, "N"):
        print("   options.N =", o.options.N)
    if hasattr(o, "ave_speed"):
        print("   ave_speed =", float(o.ave_speed))
    if hasattr(o, "optVars_nsc"):
        ov = o.optVars_nsc
        if hasattr(ov, "totalTime"):
            print("   optVars_nsc.totalTime =", float(ov.totalTime))
        if hasattr(ov, "q"):
            q = np.asarray(ov.q, dtype=float)
            print(f"   optVars_nsc.q shape={q.shape} "
                  f"pelvis_tilt(row0) deg=[{np.degrees(q[0]).min():.2f},{np.degrees(q[0]).max():.2f}]")
    if hasattr(o, "GRFs") and hasattr(o.GRFs, "R"):
        g = np.asarray(o.GRFs.R, dtype=float)
        print(f"   GRFs.R shape={g.shape}")


if __name__ == "__main__":
    tokens = sys.argv[1:] or ["Nominal", "PelvisTDwide_p0", "PelvisTD_p0"]
    for t in tokens:
        probe(t)
