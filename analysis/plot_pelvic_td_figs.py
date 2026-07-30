"""Analyze + plot the v3 (TDPT) sweep with the FULL hamstring injury-risk proxy
set (matching v2's analyze_pelvic_shift.m), from the saved _PelvisTD_*.mat.

Per hamstring (bilateral mean of the per-side peak), for the feasible dose-response:
  peakLM   = peak normalized fibre length lMtilde      (fibre strain)
  peakLMT  = peak musculotendon length lMTk_lr (m)     (MTU stretch; injury site)
  peakFpe  = peak normalized passive force Fpetilde     (connective-tissue load)
  peakEccLoad = peak (max(0,vMtilde) * FMvtilde)        (active force while lengthening)
  peakComp = peak (lMtilde * max(0,vMtilde) * Fce/Fiso) (composite strain x ecc x force)
  eccWork  = sum(Fce * max(0,vMtilde)) * dt             (eccentric impulse)
  tPeakPct = % of stride at peak lMtilde                (should be terminal swing)

Outputs (Results/PelvicTD_Study/):
  pelvic_td_summary.csv          (extended: all proxies)
  td_fig1_dose_hamstring.png     (peak lMtilde dose-response, headline)
  td_fig2_speed_feasibility.png
  td_fig3_multiproxy.png         (2x2: lMtilde / MTU length / passive / eccentric)

Run (base conda python): python analysis/plot_pelvic_td_figs.py
"""
from __future__ import annotations

import csv
import glob
import os
import sys

import numpy as np
from scipy.io import loadmat

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "Results")
STUDY = os.path.join(RESULTS, "PelvicTD_Study")

# Target mesh size (set in main from argv; default 50). The N=100 mesh-
# convergence runs share the same filename pattern as N=50, so we must filter
# candidate .mat files by their stored optimumOutput.options.N.
TARGET_N = 50
SUFFIX = ""  # appended to output filenames when TARGET_N != 50

# (offset_deg, tag, prefix) -- the most-anterior half (offset <= 0) uses the
# bound-relaxed "PelvisTDwide" runs so NO point silently rides the pelvis_tilt
# coordinate bound (~-9.92 deg). The posterior half (p2..p6) never approaches
# the bound, so its standard "PelvisTD" runs are already bound-free.
CONDITIONS = [(-8, "m8", "PelvisTDwide"), (-6, "m6", "PelvisTDwide"),
              (-4, "m4", "PelvisTDwide"), (-2, "m2", "PelvisTDwide"),
              (0, "p0", "PelvisTDwide"),
              (2, "p2", "PelvisTD"), (4, "p4", "PelvisTD"),
              (6, "p6", "PelvisTD")]
# muscle key -> (L row, R row 1-based, JP label)
HAM = {"semimem": (7, 53, "半膜様筋 semimem"),
       "semiten": (8, 54, "半腱様筋 semiten"),
       "bifemlh": (9, 55, "二頭筋長頭 bifemlh"),
       "bifemsh": (10, 56, "二頭筋短頭 bifemsh(対照)")}
PROXIES = ["peakLM", "peakLMT", "peakFpe", "peakEccLoad", "peakComp",
           "eccWork", "tPeakPct"]
MARKERS = ["o", "s", "^", "D"]
COLORS = ["#1f77b4", "#d62728", "#e8a200", "#7e3f9e"]
PT, HIP_R = 0, 6


def setup_jp_font():
    cand = ["Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP"]
    avail = {f.name for f in font_manager.fontManager.ttflist}
    pick = next((c for c in cand if c in avail), None)
    if pick:
        matplotlib.rcParams["font.family"] = pick
    matplotlib.rcParams["axes.unicode_minus"] = False


def _get(o, *names):
    for n in names:
        o = getattr(o, n) if hasattr(o, n) else o[n]
    return o


def _mat_N(path):
    """Read optimumOutput.options.N from a result .mat (None on failure)."""
    try:
        m = loadmat(path, struct_as_record=False, squeeze_me=True,
                    variable_names=["optimumOutput"])
        return int(np.asarray(_get(m["optimumOutput"], "options", "N")).ravel()[0])
    except Exception:
        return None


def latest(tag, prefix="PelvisTD"):
    """Newest result .mat for (prefix, tag) whose mesh size == TARGET_N."""
    fs = sorted(glob.glob(os.path.join(RESULTS,
                f"pred_sprinting_data_*{prefix}_{tag}.mat")),
                key=os.path.getmtime, reverse=True)
    for p in fs:
        if _mat_N(p) == TARGET_N:
            return p
    return None


def op(name):
    """Output path in STUDY with the mesh SUFFIX inserted before the extension."""
    root, ext = os.path.splitext(name)
    return os.path.join(STUDY, f"{root}{SUFFIX}{ext}")


def _side_proxies(arrs, r, dt):
    """Per-side injury-risk proxies for muscle row r (1-based)."""
    i = r - 1
    lM = arrs["lMtilde"][i]
    vM = arrs["vMtilde"][i]
    Fpe = arrs["Fpetilde"][i]
    Fce = arrs["Fce"][i]
    FMv = arrs["FMvtilde"][i]
    Fiso = arrs["Fiso"][i]
    lMT = arrs["lMTk_lr"][i]
    ecc = np.maximum(0.0, vM)
    FceN = Fce / np.maximum(Fiso, 1e-9)
    eccLoad = ecc * FMv
    comp = lM * ecc * FceN
    ncol = len(lM)
    ix = int(np.argmax(lM))
    return {
        "peakLM": float(lM.max()),
        "peakLMT": float(lMT.max()),
        "peakFpe": float(Fpe.max()),
        "peakEccLoad": float(eccLoad.max()),
        "peakComp": float(comp.max()),
        "eccWork": float(np.sum(Fce * ecc) * dt),
        "tPeakPct": float(100.0 * ix / max(ncol - 1, 1)),
    }


def load_cond(off, tag, prefix="PelvisTD"):
    p = latest(tag, prefix)
    if not p:
        return None
    m = loadmat(p, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    q = np.asarray(_get(o, "optVars_nsc", "q"), dtype=float)
    arrs = {k: np.asarray(_get(o, "muscleValues", k), dtype=float)
            for k in ("lMtilde", "vMtilde", "Fpetilde", "Fce", "FMvtilde",
                      "Fiso", "lMTk_lr")}
    try:
        tt = float(np.asarray(_get(o, "optVars_nsc", "totalTime")).ravel()[0])
    except Exception:
        tt = 0.21
    dt = tt / max(arrs["lMtilde"].shape[1] - 1, 1)
    try:
        status = str(_get(o, "stats", "return_status"))
    except Exception:
        status = "?"
    try:
        speed = float(np.asarray(_get(o, "ave_speed")).ravel()[0])
    except Exception:
        speed = float((q[3, -1] - q[3, 0]) / tt)
    row = {
        "offset": off, "tag": tag, "status": status,
        "feasible": status == "Solve_Succeeded",
        "td_tilt": float(np.degrees(q[PT, 0])),
        "anterior": float(-np.degrees(q[PT, 0])),  # +deg of anterior tilt at TD
        "mean_tilt": float(np.degrees(np.mean(q[PT, :]))),
        "td_hipflex": float(np.degrees(q[HIP_R, 0])),
        "speed": speed, "step": float(q[3, -1] - q[3, 0]),
    }
    for mk, (lr, rr, _) in HAM.items():
        pl = _side_proxies(arrs, lr, dt)
        pr = _side_proxies(arrs, rr, dt)
        for pk in PROXIES:
            row[f"{mk}_{pk}"] = 0.5 * (pl[pk] + pr[pk])
    return row


def _dose_panel(ax, feas, infe, proxy, title, ylabel, nominal_x=None):
    xf = np.array([r["anterior"] for r in feas], dtype=float)
    for (mk, (_, _, lab)), mc, cl in zip(HAM.items(), MARKERS, COLORS):
        yf = [r[f"{mk}_{proxy}"] for r in feas]
        ax.plot(xf, yf, marker=mc, color=cl, lw=1.7, mfc=cl, label=lab, ms=6)
        for r in infe:
            ax.plot(r["anterior"], r[f"{mk}_{proxy}"], marker=mc, mfc="none",
                    mec="0.6", ms=7, lw=0)
    if nominal_x is not None:
        ax.axvline(nominal_x, color="0.5", ls="--", lw=1.0, zorder=0)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("接地時の骨盤前傾角（度、右ほど強い前傾）")
    ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(True, alpha=0.3)


def main():
    global TARGET_N, SUFFIX
    if len(sys.argv) > 1:
        TARGET_N = int(sys.argv[1])
    SUFFIX = "" if TARGET_N == 50 else f"_N{TARGET_N}"
    print(f"[mesh] analysing N={TARGET_N} (output suffix '{SUFFIX}')")
    setup_jp_font()
    rows = [r for off, tag, pre in CONDITIONS
            if (r := load_cond(off, tag, pre))]
    feas = [r for r in rows if r["feasible"]]
    infe = [r for r in rows if not r["feasible"]]
    ant_f = np.array([r["anterior"] for r in feas], dtype=float)
    # nominal (offset 0) anterior tilt = baseline marker on the dose axis
    nom_x = next((r["anterior"] for r in rows if r["offset"] == 0), None)

    # ---- summary CSV (extended) ----
    base_cols = ["offset", "tag", "status", "feasible", "td_tilt", "anterior",
                 "mean_tilt", "td_hipflex", "speed", "step"]
    proxy_cols = [f"{mk}_{pk}" for mk in HAM for pk in PROXIES]
    with open(op("pelvic_td_summary.csv"), "w", newline="",
              encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=base_cols + proxy_cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v)
                        for k, v in r.items()})
    print(f"wrote pelvic_td_summary{SUFFIX}.csv")

    # ---- slopes per proxy (per deg of ANTERIOR touchdown tilt) ----
    print("\n--- dose-response slopes (per deg anterior touchdown tilt) ---")
    for pk in ("peakLM", "peakLMT", "peakFpe", "peakEccLoad"):
        print(f"[{pk}]")
        for mk, (_, _, lab) in HAM.items():
            yf = [r[f"{mk}_{pk}"] for r in feas]
            s = np.polyfit(ant_f, yf, 1)[0] if len(ant_f) >= 2 else float("nan")
            print(f"   {lab:24s}: {s:+.5f}")

    # ---- fig1: headline lMtilde dose-response ----
    fig, ax = plt.subplots(figsize=(7.8, 5.0))
    _dose_panel(ax, feas, infe, "peakLM",
                "v3(TDPT): 接地骨盤前傾 → ハムの伸び（用量反応）",
                "peak 正規化筋線維長 lMtilde（左右平均）", nominal_x=nom_x)
    if nom_x is not None:
        ax.text(nom_x, ax.get_ylim()[0], " 基準(Nominal)", va="bottom",
                ha="left", fontsize=8, color="0.4", rotation=90)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(op("td_fig1_dose_hamstring.png"), dpi=150)
    plt.close(fig)

    # ---- fig2: speed vs anterior tilt (no infeasibility: speed stays flat) ----
    fig, ax = plt.subplots(figsize=(7.8, 5.0))
    ax.plot(ant_f, [r["speed"] for r in feas], "-o", color="#2ca02c", lw=1.8,
            label="達成トップ速度")
    for r in infe:
        ax.plot(r["anterior"], r["speed"], "x", color="#d62728", ms=10,
                label="不成立（infeasible）" if r is infe[0] else None)
    if nom_x is not None:
        ax.axvline(nom_x, color="0.5", ls="--", lw=1.0)
    sp = [r["speed"] for r in feas]
    ax.set_ylim(min(sp) - 0.6, max(sp) + 0.6)
    ax.set_xlabel("接地時の骨盤前傾角（度、右ほど強い前傾）")
    ax.set_ylabel("達成トップ速度（m/s）")
    ax.set_title("v3(TDPT): 速度は前傾でほぼ一定（減速なし・力学的限界なし）")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(op("td_fig2_speed_feasibility.png"), dpi=150)
    plt.close(fig)

    # ---- fig3: multi-proxy 2x2 ----
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 9.0))
    panels = [("peakLM", "筋線維長 lMtilde", "peak lMtilde"),
              ("peakLMT", "MTU長（腱込みの伸張）", "peak MTU長 (m)"),
              ("peakFpe", "受動張力 Fpetilde", "peak Fpetilde"),
              ("peakEccLoad", "伸張性負荷（活動下の伸張）", "peak 伸張性負荷")]
    for ax, (pk, title, ylabel) in zip(axes.ravel(), panels):
        _dose_panel(ax, feas, infe, pk, title, ylabel, nominal_x=nom_x)
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.suptitle("v3(TDPT): 接地骨盤前傾 → ハムストリング肉離れリスク（複数指標の用量反応）",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(op("td_fig3_multiproxy.png"), dpi=150)
    plt.close(fig)
    print("\nfigures written:", STUDY)

    # ---- console table ----
    print("\n TDtilt anterior status            hipflex speed | "
          "peakLM peakLMT peakFpe peakEcc  tPeak%")
    for r in rows:
        print(f"{r['td_tilt']:6.2f} {r['anterior']:6.2f}  {r['status']:<20s}"
              f"{r['td_hipflex']:7.2f}{r['speed']:7.2f} | "
              f"{r['bifemlh_peakLM']:.3f}  {r['bifemlh_peakLMT']:.3f}  "
              f"{r['bifemlh_peakFpe']:.3f}  {r['bifemlh_peakEccLoad']:.3f}  "
              f"{r['bifemlh_tPeakPct']:5.1f}   (bifemlh)")


if __name__ == "__main__":
    main()
