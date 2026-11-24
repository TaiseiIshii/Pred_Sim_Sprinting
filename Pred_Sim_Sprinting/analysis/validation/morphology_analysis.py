"""
morphology_analysis.py  --  Step 10: hamstring morphology dependence of the load surrogates,
with the corrected engine, plus an explicit completed/incomplete factorial-coverage map.

Datasets (all strict unless noted), from manifest.csv:
  * fascicle-length sweep  HamFascicle_{m30..p20}  at NOMINAL pelvis   (main effect of lMo)
  * strength sweep         HamStrength_{m30..p20}   at NOMINAL pelvis   (main effect of Fmax)
  * HamPareto athletes     Nom / Sh(fascicle x0.80) / Wk(strength x0.80) x penalty weights
                           (morphology x objective; posture co-varies -> confound flagged)

Explicitly reports that the morphology x PELVIS factorial is INCOMPLETE (only standard
morphology has a strict touchdown-tilt sweep); missing cells need new solves (BLOCKED).

Outputs (Results/Validation_Master/):
  morphology_fascicle.csv, morphology_strength.csv, morphology_coverage.csv,
  fig_m1_morphology.png

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" \
       analysis/validation/morphology_analysis.py
"""
from __future__ import annotations

import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import ham_load_metrics as H

OUTDIR = os.path.join(H.RESULTS, "Validation_Master")
MANIFEST = os.path.join(OUTDIR, "manifest.csv")
BIARTIC = ["semimem", "semiten", "bifemlh"]


def read_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def biartic(m, key):
    return float(np.mean([m[f"{n}_{key}"] for n in BIARTIC]))


def fit(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    A = np.vstack([x, np.ones_like(x)]).T
    s, b = np.linalg.lstsq(A, y, rcond=None)[0]
    yh = s * x + b
    r2 = 1 - np.sum((y - yh) ** 2) / (np.sum((y - y.mean()) ** 2) + 1e-12)
    return s, r2


def sweep(rows, experiment):
    out = []
    for r in rows:
        if r["experiment"] != experiment or r["strict"] != "True":
            continue
        m = H.condition_metrics(os.path.join(H.RESULTS, r["source_file"]))
        out.append({"condition": r["condition"],
                    "scale_pct": float(r["requested_pelvis_offset_deg"]),
                    "mean_tilt_deg": float(r["achieved_pelvis_angle_deg"]),
                    "speed_mps": m["speed_mps"],
                    "peak_lMtilde": biartic(m, "peak_lMtilde"),
                    "lMo_m": biartic(m, "lMo_m"),
                    "peak_passive_N": biartic(m, "peak_passive_force_N"),
                    "neg_work_J": biartic(m, "neg_fiber_work_J")})
    out.sort(key=lambda d: d["scale_pct"])
    return out


def write(rowsout, name):
    with open(os.path.join(OUTDIR, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rowsout[0].keys()))
        w.writeheader()
        w.writerows(rowsout)
    print("wrote", name)


def main():
    rows = read_manifest()
    fasc = sweep(rows, "Morphology_fascicle")
    stre = sweep(rows, "Morphology_strength")
    write(fasc, "morphology_fascicle.csv")
    write(stre, "morphology_strength.csv")

    print("\n--- fascicle-length sweep (nominal pelvis): biarticular peak lMtilde ---")
    sx = [d["scale_pct"] for d in fasc]
    for d in fasc:
        print(f"  fascicle {d['scale_pct']:+5.0f}%  lMo={d['lMo_m']*100:.2f}cm  "
              f"speed {d['speed_mps']:.3f}  peakLMt {d['peak_lMtilde']:.3f}  "
              f"negW {d['neg_work_J']:.2f}J")
    s, r2 = fit(sx, [d["peak_lMtilde"] for d in fasc])
    print(f"  slope peak lMtilde vs fascicle-scale = {s:+.4f}/% (R2 {r2:.2f}); "
          f"shorter fascicle -> {'higher' if s < 0 else 'lower'} normalized stretch")

    print("\n--- strength sweep (nominal pelvis): biarticular peak lMtilde ---")
    tx = [d["scale_pct"] for d in stre]
    for d in stre:
        print(f"  strength {d['scale_pct']:+5.0f}%  speed {d['speed_mps']:.3f}  "
              f"peakLMt {d['peak_lMtilde']:.3f}  activeWorkNegW {d['neg_work_J']:.2f}J")
    s2, r22 = fit(tx, [d["peak_lMtilde"] for d in stre])
    print(f"  slope peak lMtilde vs strength-scale = {s2:+.4f}/% (R2 {r22:.2f})")

    # HamPareto morphology x objective: frontier steepness per athlete (dLoad/dSpeed)
    print("\n--- morphology x objective (HamPareto): load-reduction per speed-cost ---")
    athletes = {"standard": "Nom", "fascicle_x0.80": "Sh", "strength_x0.80": "Wk"}
    inter = []
    for morph, lab in athletes.items():
        pts = []
        for r in rows:
            if r["experiment"] == "HamPareto" and r["morphology"] == morph and r["strict"] == "True":
                m = H.condition_metrics(os.path.join(H.RESULTS, r["source_file"]))
                pts.append((m["speed_mps"], biartic(m, "TS_peak_lMtilde"),
                            float(r["achieved_pelvis_angle_deg"])))
        pts.sort()
        if len(pts) >= 2:
            spd = [p[0] for p in pts]
            load = [p[1] for p in pts]
            tiltspan = max(p[2] for p in pts) - min(p[2] for p in pts)
            slope, _ = fit(spd, load)   # d(load)/d(speed): steeper = costlier safety
            print(f"  {lab:3s} ({morph:15s}) n={len(pts)}  d(TSpeakLMt)/d(speed)={slope:+.4f}/(m/s)  "
                  f"tilt co-shift span={tiltspan:.1f} deg  speed range[{min(spd):.2f},{max(spd):.2f}]")
            inter.append({"athlete": lab, "morphology": morph, "n_points": len(pts),
                          "dLoad_dSpeed": round(slope, 4),
                          "tilt_coshift_span_deg": round(tiltspan, 2),
                          "speed_min": round(min(spd), 3), "speed_max": round(max(spd), 3)})

    # coverage matrix
    cov = [
        ["standard", "touchdown-tilt sweep (8 pts)", "COMPLETE (strict, N50+N100)"],
        ["standard", "fascicle sweep", f"COMPLETE ({len(fasc)} strict, nominal pelvis)"],
        ["standard", "strength sweep", f"COMPLETE ({len(stre)} strict, nominal pelvis)"],
        ["fascicle_x0.80 (short)", "penalty-weight sweep", "PARTIAL (3 pts; posture co-shifts)"],
        ["fascicle_x0.80 (short)", "controlled touchdown-tilt sweep", "MISSING -> new solves (BLOCKED)"],
        ["strength_x0.80 (weak)", "penalty-weight sweep", "PARTIAL (3 pts; posture co-shifts)"],
        ["strength_x0.80 (weak)", "controlled touchdown-tilt sweep", "MISSING -> new solves (BLOCKED)"],
    ]
    with open(os.path.join(OUTDIR, "morphology_coverage.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["morphology", "cell", "status"])
        w.writerows(cov)
    print("\n--- morphology x pelvis factorial coverage ---")
    for c in cov:
        print(f"  {c[0]:24s} | {c[1]:32s} | {c[2]}")
    print("wrote morphology_coverage.csv")

    # figure
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    ax = axes[0]
    ax.plot(sx, [d["peak_lMtilde"] for d in fasc], "-o", color="#e08214")
    ax.set_title(f"fascicle-length main effect\n(nominal pelvis; slope {s:+.4f}/%, R2 {r2:.2f})")
    ax.set_xlabel("fascicle-length scale (%)")
    ax.set_ylabel("biarticular peak lMtilde")
    ax.grid(alpha=0.3)
    ax = axes[1]
    ax.plot(tx, [d["peak_lMtilde"] for d in stre], "-s", color="#8073ac")
    ax.set_title(f"strength main effect\n(nominal pelvis; slope {s2:+.4f}/%, R2 {r22:.2f})")
    ax.set_xlabel("max-isometric-force scale (%)")
    ax.set_ylabel("biarticular peak lMtilde")
    ax.grid(alpha=0.3)
    ax = axes[2]
    for morph, lab, col in (("standard", "Nom", "#999"),
                            ("fascicle_x0.80", "Sh(short)", "#e08214"),
                            ("strength_x0.80", "Wk(weak)", "#8073ac")):
        pts = []
        for r in rows:
            if r["experiment"] == "HamPareto" and r["morphology"] == morph and r["strict"] == "True":
                m = H.condition_metrics(os.path.join(H.RESULTS, r["source_file"]))
                pts.append((m["speed_mps"], biartic(m, "TS_peak_lMtilde")))
        pts.sort()
        if pts:
            ax.plot([p[0] for p in pts], [p[1] for p in pts], "-o", color=col, label=lab, ms=5)
    ax.set_title("morphology x objective (HamPareto)\nposture co-shifts -> confounded")
    ax.set_xlabel("speed (m/s)")
    ax.set_ylabel("biarticular TS peak lMtilde")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.suptitle("Step 10 morphology dependence (hypothetical phenotypes; corrected metrics)",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "fig_m1_morphology.png"), dpi=140)
    plt.close(fig)
    print("wrote fig_m1_morphology.png")


if __name__ == "__main__":
    main()
