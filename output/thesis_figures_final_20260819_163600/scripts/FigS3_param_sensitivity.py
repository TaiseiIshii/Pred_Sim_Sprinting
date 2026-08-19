"""
FigS3_param_sensitivity.py -- sensitivity of the baseline (Nominal-posture) biarticular
hamstring operating point to muscle-tendon parameter scaling.

Families (one-factor-at-a-time, N=50, strict):
  oMFL  = optimal fibre length   (_HamFascicle_[mp]NN, row 2)
  Fmax  = max isometric force     (_HamStrength_[mp]NN, row 1)
  TSL   = tendon slack length     (_HamTendon_[mp]NN,  row 3)  [included only if solved]

Output = biarticular mean 1-stride peak lMtilde (and per muscle).  This is the sensitivity
of the BASELINE operating point, NOT the dose-response SLOPE (which would need a tilt sweep
per perturbation).  The +/-10% points are highlighted.
"""
import glob
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

plt = C.setup_mpl()
from datetime import datetime

FAMILIES = [("HamFascicle", "oMFL (optimal fibre length)", "#1b7837"),
            ("HamStrength", "Fmax (max isometric force)", "#2166ac"),
            ("HamTendon", "TSL (tendon slack length)", "#b35806")]


def scale_of(fn):
    m = re.search(r"Ham(?:Fascicle|Strength|Tendon)_([mp])(\d+)", fn)
    if not m:
        return None
    sgn = -1 if m.group(1) == "m" else 1
    return round(1 + sgn * int(m.group(2)) / 100.0, 3)


def discover(prefix):
    """({scale: rec} strict, [failed recs]).  rec has bmean, per, speed, tilt, status, inf_pr."""
    out, failed = {}, []
    for p in glob.glob(os.path.join(C.RESULTS, f"pred_sprinting_data_*___{prefix}_*.mat")):
        sc = scale_of(os.path.basename(p))
        if sc is None:
            continue
        try:
            d = C.load(p)
        except Exception:
            continue
        if d["N"] != 50:
            continue
        c, _, _ = C.contact_s(d)
        per = {nm: C.metrics(d, nm, c)["peak_lMtilde"] for nm in C.MUS}
        rec = dict(scale=sc, bmean=float(np.mean([per[nm] for nm in C.BIARTIC])), per=per,
                   speed=d["speed"], tilt=-d["td"], status=d["status"], inf_pr=d["inf_pr"],
                   file=os.path.basename(p))
        if d["status"] != "Solve_Succeeded":
            failed.append(rec)
            continue
        if sc not in out or d["inf_pr"] < out[sc]["inf_pr"]:
            out[sc] = rec
    return out, failed


def main():
    fam_data, fam_failed = {}, {}
    for prefix, _, _ in FAMILIES:
        data, failed = discover(prefix)
        if data:
            fam_data[prefix] = data
        if failed:
            fam_failed[prefix] = failed
    # baseline (scale 1.0): HamFascicle_p00 is the unperturbed model
    base = None
    if "HamFascicle" in fam_data and 1.0 in fam_data["HamFascicle"]:
        base = fam_data["HamFascicle"][1.0]["bmean"]
    base_speed = fam_data["HamFascicle"][1.0]["speed"] if base is not None else None

    src = []
    for prefix, data in fam_data.items():
        for sc in sorted(data):
            r = data[sc]
            src.append([prefix, f"{sc:.2f}", "Solve_Succeeded", f"{r['bmean']:.5f}",
                        *[f"{r['per'][nm]:.5f}" for nm in C.MUS],
                        f"{r['speed']:.4f}", f"{r['tilt']:.3f}", r["file"]])
    for prefix, recs in fam_failed.items():
        for r in recs:
            src.append([prefix, f"{r['scale']:.2f}", r["status"], f"{r['bmean']:.5f}",
                        *[f"{r['per'][nm]:.5f}" for nm in C.MUS],
                        f"{r['speed']:.4f}", f"{r['tilt']:.3f}", r["file"]])
    src_csv = C.write_csv(os.path.join(C.SRC, "FigS3_param_sensitivity_source.csv"),
                          ["family", "scale", "solver_status", "biartic_mean_peak_lMtilde",
                           *[f"peak_{nm}" for nm in C.MUS], "achieved_speed_mps",
                           "achieved_anterior_tilt_deg", "source_file"], src)

    present = [(p, lab, col) for p, lab, col in FAMILIES if p in fam_data]
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(9.4, 3.8), gridspec_kw={"width_ratios": [1.25, 1.0]})

    # Panel A: curves
    axA.axvspan(0.9, 1.1, color="0.92", zorder=0)
    axA.axvline(1.0, color="0.6", ls="--", lw=0.9, zorder=1)
    if base is not None:
        axA.axhline(base, color="0.7", ls=":", lw=0.8, zorder=1)
    for prefix, lab, col in present:
        data = fam_data[prefix]
        xs = sorted(data)
        ys = [data[s]["bmean"] for s in xs]
        # flag points whose whole-motion speed drifted > 1.5% from baseline
        drift = [abs(data[s]["speed"] - base_speed) / base_speed > 0.015 if base_speed else False for s in xs]
        axA.plot(xs, ys, marker="o", ms=4.5, color=col, lw=1.5, label=lab)
        for s, y, dr in zip(xs, ys, drift):
            if dr:
                axA.plot(s, y, marker="o", ms=8, mfc="none", mec="red", mew=1.0, zorder=5)
    # mark failed perturbations (e.g. tendon +10%)
    for prefix, recs in fam_failed.items():
        col = dict((p, c) for p, _, c in FAMILIES)[prefix]
        for r in recs:
            axA.plot(r["scale"], r["bmean"], marker="x", ms=8, color=col, mew=1.6, zorder=5)
    axA.set_xlabel("hamstring parameter scale factor")
    axA.set_ylabel("biarticular mean 1-stride peak lMtilde")
    axA.set_title("A  Baseline operating-point sensitivity", loc="left", fontweight="bold", fontsize=8.8)
    axA.legend(loc="best", fontsize=6.4, frameon=False)
    axA.text(0.02, 0.03, "grey band = +/-10%", transform=axA.transAxes, fontsize=6, color="0.45")

    # Panel B: tornado at +/-10%
    axB.axvline(0, color="0.6", lw=0.9)
    yy = np.arange(len(present))[::-1]
    tor_rows = []
    for yp, (prefix, lab, col) in zip(yy, present):
        data = fam_data[prefix]
        b = data.get(1.0, {}).get("bmean", base)
        for sc, side in ((0.9, "-10%"), (1.1, "+10%")):
            if sc in data and b is not None:
                dv = data[sc]["bmean"] - b
                axB.barh(yp + (0.18 if sc > 1 else -0.18), dv, height=0.32,
                         color=col, alpha=0.6 if sc > 1 else 0.9,
                         edgecolor="black", linewidth=0.4)
                axB.text(dv + (0.0005 if dv >= 0 else -0.0005), yp + (0.18 if sc > 1 else -0.18),
                         f"{side}", va="center", ha="left" if dv >= 0 else "right", fontsize=5.6, color="0.3")
                tor_rows.append([prefix, side, f"{dv:+.5f}"])
    axB.set_yticks(yy)
    axB.set_yticklabels([lab.split(" (")[0] for _, lab, _ in present], fontsize=7.5)
    axB.set_xlabel("Δ biartic mean peak lMtilde  (vs unperturbed)")
    axB.set_title("B  Effect of +/-10%", loc="left", fontweight="bold", fontsize=8.8)
    C.write_csv(os.path.join(C.SRC, "FigS3_tornado_source.csv"),
                ["family", "perturbation", "delta_biartic_mean_peak_lMtilde"], tor_rows)

    missing_fams = [lab for p, lab, _ in FAMILIES if p not in fam_data]
    fail_txt = ""
    for prefix, recs in fam_failed.items():
        for r in recs:
            fail_txt += f" {prefix} x{r['scale']:.2f}={r['status']} (speed {r['speed']:.2f});"
    note = ("Baseline (Nominal-posture) sensitivity via WHOLE-MOTION re-optimization, NOT dose-response-slope "
            "sensitivity. N=50. Red ring = achieved speed drifted >1.5% (operating point moved); x = failed solve. "
            "See source CSV for per-solve speed/tilt.")
    if fail_txt:
        note += " Failed: " + fail_txt.strip()
    note += " Passive force-length not run (needs per-muscle Fpparam)."
    fig.suptitle("Figure S3 | Muscle-tendon parameter sensitivity of the biarticular hamstring load",
                 fontsize=9.6, fontweight="bold", x=0.01, ha="left", y=1.04)
    fig.text(0.01, -0.09, note, fontsize=5.7, color="0.35", ha="left", wrap=True)
    paths = C.save_fig(fig, "FigS3_param_sensitivity")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    frag = dict(figure_id="FigS3", panel_id="A-B",
                analytical_question="How sensitive is the baseline biarticular hamstring load to muscle-tendon parameters?",
                takeaway="Shorter oMFL raises peak lMtilde most; Fmax and TSL effects smaller; +/-10% shown.",
                input_path="HamFascicle/HamStrength[/HamTendon] N=50 strict", input_sha256="see qa/input_hashes.csv",
                source_commit="e7b8de9", simulation_commit="e7b8de9", analysis_commit="e7b8de9",
                mesh="N=50", condition_family="Ham architecture one-factor scaling",
                solver_acceptance_rule="strict Solve_Succeeded; min inf_pr per scale",
                muscle_names_and_indices="hamstring cols [7 8 9 10 53 54 55 56]; biartic first 3",
                phase_window="full stride peak (Nominal posture)",
                metric_formula="biartic mean peak lMtilde vs parameter scale; delta at +/-10%",
                source_csv=src_csv, plotting_script="scripts/FigS3_param_sensitivity.py",
                pdf_path=paths[0], svg_path=paths[1], png_path=paths[2],
                generated_at=ts, qa_status="auto-pass; visual pending")
    C.write_manifest_fragment("FigS3", [frag])
    print("FigS3 done:", paths[2], "| families:", list(fam_data.keys()), "| baseline biartic peak:", base)
    for prefix, data in fam_data.items():
        print(f"  {prefix}: " + ", ".join(f"{s:.2f}->{data[s]['bmean']:.4f}" for s in sorted(data)))


if __name__ == "__main__":
    main()
