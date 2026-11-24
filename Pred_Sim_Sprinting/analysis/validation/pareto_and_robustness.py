"""
pareto_and_robustness.py  --  Step 9 (speed-load Pareto) + Step 11 (mesh robustness),
recomputed with the corrected load-metric engine (ham_load_metrics).

Step 9: for the HamPareto weight sweep (biarticular fascicle-overstretch penalty), plot the
achieved sprint speed against a CORRECTED biarticular load surrogate (terminal-swing peak
normalized fiber length and per-stride negative fiber work), per morphology (Nom / Sh / Wk).
Reports non-dominated (Pareto) set, knee point, and "speed-neutral load reduction" points
under PRE-DECLARED thresholds.

  Pre-declared thresholds (before inspecting results):
    speed noise floor   = 0.50%  (from the matched TDPT set spread 0.43-0.51%)
    surrogate noise floor= 1.0%  (mesh N50-vs-N100 divergence, quantified in Step 11)
    "speed-neutral load reduction" = surrogate reduced >= 3% AND |speed change| <= 0.50%.
    (No causal / "safe technique" language; these are candidate motions only.)

Step 11: for the strict TDPT 8-condition set, quantify N=50 vs N=100 divergence per metric,
and report solver success rates per experiment from the manifest.

Outputs (Results/Validation_Master/):
  pareto_nominal.csv, pareto_morphology.csv, mesh_robustness.csv, solver_success.csv,
  fig_p1_pareto.png, fig_p2_mesh_robustness.png

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" \
       analysis/validation/pareto_and_robustness.py
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
SPEED_NOISE_PCT = 0.50
SURR_REDUCE_PCT = 3.0


def read_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def surrogate(m):
    """Biarticular terminal-swing load surrogate: mean peak lMtilde and neg work."""
    lmt = float(np.mean([m[f"{nm}_TS_peak_lMtilde"] for nm in BIARTIC]))
    work = float(np.mean([m[f"{nm}_neg_fiber_work_J"] for nm in BIARTIC]))
    return lmt, work


def cond_row(r):
    m = H.condition_metrics(os.path.join(H.RESULTS, r["source_file"]))
    lmt, work = surrogate(m)
    return {"condition": r["condition"], "objective": r["objective"],
            "morphology": r["morphology"], "speed_mps": m["speed_mps"],
            "biartic_TS_peak_lMtilde": lmt, "biartic_neg_work_J": work,
            "status": r["solver_status"]}


def nondominated(points):
    """Pareto set maximizing speed and minimizing surrogate (lower lMtilde better)."""
    keep = []
    for i, p in enumerate(points):
        dom = False
        for j, q in enumerate(points):
            if j == i:
                continue
            if (q["speed_mps"] >= p["speed_mps"] and
                    q["biartic_TS_peak_lMtilde"] <= p["biartic_TS_peak_lMtilde"] and
                    (q["speed_mps"] > p["speed_mps"] or
                     q["biartic_TS_peak_lMtilde"] < p["biartic_TS_peak_lMtilde"])):
                dom = True
                break
        if not dom:
            keep.append(p)
    return keep


def knee_point(front):
    """Max-distance-from-chord knee point on a (speed, surrogate) front."""
    if len(front) < 3:
        return None
    f = sorted(front, key=lambda p: p["speed_mps"])
    x = np.array([p["speed_mps"] for p in f])
    y = np.array([p["biartic_TS_peak_lMtilde"] for p in f])
    x0, x1, y0, y1 = x[0], x[-1], y[0], y[-1]
    d = np.abs((y1 - y0) * x - (x1 - x0) * y + x1 * y0 - y1 * x0) / (np.hypot(y1 - y0, x1 - x0) + 1e-12)
    return f[int(np.argmax(d))]


def pareto_nominal(rows):
    nom = [r for r in rows if r["experiment"] == "HamPareto" and r["morphology"] == "standard"
           and r["strict"] == "True"]
    pts = [cond_row(r) for r in nom]
    # sort by penalty weight (parse from objective)
    def w(p):
        s = p["objective"].split("=")[-1]
        try:
            return float(s)
        except Exception:
            return 0.0
    pts.sort(key=w)
    base = next((p for p in pts if w(p) == 0.0), pts[0])
    for p in pts:
        p["dSpeed_pct"] = 100.0 * (p["speed_mps"] - base["speed_mps"]) / base["speed_mps"]
        p["dSurrogate_pct"] = 100.0 * (p["biartic_TS_peak_lMtilde"] - base["biartic_TS_peak_lMtilde"]) \
            / base["biartic_TS_peak_lMtilde"]
        p["dNegWork_pct"] = 100.0 * (p["biartic_neg_work_J"] - base["biartic_neg_work_J"]) \
            / base["biartic_neg_work_J"]
        p["speed_neutral_load_reduction"] = (p["dSurrogate_pct"] <= -SURR_REDUCE_PCT
                                             and abs(p["dSpeed_pct"]) <= SPEED_NOISE_PCT)
    front = nondominated(pts)
    knee = knee_point(front)
    with open(os.path.join(OUTDIR, "pareto_nominal.csv"), "w", newline="", encoding="utf-8") as f:
        cols = ["condition", "objective", "speed_mps", "dSpeed_pct", "biartic_TS_peak_lMtilde",
                "dSurrogate_pct", "biartic_neg_work_J", "dNegWork_pct",
                "speed_neutral_load_reduction", "status"]
        w_ = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w_.writeheader()
        w_.writerows(pts)
    print("wrote pareto_nominal.csv")
    print("  weight sweep (nominal athlete), corrected surrogate:")
    for p in pts:
        tag = "  <== speed-neutral load reduction" if p["speed_neutral_load_reduction"] else ""
        print(f"    {p['objective']:22s} speed {p['speed_mps']:.3f} ({p['dSpeed_pct']:+.2f}%)  "
              f"TSpkLMt {p['biartic_TS_peak_lMtilde']:.3f} ({p['dSurrogate_pct']:+.2f}%)  "
              f"negW {p['dNegWork_pct']:+.1f}%{tag}")
    print(f"  non-dominated set: {len(front)} points; knee = "
          f"{knee['objective'] if knee else 'n/a'}")
    return pts, front, knee


def pareto_morphology(rows):
    out = []
    for morph in ("fascicle_x0.80", "strength_x0.80"):
        sub = [r for r in rows if r["experiment"] == "HamPareto" and r["morphology"] == morph
               and r["strict"] == "True"]
        for r in sub:
            out.append(cond_row(r))
    with open(os.path.join(OUTDIR, "pareto_morphology.csv"), "w", newline="", encoding="utf-8") as f:
        cols = ["condition", "morphology", "objective", "speed_mps",
                "biartic_TS_peak_lMtilde", "biartic_neg_work_J", "status"]
        w_ = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w_.writeheader()
        w_.writerows(out)
    print("wrote pareto_morphology.csv")
    return out


def mesh_robustness(rows):
    """N=50 vs N=100 per-metric divergence over the strict TDPT 8-condition set."""
    def sel(mesh_N):
        cand = {}
        for r in rows:
            if r["experiment"] != "PelvicTD" or r["strict"] != "True" or int(r["mesh_N"]) != mesh_N:
                continue
            off = float(r["requested_pelvis_offset_deg"])
            resid = float(r["constraint_residual"]) if r["constraint_residual"] not in ("", "nan") else 1e9
            if off not in cand or resid < cand[off][0]:
                cand[off] = (resid, r)
        return {o: cand[o][1] for o in cand}
    s50, s100 = sel(50), sel(100)
    offs = sorted(set(s50) & set(s100))
    metrics = ["peak_lMtilde", "peak_MTU_len_m", "peak_active_force_N",
               "peak_passive_force_N", "peak_tendon_force_N", "neg_fiber_work_J"]
    agg = {mt: [] for mt in metrics}
    rows_out = []
    for off in offs:
        m50 = H.condition_metrics(os.path.join(H.RESULTS, s50[off]["source_file"]))
        m100 = H.condition_metrics(os.path.join(H.RESULTS, s100[off]["source_file"]))
        for nm in BIARTIC:
            for mt in metrics:
                a, b = m50[f"{nm}_{mt}"], m100[f"{nm}_{mt}"]
                rel = 100.0 * abs(a - b) / (abs(b) + 1e-12)
                agg[mt].append(rel)
        rows_out.append({"offset": off,
                         "speed50": m50["speed_mps"], "speed100": m100["speed_mps"],
                         **{f"{nm}_peak_lMtilde_reldiff_pct":
                            100 * abs(m50[f"{nm}_peak_lMtilde"] - m100[f"{nm}_peak_lMtilde"])
                            / m100[f"{nm}_peak_lMtilde"] for nm in BIARTIC}})
    with open(os.path.join(OUTDIR, "mesh_robustness.csv"), "w", newline="", encoding="utf-8") as f:
        cols = list(rows_out[0].keys())
        w_ = csv.DictWriter(f, fieldnames=cols)
        w_.writeheader()
        w_.writerows(rows_out)
    print("wrote mesh_robustness.csv")
    print("  N=50 vs N=100 |reldiff| over biarticular hams (median / max %):")
    for mt in metrics:
        arr = np.array(agg[mt])
        print(f"    {mt:22s} median={np.median(arr):.2f}%  max={arr.max():.2f}%")
    return agg


def solver_success(rows):
    by = {}
    for r in rows:
        e = r["experiment"]
        by.setdefault(e, {"n": 0, "strict": 0, "accept": 0, "other": 0})
        by[e]["n"] += 1
        if r["solver_status"] == "Solve_Succeeded":
            by[e]["strict"] += 1
        elif r["solver_status"] == "Solved_To_Acceptable_Level":
            by[e]["accept"] += 1
        else:
            by[e]["other"] += 1
    with open(os.path.join(OUTDIR, "solver_success.csv"), "w", newline="", encoding="utf-8") as f:
        w_ = csv.writer(f)
        w_.writerow(["experiment", "n", "strict", "acceptable", "other", "strict_rate_pct"])
        for e, d in sorted(by.items()):
            w_.writerow([e, d["n"], d["strict"], d["accept"], d["other"],
                         round(100 * d["strict"] / d["n"], 1)])
    print("wrote solver_success.csv")
    return by


def fig_pareto(pts, front, knee, morph, out):
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    x = [p["speed_mps"] for p in pts]
    y = [p["biartic_TS_peak_lMtilde"] for p in pts]
    ax.plot(x, y, "o", color="#999", ms=7, label="nominal athlete (weight sweep)")
    fx = sorted(front, key=lambda p: p["speed_mps"])
    ax.plot([p["speed_mps"] for p in fx], [p["biartic_TS_peak_lMtilde"] for p in fx],
            "-", color="#2166ac", lw=2, label="non-dominated front")
    for p in pts:
        if p["speed_neutral_load_reduction"]:
            ax.plot(p["speed_mps"], p["biartic_TS_peak_lMtilde"], "*", color="#1b7837",
                    ms=16, label="speed-neutral load reduction")
    if knee:
        ax.plot(knee["speed_mps"], knee["biartic_TS_peak_lMtilde"], "D", color="#b2182b",
                ms=9, label="knee point")
    mk = {"fascicle_x0.80": ("^", "#e08214", "short-fascicle athlete"),
          "strength_x0.80": ("v", "#8073ac", "weak-strength athlete")}
    for m in morph:
        s = mk.get(m["morphology"])
        if s:
            ax.plot(m["speed_mps"], m["biartic_TS_peak_lMtilde"], s[0], color=s[1], ms=8)
    for m in mk.values():
        ax.plot([], [], m[0], color=m[1], label=m[2])
    ax.set_xlabel("achieved sprint speed (m/s)  (performance ->)")
    ax.set_ylabel("biarticular terminal-swing peak lMtilde  (<- lower load)")
    ax.set_title("Step 9 speed-load Pareto (corrected surrogate)\n"
                 "penalty sweep; candidate motions only, no causal claim")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", os.path.basename(out))


def fig_mesh(agg, out):
    fig, ax = plt.subplots(figsize=(8, 4.6))
    labels = list(agg.keys())
    med = [np.median(agg[k]) for k in labels]
    mx = [np.max(agg[k]) for k in labels]
    xi = np.arange(len(labels))
    ax.bar(xi - 0.2, med, 0.4, label="median", color="#2166ac")
    ax.bar(xi + 0.2, mx, 0.4, label="max", color="#f4a582")
    ax.axhline(1.0, color="grey", ls=":", label="1% reference")
    ax.set_xticks(xi)
    ax.set_xticklabels([l.replace("_", "\n") for l in labels], fontsize=7)
    ax.set_ylabel("N=50 vs N=100 |reldiff| (%)")
    ax.set_title("Step 11 mesh robustness (biarticular hams, strict TDPT 8 conditions)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", os.path.basename(out))


def main():
    rows = read_manifest()
    pts, front, knee = pareto_nominal(rows)
    morph = pareto_morphology(rows)
    fig_pareto(pts, front, knee, morph, os.path.join(OUTDIR, "fig_p1_pareto.png"))
    agg = mesh_robustness(rows)
    fig_mesh(agg, os.path.join(OUTDIR, "fig_p2_mesh_robustness.png"))
    solver_success(rows)


if __name__ == "__main__":
    main()
