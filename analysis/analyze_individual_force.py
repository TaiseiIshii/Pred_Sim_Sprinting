"""
analyze_individual_force.py
STEP 8 (weight sensitivity) + STEP 9 (individualised injury-reducing technique,
now on the FORCE axis) for Experiment 2.

Three athlete archetypes re-optimised with the biarticular-hamstring fascicle-
overstretch penalty swept 0..3.2 (wJ13):
  Nom = nominal architecture
  Sh  = short fascicle  (optimal fibre length x0.80, HamFascicle_m20 base)
  Wk  = weak            (max isometric force  x0.80, HamStrength_m20 base)

The existing pareto analysis compares them on peak *fibre length* (strain
surrogate) only. Here we add the ABSOLUTE and CAPACITY-NORMALISED FORCE axis the
supervisor asked for, recovering each muscle's max isometric force self-
consistently from saved data as  Fmax = FT / FTtilde  (tendon force / normalised
tendon force), so the Weak model (Fmax x0.80) is compared fairly.

Outputs: Results/HamPareto_Study/individual_force.csv, fig7_individual_optima.png.
Saved data only; nothing re-simulated or overwritten.
"""
import glob
import os
import re

import numpy as np
from scipy.io import loadmat
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "Results")
OUTDIR = os.path.join(RESULTS, "HamPareto_Study")

HAM = ["semimem", "semiten", "bifemlh", "bifemsh"]
HAM_L = [6, 7, 8, 9]
HAM_R = [52, 53, 54, 55]
BIARTIC_IDX = [0, 1, 2]                       # semimem, semiten, bifemlh
ATHLETES = ["Nom", "Sh", "Wk"]
ATH_LABEL = {"Nom": "Nominal", "Sh": "short-fascicle", "Wk": "weak"}
ATH_COLOR = {"Nom": "#333333", "Sh": "#d62728", "Wk": "#1f77b4"}
BASE_PATTERN = {
    "Nom": "pred_sprinting_data_*HamPareto_Nom_w0000.mat",
    "Sh": "pred_sprinting_data_*HamFascicle_m20.mat",
    "Wk": "pred_sprinting_data_*HamStrength_m20.mat",
}


def _get(o, *names):
    for n in names:
        try:
            o = getattr(o, n)
        except AttributeError:
            o = o[n]
    return o


def _trap(y, x):
    y = np.asarray(y, float)
    x = np.asarray(x, float)
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x))) if y.size > 1 else 0.0


def fmax_from_data(Fpass, Fpetilde):
    """Fmax per muscle = median(Fpass / Fpetilde).

    Fpass = FMo * Fpetilde (both are muscleValues on the SAME collocation grid,
    so this avoids the mesh/collocation misalignment of FT vs the FTtilde state).
    Uses only well-conditioned samples (meaningful passive stretch).
    """
    out = np.full(Fpass.shape[0], np.nan)
    for r in range(Fpass.shape[0]):
        mask = Fpetilde[r] > 1e-3
        if mask.sum() >= 3:
            out[r] = np.median(Fpass[r, mask] / Fpetilde[r, mask])
    return out


def analyze(path):
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    mv = _get(o, "muscleValues")
    Fce = np.asarray(_get(mv, "Fce"), float)
    FT = np.asarray(_get(mv, "FT"), float)
    Fpass = np.asarray(_get(mv, "Fpass"), float)
    Fpet = np.asarray(_get(mv, "Fpetilde"), float)
    lMt = np.asarray(_get(mv, "lMtilde"), float)
    lM = np.asarray(_get(mv, "lM"), float)
    tt = float(_get(o, "optVars_nsc", "totalTime"))
    t = np.linspace(0, tt, lMt.shape[1])
    Fmax = fmax_from_data(Fpass, Fpet)

    def musc(row):
        fce = Fce[row]
        dlmdt = np.gradient(lM[row], t)
        leng = dlmdt > 0
        fm = Fmax[row] if np.isfinite(Fmax[row]) and Fmax[row] > 0 else np.nan
        return {
            "peakLM": float(lMt[row].max()),
            "peakFceN": float(fce.max()),
            "peakFceNorm": float(fce.max() / fm) if fm == fm else np.nan,
            "peakFpet": float(Fpet[row].max()),
            "eccPeakFceN": float(np.where(leng, fce, 0).max()),
            "eccPeakFceNorm": float(np.where(leng, fce, 0).max() / fm) if fm == fm else np.nan,
            "eccWorkJ": _trap(np.where(leng, fce * dlmdt, 0), t),
            "Fmax": float(fm),
        }

    # bilateral mean of the biarticular hamstrings
    agg = {}
    keys = musc(HAM_L[0]).keys()
    for j in BIARTIC_IDX:
        mL, mR = musc(HAM_L[j]), musc(HAM_R[j])
        for k in keys:
            agg.setdefault(k, []).append(0.5 * (mL[k] + mR[k]))
    row = {k: float(np.mean(v)) for k, v in agg.items()}
    row["speed"] = float(_get(o, "ave_speed"))
    # per-muscle biarticular peak force (N) for the breakdown
    for j in BIARTIC_IDX:
        mm = HAM[j]
        row[f"{mm}_peakFceN"] = 0.5 * (musc(HAM_L[j])["peakFceN"] + musc(HAM_R[j])["peakFceN"])
        row[f"{mm}_peakFceNorm"] = 0.5 * (musc(HAM_L[j])["peakFceNorm"] + musc(HAM_R[j])["peakFceNorm"])
    return row


def parse_cond(name):
    m = re.search(r"HamPareto_(Nom|Sh|Wk)_w(\d+)", name)
    if m:
        return m.group(1), int(m.group(2)) / 1000.0
    return None, None


def collect():
    seen = {}
    for f in glob.glob(os.path.join(RESULTS, "pred_sprinting_data_*HamPareto*.mat")):
        ath, wt = parse_cond(os.path.basename(f))
        if ath is None:
            continue
        key = (ath, wt)
        if key not in seen or os.path.getmtime(f) > os.path.getmtime(seen[key]):
            seen[key] = f
    by = {a: [] for a in ATHLETES}
    for (ath, wt), f in seen.items():
        try:
            r = analyze(f)
        except Exception as e:  # noqa: BLE001
            print(f"[skip] {os.path.basename(f)}: {e}")
            continue
        r["athlete"], r["weight"] = ath, wt
        by[ath].append(r)
    for ath in ATHLETES:
        if not any(abs(r["weight"]) < 1e-9 for r in by[ath]):
            fs = glob.glob(os.path.join(RESULTS, BASE_PATTERN[ath]))
            if fs:
                bf = max(fs, key=os.path.getmtime)
                try:
                    r = analyze(bf)
                    r["athlete"], r["weight"] = ath, 0.0
                    by[ath].append(r)
                except Exception as e:  # noqa: BLE001
                    print(f"[base skip] {ath}: {e}")
        by[ath].sort(key=lambda r: r["weight"])
    return by


def main():
    by = collect()
    if not any(by[a] for a in ATHLETES):
        print("No HamPareto results found.")
        return

    # ---- Fmax self-check ---------------------------------------------------
    print("=" * 90)
    print("Fmax recovered as FT/FTtilde (biarticular ham, N) -- should match model max iso force:")
    for ath in ATHLETES:
        if by[ath]:
            fm = by[ath][0]["Fmax"]
            print(f"  {ATH_LABEL[ath]:16s} base biartic-mean Fmax = {fm:7.0f} N")

    # ---- STEP 9 tables + STEP 8 sensitivity --------------------------------
    for ath in ATHLETES:
        rows = by[ath]
        if len(rows) < 2:
            continue
        base = next(r for r in rows if abs(r["weight"]) < 1e-9)
        s0, l0, f0 = base["speed"], base["peakLM"], base["peakFceNorm"]
        print("\n" + "=" * 90)
        print(f"STEP 9  {ATH_LABEL[ath]} athlete: injury-reducing technique on FORCE axis "
              f"(biarticular ham)")
        print(f"{'wJ13':>6s}{'speed':>7s}{'dSpd%':>7s}{'peakLM':>8s}{'dLM%':>7s}"
              f"{'FceNorm':>8s}{'dFce%':>7s}{'eccFN':>7s}{'peakFceN':>9s}")
        for r in rows:
            dS = 100 * (s0 - r["speed"]) / s0
            dL = 100 * (l0 - r["peakLM"]) / l0
            dF = 100 * (f0 - r["peakFceNorm"]) / f0 if f0 else np.nan
            print(f"{r['weight']:6.2f}{r['speed']:7.3f}{dS:7.2f}{r['peakLM']:8.3f}{dL:7.2f}"
                  f"{r['peakFceNorm']:8.3f}{dF:7.2f}{r['eccPeakFceNorm']:7.3f}{r['peakFceN']:9.0f}")
        # STEP 8: monotonicity of strain vs weight (no non-physical reversals)
        lms = [r["peakLM"] for r in rows]
        mono = all(lms[i] >= lms[i + 1] - 1e-3 for i in range(len(lms) - 1))
        print(f"  STEP8 sensitivity: peakLM monotered decreasing with weight = {mono} "
              f"(range {min(lms):.3f}-{max(lms):.3f}); speed range "
              f"{min(r['speed'] for r in rows):.2f}-{max(r['speed'] for r in rows):.2f}")

    # ---- Figure 7 ----------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ath in ATHLETES:
        rows = by[ath]
        if len(rows) < 2:
            continue
        sp = [r["speed"] for r in rows]
        lm = [r["peakLM"] for r in rows]
        fn = [r["peakFceNorm"] for r in rows]
        c = ATH_COLOR[ath]
        axes[0].plot(sp, lm, "o-", color=c, label=ATH_LABEL[ath])
        axes[1].plot(sp, fn, "o-", color=c, label=ATH_LABEL[ath])
        # mark weight-0 (untreated) with a ring
        axes[0].plot(sp[0], lm[0], "o", mfc="none", mec=c, ms=13, mew=2)
        axes[1].plot(sp[0], fn[0], "o", mfc="none", mec=c, ms=13, mew=2)
    axes[0].set_xlabel("sprint speed (m/s)")
    axes[0].set_ylabel("peak norm. fascicle length $\\tilde l_M$ (strain surrogate)")
    axes[0].set_title("Speed vs fascicle-strain frontier")
    axes[1].set_xlabel("sprint speed (m/s)")
    axes[1].set_ylabel("peak contractile force / $F_{max}$ (capacity use)")
    axes[1].set_title("Speed vs normalised peak force")
    for ax in axes:
        ax.grid(alpha=0.3)
        ax.legend(fontsize=9)
        ax.invert_xaxis()          # slower (safer) to the right
    fig.suptitle("Figure 7  Individualised injury-reducing technique frontiers "
                 "(open ring = untreated; penalty weight increases along each curve)",
                 fontsize=11)
    fig.tight_layout()
    figp = os.path.join(OUTDIR, "fig7_individual_optima.png")
    fig.savefig(figp, dpi=150)
    print("\nwrote", os.path.relpath(figp, HERE))

    # ---- CSV ---------------------------------------------------------------
    cols = ["athlete", "weight", "speed", "peakLM", "peakFceN", "peakFceNorm",
            "peakFpet", "eccPeakFceN", "eccPeakFceNorm", "eccWorkJ", "Fmax",
            "semimem_peakFceN", "semiten_peakFceN", "bifemlh_peakFceN",
            "semimem_peakFceNorm", "semiten_peakFceNorm", "bifemlh_peakFceNorm"]
    outcsv = os.path.join(OUTDIR, "individual_force.csv")
    with open(outcsv, "w", encoding="utf-8") as fh:
        fh.write(",".join(cols) + "\n")
        for ath in ATHLETES:
            for r in by[ath]:
                fh.write(",".join(str(r.get(c, "")) for c in cols) + "\n")
    print("wrote", os.path.relpath(outcsv, HERE))


if __name__ == "__main__":
    main()
