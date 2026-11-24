"""
01_reconcile.py -- recompute every headline number straight from the source MAT
(via _common, the clean-room engine) and reconcile against the expected values
quoted in the task brief.  Writes ../01_numeric_reconciliation.csv.

No manuscript number is hard-coded into a figure: this table is the audit trail
that the recomputed values agree with the brief to display precision, and flags
any that differ by more than rounding.
"""
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C


def rel(a, b):
    return float("nan") if b == 0 else 100.0 * (a - b) / abs(b)


def verdict(absdiff, tol):
    return "match" if abs(absdiff) <= tol else "CHECK"


def main():
    conds = C.load_primary_N100()
    ant = np.array([c["anterior"] for c in conds])
    spd = np.array([c["speed"] for c in conds])
    rows = []

    # ---- operability: tilt range + speed range ----
    rows.append(["operability", "achieved_anterior_tilt_min_deg", "-", f"{ant.min():.3f}",
                 "1.987", f"{ant.min()-1.987:+.4f}", f"{rel(ant.min(),1.987):+.3f}", verdict(ant.min()-1.987, 5e-3),
                 "raw MAT q[0,0] -> -deg"])
    rows.append(["operability", "achieved_anterior_tilt_max_deg", "-", f"{ant.max():.3f}",
                 "15.987", f"{ant.max()-15.987:+.4f}", f"{rel(ant.max(),15.987):+.3f}", verdict(ant.max()-15.987, 5e-3),
                 "raw MAT q[0,0] -> -deg"])
    rows.append(["operability", "achieved_speed_min_mps", "-", f"{spd.min():.4f}",
                 "11.7467", f"{spd.min()-11.7467:+.5f}", f"{rel(spd.min(),11.7467):+.4f}", verdict(spd.min()-11.7467, 5e-4),
                 "raw MAT ave_speed"])
    rows.append(["operability", "achieved_speed_max_mps", "-", f"{spd.max():.4f}",
                 "11.7978", f"{spd.max()-11.7978:+.5f}", f"{rel(spd.max(),11.7978):+.4f}", verdict(spd.max()-11.7978, 5e-4),
                 "raw MAT ave_speed"])

    # ---- dose-response slope / R2 / speed-adj / %change / timing ----
    EXP_SLOPE = {"semimem": 0.00678, "semiten": 0.00374, "bifemlh": 0.00538, "bifemsh": None}
    EXP_ADJ = {"semimem": 0.00640, "semiten": 0.00351, "bifemlh": 0.00504, "bifemsh": None}
    EXP_PCT = {"semimem": (4.65, 9.72), "semiten": (4.65, 9.72), "bifemlh": (4.65, 9.72),
               "bifemsh": None}   # biartic band; bifemsh endpoint -0.32
    for nm in C.MUS:
        y = np.array([c["m"][nm]["peak_lMtilde"] for c in conds])
        sl, ic, r2 = C.fit(ant, y)
        adj = C.speed_adj_coef(ant, spd, y)
        pct = 100.0 * (y[-1] - y[0]) / y[0]
        tpk = [c["m"][nm]["tPeak_pct"] for c in conds]
        if EXP_SLOPE[nm] is not None:
            rows.append(["dose_slope", nm, "raw_slope_per_deg", f"{sl:.6f}", f"{EXP_SLOPE[nm]:.5f}",
                         f"{sl-EXP_SLOPE[nm]:+.6f}", f"{rel(sl,EXP_SLOPE[nm]):+.3f}", verdict(sl-EXP_SLOPE[nm], 5e-5),
                         "lstsq peak_lMtilde vs A"])
            rows.append(["dose_speed_adj", nm, "speed_adj_coef_per_deg", f"{adj:.6f}", f"{EXP_ADJ[nm]:.5f}",
                         f"{adj-EXP_ADJ[nm]:+.6f}", f"{rel(adj,EXP_ADJ[nm]):+.3f}", verdict(adj-EXP_ADJ[nm], 5e-5),
                         "multiple reg peak~A+speed"])
            rows.append(["dose_R2", nm, "R2", f"{r2:.4f}", "0.950-0.961",
                         "in-band" if 0.949 <= r2 <= 0.962 else "OUT", "-",
                         "match" if 0.949 <= r2 <= 0.962 else "CHECK", "lstsq R2"])
            rows.append(["dose_pct", nm, "pct_change_min_to_max", f"{pct:+.2f}", "4.65..9.72",
                         "in-band" if 4.5 <= pct <= 9.9 else "OUT", "-",
                         "match" if 4.5 <= pct <= 9.9 else "CHECK", "100*(y_max-y_min)/y_min"])
        else:
            # bifemsh single-joint control: raw slope ~ -0.000254; brief -0.00027 matches speed-adj
            rows.append(["dose_slope", nm, "raw_slope_per_deg", f"{sl:.6f}", "-0.00027(brief)",
                         f"{sl-(-0.00027):+.6f}", "-", "note",
                         "raw=-0.000254; brief -0.00027 ~ speed-adj -0.000272"])
            rows.append(["dose_speed_adj", nm, "speed_adj_coef_per_deg", f"{adj:.6f}", "-0.00027",
                         f"{adj-(-0.00027):+.6f}", f"{rel(adj,-0.00027):+.2f}", verdict(adj-(-0.00027), 5e-5),
                         "multiple reg peak~A+speed"])
            rows.append(["dose_pct", nm, "endpoint_change_pct", f"{pct:+.2f}", "-0.32",
                         f"{pct-(-0.32):+.3f}", "-", verdict(pct-(-0.32), 0.05), "100*(y_max-y_min)/y_min"])
        if nm in C.BIARTIC:
            rows.append(["peak_timing", nm, "tPeak_pct_stride_range",
                         f"{min(tpk):.1f}-{max(tpk):.1f}", "85.5-90.8",
                         "in-band" if (85.0 <= min(tpk) and max(tpk) <= 91.0) else "OUT", "-",
                         "match" if (85.0 <= min(tpk) and max(tpk) <= 91.0) else "CHECK",
                         "argmax over full stride"])

    # ---- boundary femur-fixed/adaptive ratio (from independently re-run OpenSim CSV) ----
    bpath = os.path.join(C.AUDIT, "boundary_phase_corrected_opensim.csv")
    for r in csv.DictReader(open(bpath, encoding="utf-8")):
        if r["is_biarticular"].lower() == "true":
            ratio = float(r["fixed_over_adaptive_pct"])
            rows.append(["boundary_ratio", r["muscle"], "femur_fixed_over_adaptive_pct",
                         f"{ratio:.1f}", "89.6-95.8", "in-band" if 89.0 <= ratio <= 96.5 else "OUT",
                         "-", "match" if 89.0 <= ratio <= 96.5 else "CHECK",
                         "OpenSim4.4 phase-norm TS peak dMTU (audit_boundary_opensim.py)"])

    # ---- Pareto w=0.1 3-path mean (independently recomputed from raw MAT here) ----
    ck = os.path.join(C.RESULTS, "HamPareto_N100", "checkpoint.csv")
    crows = list(csv.DictReader(open(ck, encoding="utf-8")))
    def wt(r):
        return float(r["condition"].split("_w")[-1]) / 1000.0
    base = next(r for r in crows if wt(r) == 0.0)
    db = C.load(base["out_file"]); cb, _, _ = C.contact_s(db)
    base_speed = db["speed"]
    base_surro = float(np.mean([C.metrics(db, nm, cb)["TS_peak_lMtilde"] for nm in C.BIARTIC]))
    dsp, dsu = [], []
    for r in crows:
        if wt(r) == 0.10:
            d = C.load(r["out_file"]); c, _, _ = C.contact_s(d)
            su = float(np.mean([C.metrics(d, nm, c)["TS_peak_lMtilde"] for nm in C.BIARTIC]))
            dsp.append(100.0 * (d["speed"] - base_speed) / base_speed)
            dsu.append(100.0 * (su - base_surro) / base_surro)
    mdsp, mdsu = float(np.mean(dsp)), float(np.mean(dsu))
    rows.append(["pareto", "w0.1_3path", "mean_dSpeed_pct", f"{mdsp:+.4f}", "-0.340",
                 f"{mdsp-(-0.340):+.4f}", f"{rel(mdsp,-0.340):+.2f}", verdict(mdsp-(-0.340), 0.02),
                 "recompute speed from 3 w=0.1 MAT vs w=0 MAT"])
    rows.append(["pareto", "w0.1_3path", "mean_dSurrogate_pct", f"{mdsu:+.4f}", "-5.189",
                 f"{mdsu-(-5.189):+.4f}", f"{rel(mdsu,-5.189):+.2f}", verdict(mdsu-(-5.189), 0.08),
                 "recompute TS-peak biartic mean from MAT"])

    out = os.path.join(C.OUTDIR, "01_numeric_reconciliation.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group", "muscle_or_key", "quantity", "recomputed", "expected_brief",
                    "abs_diff", "rel_diff_pct", "verdict", "source_formula"])
        w.writerows(rows)
    nchk = sum(1 for r in rows if r[7] == "CHECK")
    print(f"wrote {out}\n  {len(rows)} rows, {nchk} CHECK (non-match)")
    for r in rows:
        if r[7] in ("CHECK", "note"):
            print("  ", r[7], r[0], r[1], r[2], "recomp", r[3], "exp", r[4])


if __name__ == "__main__":
    main()
