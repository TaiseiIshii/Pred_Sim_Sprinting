"""
phaseD_objective_frontier.py -- Phase D/E analysis: characterize the active-eccentric (D2) load
objective and compare its speed<->load frontier against the fiber-length (D1) objective, at N=50.

For each solution computes biarticular-mean load surrogates on the corrected engine
(ham_load_metrics), the % change vs the shared baseline (w=0), and flags near-matched-speed
load-reduction candidates (|dSpeed|<=0.5% AND target surrogate reduced >=3%). Answers the Phase E
questions: does lowering active-eccentric loading also lower fiber length / passive force / work?
are there trade-offs? is the reduction explained by speed alone?

Objectives (all N=50, standard morphology):
  D1 length  = HamPareto_Nom_w{0000,0050,0100,0200,0400,0800}  (penalizes peak lMtilde)
  D2 ecc     = HamEcc_w{0000,0100,0500,2000,8000}              (penalizes Fce*[vMtilde]+)

Outputs (Results/Validation_Master/):
  phaseD_objective_frontier.csv, fig_D1_objective_frontier.png

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" analysis/validation/phaseD_objective_frontier.py
"""
from __future__ import annotations

import csv
import glob
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import ham_load_metrics as H

OUTDIR = os.path.join(H.RESULTS, "Validation_Master")
BIARTIC = ["semimem", "semiten", "bifemlh"]

D1 = [("length", "HamPareto_Nom_w0000", 0.0), ("length", "HamPareto_Nom_w0050", 0.05),
      ("length", "HamPareto_Nom_w0100", 0.10), ("length", "HamPareto_Nom_w0200", 0.20),
      ("length", "HamPareto_Nom_w0400", 0.40), ("length", "HamPareto_Nom_w0800", 0.80)]
D2 = [("ecc", "HamEcc_w0000", 0.0), ("ecc", "HamEcc_w0100", 0.10), ("ecc", "HamEcc_w0500", 0.50),
      ("ecc", "HamEcc_w2000", 2.00), ("ecc", "HamEcc_w8000", 8.00)]
D3 = [("passive", "HamPasv_w0200", 0.20), ("passive", "HamPasv_w0800", 0.80)]
D5 = [("composite", "HamCompEQ_w0100", 0.10), ("composite", "HamCompEQ_w0500", 0.50),
      ("composite", "HamCompEQ_w2000", 2.00)]
SHARED_BASE = "HamPareto_Nom_w0000"   # shared penalty-off baseline for all objectives

SURR = [("peak_lMtilde", "TS_peak_lMtilde"), ("act_ecc_power", "peak_act_ecc_power_W"),
        ("neg_work_J", "neg_fiber_work_J"), ("passive_N", "peak_passive_force_N"),
        ("active_N", "peak_active_force_N"), ("tendon_N", "peak_tendon_force_N")]


def find_n50(token):
    """Newest .mat for token at mesh N=50 (avoid picking a new N=100 file)."""
    fs = sorted(glob.glob(os.path.join(H.RESULTS, f"pred_sprinting_data_*{token}.mat")),
                key=os.path.getmtime, reverse=True)
    for p in fs:
        try:
            d = H.load_optimum(p)
            if d["N"] == 50:
                return p
        except Exception:
            continue
    return None


def biartic_mean(m, key):
    return float(np.mean([m[f"{n}_{key}"] for n in BIARTIC]))


def main():
    rows = []
    base = None   # shared penalty-off baseline metrics
    bp = find_n50(SHARED_BASE)
    if bp:
        bd = H.load_optimum(bp); bm = H.condition_metrics(bp)
        base = {"speed_mps": round(bd["speed"], 5)}
        for name, key in SURR:
            base[name] = round(biartic_mean(bm, key), 5)
    for obj, token, w in D1 + D2 + D3 + D5:
        p = find_n50(token)
        if not p:
            print(f"  [skip] {token} (no N=50 mat)"); continue
        d = H.load_optimum(p); m = H.condition_metrics(p)
        rec = {"objective": obj, "weight": w, "source_file": os.path.basename(p),
               "solver_status": d["return_status"], "speed_mps": round(d["speed"], 5),
               "td_tilt_deg": round(d["td_tilt_deg"], 4)}
        for name, key in SURR:
            rec[name] = round(biartic_mean(m, key), 5)
        rows.append(rec)

    # % change vs the SHARED baseline (w=0), so objectives are directly comparable
    for r in rows:
        if not base:
            continue
        r["dSpeed_pct"] = round(100.0 * (r["speed_mps"] - base["speed_mps"]) / base["speed_mps"], 4)
        for name, _ in SURR:
            r[f"d_{name}_pct"] = round(100.0 * (r[name] - base[name]) / (abs(base[name]) + 1e-9), 3)
        target = {"ecc": "act_ecc_power", "passive": "passive_N",
                  "composite": "peak_lMtilde"}.get(r["objective"], "peak_lMtilde")
        r["near_matched_candidate"] = bool(abs(r["dSpeed_pct"]) <= 0.5 and r[f"d_{target}_pct"] <= -3.0)

    fields = (["objective", "weight", "source_file", "solver_status", "speed_mps", "dSpeed_pct",
               "td_tilt_deg"] + [n for n, _ in SURR] + [f"d_{n}_pct" for n, _ in SURR]
              + ["near_matched_candidate"])
    with open(os.path.join(OUTDIR, "phaseD_objective_frontier.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print("wrote phaseD_objective_frontier.csv")

    # ---- report ----
    print("\n=== speed vs load surrogates (biarticular mean, % vs w=0) ===")
    print(f"{'obj':7s}{'w':>6s}{'dSpd%':>8s}{'dLMt%':>8s}{'dEccPw%':>9s}{'dNegW%':>8s}"
          f"{'dPas%':>8s}{'cand':>6s}  status")
    for r in rows:
        if "dSpeed_pct" not in r:
            continue
        print(f"{r['objective']:7s}{r['weight']:6.2f}{r['dSpeed_pct']:8.3f}"
              f"{r['d_peak_lMtilde_pct']:8.2f}{r['d_act_ecc_power_pct']:9.2f}"
              f"{r['d_neg_work_J_pct']:8.2f}{r['d_passive_N_pct']:8.2f}"
              f"{str(r['near_matched_candidate']):>6s}  {r['solver_status']}")

    _fig(rows)


def _fig(rows):
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.4))
    panels = [("d_act_ecc_power_pct", "active eccentric power change (%)"),
              ("d_peak_lMtilde_pct", "TS peak fiber length change (%)"),
              ("d_neg_work_J_pct", "active negative work change (%)")]
    styles = {"length": ("#2166ac", "o", "-"), "ecc": ("#b2182b", "s", "--"),
              "passive": ("#1b7837", "^", ":"), "composite": ("#e08214", "D", "-.")}
    for ax, (key, ylab) in zip(axs, panels):
        for obj in ("length", "ecc", "passive", "composite"):
            pts = [(r["dSpeed_pct"], r[key]) for r in rows
                   if r.get("objective") == obj and "dSpeed_pct" in r]
            pts.sort()
            if not pts:
                continue
            xs, ys = zip(*pts)
            c, mk, ls = styles[obj]
            ax.plot(xs, ys, ls, marker=mk, color=c, label=f"{obj} objective")
        ax.axhline(0, color="k", lw=0.6); ax.axvline(0, color="k", lw=0.6)
        ax.axvspan(-0.5, 0.5, color="green", alpha=0.08)  # near-matched-speed band
        ax.set_xlabel("speed change vs w=0 (%)"); ax.set_ylabel(ylab); ax.grid(alpha=0.3)
    axs[0].legend(fontsize=9)
    fig.suptitle("Figure D1  Objective comparison at N=50: active-eccentric (D2) vs fiber-length (D1)", y=1.0)
    fig.text(0.5, 0.005, "green band = near-matched speed (|dSpeed|<=0.5%); biarticular mean; strict "
             "Solve_Succeeded; mechanical-load surrogates, not injury.", ha="center", fontsize=7.5, color="#444")
    fig.tight_layout(rect=[0, 0.05, 1, 0.96])
    fig.savefig(os.path.join(OUTDIR, "fig_D1_objective_frontier.png"), dpi=150, bbox_inches="tight")
    plt.close(fig); print("wrote fig_D1_objective_frontier.png")


if __name__ == "__main__":
    main()
