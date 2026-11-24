"""
qa_checks.py -- automated numeric / implementation QA for the figure set (task section 12).
Reads the written source CSVs (not the live objects) so it validates the ACTUAL figure inputs.
Writes qa/qa_results.csv and exits non-zero if any hard check fails.
"""
import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

results = []


def check(name, ok, detail=""):
    results.append([name, "PASS" if ok else "FAIL", detail])
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")


def rd(rel):
    return list(csv.DictReader(open(os.path.join(C.OUTDIR, rel), encoding="utf-8")))


def fnum(x):
    try:
        return float(x)
    except Exception:
        return math.nan


def main():
    # 1. Fig2 source: 32 point rows, 8 unique offsets, all N=100 strict, anterior 1.987-15.987, A=-td sign
    f2 = rd("source_data/Fig2_primary_N100_source.csv")
    pts = [r for r in f2 if r["record_type"] == "point"]
    offs = {r["offset"] for r in pts}
    check("Fig2 has 32 point rows (8 cond x 4 mus)", len(pts) == 32, f"{len(pts)}")
    check("Fig2 has 8 unique conditions", len(offs) == 8, f"{sorted(offs)}")
    check("Fig2 all points strict Solve_Succeeded",
          all(r["solver_status"] == "Solve_Succeeded" for r in pts))
    ant = [float(r["anterior_tilt_deg"]) for r in pts]
    check("Fig2 anterior tilt in [1.987,15.987]", min(ant) >= 1.986 and max(ant) <= 15.988,
          f"[{min(ant)},{max(ant)}]")
    check("Fig2 anterior tilt all positive (A=-pelvis_tilt)", all(a > 0 for a in ant))

    # 2. reconciliation: 0 CHECK verdicts
    rec = rd("01_numeric_reconciliation.csv")
    nbad = sum(1 for r in rec if r["verdict"] == "CHECK")
    check("reconciliation has 0 CHECK verdicts", nbad == 0, f"{nbad} bad of {len(rec)}")

    # 3. Fig3 waveforms: no NaN/Inf, pct in [0,100], lMtilde plausible, full-stride peak >= TS peak
    f3 = rd("source_data/Fig3_lMtilde_waveforms_N100_source.csv")
    vals = [fnum(r["lMtilde"]) for r in f3]
    pcts = [fnum(r["pct_stride"]) for r in f3]
    check("Fig3 no NaN/Inf in lMtilde", all(math.isfinite(v) for v in vals))
    check("Fig3 pct_stride in [0,100]", min(pcts) >= 0 and max(pcts) <= 100)
    check("Fig3 lMtilde in plausible [0.2,1.35]", min(vals) > 0.2 and max(vals) < 1.35,
          f"[{min(vals):.3f},{max(vals):.3f}]")
    # full vs TS peak from live metrics
    conds = C.load_primary_N100()
    ok_peak = True
    for c in conds:
        for nm in C.BIARTIC:
            if c["m"][nm]["peak_lMtilde"] + 1e-9 < c["m"][nm]["TS_peak_lMtilde"]:
                ok_peak = False
    check("full-stride peak >= terminal-swing peak (biartic)", ok_peak)

    # 4. Fig6 all_attempts: 95 rows, 8 adopted, adopted all N=100 strict
    f6 = rd("source_data/Fig6_all_attempts.csv")
    adopted = [r for r in f6 if r["adopted"] == "primary"]
    check("Fig6 discovered 95 MAT", len(f6) == 95, f"{len(f6)}")
    check("Fig6 exactly 8 adopted", len(adopted) == 8, f"{len(adopted)}")
    check("Fig6 adopted all N=100 strict",
          all(r["mesh_N"] == "100" and r["return_status"] == "Solve_Succeeded" for r in adopted))

    # 5. Fig7 pareto: 3 paths at w=0.1, mean dSpeed ~ -0.340, dSurro ~ -5.189
    f7 = rd("source_data/Fig7_pareto_N100_source.csv")
    w1 = [r for r in f7 if abs(fnum(r["weight"]) - 0.1) < 1e-9]
    check("Fig7 w=0.1 has 3 warm-start paths", len(w1) == 3, f"{len(w1)}")
    mds = sum(fnum(r["dSpeed_pct"]) for r in w1) / max(len(w1), 1)
    mdu = sum(fnum(r["dSurro_pct"]) for r in w1) / max(len(w1), 1)
    check("Fig7 mean dSpeed ~ -0.340%", abs(mds + 0.340) < 0.02, f"{mds:.4f}")
    check("Fig7 mean dSurro ~ -5.189%", abs(mdu + 5.189) < 0.08, f"{mdu:.4f}")
    check("Fig7 all strict Solve_Succeeded", all(r["solver_status"] == "Solve_Succeeded" for r in f7))

    # 6. Fig5 peaks match audit ratios (89-96%), tree-rigid ~ 0
    f5 = rd("source_data/Fig5_mtu_peaks_source.csv")
    aud = {r["muscle"]: r for r in csv.DictReader(
        open(os.path.join(C.AUDIT, "boundary_phase_corrected_opensim.csv"), encoding="utf-8"))}
    ok5 = True
    for r in f5:
        if r["is_biarticular"] == "True":
            if abs(fnum(r["C_adaptive_TSpeak_mm"]) - fnum(aud[r["muscle"]]["C_adaptive_peak_phaseNorm_mm"])) > 0.02:
                ok5 = False
        if abs(fnum(r["A_tree_rigid_TSpeak_mm"])) > 1e-6:
            ok5 = False
    check("Fig5 adaptive peaks match audit & tree-rigid ~ 0", ok5)

    # 7. Fig4 metrics: kinematic RMSE present, GRF/EMG marked not available
    f4 = rd("source_data/Fig4_baseline_validation_metrics.csv")
    na = [r for r in f4 if r["signal"] in ("GRF_vertical", "EMG")]
    check("Fig4 marks GRF & EMG error not available", len(na) == 2 and
          all("not available" in r["RMSE_after_offset_removed_deg"] for r in na))

    # 8b. S4 mesh robustness: N=50 wide has all 8 offsets (strict), qualitative direction matches N=100
    s4 = os.path.join(C.OUTDIR, "source_data", "FigS4_slopes_source.csv")
    if os.path.isfile(s4):
        rows_s4 = rd("source_data/FigS4_slopes_source.csv")
        src_s4 = rd("source_data/FigS4_mesh_robustness_source.csv")
        n50 = {r["offset"] for r in src_s4 if r["mesh"] == "N50"}
        check("S4 N=50 wide has 8 conditions", len(n50) == 8, f"{sorted(n50)}")
        biartic_ok = all(float(r["slope_N100"]) > 0 and float(r["slope_N50"]) > 0
                         for r in rows_s4 if r["muscle"] in C.BIARTIC)
        check("S4 biartic slopes positive at both meshes", biartic_ok)

    # 8c. S3 present with >=2 parameter families
    s3 = os.path.join(C.OUTDIR, "source_data", "FigS3_param_sensitivity_source.csv")
    if os.path.isfile(s3):
        rows_s3 = rd("source_data/FigS3_param_sensitivity_source.csv")
        fams = {r["family"] for r in rows_s3}
        check("S3 has >=2 parameter families", len(fams) >= 2, f"{sorted(fams)}")

    # 8. output files exist for the main + suppl figures
    missing = []
    figs = ["Fig1_study_logic", "Fig2_primary_N100", "Fig3_lMtilde_waveforms_N100",
            "Fig4_baseline_validation", "Fig5_pelvis_femur_mechanism", "Fig6_numerical_robustness",
            "Fig7_pareto_N100", "FigS1_force_length", "FigS2_muscle_metric_heatmap"]
    for extra in ("FigS3_param_sensitivity", "FigS4_mesh_robustness"):
        if os.path.isfile(os.path.join(C.OUTDIR, "figures", "png", extra + ".png")):
            figs.append(extra)
    for fig in figs:
        for sub, ext in (("pdf", "pdf"), ("svg", "svg"), ("png", "png")):
            p = os.path.join(C.OUTDIR, "figures", sub, fig + "." + ext)
            if not os.path.isfile(p):
                missing.append(f"{fig}.{ext}")
    check(f"all {len(figs)} figures have PDF+SVG+PNG", not missing, f"missing={missing}")

    # write results
    out = os.path.join(C.QA, "qa_results.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["check", "status", "detail"])
        w.writerows(results)
    nfail = sum(1 for r in results if r[1] == "FAIL")
    print(f"\n{len(results)} checks, {nfail} FAIL -> {out}")
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    print("=== automated QA checks ===")
    main()
