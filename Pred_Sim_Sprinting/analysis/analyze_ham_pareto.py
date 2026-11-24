"""
analyze_ham_pareto.py
=====================
Research Questions 3 & 4 analysis: the PRESCRIPTIVE speed<->safety trade-off.

RQ3 (Pareto frontier)
---------------------
Each `_HamPareto_[Nom|Sh|Wk]_wXXXX` condition re-optimises the SAME maximal
sprint with a smooth biarticular-hamstring fascicle-overstretch penalty of
weight wJ(13)=XXXX/1000 added to the objective. Sweeping the weight traces the
Pareto frontier between top speed and peak fascicle strain (the mechanistically
appropriate stretch-injury surrogate; Kalkhoven 2023, Timmins 2016). We look
for the "free-lunch" region: technique changes that cut peak fascicle strain at
negligible speed cost.

RQ4 (technique vs training, individualised)
-------------------------------------------
For an at-risk athlete (Sh = short fascicle, Wk = weak) we compare two levers in
the SAME speed<->strain plane:
  * TECHNIQUE path  = that athlete's Pareto frontier (this study), i.e. change how
                      you run at fixed architecture.
  * TRAINING path   = the RQ2 architecture dose-response (analyze_ham_architecture),
                      i.e. lengthen fascicles / strengthen at the athlete's own
                      (unpenalised) technique.
Whichever path reaches lower peak strain per unit speed lost is the more
efficient intervention for that athlete.

Reads saved data only (no MATLAB). The optimiser minimises a smooth surrogate;
here we report the TRUE peak normalised fibre length recomputed post-hoc.

Usage:
    python analyze_ham_pareto.py            # frontier tables + CSV (+ figure hook)
"""
import glob
import os
import re
import sys

import numpy as np

from injury_metrics import BIARTIC, HAM, RESULTS, compute_injury_metrics

OUTDIR = os.path.join(RESULTS, "HamPareto_Study")
ATHLETES = ("Nom", "Sh", "Wk")
ATH_LABEL = {"Nom": "nominal", "Sh": "short-fascicle", "Wk": "weak"}
# Unpenalised (weight 0) architecture base per athlete, used as the w=0 anchor
# when an explicit _wXXXX=0000 run is absent, and as the RQ2 training-path start.
BASE_PATTERN = {
    "Nom": "pred_sprinting_data_*Nominal.mat",
    "Sh": "pred_sprinting_data_*HamFascicle_m20.mat",
    "Wk": "pred_sprinting_data_*HamStrength_m20.mat",
}


def parse_cond(cond):
    """'HamPareto_Sh_w0800' -> ('Sh', 0.80). Returns (None, None) if not Pareto."""
    m = re.search(r"HamPareto_(Nom|Sh|Wk)_w(\d+)", cond)
    if not m:
        return None, None
    return m.group(1), int(m.group(2)) / 1000.0


def _biartic(d, key):
    return float(np.mean([d[m + "_" + key] for m in BIARTIC]))


def _row_from_file(f, athlete, weight):
    d = compute_injury_metrics(f)
    return {
        "cond": os.path.splitext(os.path.basename(f))[0].split("___")[-1],
        "athlete": athlete,
        "weight": weight,
        "speed": d["speed"],
        "peak_lMtilde": _biartic(d, "peak_lMtilde"),
        "ecc_work": _biartic(d, "ecc_work"),
        "peak_Fpetilde": _biartic(d, "peak_Fpetilde"),
        "fasc_mtu": _biartic(d, "fasc_mtu_ratio"),
        "N": d.get("N"),
        "_file": f,
    }


def _newest(pattern):
    fs = glob.glob(os.path.join(RESULTS, pattern))
    return max(fs, key=os.path.getmtime) if fs else None


def collect(target_N=50):
    """Newest result per Pareto condition, grouped by athlete and sorted by weight.

    Each athlete's list is anchored at weight 0 by the explicit _w0000 run if it
    exists, else by the unpenalised architecture base (Nominal / RQ2 solution).
    """
    # newest file per (athlete, weight) token
    seen = {}
    for f in glob.glob(os.path.join(RESULTS, "pred_sprinting_data_*HamPareto*.mat")):
        ath, wt = parse_cond(os.path.basename(f))
        if ath is None:
            continue
        key = (ath, wt)
        if key not in seen or os.path.getmtime(f) > os.path.getmtime(seen[key]):
            seen[key] = f

    by_ath = {a: [] for a in ATHLETES}
    for (ath, wt), f in seen.items():
        try:
            r = _row_from_file(f, ath, wt)
        except Exception as e:  # noqa: BLE001
            print(f"[skip] {os.path.basename(f)}: {e}")
            continue
        if target_N is not None and r["N"] not in (target_N, None):
            continue
        by_ath[ath].append(r)

    # Ensure a weight-0 anchor per athlete from the architecture base if missing.
    for ath in ATHLETES:
        if not any(abs(r["weight"]) < 1e-9 for r in by_ath[ath]):
            bf = _newest(BASE_PATTERN[ath])
            if bf is not None:
                try:
                    r = _row_from_file(bf, ath, 0.0)
                    if target_N is None or r["N"] in (target_N, None):
                        r["cond"] += " (base)"
                        by_ath[ath].append(r)
                except Exception as e:  # noqa: BLE001
                    print(f"[base skip] {ath}: {e}")
        by_ath[ath].sort(key=lambda r: r["weight"])
    return by_ath


def print_tables(by_ath):
    for ath in ATHLETES:
        rows = by_ath[ath]
        if not rows:
            continue
        print(f"\n=== RQ3 Pareto frontier: {ATH_LABEL[ath]} athlete "
              f"(biarticular hamstring mean) ===")
        print(f"{'cond':28s} {'wJ13':>6s} {'speed':>6s} {'peakLMtil':>9s} "
              f"{'eccWork':>8s} {'peakFpe':>8s}")
        for r in rows:
            print(f"{r['cond']:28s} {r['weight']:6.3f} {r['speed']:6.3f} "
                  f"{r['peak_lMtilde']:9.3f} {r['ecc_work']:8.2f} {r['peak_Fpetilde']:8.3f}")


def free_lunch(rows):
    """Relative to weight 0: % speed loss and peak-strain reduction per weight.

    Returns list of dicts with dstrain (reduction, +ve is good), dspeed_pct
    (loss, +ve is a cost) and efficiency = dstrain / max(dspeed_pct, eps).
    The 'knee' (max efficiency) is the best strain-per-speed technique change;
    'free-lunch' points cut strain >=2% while losing <0.5% speed.
    """
    if not rows:
        return []
    base = next((r for r in rows if abs(r["weight"]) < 1e-9), rows[0])
    s0, l0 = base["speed"], base["peak_lMtilde"]
    out = []
    for r in rows:
        dspeed_pct = 100.0 * (s0 - r["speed"]) / s0 if s0 else np.nan
        dstrain = l0 - r["peak_lMtilde"]
        dstrain_pct = 100.0 * dstrain / l0 if l0 else np.nan
        eff = dstrain_pct / dspeed_pct if dspeed_pct > 1e-6 else np.inf
        out.append({**r, "dspeed_pct": dspeed_pct, "dstrain": dstrain,
                    "dstrain_pct": dstrain_pct, "efficiency": eff,
                    "free_lunch": (dstrain_pct >= 2.0 and dspeed_pct < 0.5)})
    return out


def print_free_lunch(by_ath):
    for ath in ATHLETES:
        rows = free_lunch(by_ath[ath])
        if len(rows) < 2:
            continue
        print(f"\n=== RQ3/RQ4 speed-safety trade-off: {ATH_LABEL[ath]} athlete "
              f"(vs its own weight-0 technique) ===")
        print(f"{'wJ13':>6s} {'speed':>6s} {'dSpeed%':>8s} {'peakLMtil':>9s} "
              f"{'dStrain%':>8s} {'eff':>6s} {'free-lunch':>10s}")
        for r in rows:
            eff = "inf" if not np.isfinite(r["efficiency"]) else f"{r['efficiency']:.1f}"
            print(f"{r['weight']:6.3f} {r['speed']:6.3f} {r['dspeed_pct']:8.3f} "
                  f"{r['peak_lMtilde']:9.3f} {r['dstrain_pct']:8.2f} {eff:>6s} "
                  f"{('YES' if r['free_lunch'] else ''):>10s}")
        cand = [r for r in rows if r["weight"] > 0 and np.isfinite(r["efficiency"])]
        if cand:
            knee = max(cand, key=lambda r: r["efficiency"])
            print(f"  -> knee (best strain-per-speed): wJ13={knee['weight']:.3f} "
                  f"cuts peak fascicle strain {knee['dstrain_pct']:.1f}% for "
                  f"{knee['dspeed_pct']:.2f}% speed loss.")


def write_csv(by_ath):
    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, "pareto_frontier.csv")
    cols = ["athlete", "weight", "cond", "speed", "peak_lMtilde", "ecc_work",
            "peak_Fpetilde", "fasc_mtu", "dspeed_pct", "dstrain_pct",
            "efficiency", "free_lunch", "N"]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(",".join(cols) + "\n")
        for ath in ATHLETES:
            for r in free_lunch(by_ath[ath]):
                fh.write(",".join(str(r.get(c, "")) for c in cols) + "\n")
    print(f"\nCSV saved: {out}")
    return out


def main():
    by_ath = collect(target_N=50)
    if not any(by_ath[a] for a in ATHLETES):
        print("No Pareto results found under", os.path.abspath(RESULTS))
        print("Run: run_ham_pareto.bat pilot   (then nominal / athletes)")
        return
    print_tables(by_ath)
    print_free_lunch(by_ath)
    write_csv(by_ath)


if __name__ == "__main__":
    main()
