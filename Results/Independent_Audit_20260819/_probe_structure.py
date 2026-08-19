"""Independent audit probe: dump the raw structure of a result .mat so the audit
scripts can be written against the ACTUAL fields (stats, constraint residual, warm-start
provenance). Read-only. Run with base miniconda python."""
import os
import sys
import numpy as np
from scipy.io import loadmat

RESULTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RES = os.path.join(RESULTS, "Results")


def _fields(o):
    if hasattr(o, "_fieldnames"):
        return list(o._fieldnames)
    if isinstance(o, dict):
        return [k for k in o if not k.startswith("__")]
    return []


def _get(o, name):
    return getattr(o, name) if hasattr(o, name) else o[name]


def dump(path, depth_fields=True):
    print("=" * 78)
    print("FILE:", os.path.basename(path))
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    top = [k for k in m if not k.startswith("__")]
    print("top-level vars:", top)
    o = m["optimumOutput"]
    print("optimumOutput fields:", _fields(o))
    # options.N
    try:
        opt = _get(o, "options")
        print("options fields:", _fields(opt))
        print("  options.N =", int(np.asarray(_get(opt, "N")).ravel()[0]))
    except Exception as e:
        print("  options err:", e)
    # stats
    try:
        st = _get(o, "stats")
        print("stats fields:", _fields(st))
        for k in _fields(st):
            v = _get(st, k)
            va = np.asarray(v)
            if va.dtype.kind in "iufb" and va.size <= 4:
                print(f"  stats.{k} = {va.ravel()}")
            elif va.dtype.kind in "US":
                print(f"  stats.{k} = {str(v)!r}")
            elif hasattr(v, "_fieldnames"):
                sub = _fields(v)
                print(f"  stats.{k} = <struct fields={sub}>")
                for sk in sub:
                    try:
                        sv = np.asarray(_get(v, sk), float).ravel()
                        print(f"       .{sk}: shape={sv.shape} last={sv[-1] if sv.size else 'NA'}")
                    except Exception:
                        pass
            else:
                print(f"  stats.{k}: shape={va.shape} dtype={va.dtype}")
    except Exception as e:
        print("  stats err:", e)
    # ave_speed, totalTime
    for f in ("ave_speed",):
        try:
            print(f"{f} =", float(np.asarray(_get(o, f)).ravel()[0]))
        except Exception as e:
            print(f"{f} err:", e)
    # optVars_nsc
    try:
        ov = _get(o, "optVars_nsc")
        print("optVars_nsc fields:", _fields(ov))
        q = np.asarray(_get(ov, "q"), float)
        print("  q shape:", q.shape, " td pelvis_tilt deg = %.4f" % np.degrees(q[0, 0]),
              " mean = %.4f" % np.degrees(q[0].mean()))
        tt = _get(ov, "totalTime")
        print("  totalTime =", float(np.asarray(tt).ravel()[0]))
    except Exception as e:
        print("  optVars err:", e)
    # muscleValues
    try:
        mv = _get(o, "muscleValues")
        fs = _fields(mv)
        print("muscleValues fields:", fs)
        for k in fs:
            try:
                a = np.asarray(_get(mv, k), float)
                print(f"  mv.{k}: shape={a.shape}")
            except Exception:
                print(f"  mv.{k}: (non-numeric)")
    except Exception as e:
        print("  muscleValues err:", e)
    # timeNodes
    try:
        t = np.asarray(_get(o, "timeNodes"), float).ravel()
        dt = np.diff(t)
        print("timeNodes: n=%d t0=%.4f tE=%.4f dt[min,max]=[%.5f,%.5f]" %
              (t.size, t[0], t[-1], dt.min(), dt.max()))
    except Exception as e:
        print("timeNodes err:", e)
    # GRFs
    try:
        g = _get(o, "GRFs")
        print("GRFs fields:", _fields(g))
        R = np.asarray(_get(g, "R"), float)
        print("  GRFs.R shape:", R.shape)
    except Exception as e:
        print("GRFs err:", e)
    # search for any warm-start / guess / provenance-like field
    print("candidate provenance/warm-start fields:",
          [f for f in _fields(o) if any(s in f.lower()
           for s in ("guess", "warm", "prev", "init", "source", "start", "file", "name"))])


if __name__ == "__main__":
    files = sys.argv[1:]
    for p in files:
        if not os.path.isabs(p):
            p = os.path.join(RES, p)
        dump(p)
