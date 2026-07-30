"""
injury_metrics.py
==================
Fascicle-level hamstring injury-surrogate metrics for the saved predictive-
sprinting results (Research Question 1: "what is the mechanistically appropriate
injury surrogate, and where/when does strain localise?").

Motivation
----------
The existing analysis (probe_ham_metrics.py) reports peak normalised *fibre*
length (lMtilde), peak passive force (Fpetilde) and peak *MTU* length. Peak MTU
stretch is a crude injury proxy: the muscle-tendon UNIT can lengthen while the
contractile FASCICLE stays near-isometric, the tendon/aponeurosis absorbing the
excursion (Kalkhoven et al. 2023, Sports Med 53:2321-2346, PMID 37668895). Tissue
damage is driven by ACTIVE eccentric fascicle loading (Lieber & Friden 1993).

This module therefore derives, per hamstring and as bilateral means, from the
quantities already saved in optimumOutput.muscleValues:

  peak_lMtilde        peak normalised fibre length          (descending-limb stretch)
  fib_strain          normalised fibre excursion  (dlM / lMo)
  mtu_strain          normalised MTU excursion    (dlMT / mean lMT)
  fasc_mtu_ratio      dlM_fibre / dlMT            (Kalkhoven decoupling ratio;
                                                   ~0 -> tendon takes the stretch,
                                                   ~1 -> fibre takes the stretch)
  peak_Fpetilde       peak normalised passive fibre force
  ecc_work            active eccentric fibre work  = integral Fce * max(dlM/dt,0) dt  (J)
  peak_ecc_power      peak active eccentric fibre power = max(Fce * dlM/dt)           (W)
  peak_len_rate       peak fibre lengthening rate while lengthening  (1/s, per lMo)
  t_peak_pct          instant of peak fibre strain, % of the simulated interval
  peak_in_stance      True if peak fibre strain occurs during right-foot stance
                      (best-effort, from GRFs.R); None if undetectable

Everything is computed from saved data only -- no MATLAB, no re-simulation.

Hamstring rows in the 92-row muscle arrays (1-based MATLAB -> 0-based here):
  LEFT  semimem,semiten,bifemlh,bifemsh = 7,8,9,10  -> idx 6,7,8,9
  RIGHT                                  = 53,54,55,56 -> idx 52,53,54,55
"""
import glob
import os
import re

import numpy as np
from scipy.io import loadmat

RESULTS = os.path.join(os.path.dirname(__file__), "..", "Results")
HAM = ["semimem", "semiten", "bifemlh", "bifemsh"]
HAM_L = [6, 7, 8, 9]
HAM_R = [52, 53, 54, 55]
# Biarticular hamstrings (the stretch-injury-relevant group; bifemsh is
# monoarticular and used here as a mechanistic control).
BIARTIC = ["semimem", "semiten", "bifemlh"]


def _get(o, *names):
    for n in names:
        try:
            o = getattr(o, n)
        except AttributeError:
            o = o[n]
    return o


def _trap(y, x):
    """Trapezoidal integral, version-agnostic (avoids np.trapz/trapezoid churn)."""
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    if y.size < 2:
        return 0.0
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x)))


def _stance_mask_R(o, ncols):
    """Best-effort right-foot stance mask (bool [ncols]) from GRFs.R.

    The vertical component is taken as the column/row with the largest peak
    magnitude; stance = that component above 2% of its own peak. Returns None
    if GRFs.R is missing or its shape cannot be reconciled with ncols.
    """
    try:
        grf = np.asarray(_get(o, "GRFs", "R"), dtype=float)
    except Exception:
        return None
    if grf.ndim != 2:
        return None
    # Orient so that time is along axis 0.
    if grf.shape[0] != ncols and grf.shape[1] == ncols:
        grf = grf.T
    if grf.shape[0] != ncols:
        return None
    vert = grf[:, np.argmax(np.ptp(grf, axis=0))]
    peak = np.max(np.abs(vert))
    if not np.isfinite(peak) or peak <= 0:
        return None
    return np.abs(vert) > 0.02 * peak


def _musc_metrics(row, lMtilde, lM, lMT, Fce, Fpe, t, stance):
    """Fascicle-level metrics for a single muscle row."""
    lMt = np.asarray(lMtilde[row], dtype=float)
    lm = np.asarray(lM[row], dtype=float)
    lmt = np.asarray(lMT[row], dtype=float)
    fce = np.asarray(Fce[row], dtype=float)
    fpe = np.asarray(Fpe[row], dtype=float)

    # Optimal fibre length recovered from lM / lMtilde (constant per muscle).
    ratio = np.divide(lm, lMt, out=np.full_like(lm, np.nan), where=lMt > 0)
    lMo = float(np.nanmedian(ratio))

    fib_exc = float(lm.max() - lm.min())          # m
    mtu_exc = float(lmt.max() - lmt.min())         # m
    eps = 1e-9

    # Fibre lengthening velocity (m/s) from saved fibre length.
    dlmdt = np.gradient(lm, t)
    ecc = np.clip(dlmdt, 0.0, None)                # lengthening only
    ecc_power = fce * ecc                          # W (active eccentric power)

    i_peak = int(np.argmax(lMt))
    out = {
        "peak_lMtilde": float(lMt.max()),
        "fib_strain": fib_exc / lMo if lMo > 0 else np.nan,
        "mtu_strain": mtu_exc / (float(lmt.mean()) + eps),
        "fasc_mtu_ratio": fib_exc / (mtu_exc + eps),
        "peak_Fpetilde": float(fpe.max()),
        "ecc_work": _trap(np.where(dlmdt > 0, fce * dlmdt, 0.0), t),
        "peak_ecc_power": float(ecc_power.max()),
        "peak_len_rate": float((ecc / (lMo + eps)).max()),
        "t_peak_pct": 100.0 * float(t[i_peak]) / (float(t[-1]) + eps),
    }
    if stance is not None and stance.shape[0] == lMt.shape[0]:
        out["peak_in_stance"] = bool(stance[i_peak])
    else:
        out["peak_in_stance"] = None
    return out


def compute_injury_metrics(path):
    """Return a dict of bilateral-mean fascicle metrics per hamstring for one .mat."""
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    mv = _get(o, "muscleValues")
    lMtilde = np.asarray(_get(mv, "lMtilde"), dtype=float)
    lM = np.asarray(_get(mv, "lM"), dtype=float)
    lMT = np.asarray(_get(mv, "lMTk_lr"), dtype=float)
    Fce = np.asarray(_get(mv, "Fce"), dtype=float)
    Fpe = np.asarray(_get(mv, "Fpetilde"), dtype=float)

    ncols = lMtilde.shape[1]
    try:
        totalTime = float(_get(o, "optVars_nsc", "totalTime"))
    except Exception:
        totalTime = 1.0
    t = np.linspace(0.0, totalTime, ncols)
    stance = _stance_mask_R(o, ncols)

    out = {}
    for i, nm in enumerate(HAM):
        ml = _musc_metrics(HAM_L[i], lMtilde, lM, lMT, Fce, Fpe, t, stance)
        mr = _musc_metrics(HAM_R[i], lMtilde, lM, lMT, Fce, Fpe, t, stance)
        for k in ml:
            if k == "peak_in_stance":
                # Report stance-timing agreement (True only if BOTH legs peak in stance)
                out[nm + "_" + k] = (ml[k] and mr[k]) if ml[k] is not None else None
            else:
                out[nm + "_" + k] = 0.5 * (ml[k] + mr[k])

    try:
        out["speed"] = float(_get(o, "ave_speed"))
    except Exception:
        out["speed"] = np.nan
    try:
        q = np.asarray(_get(o, "optVars_nsc", "q"), dtype=float)
        out["meanTilt"] = float(np.degrees(q[0]).mean())
    except Exception:
        out["meanTilt"] = np.nan
    try:
        out["N"] = int(_get(o, "options", "N"))
    except Exception:
        out["N"] = None
    return out


def _collect(patterns):
    """Newest file per condition token matched from RESULTS."""
    seen = {}
    for pat in patterns:
        for f in glob.glob(os.path.join(RESULTS, pat)):
            key = os.path.basename(f)
            tok = re.search(r"___(.+)\.mat$", key)
            tok = tok.group(1) if tok else key
            if tok not in seen or os.path.getmtime(f) > os.path.getmtime(seen[tok]):
                seen[tok] = f
    return seen


def _sort_key(cond):
    m = re.search(r"([mp])(\d+)", cond)
    if not m:
        return (0, 0.0)
    return (1, (-1 if m.group(1) == "m" else 1) * float(m.group(2)))


def main():
    files = _collect([
        "pred_sprinting_data_*Nominal.mat",
        "pred_sprinting_data_*PelvisShift*.mat",
        "pred_sprinting_data_*PelvisTD_*.mat",
        "pred_sprinting_data_*HamFascicle*.mat",
        "pred_sprinting_data_*HamStrength*.mat",
    ])
    rows = []
    for cond, f in files.items():
        try:
            d = compute_injury_metrics(f)
        except Exception as e:  # noqa: BLE001 - report and continue
            print(f"[skip] {cond}: {e}")
            continue
        d["cond"] = cond
        rows.append(d)
    rows.sort(key=lambda r: _sort_key(r["cond"]))

    if not rows:
        print("No result .mat files found under", os.path.abspath(RESULTS))
        return

    def table(title, suffix, fmt="{:6.3f}"):
        hdr = f"{'cond':28s} {'tilt':>6s} {'speed':>6s} | " + \
            " ".join(f"{h[:4]:>7s}" for h in HAM)
        print("\n=== " + title + " ===")
        print(hdr)
        for r in rows:
            vals = " ".join(fmt.format(r[h + suffix]) for h in HAM)
            print(f"{r['cond']:28s} {r['meanTilt']:6.2f} {r['speed']:6.2f} | {vals}")

    table("peak normalised fibre length lMtilde (bilateral mean)", "_peak_lMtilde")
    table("fascicle:MTU excursion ratio  (Kalkhoven decoupling; low=tendon-dominated)",
          "_fasc_mtu_ratio")
    table("active eccentric fibre work (J, bilateral mean)", "_ecc_work")
    table("peak active eccentric fibre power (W, bilateral mean)", "_peak_ecc_power")
    table("peak passive fibre force Fpetilde (bilateral mean)", "_peak_Fpetilde")
    table("time of peak fibre strain (% of interval)", "_t_peak_pct", fmt="{:6.1f}")


if __name__ == "__main__":
    main()
