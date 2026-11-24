"""
objective_evaluation.py  --  Step 8: evaluate the load objective per-surrogate and across
aggregation schemes, so conclusions are shown to (not) depend on the objective construction.

Part 1 - individual surrogates: dose-response (slope vs achieved touchdown tilt, R^2, direction)
  for each candidate load objective on the strict TDPT N=100 set:
    (1) normalized fiber length lMtilde        (2) fiber lengthening velocity
    (3) active force during lengthening         (4) passive force
    (5) negative fiber work                     (each biarticular mean)
  A composite requires explicit per-term scales/weights (documented, not silently combined).

Part 2 - aggregation across muscles for the primary surrogate (peak lMtilde):
    muscle_mean, max_across_muscles, threshold_exceedance_integral (sum max(lMtilde-1,0)),
    phase_specific_max (terminal swing), smooth_max (log-sum-exp).
  Reports the dose-response slope per scheme and the Spearman rank agreement between schemes
  (does the condition ranking survive the aggregation choice?).

Outputs (Results/Validation_Master/):
  objective_surrogates.csv, objective_aggregation.csv, fig_o1_objective.png

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" \
       analysis/validation/objective_evaluation.py
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


def select(rows, mesh_N=100):
    cand = {}
    for r in rows:
        if r["experiment"] != "PelvicTD" or r["strict"] != "True" or int(r["mesh_N"]) != mesh_N:
            continue
        off = float(r["requested_pelvis_offset_deg"])
        resid = float(r["constraint_residual"]) if r["constraint_residual"] not in ("", "nan") else 1e9
        if off not in cand or resid < cand[off][0]:
            cand[off] = (resid, r)
    return [cand[o][1] for o in sorted(cand)]


def fit(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    A = np.vstack([x, np.ones_like(x)]).T
    s, b = np.linalg.lstsq(A, y, rcond=None)[0]
    yh = s * x + b
    r2 = 1 - np.sum((y - yh) ** 2) / (np.sum((y - y.mean()) ** 2) + 1e-12)
    return s, r2


def spearman(a, b):
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def main():
    rows = read_manifest()
    sel = select(rows, 100)
    data = []
    for r in sel:
        m = H.condition_metrics(os.path.join(H.RESULTS, r["source_file"]))
        data.append((float(r["achieved_td_tilt_deg"]), m))
    data.sort(key=lambda t: t[0])
    tilt = [t for t, _ in data]

    # ---- Part 1: individual surrogates (biarticular mean) ----
    surro = {
        "1_norm_fiber_length_lMtilde": lambda m: np.mean([m[f"{n}_peak_lMtilde"] for n in BIARTIC]),
        "2_fiber_lengthening_vel_mps": lambda m: np.mean([m[f"{n}_peak_leng_vel_mps"] for n in BIARTIC]),
        "3_active_force_N": lambda m: np.mean([m[f"{n}_peak_active_force_N"] for n in BIARTIC]),
        "4_passive_force_N": lambda m: np.mean([m[f"{n}_peak_passive_force_N"] for n in BIARTIC]),
        "5_negative_work_J": lambda m: np.mean([m[f"{n}_neg_fiber_work_J"] for n in BIARTIC]),
    }
    print("--- Part 1: individual load surrogates vs achieved touchdown tilt (N=100) ---")
    print(f"{'surrogate':32s}{'slope/deg':>11s}{'R2':>7s}{'dir(ant->)':>12s}")
    p1 = []
    for name, fn in surro.items():
        y = [fn(m) for _, m in data]
        s, r2 = fit(tilt, y)
        # tilt more negative = anterior; anterior effect sign = -slope
        direction = "increase" if s < 0 else ("decrease" if s > 0 else "flat")
        print(f"{name:32s}{s:>11.4f}{r2:>7.2f}{direction:>12s}")
        p1.append({"surrogate": name, "slope_per_deg": round(s, 5), "R2": round(r2, 3),
                   "anterior_effect": direction,
                   **{f"tilt{td:+.0f}": round(v, 4) for td, v in zip(tilt, y)}})
    with open(os.path.join(OUTDIR, "objective_surrogates.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(p1[0].keys()))
        w.writeheader()
        w.writerows(p1)
    print("wrote objective_surrogates.csv")

    # ---- Part 2: aggregation schemes for peak lMtilde ----
    def per_muscle(m, key):
        return np.array([m[f"{n}_{key}"] for n in BIARTIC])

    beta = 20.0   # smooth-max sharpness (documented)
    schemes = {
        "muscle_mean": lambda m: per_muscle(m, "peak_lMtilde").mean(),
        "max_across_muscles": lambda m: per_muscle(m, "peak_lMtilde").max(),
        "threshold_exceedance": lambda m: np.clip(per_muscle(m, "peak_lMtilde") - 1.0, 0, None).sum(),
        "phase_specific_max": lambda m: per_muscle(m, "TS_peak_lMtilde").max(),
        "smooth_max_lse": lambda m: (1.0 / beta) * np.log(np.exp(beta * per_muscle(m, "peak_lMtilde")).sum()),
    }
    print("\n--- Part 2: aggregation schemes for peak lMtilde (dose-response slope) ---")
    agg_vals = {}
    p2 = []
    for name, fn in schemes.items():
        y = [fn(m) for _, m in data]
        agg_vals[name] = y
        s, r2 = fit(tilt, y)
        print(f"  {name:24s} slope={s:+.4f}/deg  R2={r2:.2f}  "
              f"range[{min(y):.3f},{max(y):.3f}]")
        p2.append({"scheme": name, "slope_per_deg": round(s, 5), "R2": round(r2, 3),
                   **{f"tilt{td:+.0f}": round(v, 4) for td, v in zip(tilt, y)}})
    with open(os.path.join(OUTDIR, "objective_aggregation.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(p2[0].keys()))
        w.writeheader()
        w.writerows(p2)
    print("wrote objective_aggregation.csv")

    print("\n--- rank robustness: Spearman rho between aggregation schemes ---")
    names = list(schemes)
    mn = 1.0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            rho = spearman(agg_vals[names[i]], agg_vals[names[j]])
            mn = min(mn, rho)
    print(f"  minimum pairwise Spearman rho = {mn:.3f}  "
          f"({'ranking robust to aggregation' if mn > 0.9 else 'aggregation-sensitive ranking'})")

    # figure
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    for name, fn in surro.items():
        y = np.array([fn(m) for _, m in data])
        yn = (y - y.min()) / (y.max() - y.min() + 1e-12)
        ax.plot(tilt, yn, "-o", ms=4, label=name.split("_", 1)[1])
    ax.set_title("Part 1: individual surrogates (min-max normalized)\nall increase with anterior tilt")
    ax.set_xlabel("achieved touchdown pelvic tilt (deg)")
    ax.set_ylabel("normalized surrogate")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    ax = axes[1]
    for name in schemes:
        y = np.array(agg_vals[name])
        yn = (y - y.min()) / (y.max() - y.min() + 1e-12)
        ax.plot(tilt, yn, "-o", ms=4, label=name)
    ax.set_title(f"Part 2: aggregation schemes (min-max)\nmin Spearman rho={mn:.2f}")
    ax.set_xlabel("achieved touchdown pelvic tilt (deg)")
    ax.set_ylabel("normalized aggregate")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    fig.suptitle("Step 8 objective-function evaluation (strict TDPT N=100)", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "fig_o1_objective.png"), dpi=140)
    plt.close(fig)
    print("wrote fig_o1_objective.png")


if __name__ == "__main__":
    main()
