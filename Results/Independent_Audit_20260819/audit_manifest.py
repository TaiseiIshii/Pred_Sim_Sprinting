"""
audit_manifest.py -- INDEPENDENT source manifest for the reproducibility audit.

Scans EVERY Results/pred_sprinting_data_*.mat (no dedup, no reliance on the prior
Results/Validation_Master/manifest.csv). For each file records absolute path, SHA256,
size, mtime, parsed experiment/condition/requested-offset, mesh N, solver return_status,
success, iter_count, final primal infeasibility (stats.iterations.inf_pr[-1]) and dual
inf_du, final objective, signed touchdown pelvis_tilt q[0,0] (deg) and its negation
("anterior tilt amount"), mean pelvis tilt, achieved speed, totalTime, t0/tE.

Writes Results/Independent_Audit_20260819/final_source_manifest.csv.
Read-only w.r.t. all existing data. Run with base miniconda python.
"""
from __future__ import annotations
import csv
import datetime as dt
import glob
import hashlib
import os
import re
import numpy as np
from scipy.io import loadmat

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, ".."))          # ...\Results
REPO = os.path.abspath(os.path.join(RESULTS, ".."))
OUT = os.path.join(HERE, "final_source_manifest.csv")


def sha256(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def _get(o, *names):
    for n in names:
        o = getattr(o, n) if hasattr(o, n) else o[n]
    return o


def token_of(path):
    m = re.search(r"___(.+)\.mat$", os.path.basename(path))
    return m.group(1) if m else os.path.basename(path)


def classify(tok):
    off = np.nan
    mo = re.search(r"_([mp])(\d+)$", tok) or re.search(r"_([mp])(\d+)_", tok)
    if mo:
        off = (-1 if mo.group(1) == "m" else 1) * float(mo.group(2))
    if tok == "Nominal":
        return "Nominal", "nominal", 0.0
    for pre, exp in (("PelvisTDwide", "PelvicTD_wide"), ("PelvisTD", "PelvicTD_standard"),
                     ("PelvisShift", "PelvicShift"), ("PelvisTilt", "PelvicTilt"),
                     ("HamFascicle", "Morphology_fascicle"), ("HamStrength", "Morphology_strength"),
                     ("HamArch", "Morphology_architecture"), ("HamPareto", "HamPareto"),
                     ("HamEcc", "HamEcc"), ("HamCompEQ", "HamCompEQ"), ("HamPasv", "HamPasv"),
                     ("HamObj", "HamObj")):
        if tok.startswith(pre):
            return exp, tok, off
    if re.match(r"(IKTD|HTD)_", tok):
        return "Haralabidis_TD", tok, off
    return "other", tok, off


def read_meta(path):
    m = loadmat(path, struct_as_record=False, squeeze_me=True,
                variable_names=["optimumOutput"])
    o = m["optimumOutput"]
    mv = _get(o, "muscleValues")
    ncol = int(np.asarray(_get(mv, "lMtilde"), float).shape[1])
    N = int(np.asarray(_get(o, "options", "N")).ravel()[0])
    status, success, itc = "unknown", False, -1
    inf_pr = inf_du = obj = np.nan
    try:
        st = _get(o, "stats")
        status = str(_get(st, "return_status"))
        success = bool(int(np.asarray(_get(st, "success")).ravel()[0]))
        itc = int(np.asarray(_get(st, "iter_count")).ravel()[0])
        it = _get(st, "iterations")
        inf_pr = float(np.asarray(_get(it, "inf_pr"), float).ravel()[-1])
        inf_du = float(np.asarray(_get(it, "inf_du"), float).ravel()[-1])
        obj = float(np.asarray(_get(it, "obj"), float).ravel()[-1])
    except Exception:
        pass
    q = np.asarray(_get(o, "optVars_nsc", "q"), float)
    td = float(np.degrees(q[0, 0]))
    mean_t = float(np.degrees(q[0].mean()))
    try:
        spd = float(np.asarray(_get(o, "ave_speed")).ravel()[0])
    except Exception:
        spd = np.nan
    try:
        tt = float(np.asarray(_get(o, "optVars_nsc", "totalTime")).ravel()[0])
    except Exception:
        tt = np.nan
    try:
        t = np.asarray(_get(o, "timeNodes"), float).ravel()
        t0, tE = float(t[0]), float(t[-1])
    except Exception:
        t0 = tE = np.nan
    return dict(N=N, ncol=ncol, q_cols=q.shape[1], status=status, success=success,
                iter_count=itc, inf_pr=inf_pr, inf_du=inf_du, obj=obj,
                td_tilt_deg=td, anterior_tilt_deg=-td, mean_tilt_deg=mean_t,
                speed_mps=spd, totalTime_s=tt, t0=t0, tE=tE)


def main():
    files = sorted(glob.glob(os.path.join(RESULTS, "pred_sprinting_data_*.mat")))
    print(f"scanning {len(files)} MAT files (no dedup) ...")
    rows = []
    for i, p in enumerate(files):
        tok = token_of(p)
        exp, cond, off = classify(tok)
        try:
            meta = read_meta(p)
        except Exception as e:
            print(f"  [skip] {os.path.basename(p)}: {e}")
            rows.append(dict(source_file=os.path.basename(p), abspath=p, error=str(e),
                             experiment=exp, condition=cond, requested_offset_deg=off))
            continue
        st = os.stat(p)
        rows.append(dict(
            source_file=os.path.basename(p), abspath=p,
            sha256=sha256(p), size_bytes=st.st_size,
            mtime=dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            experiment=exp, condition=cond, requested_offset_deg=off,
            mesh_N=meta["N"], muscle_cols=meta["ncol"], q_cols=meta["q_cols"],
            return_status=meta["status"],
            strict=(meta["status"] == "Solve_Succeeded"),
            success=meta["success"], iter_count=meta["iter_count"],
            final_inf_pr=meta["inf_pr"], final_inf_du=meta["inf_du"],
            final_obj=meta["obj"],
            td_tilt_deg_signed=round(meta["td_tilt_deg"], 4),
            anterior_tilt_deg=round(meta["anterior_tilt_deg"], 4),
            mean_tilt_deg=round(meta["mean_tilt_deg"], 4),
            speed_mps=round(meta["speed_mps"], 6) if np.isfinite(meta["speed_mps"]) else "",
            totalTime_s=round(meta["totalTime_s"], 6) if np.isfinite(meta["totalTime_s"]) else "",
            t0_s=round(meta["t0"], 5), tE_s=round(meta["tE"], 5),
            warm_start_source="see_logs",
        ))
        if (i + 1) % 25 == 0:
            print(f"  ...{i+1}/{len(files)}")

    # achieved offset vs mesh-matched Nominal + speed_error_pct
    nom_td = {}
    nom_sp = {}
    for r in rows:
        if r.get("experiment") == "Nominal" and "mesh_N" in r:
            nom_td[r["mesh_N"]] = r["td_tilt_deg_signed"]
            nom_sp[r["mesh_N"]] = r.get("speed_mps")
    for r in rows:
        N = r.get("mesh_N")
        if N in nom_td and isinstance(r.get("td_tilt_deg_signed"), float):
            r["achieved_offset_vs_nomN_deg"] = round(r["td_tilt_deg_signed"] - nom_td[N], 4)
        else:
            r["achieved_offset_vs_nomN_deg"] = ""
        ref = nom_sp.get(N)
        try:
            if ref not in ("", None) and float(ref) > 0 and r.get("speed_mps") not in ("", None):
                r["speed_error_pct_vs_nomN"] = round(100.0 * (float(r["speed_mps"]) - float(ref)) / float(ref), 4)
            else:
                r["speed_error_pct_vs_nomN"] = ""
        except Exception:
            r["speed_error_pct_vs_nomN"] = ""

    cols = ["source_file", "abspath", "sha256", "size_bytes", "mtime",
            "experiment", "condition", "requested_offset_deg", "mesh_N",
            "muscle_cols", "q_cols", "return_status", "strict", "success",
            "iter_count", "final_inf_pr", "final_inf_du", "final_obj",
            "td_tilt_deg_signed", "anterior_tilt_deg", "achieved_offset_vs_nomN_deg",
            "mean_tilt_deg", "speed_mps", "speed_error_pct_vs_nomN",
            "totalTime_s", "t0_s", "tE_s", "warm_start_source", "error"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r.get("experiment", ""), r.get("condition", ""),
                                             r.get("mesh_N", 0), r.get("mtime", ""))):
            w.writerow({c: r.get(c, "") for c in cols})
    print(f"\nwrote {OUT}  ({len(rows)} rows)")

    # summary: strict counts + nominal td by N + PelvicTD candidates per (cond,N)
    print("\nNominal touchdown pelvis_tilt (signed deg) by mesh N:")
    for N in sorted(nom_td):
        print(f"  N={N}: td={nom_td[N]:+.4f} deg  speed={nom_sp.get(N)}")
    print("\nPelvicTD candidates (experiment, condition, N): status / inf_pr / td / speed / mtime")
    for r in sorted([r for r in rows if str(r.get("experiment", "")).startswith("PelvicTD")],
                    key=lambda r: (r["condition"], r.get("mesh_N", 0), r.get("mtime", ""))):
        print(f"  {r['condition']:20s} N={r.get('mesh_N'):>3}  {r.get('return_status',''):28s} "
              f"inf_pr={r.get('final_inf_pr')}  td={r.get('td_tilt_deg_signed')}  "
              f"spd={r.get('speed_mps')}  {r.get('mtime','')}  {r['source_file']}")


if __name__ == "__main__":
    main()
