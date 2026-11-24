"""
analyze_pelvic_athlete_cross.py
Analysis for the individual x pelvic-tilt CROSS experiment (run via
run_pelvic_athlete_sweep). Tests the interaction: does the tilt -> hamstring
loading response differ by muscle architecture (Nominal vs short-fascicle vs
weak)?

Groups saved results by athlete:
  Nom = plain _PelvisShift_[mp]NN            (nominal architecture)
  Sh  = _PelvisShift_[mp]NN_athSh            (short fascicle, oMFL x0.80)
  Wk  = _PelvisShift_[mp]NN_athWk            (weak, Fmax x0.80)
and, per athlete, fits peak fascicle length & (Fmax-normalised) peak force vs
realised mean pelvis tilt. Divergent slopes => the optimal intervention is
architecture-dependent even for the SAME postural manipulation.

Reuses analyze_file() (metrics) and fmax_from_data() (capacity normalisation)
from the existing modules. Saved data only. If no combined conditions exist yet,
prints how to generate them.
"""
import glob
import os
import re

import numpy as np
from scipy.io import loadmat
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analyze_pelvic_force_eccentric import analyze_file, RESULTS
from analyze_individual_force import fmax_from_data, HAM_L, HAM_R

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(RESULTS, "PelvicAthlete_Study")
HAM = ["semimem", "semiten", "bifemlh"]
COL = {"Nom": "#333333", "Sh": "#d62728", "Wk": "#1f77b4"}
LAB = {"Nom": "Nominal", "Sh": "short-fascicle", "Wk": "weak"}


def athlete_of(name):
    if "_athSh" in name:
        return "Sh"
    if "_athWk" in name:
        return "Wk"
    if "PelvisShift" in name:
        return "Nom"
    return None


def ham_fmax(path):
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    mv = o.muscleValues
    Fpass = np.asarray(mv.Fpass, float)
    Fpet = np.asarray(mv.Fpetilde, float)
    fm = fmax_from_data(Fpass, Fpet)
    return {nm: 0.5 * (fm[HAM_L[i]] + fm[HAM_R[i]]) for i, nm in enumerate(
        ["semimem", "semiten", "bifemlh", "bifemsh"])}


def collect():
    seen = {}
    for f in glob.glob(os.path.join(RESULTS, "pred_sprinting_data_*PelvisShift*.mat")):
        tok = re.search(r"___(.+)\.mat$", os.path.basename(f))
        tok = tok.group(1) if tok else os.path.basename(f)
        if tok not in seen or os.path.getmtime(f) > os.path.getmtime(seen[tok]):
            seen[tok] = f
    rows = []
    for tok, f in seen.items():
        ath = athlete_of(tok)
        if ath is None:
            continue
        try:
            r = analyze_file(f)
            fm = ham_fmax(f)
        except Exception as e:  # noqa: BLE001
            print(f"[skip] {tok}: {e}")
            continue
        r["athlete"], r["cond"] = ath, tok
        for nm in HAM:
            r[f"{nm}_peakFceNorm"] = r[f"{nm}_peakFceN"] / fm[nm] if fm[nm] > 0 else np.nan
        rows.append(r)
    return rows


def _fit(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.size < 2:
        return np.nan, np.nan, np.nan
    s, b = np.polyfit(x, y, 1)
    yh = s * x + b
    r2 = 1 - np.sum((y - yh) ** 2) / np.sum((y - y.mean()) ** 2) if np.std(y) > 0 else np.nan
    return s, b, r2


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    rows = collect()
    ath_present = sorted({r["athlete"] for r in rows})
    combined = [a for a in ath_present if a in ("Sh", "Wk")]
    if not combined:
        print("=" * 78)
        print("No combined pelvic-tilt x athlete conditions found yet.")
        print("Generate them in MATLAB (each ~20-30 min, N=50):")
        print("  setup_paths; run_pelvic_athlete_sweep({'_PelvisShift_m02_athSh'})   % pilot")
        print("  run_pelvic_athlete_sweep   % Sh/Wk x several tilts")
        print("Then re-run this script.")
        print(f"(currently found only: {ath_present or 'nothing'})")
        return

    print("=" * 90)
    print("CROSS experiment: tilt -> hamstring loading, by athlete architecture")
    for ath in ["Nom", "Sh", "Wk"]:
        rr = sorted([r for r in rows if r["athlete"] == ath], key=lambda r: r["ptMean"])
        if not rr:
            continue
        print(f"\n{LAB[ath]} (n={len(rr)}): tilt "
              f"{min(r['ptMean'] for r in rr):.1f}..{max(r['ptMean'] for r in rr):.1f}, "
              f"speed {min(r['speed'] for r in rr):.2f}-{max(r['speed'] for r in rr):.2f}")
        for nm in HAM:
            x = [r["ptMean"] for r in rr]
            sL, _, r2L = _fit(x, [r[f"{nm}_peakLM"] for r in rr])
            sF, _, r2F = _fit(x, [r[f"{nm}_peakFceNorm"] for r in rr])
            print(f"  {nm:8s} peakLM slope {sL:+.4f}/deg (R2 {r2L:.2f}) | "
                  f"peakFceNorm slope {sF:+.4f}/deg (R2 {r2F:.2f})")

    # figure: peakLM & normalised force vs tilt, one line per athlete (semimem)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ath in ["Nom", "Sh", "Wk"]:
        rr = sorted([r for r in rows if r["athlete"] == ath], key=lambda r: r["ptMean"])
        if len(rr) < 2:
            continue
        x = [r["ptMean"] for r in rr]
        axes[0].plot(x, [r["semimem_peakLM"] for r in rr], "o-", color=COL[ath], label=LAB[ath])
        axes[1].plot(x, [r["semimem_peakFceNorm"] for r in rr], "o-", color=COL[ath], label=LAB[ath])
    for ax, t in zip(axes, ["semimembranosus peak fascicle length",
                            "semimembranosus peak force / Fmax"]):
        ax.set_xlabel("realised mean pelvis tilt (deg)  (- = anterior)")
        ax.set_title(t)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=9)
        ax.invert_xaxis()
    fig.suptitle("CROSS experiment: does the pelvic-tilt loading response depend on "
                 "hamstring architecture?", fontsize=11)
    fig.tight_layout()
    p = os.path.join(OUTDIR, "pelvic_athlete_cross.png")
    fig.savefig(p, dpi=150)
    print("\nwrote", os.path.relpath(p, HERE))


if __name__ == "__main__":
    main()
