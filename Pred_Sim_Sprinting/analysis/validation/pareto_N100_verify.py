"""
pareto_N100_verify.py -- Phase 2 final verification of the N=100 multi-start speed-load Pareto.

Reads Results/HamPareto_N100/checkpoint.csv (7 strict solves: forward w0/0.05/0.1/0.2, plus w0.1 and
w0.2 from Nominal, plus w0.1 backward), computes the biarticular-mean load surrogate (terminal-swing
peak lMtilde) on the corrected engine, checks multi-start reproducibility of w=0.1, compares to N=50,
tests non-dominance, and applies the Phase-2.4 gates -> a Supported/Conditional/Rejected verdict.

Outputs (Results/Validation_Master/): pareto_N100.csv, fig_4_pareto_N100.png
Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" analysis/validation/pareto_N100_verify.py
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
CKPT = os.path.join(H.RESULTS, "HamPareto_N100", "checkpoint.csv")
BIARTIC = ["semimem", "semiten", "bifemlh"]


def biartic_mean(m, key):
    return float(np.mean([m[f"{n}_{key}"] for n in BIARTIC]))


def surro(m):
    return biartic_mean(m, "TS_peak_lMtilde")


def main():
    rows = [r for r in csv.DictReader(open(CKPT, encoding="utf-8"))
            if r["solver_status"] == "Solve_Succeeded" and r["out_file"]]
    recs = []
    for r in rows:
        p = os.path.join(H.RESULTS, r["out_file"])
        if not os.path.isfile(p):
            print(f"  [skip] {r['out_file']} missing"); continue
        m = H.condition_metrics(p)
        w = float(r["condition"].split("_w")[-1]) / 1000.0
        recs.append({"tag": r["tag"], "weight": w, "init": r["init_method"],
                     "speed": float(r["speed_mps"]), "tilt": float(r["td_tilt_deg"]),
                     "surrogate": surro(m),
                     "passive_N": biartic_mean(m, "peak_passive_force_N"),
                     "negwork_J": biartic_mean(m, "neg_fiber_work_J"),
                     "iters": int(r["iters"]), "status": r["solver_status"]})
    base = next(x for x in recs if x["weight"] == 0.0)
    for x in recs:
        x["dSpeed_pct"] = round(100.0 * (x["speed"] - base["speed"]) / base["speed"], 4)
        x["dSurro_pct"] = round(100.0 * (x["surrogate"] - base["surrogate"]) / base["surrogate"], 4)
        x["dNegW_pct"] = round(100.0 * (x["negwork_J"] - base["negwork_J"]) / base["negwork_J"], 3)

    with open(os.path.join(OUTDIR, "pareto_N100.csv"), "w", newline="", encoding="utf-8") as f:
        fields = ["tag", "weight", "init", "speed", "dSpeed_pct", "tilt", "surrogate", "dSurro_pct",
                  "passive_N", "negwork_J", "dNegW_pct", "iters", "status"]
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for x in sorted(recs, key=lambda z: (z["weight"], z["init"])):
            w.writerow(x)
    print("wrote pareto_N100.csv")

    # ---- multi-start reproducibility of w=0.1 ----
    cand = [x for x in recs if x["weight"] == 0.10]
    sp = np.array([x["speed"] for x in cand]); su = np.array([x["surrogate"] for x in cand])
    sp_spread = 100.0 * (sp.max() - sp.min()) / sp.mean()
    su_spread = 100.0 * (su.max() - su.min()) / su.mean()
    print(f"\n=== w=0.1 multi-start ({len(cand)} inits: "
          f"{', '.join(sorted(x['init'].split('_')[0] for x in cand))}) ===")
    for x in sorted(cand, key=lambda z: z["init"]):
        print(f"  {x['init']:26s} speed={x['speed']:.5f} ({x['dSpeed_pct']:+.3f}%) "
              f"surro={x['surrogate']:.4f} ({x['dSurro_pct']:+.2f}%)")
    print(f"  spread: speed {sp_spread:.3f}% , surrogate {su_spread:.3f}%")

    # ---- N=50 vs N=100 for w=0.1 (from pareto_nominal.csv) ----
    n50 = {float(r["objective"].split("=")[-1]): r
           for r in csv.DictReader(open(os.path.join(OUTDIR, "pareto_nominal.csv"), encoding="utf-8"))}
    n50_w01 = n50.get(0.1)
    cand_mean_dsurro = float(np.mean([x["dSurro_pct"] for x in cand]))
    cand_mean_dspeed = float(np.mean([x["dSpeed_pct"] for x in cand]))
    d_load = d_speed = None
    if n50_w01:
        n50_dsurro = float(n50_w01["dSurrogate_pct"]); n50_dspeed = float(n50_w01["dSpeed_pct"])
        d_load = abs(cand_mean_dsurro - n50_dsurro); d_speed = abs(cand_mean_dspeed - n50_dspeed)
        print(f"\n=== N=50 vs N=100 (w=0.1) ===")
        print(f"  surrogate: N50 {n50_dsurro:+.2f}%  N100 {cand_mean_dsurro:+.2f}%  |diff| {d_load:.2f} pp")
        print(f"  speed:     N50 {n50_dspeed:+.3f}% N100 {cand_mean_dspeed:+.3f}% |diff| {d_speed:.3f} pp")

    # ---- non-dominance among the forward frontier ----
    fwd = sorted([x for x in recs if x["init"].startswith("forward")], key=lambda z: z["weight"])
    nondom = []
    for x in fwd:
        dominated = any((y["speed"] >= x["speed"] and y["surrogate"] <= x["surrogate"]
                         and (y["speed"] > x["speed"] or y["surrogate"] < x["surrogate"]))
                        for y in fwd if y is not x)
        if not dominated:
            nondom.append(x["weight"])
    print(f"\nnon-dominated forward weights: {nondom}")

    # ---- Phase-2.4 gates for w=0.1 ----
    g = {}
    g["strict"] = all(x["status"] == "Solve_Succeeded" for x in cand)
    g["speed<=0.5%"] = abs(cand_mean_dspeed) <= 0.5
    g["surrogate<=-3%"] = cand_mean_dsurro <= -3.0
    g["non_dominated"] = 0.10 in nondom
    g["load_N50N100<=2pp"] = (d_load is not None and d_load <= 2.0)
    g["speed_N50N100<=0.5pp"] = (d_speed is not None and d_speed <= 0.5)
    g["basins_agree"] = sp_spread <= 1.0 and su_spread <= 1.0
    verdict = "Supported" if all(g.values()) else (
        "Conditional" if sum(g.values()) >= len(g) - 1 else "Rejected")
    print("\n=== Phase-2.4 gate (w=0.1, N=100) ===")
    for k, v in g.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print(f"  VERDICT: Pareto candidate w=0.1 -> {verdict}")

    _fig(recs, cand)
    return verdict


def _fig(recs, cand):
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
    fwd = sorted([x for x in recs if x["init"].startswith("forward")], key=lambda z: z["weight"])
    axs[0].plot([x["dSpeed_pct"] for x in fwd], [x["dSurro_pct"] for x in fwd], "-o",
                color="#2166ac", label="N=100 forward frontier")
    for x in cand:
        axs[0].scatter(x["dSpeed_pct"], x["dSurro_pct"], s=90, facecolors="none",
                       edgecolors="#b2182b", linewidths=1.6, zorder=5)
    axs[0].scatter([], [], s=90, facecolors="none", edgecolors="#b2182b", label="w=0.1 multi-start")
    axs[0].axvspan(-0.5, 0.5, color="green", alpha=0.08)
    axs[0].set_xlabel("speed change vs w=0 (%)")
    axs[0].set_ylabel("biarticular TS peak lMtilde change (%)")
    axs[0].set_title("N=100 speed-load Pareto"); axs[0].grid(alpha=0.3); axs[0].legend(fontsize=8)
    for x in cand:
        axs[1].bar(x["init"].split("_")[0], x["speed"], color="#2166ac")
    axs[1].set_ylim(min(x["speed"] for x in cand) - 0.01, max(x["speed"] for x in cand) + 0.01)
    axs[1].set_ylabel("achieved speed (m/s)"); axs[1].set_title("w=0.1 multi-start reproducibility")
    axs[1].tick_params(axis="x", rotation=15)
    fig.suptitle("Figure 4  N=100 multi-start speed-load Pareto (Nominal)", y=1.0)
    fig.text(0.5, 0.005, "strict Solve_Succeeded; surrogate = biarticular terminal-swing peak "
             "normalized fibre length; not injury.", ha="center", fontsize=7.5, color="#444")
    fig.tight_layout(rect=[0, 0.05, 1, 0.96])
    fig.savefig(os.path.join(OUTDIR, "fig_4_pareto_N100.png"), dpi=150, bbox_inches="tight")
    plt.close(fig); print("wrote fig_4_pareto_N100.png")


if __name__ == "__main__":
    main()
