"""
analyze_athlete_tilt_interaction.py
Cross-experiment (pilot) as a 2x2 INTERACTION: does anterior pelvic tilt load
the hamstrings MORE in a short-fascicle athlete than in a nominal one?

Four cells (all re-optimised, N=50, roughly speed-matched):
  (Nom, baseline tilt ~-7.3 deg)  = Nominal
  (Nom, anterior   ~-9.2 deg)     = _PelvisShift_m02
  (Sh , baseline   ~-7.3 deg)     = _HamFascicle_m20      (short fascicle, offset 0)
  (Sh , anterior   ~-9.3 deg)     = _PelvisShift_m02_athSh (short fascicle + tilt)

Reports, for the biarticular hamstrings (bilateral mean), peak fascicle length,
peak contractile force (N and /Fmax) and eccentric peak force, plus:
  tilt effect within each architecture, architecture effect at each tilt, and
  the INTERACTION = (Sh tilt effect) - (Nom tilt effect).

Saved data only. Fmax recovered self-consistently as Fpass/Fpetilde.
"""
import glob
import os

import numpy as np
from scipy.io import loadmat
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analyze_pelvic_force_eccentric import analyze_file, RESULTS
from analyze_individual_force import fmax_from_data, HAM_L, HAM_R

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(RESULTS, "PelvicAthlete_Study")
BIARTIC = ["semimem", "semiten", "bifemlh"]

CELLS = {
    ("Nom", "base"): "pred_sprinting_data_*04-February-2026*Nominal.mat",
    ("Nom", "ant"):  "pred_sprinting_data_*___PelvisShift_m02.mat",
    ("Sh", "base"):  "pred_sprinting_data_*___HamFascicle_m20.mat",
    ("Sh", "ant"):   "pred_sprinting_data_*___PelvisShift_m02_athSh.mat",
}


def newest(pat):
    fs = glob.glob(os.path.join(RESULTS, pat))
    return max(fs, key=os.path.getmtime) if fs else None


def ham_fmax(path):
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    mv = m["optimumOutput"].muscleValues
    fm = fmax_from_data(np.asarray(mv.Fpass, float), np.asarray(mv.Fpetilde, float))
    return {nm: 0.5 * (fm[HAM_L[i]] + fm[HAM_R[i]])
            for i, nm in enumerate(["semimem", "semiten", "bifemlh", "bifemsh"])}


def cell_metrics(path):
    r = analyze_file(path)
    fm = ham_fmax(path)
    out = {"speed": r["speed"], "ptMean": r["ptMean"]}
    # biarticular bilateral-mean aggregates
    out["peakLM"] = float(np.mean([r[f"{nm}_peakLM"] for nm in BIARTIC]))
    out["peakFceN"] = float(np.mean([r[f"{nm}_peakFceN"] for nm in BIARTIC]))
    out["eccPeakFceN"] = float(np.mean([r[f"{nm}_eccPeakFceN"] for nm in BIARTIC]))
    out["peakFceNorm"] = float(np.mean([r[f"{nm}_peakFceN"] / fm[nm] for nm in BIARTIC]))
    out["eccPeakFceNorm"] = float(np.mean([r[f"{nm}_eccPeakFceN"] / fm[nm] for nm in BIARTIC]))
    out["_per"] = {nm: {"peakLM": r[f"{nm}_peakLM"],
                        "peakFceNorm": r[f"{nm}_peakFceN"] / fm[nm]} for nm in BIARTIC}
    return out


def main():
    data = {}
    for key, pat in CELLS.items():
        f = newest(pat)
        if f is None:
            print(f"[missing] cell {key}: no file for {pat}")
            continue
        data[key] = cell_metrics(f)

    need = [("Nom", "base"), ("Nom", "ant"), ("Sh", "base"), ("Sh", "ant")]
    if not all(k in data for k in need):
        print("Incomplete 2x2; have:", list(data.keys()))
        return

    print("=" * 88)
    print("2x2 CROSS: anterior pelvic tilt x hamstring architecture (biarticular mean)")
    print(f"\n{'cell':22s}{'ptMean':>8s}{'speed':>7s}{'peakLM':>8s}"
          f"{'FceNorm':>8s}{'eccFNorm':>9s}{'peakFceN':>9s}")
    for k in need:
        d = data[k]
        lab = f"{k[0]}/{k[1]}"
        print(f"{lab:22s}{d['ptMean']:8.2f}{d['speed']:7.2f}{d['peakLM']:8.3f}"
              f"{d['peakFceNorm']:8.3f}{d['eccPeakFceNorm']:9.3f}{d['peakFceN']:9.0f}")

    print("\n--- effects PER DEGREE of anterior tilt (baselines are at DIFFERENT tilt: "
          f"Nom {data[('Nom','base')]['ptMean']:.1f}, Sh {data[('Sh','base')]['ptMean']:.1f}) ---")
    dt_nom = data[("Nom", "base")]["ptMean"] - data[("Nom", "ant")]["ptMean"]   # deg more anterior
    dt_sh = data[("Sh", "base")]["ptMean"] - data[("Sh", "ant")]["ptMean"]
    print(f"  tilt step: Nom {dt_nom:.2f} deg (2 pts), Sh {dt_sh:.2f} deg (2 pts)")
    for metric, lab in (("peakLM", "peak fascicle length"),
                        ("peakFceNorm", "peak force / Fmax"),
                        ("eccPeakFceNorm", "eccentric peak force / Fmax")):
        nom_pd = (data[("Nom", "ant")][metric] - data[("Nom", "base")][metric]) / dt_nom
        sh_pd = (data[("Sh", "ant")][metric] - data[("Sh", "base")][metric]) / dt_sh
        print(f"  {lab:28s}  Nom {nom_pd:+.4f}/deg | Sh {sh_pd:+.4f}/deg | "
              f"ratio {sh_pd/nom_pd:+.2f}x" if abs(nom_pd) > 1e-6 else
              f"  {lab:28s}  Nom {nom_pd:+.4f}/deg | Sh {sh_pd:+.4f}/deg")

    print("\n--- CLEAN comparison at MATCHED anterior tilt "
          f"(Nom {data[('Nom','ant')]['ptMean']:.1f} vs Sh {data[('Sh','ant')]['ptMean']:.1f} deg) ---")
    for metric, lab in (("peakLM", "peak fascicle length"),
                        ("peakFceNorm", "peak force / Fmax"),
                        ("eccPeakFceNorm", "eccentric peak force / Fmax")):
        nv, sv = data[("Nom", "ant")][metric], data[("Sh", "ant")][metric]
        print(f"  {lab:28s}  Nom {nv:.3f} | Sh {sv:.3f} | diff {sv-nv:+.3f}")
    print("  CAVEAT: pilot = 1 short-fascicle tilt point; per-degree slope is a 2-point "
          "estimate. A full tilt x architecture interaction needs Sh swept across tilts.")

    # per-muscle peakLM interaction
    print("\n--- per-muscle peak fascicle length tilt effect ---")
    print(f"{'muscle':10s}{'Nom dTilt':>11s}{'Sh dTilt':>10s}{'interaction':>13s}")
    for nm in BIARTIC:
        nt = data[("Nom", "ant")]["_per"][nm]["peakLM"] - data[("Nom", "base")]["_per"][nm]["peakLM"]
        st = data[("Sh", "ant")]["_per"][nm]["peakLM"] - data[("Sh", "base")]["_per"][nm]["peakLM"]
        print(f"{nm:10s}{nt:+11.4f}{st:+10.4f}{st-nt:+13.4f}")

    # figure: interaction plot using ACTUAL realised tilt (baselines differ!)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for metric, ax, ylab in (("peakLM", axes[0], "peak fascicle length (biartic mean)"),
                             ("peakFceNorm", axes[1], "peak force / Fmax (biartic mean)")):
        for ath, col in (("Nom", "#333333"), ("Sh", "#d62728")):
            xs = [data[(ath, "base")]["ptMean"], data[(ath, "ant")]["ptMean"]]
            ys = [data[(ath, "base")][metric], data[(ath, "ant")][metric]]
            ax.plot(xs, ys, "o-", color=col, label={"Nom": "Nominal", "Sh": "short-fascicle"}[ath])
        ax.set_xlabel("realised mean pelvis tilt (deg)  (- = anterior)")
        ax.set_ylabel(ylab)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=9)
        ax.invert_xaxis()
    fig.suptitle("Pilot 2x2 (actual tilt; Sh baseline sits at less-anterior tilt): "
                 "short athlete higher strain, lower normalised force", fontsize=10)
    fig.tight_layout()
    p = os.path.join(OUTDIR, "athlete_tilt_interaction.png")
    fig.savefig(p, dpi=150)
    print("\nwrote", os.path.relpath(p, HERE))


if __name__ == "__main__":
    main()
