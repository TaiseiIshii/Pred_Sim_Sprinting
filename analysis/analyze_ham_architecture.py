"""
analyze_ham_architecture.py
===========================
Research Question 2 analysis: how do the principal MODIFIABLE epidemiological
hamstring-strain-injury (HSI) risk factors -- short biceps-femoris fascicle
length (Timmins 2016) and hamstring weakness -- reshape hamstring FASCICLE
strain and achievable top sprinting speed?

This is the epidemiology<->biomechanics bridge: each "virtual athlete"
(_HamFascicle_[mp]NN or _HamStrength_[mp]NN) re-optimises the same maximal
sprint with only the hamstring architecture changed. We then read the
fascicle-level injury surrogates (from injury_metrics.py) and build the
dose-response of injury risk and speed against the architecture factor.

Prediction to test (bridge): shorter fascicles (factor < 1) -> higher peak
fascicle strain / eccentric work at top speed, mechanistically reproducing the
epidemiological association between short BFlh fascicles and HSI.

Usage:
    python analyze_ham_architecture.py               # fascicle family (default)
    python analyze_ham_architecture.py strength      # strength family
Outputs a printed dose-response table and, if matplotlib is available, a figure
saved under Results/HamArch_Study/.
"""
import glob
import os
import re
import sys

import numpy as np

from injury_metrics import BIARTIC, RESULTS, compute_injury_metrics


def _factor_from_name(cond):
    """_HamFascicle_m20 -> 0.80 ; p10 -> 1.10 ; p00/Nominal -> 1.00."""
    m = re.search(r"Ham(?:Fascicle|Strength)_([mp])(\d+)", cond)
    if not m:
        return 1.0  # Nominal is the factor-1.0 reference
    s = -1 if m.group(1) == "m" else 1
    return 1.0 + s * int(m.group(2)) / 100.0


def collect(mode, target_N=50):
    """Newest result per condition for Nominal + the requested Ham* family.

    Restricted to a single mesh size (target_N) so the dose-response is
    mesh-consistent; pass target_N=None to include every mesh.
    """
    files = {}
    pats = ["pred_sprinting_data_*Nominal.mat",
            f"pred_sprinting_data_*Ham{mode}*.mat"]
    for pat in pats:
        for f in glob.glob(os.path.join(RESULTS, pat)):
            tok = re.search(r"___(.+)\.mat$", os.path.basename(f))
            tok = tok.group(1) if tok else os.path.basename(f)
            if tok not in files or os.path.getmtime(f) > os.path.getmtime(files[tok]):
                files[tok] = f
    rows = []
    for tok, f in files.items():
        try:
            d = compute_injury_metrics(f)
        except Exception as e:  # noqa: BLE001
            print(f"[skip] {tok}: {e}")
            continue
        if target_N is not None and d.get("N") not in (target_N, None):
            continue
        d["cond"] = tok
        d["factor"] = _factor_from_name(tok)
        # Biarticular-mean fascicle-level injury surrogates.
        d["biartic_peak_lMtilde"] = float(np.mean([d[m + "_peak_lMtilde"] for m in BIARTIC]))
        d["biartic_ecc_work"] = float(np.mean([d[m + "_ecc_work"] for m in BIARTIC]))
        d["biartic_fasc_mtu"] = float(np.mean([d[m + "_fasc_mtu_ratio"] for m in BIARTIC]))
        rows.append(d)
    rows.sort(key=lambda r: r["factor"])
    return rows


def print_table(rows, mode):
    label = "fibre-length" if mode == "Fascicle" else "strength"
    print(f"\n=== RQ2 dose-response: hamstring {label} factor vs injury surrogate & speed ===")
    print(f"{'cond':24s} {'factor':>6s} {'speed':>6s} {'peakLMtil':>9s} "
          f"{'eccWork':>8s} {'fasc:MTU':>8s}")
    for r in rows:
        print(f"{r['cond']:24s} {r['factor']:6.2f} {r['speed']:6.2f} "
              f"{r['biartic_peak_lMtilde']:9.3f} {r['biartic_ecc_work']:8.2f} "
              f"{r['biartic_fasc_mtu']:8.3f}")
    # Dose-response slopes (per unit factor) via least squares.
    if len(rows) >= 2:
        x = np.array([r["factor"] for r in rows])
        for key, name in [("biartic_peak_lMtilde", "peak fascicle strain"),
                          ("biartic_ecc_work", "eccentric work"),
                          ("speed", "top speed")]:
            y = np.array([r[key] for r in rows])
            slope = np.polyfit(x, y, 1)[0]
            print(f"  d({name})/d(factor) = {slope:+.3f}")


def make_plot(rows, mode):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:  # noqa: BLE001
        print(f"[plot skipped] matplotlib unavailable: {e}")
        return
    if len(rows) < 2:
        print("[plot skipped] need >=2 conditions")
        return
    x = np.array([r["factor"] for r in rows])
    label = "fibre-length" if mode == "Fascicle" else "strength"
    fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    ax[0].plot(x, [r["biartic_peak_lMtilde"] for r in rows], "o-", color="crimson")
    ax[0].set_ylabel("peak fascicle strain (norm. fibre length)")
    ax[0].set_title("Injury surrogate")
    ax[1].plot(x, [r["biartic_ecc_work"] for r in rows], "s-", color="darkorange")
    ax[1].set_ylabel("active eccentric fibre work (J)")
    ax[1].set_title("Eccentric loading")
    ax[2].plot(x, [r["speed"] for r in rows], "^-", color="navy")
    ax[2].set_ylabel("top speed (m/s)")
    ax[2].set_title("Performance")
    for a in ax:
        a.axvline(1.0, ls="--", color="grey", lw=1)
        a.set_xlabel(f"hamstring {label} factor")
        a.grid(alpha=0.3)
    fig.suptitle(f"RQ2: hamstring {label} shapes the speed-injury trade-off "
                 f"(biarticular mean)", fontsize=12)
    fig.tight_layout()
    outdir = os.path.join(RESULTS, "HamArch_Study")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"rq2_doseresponse_{mode.lower()}.png")
    fig.savefig(out, dpi=140)
    print(f"\nFigure saved: {out}")


def main():
    mode = "Fascicle"
    if len(sys.argv) > 1 and sys.argv[1].lower().startswith("s"):
        mode = "Strength"
    rows = collect(mode)
    if not rows:
        print("No results found under", os.path.abspath(RESULTS))
        return
    print_table(rows, mode)
    make_plot(rows, mode)


if __name__ == "__main__":
    main()
