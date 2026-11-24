"""
phaseA_muscle_tension.py -- Phase A: freeze the strict 8-condition touchdown-pelvic-tilt (TDPT)
per-muscle tension/length/work results for the paper, at BOTH meshes (N=50, N=100).

Builds on the already-computed wide tables eight_condition_metrics_N50.csv / _N100.csv (engine
ham_load_metrics.py v1.0.0) and produces the paper-ready long-format table, dose-response fits,
mesh-sensitivity, and per-muscle-per-metric verdicts, plus Figures A1-A4.

Muscles: semimem, semiten, bifemlh (biarticular) + bifemsh (mono-articular control).
Metrics separated: active / passive / tendon force, active & total negative work, fiber length,
lengthening velocity, terminal-swing (TS) & early-stance (ES) values, peak timing.

Outputs (Results/Validation_Master/, versioned; nothing overwritten):
  phaseA_long.csv           -- long format: mesh x offset x muscle x metric x value (+ context)
  phaseA_doseresponse.csv   -- per (mesh, muscle, metric): slope/deg, R2, spearman rho, direction, span
  phaseA_mesh_sensitivity.csv-- per (muscle, metric): mean/max abs rel diff N50-vs-N100, sign match
  phaseA_verdicts.csv       -- per (muscle, metric): 6-category verdict + magnitude_mesh_conditional
  fig_A1_force_doseresponse.png  fig_A2_TS_vs_ES.png  fig_A3_length_tension_work.png
  fig_A4_mesh_sensitivity.png

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" analysis/validation/phaseA_muscle_tension.py
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
MUS = ["semimem", "semiten", "bifemlh", "bifemsh"]
BIARTIC = ["semimem", "semiten", "bifemlh"]
COLORS = {"semimem": "#1b7837", "semiten": "#762a83", "bifemlh": "#2166ac", "bifemsh": "#b2182b"}

# (metric column suffix, unit, human label, phase)
FULL = [
    ("peak_lMtilde", "-", "peak normalized fiber length", "full-stride"),
    ("peak_active_force_N", "N", "peak active fiber force", "full-stride"),
    ("peak_passive_force_N", "N", "peak passive fiber force", "full-stride"),
    ("peak_tendon_force_N", "N", "peak tendon force", "full-stride"),
    ("peak_act_ecc_power_W", "W", "peak active eccentric power", "full-stride"),
    ("neg_fiber_work_J", "J", "negative active fiber work", "full-stride"),
    ("neg_fiber_work_tot_J", "J", "negative total fiber work", "full-stride"),
    ("peak_leng_vel_mps", "m/s", "peak fiber lengthening velocity", "full-stride"),
    ("tPeak_lMtilde_pct", "%stride", "timing of peak fiber length", "full-stride"),
    ("tPeak_Fce_pct", "%stride", "timing of peak active force", "full-stride"),
]
TS = [
    ("TS_peak_lMtilde", "-", "TS peak normalized fiber length", "terminal-swing"),
    ("TS_peak_passive_force_N", "N", "TS peak passive fiber force", "terminal-swing"),
    ("TS_peak_tendon_force_N", "N", "TS peak tendon force", "terminal-swing"),
    ("TS_peak_leng_vel_mps", "m/s", "TS peak fiber lengthening velocity", "terminal-swing"),
    ("TS_neg_fiber_work_J", "J", "TS negative active fiber work", "terminal-swing"),
]
ES = [
    ("ES_peak_lMtilde", "-", "ES peak normalized fiber length", "early-stance"),
    ("ES_peak_active_force_N", "N", "ES peak active fiber force", "early-stance"),
    ("ES_peak_tendon_force_N", "N", "ES peak tendon force", "early-stance"),
    ("ES_neg_fiber_work_J", "J", "ES negative active fiber work", "early-stance"),
]
ALL_METRICS = FULL + TS + ES

# verdict thresholds (documented, adjustable)
ROBUST_RHO = 0.90    # |Spearman| for a robust monotonic dose-response (primary mesh N=100)
CONSIST_RHO = 0.70   # min |Spearman| on N=50 to call the direction reproducible
INVAR_SPAN = 3.0     # % relative span (N=100) below which -> approximately invariant
MESH_HI = 10.0       # % mean-abs-rel-diff N50-vs-N100 -> magnitude is mesh-conditional


def read(mesh):
    p = os.path.join(OUTDIR, f"eight_condition_metrics_{mesh}.csv")
    rows = [r for r in csv.DictReader(open(p, encoding="utf-8")) if r.get("source_file")]
    for r in rows:
        r["_tilt"] = float(r["achieved_td_tilt_deg"])
        r["_off"] = float(r["requested_offset_deg"])
    rows.sort(key=lambda r: r["_tilt"])
    return rows


def fit(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    s, b = np.polyfit(x, y, 1)
    yh = s * x + b
    r2 = 1 - np.sum((y - yh) ** 2) / (np.sum((y - y.mean()) ** 2) + 1e-15)
    return float(s), float(r2)


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def col(muscle, metric):
    return f"{muscle}_{metric}"


def main():
    d = {"N50": read("N50"), "N100": read("N100")}
    speeds = {m: [float(r["speed_mps"]) for r in d[m]] for m in d}
    print(f"N50 speed {min(speeds['N50']):.3f}-{max(speeds['N50']):.3f}  "
          f"N100 speed {min(speeds['N100']):.3f}-{max(speeds['N100']):.3f} m/s")

    # ---- 1. long format ----
    long_rows = []
    for mesh, rows in d.items():
        for r in rows:
            for metric, unit, label, phase in ALL_METRICS:
                for mu in MUS:
                    c = col(mu, metric)
                    if c not in r or r[c] == "":
                        continue
                    long_rows.append({
                        "mesh_N": mesh[1:], "requested_offset_deg": r["_off"],
                        "achieved_td_tilt_deg": round(r["_tilt"], 4),
                        "achieved_mean_tilt_deg": round(float(r["achieved_mean_tilt_deg"]), 4),
                        "speed_mps": round(float(r["speed_mps"]), 5),
                        "speed_error_pct": r["speed_error_pct"], "solver_status": r["solver_status"],
                        "muscle": mu, "biarticular": mu in BIARTIC, "phase": phase,
                        "metric": metric, "unit": unit, "label": label,
                        "value": float(r[c]),
                    })
    _write("phaseA_long.csv", long_rows,
           ["mesh_N", "requested_offset_deg", "achieved_td_tilt_deg", "achieved_mean_tilt_deg",
            "speed_mps", "speed_error_pct", "solver_status", "muscle", "biarticular", "phase",
            "metric", "unit", "label", "value"])

    # ---- 2. dose-response per (mesh, muscle, metric) ----
    dr_rows = []
    dr = {}  # (mesh, muscle, metric) -> dict
    for mesh, rows in d.items():
        tilt = [r["_tilt"] for r in rows]
        for metric, unit, label, phase in ALL_METRICS:
            for mu in MUS:
                c = col(mu, metric)
                if any(c not in r for r in rows):
                    continue
                y = [float(r[c]) for r in rows]
                s, r2 = fit(tilt, y)
                rho = spearman(tilt, y)
                mean = float(np.mean(y)) or 1e-12
                span = 100.0 * (max(y) - min(y)) / (abs(mean) + 1e-12)
                direction = ("increases" if s < 0 else "decreases" if s > 0 else "flat")
                rec = {"mesh_N": mesh[1:], "muscle": mu, "biarticular": mu in BIARTIC,
                       "phase": phase, "metric": metric, "unit": unit,
                       "slope_per_deg_tilt": round(s, 6), "R2": round(r2, 4),
                       "spearman_rho": round(rho, 4),
                       "anterior_effect": f"{direction} with anterior tilt",
                       "value_min_tilt": round(y[0], 5), "value_max_tilt": round(y[-1], 5),
                       "rel_span_pct": round(span, 3)}
                dr_rows.append(rec)
                dr[(mesh, mu, metric)] = rec
    _write("phaseA_doseresponse.csv", dr_rows,
           list(dr_rows[0].keys()))

    # ---- 3. mesh sensitivity per (muscle, metric): match by requested offset ----
    off50 = {r["_off"]: r for r in d["N50"]}
    off100 = {r["_off"]: r for r in d["N100"]}
    common = sorted(set(off50) & set(off100))
    ms_rows = []
    ms = {}
    for metric, unit, label, phase in ALL_METRICS:
        for mu in MUS:
            c = col(mu, metric)
            diffs = []
            for o in common:
                if c not in off50[o] or c not in off100[o]:
                    continue
                v50 = float(off50[o][c]); v100 = float(off100[o][c])
                if abs(v50) < 1e-9:
                    continue
                diffs.append(100.0 * (v100 - v50) / abs(v50))
            if not diffs:
                continue
            ad = np.abs(diffs)
            rec = {"muscle": mu, "biarticular": mu in BIARTIC, "phase": phase, "metric": metric,
                   "unit": unit, "mean_abs_rel_diff_pct": round(float(ad.mean()), 3),
                   "max_abs_rel_diff_pct": round(float(ad.max()), 3),
                   "signed_mean_rel_diff_pct": round(float(np.mean(diffs)), 3)}
            ms_rows.append(rec)
            ms[(mu, metric)] = rec
    _write("phaseA_mesh_sensitivity.csv", ms_rows, list(ms_rows[0].keys()))

    # ---- 4. verdicts per (muscle, metric) ----
    v_rows = []
    for metric, unit, label, phase in ALL_METRICS:
        for mu in MUS:
            k100 = ("N100", mu, metric); k50 = ("N50", mu, metric)
            if k100 not in dr or k50 not in dr or (mu, metric) not in ms:
                continue
            rho100 = dr[k100]["spearman_rho"]; rho50 = dr[k50]["spearman_rho"]
            span100 = dr[k100]["rel_span_pct"]
            mesh_diff = ms[(mu, metric)]["mean_abs_rel_diff_pct"]
            slope100 = dr[k100]["slope_per_deg_tilt"]
            strong = abs(rho100) >= ROBUST_RHO and abs(rho50) >= CONSIST_RHO and \
                (rho100 < 0) == (rho50 < 0)
            if span100 < INVAR_SPAN:
                verdict = "approximately invariant"
            elif strong:
                verdict = "robust increase" if rho100 < 0 else "robust decrease"
            elif (rho100 < 0) != (rho50 < 0) and mesh_diff > MESH_HI:
                verdict = "mesh-sensitive"
            elif abs(rho100) < CONSIST_RHO:
                verdict = "non-monotonic"
            else:
                verdict = "inconclusive"
            direction = "increase" if slope100 < 0 else "decrease"
            v_rows.append({
                "muscle": mu, "biarticular": mu in BIARTIC, "phase": phase, "metric": metric,
                "unit": unit, "verdict": verdict,
                "direction_with_anterior_tilt": direction,
                "magnitude_mesh_conditional": mesh_diff > MESH_HI,
                "rho_N100": rho100, "rho_N50": rho50, "R2_N100": dr[k100]["R2"],
                "rel_span_pct_N100": span100, "mesh_mean_abs_rel_pct": mesh_diff,
                "value_N100_min_tilt": dr[k100]["value_min_tilt"],
                "value_N100_max_tilt": dr[k100]["value_max_tilt"]})
    _write("phaseA_verdicts.csv", v_rows, list(v_rows[0].keys()))

    _summary(v_rows)
    _figs(d)


def _write(name, rows, fields):
    p = os.path.join(OUTDIR, name)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"wrote {name} ({len(rows)} rows)")


def _summary(v_rows):
    print("\n=== per-muscle verdict summary (primary metrics) ===")
    keym = ["peak_lMtilde", "peak_active_force_N", "peak_passive_force_N", "peak_tendon_force_N",
            "neg_fiber_work_J", "peak_leng_vel_mps"]
    idx = {(r["muscle"], r["metric"]): r for r in v_rows}
    print(f"{'muscle':9s} " + " ".join(f"{m.split('_')[0][:5]:>7s}" for m in keym))
    for mu in MUS:
        cells = []
        for m in keym:
            r = idx.get((mu, m))
            cells.append(f"{(r['verdict'][:7] if r else '-'):>7s}")
        print(f"{mu:9s} " + " ".join(cells))


# ------------------------------------------------------------------ figures
def _series(rows, mu, metric):
    return [r["_tilt"] for r in rows], [float(r[col(mu, metric)]) for r in rows]


def _cap(ax, txt):
    ax.text(0.5, -0.30, txt, transform=ax.transAxes, ha="center", va="top", fontsize=7,
            color="#444")


def _figs(d):
    ctx = ("strict TDPT 8-cond; speed 11.72-11.80 m/s; solver=Solve_Succeeded; "
           "x=achieved touchdown pelvic tilt (deg, more negative=anterior); "
           "solid=N100 dashed=N50; mechanical-load SURROGATES (not injury).")

    # Fig A1: active / passive / tendon force vs tilt (3 panels x 4 muscles)
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.2))
    for ax, (metric, ylab) in zip(axs, [("peak_active_force_N", "peak active force (N)"),
                                        ("peak_passive_force_N", "peak passive force (N)"),
                                        ("peak_tendon_force_N", "peak tendon force (N)")]):
        for mu in MUS:
            x100, y100 = _series(d["N100"], mu, metric)
            x50, y50 = _series(d["N50"], mu, metric)
            ax.plot(x100, y100, "-o", color=COLORS[mu], ms=4, label=mu)
            ax.plot(x50, y50, "--", color=COLORS[mu], alpha=0.55)
        ax.set_xlabel("touchdown pelvic tilt (deg)"); ax.set_ylabel(ylab)
        ax.invert_xaxis(); ax.grid(alpha=0.3)
    axs[0].legend(fontsize=8, loc="best")
    fig.suptitle("Figure A1  Pelvic tilt vs active / passive / tendon force (per hamstring)", y=1.0)
    fig.text(0.5, 0.005, ctx, ha="center", fontsize=7, color="#444")
    fig.tight_layout(rect=[0, 0.05, 1, 0.97])
    _save(fig, "fig_A1_force_doseresponse.png")

    # Fig A2: terminal swing vs early stance (2 panels: TS peak lMtilde & passive; ES peak lMtilde & active)
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
    for mu in MUS:
        xs, ts = _series(d["N100"], mu, "TS_peak_lMtilde")
        _, es = _series(d["N100"], mu, "ES_peak_lMtilde")
        axs[0].plot(xs, ts, "-o", color=COLORS[mu], ms=4, label=f"{mu} TS")
        axs[0].plot(xs, es, ":s", color=COLORS[mu], ms=3, alpha=0.7)
    axs[0].set_title("peak norm. fiber length: terminal-swing (o) vs early-stance (s)")
    axs[0].set_xlabel("touchdown pelvic tilt (deg)"); axs[0].set_ylabel("lMtilde (-)")
    axs[0].invert_xaxis(); axs[0].grid(alpha=0.3); axs[0].legend(fontsize=7, ncol=2)
    for mu in MUS:
        xs, ts = _series(d["N100"], mu, "TS_peak_passive_force_N")
        _, es = _series(d["N100"], mu, "ES_peak_active_force_N")
        axs[1].plot(xs, ts, "-o", color=COLORS[mu], ms=4, label=f"{mu} TS passive")
        axs[1].plot(xs, es, ":s", color=COLORS[mu], ms=3, alpha=0.7)
    axs[1].set_title("TS passive force (o) vs ES active force (s)")
    axs[1].set_xlabel("touchdown pelvic tilt (deg)"); axs[1].set_ylabel("force (N)")
    axs[1].invert_xaxis(); axs[1].grid(alpha=0.3); axs[1].legend(fontsize=7, ncol=2)
    fig.suptitle("Figure A2  Terminal-swing vs early-stance per-muscle load (N=100)", y=1.0)
    fig.text(0.5, 0.005, ctx, ha="center", fontsize=7, color="#444")
    fig.tight_layout(rect=[0, 0.05, 1, 0.96])
    _save(fig, "fig_A2_TS_vs_ES.png")

    # Fig A3: length / tension / negative work dose-response (3 panels)
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.2))
    for ax, (metric, ylab) in zip(axs, [("peak_lMtilde", "peak norm. fiber length (-)"),
                                        ("peak_active_force_N", "peak active force (N)"),
                                        ("neg_fiber_work_J", "negative active work (J)")]):
        for mu in MUS:
            x100, y100 = _series(d["N100"], mu, metric)
            x50, y50 = _series(d["N50"], mu, metric)
            ax.plot(x100, y100, "-o", color=COLORS[mu], ms=4, label=mu)
            ax.plot(x50, y50, "--", color=COLORS[mu], alpha=0.55)
        ax.set_xlabel("touchdown pelvic tilt (deg)"); ax.set_ylabel(ylab)
        ax.invert_xaxis(); ax.grid(alpha=0.3)
    axs[0].legend(fontsize=8)
    fig.suptitle("Figure A3  Fiber length, tension, and negative work dose-response", y=1.0)
    fig.text(0.5, 0.005, ctx, ha="center", fontsize=7, color="#444")
    fig.tight_layout(rect=[0, 0.05, 1, 0.97])
    _save(fig, "fig_A3_length_tension_work.png")

    # Fig A4: mesh sensitivity bar chart (mean abs rel diff per metric, grouped by muscle)
    metrics4 = ["peak_lMtilde", "peak_active_force_N", "peak_passive_force_N",
                "peak_tendon_force_N", "neg_fiber_work_J", "neg_fiber_work_tot_J",
                "peak_leng_vel_mps"]
    off50 = {r["_off"]: r for r in d["N50"]}; off100 = {r["_off"]: r for r in d["N100"]}
    common = sorted(set(off50) & set(off100))
    fig, ax = plt.subplots(figsize=(12, 4.6))
    width = 0.2
    x = np.arange(len(metrics4))
    for i, mu in enumerate(MUS):
        vals = []
        for metric in metrics4:
            c = col(mu, metric)
            ds = [abs(100.0 * (float(off100[o][c]) - float(off50[o][c])) /
                      (abs(float(off50[o][c])) + 1e-9)) for o in common]
            vals.append(np.mean(ds))
        ax.bar(x + (i - 1.5) * width, vals, width, color=COLORS[mu], label=mu)
    ax.axhline(MESH_HI, color="k", ls="--", lw=1, label=f"{MESH_HI:.0f}% mesh-conditional")
    ax.set_xticks(x)
    ax.set_xticklabels([m.replace("peak_", "").replace("_N", "").replace("_", " ") for m in metrics4],
                       rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("mean |N100-N50| / N50  (%)")
    ax.set_title("Figure A4  Mesh sensitivity (N=50 vs N=100) per muscle & metric")
    ax.legend(fontsize=8, ncol=5); ax.grid(alpha=0.3, axis="y")
    fig.text(0.5, 0.005, "matched by requested offset; passive force & negative work are the "
             "mesh-sensitive metrics -> report direction, treat magnitude as conditional.",
             ha="center", fontsize=7, color="#444")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _save(fig, "fig_A4_mesh_sensitivity.png")


def _save(fig, name):
    p = os.path.join(OUTDIR, name)
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {name}")


if __name__ == "__main__":
    main()
