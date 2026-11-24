"""
probe_ham_metrics.py
Quick hamstring strain-metric extractor for the saved _PelvisShift_* conditions
(plus the Nominal reference). Pure Python/scipy — does NOT need MATLAB and does
not compete with a running sweep. Prints, per condition and per hamstring, the
peak normalised fibre length (lMtilde), peak passive force (Fpetilde) and peak
MTU length (lMTk_lr), as bilateral means, so the dose-response can be inspected
before the full MATLAB analysis runs.

Hamstring rows in the 92-row muscle arrays (1-based -> 0-based here):
  LEFT  semimem,semiten,bifemlh,bifemsh = 7,8,9,10  -> idx 6,7,8,9
  RIGHT                                  = 53,54,55,56 -> idx 52,53,54,55
"""
import glob
import os
import re

import numpy as np
from scipy.io import loadmat

RESULTS = os.path.join(os.path.dirname(__file__), "..", "Results")
HAM = ["semimem", "semiten", "bifemlh", "bifemsh"]
HAM_L = [6, 7, 8, 9]
HAM_R = [52, 53, 54, 55]


def _get(o, *names):
    for n in names:
        try:
            o = getattr(o, n)
        except AttributeError:
            o = o[n]
    return o


def metrics(path):
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    mv = _get(o, "muscleValues")
    lM = np.asarray(_get(mv, "lMtilde"), dtype=float)
    Fpe = np.asarray(_get(mv, "Fpetilde"), dtype=float)
    lMT = np.asarray(_get(mv, "lMTk_lr"), dtype=float)
    out = {}
    for i, nm in enumerate(HAM):
        l = HAM_L[i]
        r = HAM_R[i]
        out[nm + "_peakLM"] = 0.5 * (lM[l].max() + lM[r].max())
        out[nm + "_peakFpe"] = 0.5 * (Fpe[l].max() + Fpe[r].max())
        out[nm + "_peakLMT"] = 0.5 * (lMT[l].max() + lMT[r].max())
        out[nm + "_LMTexc"] = 0.5 * ((lMT[l].max() - lMT[l].min()) +
                                     (lMT[r].max() - lMT[r].min()))
    try:
        out["speed"] = float(_get(o, "ave_speed"))
    except Exception:
        out["speed"] = np.nan
    q = np.asarray(_get(o, "optVars_nsc", "q"), dtype=float)
    out["meanTilt"] = float(np.degrees(q[0]).mean())
    return out


def main():
    files = sorted(glob.glob(os.path.join(RESULTS, "pred_sprinting_data_*PelvisShift*.mat")))
    nom = sorted(glob.glob(os.path.join(RESULTS, "pred_sprinting_data_*04-February-2026*Nominal.mat")))
    rows = []
    for f in nom:
        d = metrics(f)
        d["cond"] = "Nominal"
        d["offset"] = 0.0
        rows.append(d)
    # newest per offset token
    seen = {}
    for f in files:
        tk = re.search(r"PelvisShift_([mp])(\d+)", os.path.basename(f))
        if not tk:
            continue
        off = (-1 if tk.group(1) == "m" else 1) * int(tk.group(2))
        if off not in seen or os.path.getmtime(f) > os.path.getmtime(seen[off]):
            seen[off] = f
    for off in sorted(seen):
        d = metrics(seen[off])
        d["cond"] = f"shift{off:+d}"
        d["offset"] = float(off)
        rows.append(d)

    rows.sort(key=lambda r: r["offset"])
    # print peak lMtilde dose-response
    hdr = f"{'cond':9s} {'off':>4s} {'tilt':>7s} {'speed':>6s} | " + \
        " ".join(f"{h[:4]:>6s}" for h in HAM)
    print("=== peak lMtilde (bilateral mean) ===")
    print(hdr)
    for r in rows:
        print(f"{r['cond']:9s} {r['offset']:4.0f} {r['meanTilt']:7.2f} {r['speed']:6.2f} | " +
              " ".join(f"{r[h+'_peakLM']:6.3f}" for h in HAM))
    print("\n=== peak Fpetilde (bilateral mean) ===")
    print(hdr)
    for r in rows:
        print(f"{r['cond']:9s} {r['offset']:4.0f} {r['meanTilt']:7.2f} {r['speed']:6.2f} | " +
              " ".join(f"{r[h+'_peakFpe']:6.3f}" for h in HAM))
    print("\n=== peak MTU length lMTk_lr (bilateral mean, m) ===")
    print(hdr)
    for r in rows:
        print(f"{r['cond']:9s} {r['offset']:4.0f} {r['meanTilt']:7.2f} {r['speed']:6.2f} | " +
              " ".join(f"{r[h+'_peakLMT']:6.3f}" for h in HAM))


if __name__ == "__main__":
    main()
