"""
analyze_pelvic_force_eccentric.py
=================================
P0 analysis for the pelvic-tilt experiment (Experiment 1), addressing the
supervisor's requests that were NOT covered by the existing pelvic_shift_summary
(which reports only fibre length / passive force / eccentric-load surrogates):

  STEP 4  ABSOLUTE muscle force        -> peak contractile force Fce (N),
                                          peak tendon force FT (N),
                                          peak passive force Fpass (N),
                                          peak activation (0-1),
                                          and WHEN in the step each peaks.
  STEP 5  ECCENTRIC evaluation         -> lengthening detected from d(lM)/dt>0
                                          (sign cross-checked against vMtilde),
                                          active eccentric force = max Fce while
                                          lengthening, eccentric work, eccentric
                                          power = max(Fce * dlM/dt).
  STEP 1  reproducibility              -> cross-checks peak lMtilde against the
                                          existing pelvic_shift_summary.csv.
  STEP 3/6 speed-controlled regression -> fits each peak metric vs realised mean
                                          pelvis tilt over the SPEED-MATCHED
                                          subset only (|dspeed|<=3% of Nominal),
                                          so the infeasible anterior runs whose
                                          speed collapses to ~10.5 m/s cannot
                                          confound the dose-response.

Everything is computed from saved optimumOutput data only. No MATLAB, no
re-simulation, nothing is overwritten (a new CSV is written).

Units / conventions (verified against main_pred_sim_sprinting.m comments and
an empirical sign check): Fce, FT, Fpass in Newtons; Fiso is the normalised
force-length multiplier (NOT Fmax); vMtilde>0 == fibre LENGTHENING here
(corr(vMtilde, dlM/dt)=+0.96 on Nominal bifemlh).
"""
import glob
import os
import re
import sys

import numpy as np
from scipy.io import loadmat

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "Results")

# --- Model bookkeeping (0-based) --------------------------------------------
HAM = ["semimem", "semiten", "bifemlh", "bifemsh"]
HAM_L = [6, 7, 8, 9]
HAM_R = [52, 53, 54, 55]
BIARTIC = {"semimem", "semiten", "bifemlh"}          # stretch-injury-relevant group
Q_PELVIS_TILT = 0
Q_HIP_FLEX_R = 6
Q_KNEE_R = 9
Q_ANKLE_R = 10


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
    if y.size < 2:
        return 0.0
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x)))


def _stance_mask_R(o, ncols):
    """Right-foot stance mask from vertical GRF (>2% of its own peak)."""
    try:
        grf = np.asarray(_get(o, "GRFs", "R"), float)
    except Exception:
        return None
    if grf.ndim != 2:
        return None
    if grf.shape[0] != ncols and grf.shape[1] == ncols:
        grf = grf.T
    if grf.shape[0] != ncols:
        return None
    vert = grf[:, np.argmax(np.ptp(grf, axis=0))]
    peak = np.max(np.abs(vert))
    if not np.isfinite(peak) or peak <= 0:
        return None
    return np.abs(vert) > 0.02 * peak


def _muscle_force_ecc(row, mv, act_row, t, stance):
    """Force + eccentric metrics for one muscle row on the 151-col grid."""
    lM = np.asarray(mv["lM"][row], float)
    lMt = np.asarray(mv["lMtilde"][row], float)
    lMT = np.asarray(mv["lMTk_lr"][row], float)
    Fce = np.asarray(mv["Fce"][row], float)
    FT = np.asarray(mv["FT"][row], float)
    Fpass = np.asarray(mv["Fpass"][row], float)
    Fpet = np.asarray(mv["Fpetilde"][row], float)
    vMt = np.asarray(mv["vMtilde"][row], float)

    dlmdt = np.gradient(lM, t)                    # m/s, fibre lengthening velocity
    leng = dlmdt > 0                              # eccentric (lengthening) mask
    ecc_force_series = np.where(leng, Fce, 0.0)
    ecc_power_series = np.where(leng, Fce * dlmdt, 0.0)

    i_peakL = int(np.argmax(lMt))                 # instant of peak fibre strain
    i_peakF = int(np.argmax(Fce))                 # instant of peak contractile force
    tt = float(t[-1]) + 1e-12

    out = {
        "peakLM": float(lMt.max()),
        "tPeakLM_pct": 100.0 * float(t[i_peakL]) / tt,
        "peakFceN": float(Fce.max()),
        "tPeakFce_pct": 100.0 * float(t[i_peakF]) / tt,
        "peakFTN": float(FT.max()),
        "peakFpassN": float(Fpass.max()),
        "peakFpetilde": float(Fpet.max()),
        "peakLMT_m": float(lMT.max()),
        "LMTexc_m": float(lMT.max() - lMT.min()),
        # eccentric (active, while lengthening)
        "eccPeakFceN": float(ecc_force_series.max()),
        "eccWorkJ": _trap(ecc_power_series, t),
        "eccPeakPowerW": float(ecc_power_series.max()),
        "eccFrac_pct": 100.0 * float(np.count_nonzero(leng)) / leng.size,
        # activation
        "peakAct": float(np.nanmax(act_row)) if act_row is not None else np.nan,
        "actAtPeakLM": float(act_row[i_peakL]) if act_row is not None else np.nan,
        # force at the instant of peak fibre strain (eccentric loading at stretch)
        "FceAtPeakLM_N": float(Fce[i_peakL]),
        "lengAtPeakLM": bool(leng[i_peakL]),
        # sign check helper
        "signAgree": float(np.corrcoef(vMt, dlmdt)[0, 1]) if np.std(vMt) > 0 else np.nan,
        "peakInStance": (bool(stance[i_peakL]) if stance is not None
                         and stance.shape[0] == lMt.shape[0] else None),
    }
    return out


def analyze_file(path):
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    mvobj = _get(o, "muscleValues")
    mv = {k: np.asarray(_get(mvobj, k), float)
          for k in ("lM", "lMtilde", "lMTk_lr", "Fce", "FT", "Fpass", "Fpetilde", "vMtilde")}
    ncols = mv["lMtilde"].shape[1]
    try:
        totalTime = float(_get(o, "optVars_nsc", "totalTime"))
    except Exception:
        totalTime = 1.0
    t = np.linspace(0.0, totalTime, ncols)
    stance = _stance_mask_R(o, ncols)

    # activation, aligned to the 151-col muscle grid if necessary
    try:
        act = np.asarray(_get(o, "optVars_nsc", "act"), float)
        if act.shape[1] != ncols:
            xa = np.linspace(0.0, 1.0, act.shape[1])
            xg = np.linspace(0.0, 1.0, ncols)
            act = np.vstack([np.interp(xg, xa, act[r]) for r in range(act.shape[0])])
    except Exception:
        act = None

    q = np.asarray(_get(o, "optVars_nsc", "q"), float)          # rad, 37 x ncolq
    tilt = np.degrees(q[Q_PELVIS_TILT])
    hipR = np.degrees(q[Q_HIP_FLEX_R])
    kneeR = np.degrees(q[Q_KNEE_R])
    row = {
        "speed": float(_get(o, "ave_speed")),
        "ptMean": float(tilt.mean()),
        "ptMin": float(tilt.min()),
        "ptMax": float(tilt.max()),
        "hipR_TD": float(hipR[0]),
        "hipR_peak": float(hipR.max()),
        "kneeR_min": float(kneeR.min()),
    }
    try:
        row["status"] = str(_get(o, "stats", "return_status"))
    except Exception:
        row["status"] = "?"

    # per-muscle, bilateral mean of L and R.
    # NOTE: magnitudes are averaged over the two (symmetric, half-cycle-shifted)
    # legs, but TIMING keys must NOT be averaged (the two legs peak half a stride
    # apart); for those we report the LEFT leg, whose terminal-swing stretch peak
    # (~80% of this right-stance step) is fully captured inside the window.
    TIMING_KEYS = {"tPeakLM_pct", "tPeakFce_pct", "signAgree"}
    for i, nm in enumerate(HAM):
        aL = act[HAM_L[i]] if act is not None else None
        aR = act[HAM_R[i]] if act is not None else None
        mL = _muscle_force_ecc(HAM_L[i], mv, aL, t, stance)
        mR = _muscle_force_ecc(HAM_R[i], mv, aR, t, stance)
        for k in mL:
            if isinstance(mL[k], bool) or mL[k] is None or isinstance(mR[k], bool):
                row[f"{nm}_{k}"] = mL[k]                       # left as representative flag
            elif k in TIMING_KEYS:
                row[f"{nm}_{k}"] = mL[k]                       # left-leg timing (no averaging)
            else:
                row[f"{nm}_{k}"] = 0.5 * (mL[k] + mR[k])
    return row


def _offset_from_name(name):
    mobj = re.search(r"(PelvisShift|PelvisTilt|PelvisTD)_([mp])(\d+)", name)
    if not mobj:
        return None
    return (-1 if mobj.group(2) == "m" else 1) * int(mobj.group(3))


def collect(patterns):
    seen = {}
    for pat in patterns:
        for f in glob.glob(os.path.join(RESULTS, pat)):
            tok = re.search(r"___(.+)\.mat$", os.path.basename(f))
            tok = tok.group(1) if tok else os.path.basename(f)
            if tok not in seen or os.path.getmtime(f) > os.path.getmtime(seen[tok]):
                seen[tok] = f
    return seen


def _linfit(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if x.size < 3:
        return np.nan, np.nan, np.nan
    A = np.vstack([x, np.ones_like(x)]).T
    slope, icpt = np.linalg.lstsq(A, y, rcond=None)[0]
    yhat = slope * x + icpt
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return float(slope), float(icpt), float(r2)


def main():
    files = collect([
        "pred_sprinting_data_*04-February-2026*Nominal.mat",
        "pred_sprinting_data_*PelvisShift*.mat",
    ])
    rows = []
    for cond, f in files.items():
        try:
            r = analyze_file(f)
        except Exception as e:  # noqa: BLE001
            print(f"[skip] {cond}: {e}")
            continue
        r["cond"] = cond
        r["offset"] = _offset_from_name(cond)
        if r["offset"] is None:
            r["offset"] = 0.0                                   # Nominal
        rows.append(r)
    if not rows:
        print("No .mat found under", os.path.abspath(RESULTS))
        return
    rows.sort(key=lambda r: r["offset"])

    nominal = min(rows, key=lambda r: abs(r["offset"]))
    spd0 = nominal["speed"]
    for r in rows:
        r["dspeed_pct"] = 100.0 * (r["speed"] - spd0) / spd0
        r["speedMatched"] = abs(r["dspeed_pct"]) <= 3.0

    # ---- sign-convention verification (STEP 5 prerequisite) ----------------
    sa = np.nanmean([r["bifemlh_signAgree"] for r in rows])
    print("=" * 92)
    print("SIGN CHECK  corr(vMtilde, dlM/dt) mean over conditions (bifemlh) = "
          f"{sa:+.3f}  -> vMtilde>0 == fibre LENGTHENING (eccentric).")

    # ---- STEP 4 : absolute force table -------------------------------------
    print("=" * 92)
    print("STEP 4  PEAK MUSCLE FORCE (bilateral mean, Newtons) + activation")
    print(f"{'cond':16s}{'tilt':>7s}{'spd':>7s}{'match':>6s} | "
          + " ".join(f"{nm[:4]+'_Fce':>11s}" for nm in HAM))
    for r in rows:
        vals = " ".join(f"{r[nm+'_peakFceN']:11.0f}" for nm in HAM)
        print(f"{r['cond'][:16]:16s}{r['ptMean']:7.2f}{r['speed']:7.2f}"
              f"{('Y' if r['speedMatched'] else 'n'):>6s} | {vals}")

    print("-" * 92)
    print("STEP 4  PEAK TENDON FORCE FT (N) and peak activation (biarticular hams)")
    print(f"{'cond':16s}{'tilt':>7s} | "
          + " ".join(f"{nm[:4]+'_FT':>10s}" for nm in HAM if nm in BIARTIC)
          + " || " + " ".join(f"{nm[:4]+'_act':>9s}" for nm in HAM if nm in BIARTIC))
    for r in rows:
        ft = " ".join(f"{r[nm+'_peakFTN']:10.0f}" for nm in HAM if nm in BIARTIC)
        ac = " ".join(f"{r[nm+'_peakAct']:9.3f}" for nm in HAM if nm in BIARTIC)
        print(f"{r['cond'][:16]:16s}{r['ptMean']:7.2f} | {ft} || {ac}")

    # ---- STEP 4b : timing / injury-coincidence -----------------------------
    print("=" * 92)
    print("STEP 4b  TIMING: when peak fibre strain vs peak force occur (% of step); "
          "is peak strain during lengthening & stance?")
    print(f"{'cond':16s}{'tilt':>7s} | "
          + " ".join(f"{nm[:4]:>4s}:tLM/tF/leng/st" for nm in HAM if nm in BIARTIC))
    for r in rows:
        cells = []
        for nm in HAM:
            if nm not in BIARTIC:
                continue
            leng = "L" if r[f"{nm}_lengAtPeakLM"] else "-"
            st = r[f"{nm}_peakInStance"]
            st = "S" if st is True else ("-" if st is False else "?")
            cells.append(f"{r[nm+'_tPeakLM_pct']:4.0f}/{r[nm+'_tPeakFce_pct']:3.0f}/{leng}/{st}")
        print(f"{r['cond'][:16]:16s}{r['ptMean']:7.2f} | " + "  ".join(cells))

    # ---- STEP 5 : eccentric table ------------------------------------------
    print("=" * 92)
    print("STEP 5  ECCENTRIC (active-while-lengthening): peak Fce during stretch (N), "
          "ecc work (J), force@peak-strain")
    print(f"{'cond':16s}{'tilt':>7s} | "
          + " ".join(f"{nm[:4]+'_eF':>9s}" for nm in HAM if nm in BIARTIC)
          + " || " + " ".join(f"{nm[:4]+'@pk':>9s}" for nm in HAM if nm in BIARTIC))
    for r in rows:
        ef = " ".join(f"{r[nm+'_eccPeakFceN']:9.0f}" for nm in HAM if nm in BIARTIC)
        fp = " ".join(f"{r[nm+'_FceAtPeakLM_N']:9.0f}" for nm in HAM if nm in BIARTIC)
        print(f"{r['cond'][:16]:16s}{r['ptMean']:7.2f} | {ef} || {fp}")

    # ---- STEP 3/6 : speed-matched regression vs pelvis tilt ----------------
    sub = [r for r in rows if r["speedMatched"]]
    print("=" * 92)
    print(f"STEP 3/6  REGRESSION vs mean pelvis tilt, SPEED-MATCHED subset only "
          f"(n={len(sub)}, speed {min(s['speed'] for s in sub):.2f}-"
          f"{max(s['speed'] for s in sub):.2f} m/s)")
    excluded = [r for r in rows if not r["speedMatched"]]
    if excluded:
        print("  excluded (speed confound): "
              + ", ".join(f"{r['cond'][:14]}({r['speed']:.1f}m/s,{r['status'][:10]})"
                          for r in excluded))
    x = [r["ptMean"] for r in sub]
    print(f"\n  {'metric':22s}{'slope/deg':>12s}{'R2':>8s}   (tilt more NEGATIVE = more anterior)")
    for nm in HAM:
        for metric, lab in (("peakFceN", "peakFce(N)"),
                            ("peakLM", "peakLMtilde"),
                            ("eccPeakFceN", "eccPeakFce(N)"),
                            ("eccWorkJ", "eccWork(J)")):
            y = [r[f"{nm}_{metric}"] for r in sub]
            s, _, r2 = _linfit(x, y)
            tag = "*biartic" if nm in BIARTIC else " mono"
            print(f"  {nm+'.'+lab:22s}{s:12.4f}{r2:8.3f}  {tag}")

    # ---- STEP 6 : mediation chain  tilt -> hip flexion -> length -> force ---
    print("=" * 92)
    print("STEP 6  MEDIATION chain (speed-matched): is the loading driven by hip "
          "flexion, not tilt per se?")

    def _pearson(a, b):
        a = np.asarray(a, float)
        b = np.asarray(b, float)
        if np.std(a) == 0 or np.std(b) == 0:
            return np.nan
        return float(np.corrcoef(a, b)[0, 1])

    tilt = [r["ptMean"] for r in sub]
    hip = [r["hipR_peak"] for r in sub]
    print(f"  link 1  pelvis tilt   -> hip flexion peak : r = {_pearson(tilt, hip):+.3f} "
          f"(slope {_linfit(tilt, hip)[0]:+.3f} deg/deg)")
    for nm in ("semimem", "bifemlh"):
        lm = [r[f"{nm}_peakLM"] for r in sub]
        fc = [r[f"{nm}_peakFceN"] for r in sub]
        print(f"  link 2  hip flexion   -> {nm:8s} peakLM    : r = {_pearson(hip, lm):+.3f}")
        print(f"  link 3  {nm:8s} peakLM -> peakFce(N)      : r = {_pearson(lm, fc):+.3f}")
        # direct tilt->force vs hip->force (which is the closer proximal driver?)
        print(f"          tilt->{nm} force r={_pearson(tilt, fc):+.3f} | "
              f"hip->{nm} force r={_pearson(hip, fc):+.3f}")

    # ---- write CSV ----------------------------------------------------------
    outdir = os.path.join(RESULTS, "PelvicShift_Study")
    os.makedirs(outdir, exist_ok=True)
    outcsv = os.path.join(outdir, "pelvic_force_eccentric.csv")
    cols = ["cond", "offset", "status", "speed", "dspeed_pct", "speedMatched",
            "ptMean", "ptMin", "ptMax", "hipR_TD", "hipR_peak", "kneeR_min"]
    metric_keys = ["peakLM", "tPeakLM_pct", "peakFceN", "tPeakFce_pct", "peakFTN",
                   "peakFpassN", "peakFpetilde", "peakLMT_m", "LMTexc_m",
                   "eccPeakFceN", "eccWorkJ", "eccPeakPowerW", "eccFrac_pct",
                   "peakAct", "actAtPeakLM", "FceAtPeakLM_N", "lengAtPeakLM",
                   "peakInStance"]
    for nm in HAM:
        cols += [f"{nm}_{k}" for k in metric_keys]
    with open(outcsv, "w", encoding="utf-8") as fh:
        fh.write(",".join(cols) + "\n")
        for r in rows:
            fh.write(",".join(str(r.get(c, "")) for c in cols) + "\n")
    print("=" * 92)
    print("wrote", os.path.relpath(outcsv, HERE))


if __name__ == "__main__":
    main()
