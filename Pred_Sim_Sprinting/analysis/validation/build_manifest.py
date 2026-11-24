"""
build_manifest.py -- provenance + convergence manifest for every saved result used by
the validation analyses.  One row per (experiment, condition, mesh_N), newest file kept.

Columns (audit-required):
  commit, source_file, source_sha256, experiment, condition, morphology, objective,
  mesh_N, solver_status, feasible, requested_pelvis_offset_deg, achieved_pelvis_angle_deg,
  achieved_td_tilt_deg, achieved_speed_mps, speed_error_pct, constraint_residual,
  time_grid_type, iter_count, analysis_script, analysis_version, generated_at

speed_error_pct is relative to the mesh-matched Nominal (the performance reference).
Strict (Solve_Succeeded) / acceptable (Solved_To_Acceptable_Level) / other are NOT mixed:
the column solver_status carries the exact IPOPT status and `strict` is a boolean helper.

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" \
       analysis/validation/build_manifest.py
"""
from __future__ import annotations

import csv
import datetime as _dt
import glob
import os
import re
import subprocess

import numpy as np
from scipy.io import loadmat

import ham_load_metrics as H

OUTDIR = os.path.join(H.RESULTS, "Validation_Master")
ANALYSIS_SCRIPT = "build_manifest.py"


def git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=H.RESULTS,
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def classify(token):
    """(experiment, condition, morphology, objective, requested_offset_deg) from token."""
    t = token
    off = np.nan
    mo = re.search(r"_([mp])(\d+)", t)
    if mo:
        off = (-1 if mo.group(1) == "m" else 1) * float(mo.group(2))
    morph, obj = "standard", "max_performance"
    if t == "Nominal":
        return "Nominal", "nominal", "standard", "max_performance", 0.0
    if t.startswith("PelvisTDwide"):
        return "PelvicTD", token, "standard", "max_performance", off
    if t.startswith("PelvisTD"):
        return "PelvicTD", token, "standard", "max_performance", off
    if t.startswith("PelvisShift"):
        morph = "fascicle_x0.80" if "athSh" in t else "standard"
        return "PelvicShift", token, morph, "max_performance", off
    if t.startswith("PelvisTilt"):
        return "PelvicTilt", token, "standard", "max_performance", off
    if t.startswith("HamFascicle"):
        return "Morphology_fascicle", token, "fascicle_scaled", "max_performance", off
    if t.startswith("HamStrength"):
        return "Morphology_strength", token, "strength_scaled", "max_performance", off
    if t.startswith("HamArch"):
        return "Morphology_architecture", token, "architecture", "max_performance", off
    if t.startswith("HamPareto"):
        m = re.search(r"HamPareto_(Nom|Sh|Wk)_w(\d+)", t)
        if m:
            morph = {"Nom": "standard", "Sh": "fascicle_x0.80", "Wk": "strength_x0.80"}[m.group(1)]
            w = int(m.group(2)) / 1000.0
            return "HamPareto", token, morph, f"load_penalty_w={w:g}", np.nan
        return "HamPareto", token, "standard", "load_penalty", np.nan
    if re.match(r"(IKTD|HTD)_", t):
        return "Haralabidis_TD", token, "standard", "max_performance", off
    return "other", token, morph, obj, off


def token_of(path):
    m = re.search(r"___(.+)\.mat$", os.path.basename(path))
    return m.group(1) if m else os.path.basename(path)


def _get(o, *n):
    for k in n:
        o = getattr(o, k) if hasattr(o, k) else o[k]
    return o


def read_meta(path):
    m = loadmat(path, struct_as_record=False, squeeze_me=True, variable_names=["optimumOutput"])
    o = m["optimumOutput"]
    mv = _get(o, "muscleValues")
    ncol = np.asarray(_get(mv, "lMtilde"), float).shape[1]
    N = int(np.asarray(_get(o, "options", "N")).ravel()[0])
    status, success, itc = "unknown", False, -1
    resid = np.nan
    try:
        st = _get(o, "stats")
        status = str(_get(st, "return_status"))
        success = bool(int(np.asarray(_get(st, "success")).ravel()[0]))
        itc = int(np.asarray(_get(st, "iter_count")).ravel()[0])
        try:  # final primal infeasibility if IPOPT iteration log was saved
            it = _get(st, "iterations")
            resid = float(np.asarray(_get(it, "inf_pr"), float).ravel()[-1])
        except Exception:
            resid = np.nan
    except Exception:
        pass
    q = np.asarray(_get(o, "optVars_nsc", "q"), float)
    td = float(np.degrees(q[0, 0]))
    mean_t = float(np.degrees(q[0].mean()))
    try:
        spd = float(np.asarray(_get(o, "ave_speed")).ravel()[0])
    except Exception:
        spd = np.nan
    return dict(N=N, ncol=ncol, status=status, success=success, iter_count=itc,
                constraint_residual=resid, td_tilt=td, mean_tilt=mean_t, speed=spd)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    commit = git_commit()
    gen = _dt.datetime.now().isoformat(timespec="seconds")
    files = glob.glob(os.path.join(H.RESULTS, "pred_sprinting_data_*.mat"))
    print(f"scanning {len(files)} result files ...")

    rows = {}
    for i, p in enumerate(sorted(files)):
        tok = token_of(p)
        try:
            meta = read_meta(p)
        except Exception as e:
            print(f"  [skip] {os.path.basename(p)}: {e}")
            continue
        exp, cond, morph, obj, off = classify(tok)
        key = (exp, cond, meta["N"])
        if key in rows and os.path.getmtime(p) <= rows[key]["_mtime"]:
            continue
        rows[key] = dict(
            commit=commit, source_file=os.path.basename(p), source_sha256=H.sha256(p),
            experiment=exp, condition=cond, morphology=morph, objective=obj,
            mesh_N=meta["N"], solver_status=meta["status"],
            strict=(meta["status"] == "Solve_Succeeded"),
            feasible=meta["success"], requested_pelvis_offset_deg=off,
            achieved_pelvis_angle_deg=round(meta["mean_tilt"], 4),
            achieved_td_tilt_deg=round(meta["td_tilt"], 4),
            achieved_speed_mps=round(meta["speed"], 5),
            constraint_residual=meta["constraint_residual"],
            time_grid_type="radau_timeNodes_nonuniform", iter_count=meta["iter_count"],
            analysis_script=ANALYSIS_SCRIPT, analysis_version=H.__version__,
            generated_at=gen, _mtime=os.path.getmtime(p))
        if (i + 1) % 25 == 0:
            print(f"  ...{i + 1}/{len(files)}")

    # speed_error_pct vs mesh-matched Nominal
    nom = {k[2]: v["achieved_speed_mps"] for k, v in rows.items() if v["experiment"] == "Nominal"}
    for v in rows.values():
        ref = nom.get(v["mesh_N"], next(iter(nom.values()), np.nan))
        v["speed_error_pct"] = round(100.0 * (v["achieved_speed_mps"] - ref) / ref, 3) \
            if ref and np.isfinite(ref) else np.nan
        v.pop("_mtime", None)

    cols = ["commit", "source_file", "source_sha256", "experiment", "condition",
            "morphology", "objective", "mesh_N", "solver_status", "strict", "feasible",
            "requested_pelvis_offset_deg", "achieved_pelvis_angle_deg",
            "achieved_td_tilt_deg", "achieved_speed_mps", "speed_error_pct",
            "constraint_residual", "time_grid_type", "iter_count", "analysis_script",
            "analysis_version", "generated_at"]
    ordered = sorted(rows.values(), key=lambda r: (r["experiment"], r["condition"], r["mesh_N"]))
    out = os.path.join(OUTDIR, "manifest.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in ordered:
            w.writerow({c: r.get(c, "") for c in cols})

    n_strict = sum(1 for r in ordered if r["strict"])
    print(f"\nwrote {out}")
    print(f"  {len(ordered)} rows;  strict(Solve_Succeeded)={n_strict};  "
          f"acceptable={sum(1 for r in ordered if r['solver_status']=='Solved_To_Acceptable_Level')};  "
          f"other={sum(1 for r in ordered if not r['strict'] and r['solver_status']!='Solved_To_Acceptable_Level')}")
    by_exp = {}
    for r in ordered:
        by_exp.setdefault(r["experiment"], []).append(r)
    for e, rs in sorted(by_exp.items()):
        print(f"  {e:26s} {len(rs):3d} rows  (N={sorted(set(r['mesh_N'] for r in rs))}, "
              f"strict={sum(1 for r in rs if r['strict'])})")


if __name__ == "__main__":
    main()
