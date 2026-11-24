"""
audit_recalc_N100.py -- INDEPENDENT (clean-room) Phase-2 recomputation of the N=100
8-condition touchdown-pelvic-tilt dose-response, straight from the raw .mat files.

Does NOT import ham_load_metrics or read Validation_Master CSVs. Implements the documented
definitions fresh:
  * non-uniform timeNodes trapezoid integration
  * physical fibre velocity vM = vMtilde * vMax  (m/s), >0 = lengthening
  * negative (active eccentric) fibre work = INT max(Fce*vM,0) dt   [J]
  * one full stride reconstructed by concatenating the right-leg step [0,T] with the
    left-leg step mapped to [T,2T] (half-stride mirror symmetry)
  * peak_lMtilde = max over the FULL reconstructed stride (not TS-limited)
  * terminal swing = last 25% of the swing phase (swing = stride - ground contact)
Also VERIFIES muscle-row indexing by L/R symmetry (row r vs r+46) and reports the
stride seam discontinuity.

Outputs (Results/Independent_Audit_20260819/):
  raw_mat_recalculated_primary_N100.csv     (per condition x muscle: lengths, timing)
  raw_mat_recalculated_secondary_N100.csv   (per condition x muscle: forces, work)
  regression_summary_N100.csv               (per muscle: slope, R2, LOO, speed-adj, min->max%)
Prints a side-by-side vs the user's expected values.
"""
from __future__ import annotations
import csv
import hashlib
import os
import numpy as np
from scipy.io import loadmat

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, ".."))

# selected strict Solve_Succeeded N=100 files (from final_source_manifest.csv)
SELECTED = [
    ("m8", "pred_sprinting_data_24-June-2026__23-17-49___PelvisTDwide_m8.mat"),
    ("m6", "pred_sprinting_data_25-June-2026__00-01-41___PelvisTDwide_m6.mat"),
    ("m4", "pred_sprinting_data_25-June-2026__01-05-16___PelvisTDwide_m4.mat"),
    ("m2", "pred_sprinting_data_25-June-2026__02-31-10___PelvisTDwide_m2.mat"),
    ("p0", "pred_sprinting_data_25-June-2026__03-15-59___PelvisTDwide_p0.mat"),
    ("p2", "pred_sprinting_data_25-June-2026__04-33-19___PelvisTDwide_p2.mat"),
    ("p4", "pred_sprinting_data_25-June-2026__05-43-11___PelvisTDwide_p4.mat"),
    ("p6", "pred_sprinting_data_25-June-2026__07-24-05___PelvisTDwide_p6.mat"),
]
MUS = ["semimem", "semiten", "bifemlh", "bifemsh"]
BIARTIC = ["semimem", "semiten", "bifemlh"]
L = {"semimem": 6, "semiten": 7, "bifemlh": 8, "bifemsh": 9}
R = {"semimem": 52, "semiten": 53, "bifemlh": 54, "bifemsh": 55}
BODY_MASS = 72.17
BW = BODY_MASS * 9.80665
TS_SWING_FRAC = 0.25


def sha256(p, buf=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(buf), b""):
            h.update(c)
    return h.hexdigest()


def _g(o, *n):
    for k in n:
        o = getattr(o, k) if hasattr(o, k) else o[k]
    return o


def trap(y, x):
    y = np.asarray(y, float); x = np.asarray(x, float)
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x))) if y.size > 1 else 0.0


def load(path):
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    mv = _g(o, "muscleValues")
    A = lambda k: np.asarray(_g(mv, k), float)
    t = np.asarray(_g(o, "timeNodes"), float).ravel()
    lMtilde = A("lMtilde"); ncol = lMtilde.shape[1]
    assert t.size == ncol, f"timeNodes {t.size} != cols {ncol}"
    vMax = A("vMax")
    if vMax.ndim == 1:
        vMax = np.repeat(vMax[:, None], ncol, axis=1)
    q = np.asarray(_g(o, "optVars_nsc", "q"), float)
    d = dict(name=os.path.basename(path), t=t, lMtilde=lMtilde, lM=A("lM"),
             lMT=A("lMTk_lr"), Fce=A("Fce"), Fpass=A("Fpass"), FT=A("FT"),
             vMtilde=A("vMtilde"), vMax=vMax, Fpetilde=A("Fpetilde"),
             N=int(np.asarray(_g(o, "options", "N")).ravel()[0]),
             status=str(_g(o, "stats", "return_status")),
             inf_pr=float(np.asarray(_g(o, "stats", "iterations", "inf_pr"), float).ravel()[-1]),
             speed=float(np.asarray(_g(o, "ave_speed")).ravel()[0]),
             td=float(np.degrees(q[0, 0])),
             totalTime=float(np.asarray(_g(o, "optVars_nsc", "totalTime")).ravel()[0]),
             GRF_R=np.asarray(_g(o, "GRFs", "R"), float))
    return d


def contact_s(d):
    g = d["GRF_R"]; t = d["t"]; n = t.size
    if g.shape[0] != n and g.shape[1] == n:
        g = g.T
    vert = g[:, int(np.argmax(np.ptp(g, axis=0)))]   # vertical = largest peak-to-peak col
    stance = vert > 0.05 * BW
    to = 0
    while to + 1 < n and stance[to + 1]:
        to += 1
    return float(t[to] - t[0]), float(vert.max() / BW), bool(stance[0])


def stride(d, nm):
    """reconstructed reference (right)-limb full stride."""
    t = d["t"]; T = float(t[-1] - t[0]); rR, rL = R[nm], L[nm]
    cat = lambda f: np.concatenate([d[f][rR], d[f][rL]])
    vM = np.concatenate([d["vMtilde"][rR] * d["vMax"][rR], d["vMtilde"][rL] * d["vMax"][rL]])
    ts = np.concatenate([t - t[0], (t - t[0]) + T])
    seam_gap = abs(float(d["lMtilde"][rR][-1] - d["lMtilde"][rL][0]))
    return dict(t=ts, T=T, lMtilde=cat("lMtilde"), lMT=cat("lMT"), Fce=cat("Fce"),
                Fpass=cat("Fpass"), FT=cat("FT"), Fpetilde=cat("Fpetilde"), vM=vM,
                seam_gap=seam_gap)


def metrics(d, nm, contact):
    s = stride(d, nm); t = s["t"]; lMt = s["lMtilde"]
    fce, fpa, ft, vM, fpet = s["Fce"], s["Fpass"], s["FT"], s["vM"], s["Fpetilde"]
    strideT = 2.0 * s["T"]
    ip = int(np.argmax(lMt))
    tpk = 100.0 * t[ip] / strideT
    tsw_start = strideT - TS_SWING_FRAC * (strideT - contact) if np.isfinite(contact) else 0.8 * strideT
    m = t >= tsw_start
    act_pow = np.clip(fce * vM, 0.0, None)
    # per-leg cross-check
    pkR = float(d["lMtilde"][R[nm]].max()); pkL = float(d["lMtilde"][L[nm]].max())
    return dict(
        peak_lMtilde=float(lMt.max()), tPeak_pct=tpk,
        peak_lMtilde_R=pkR, peak_lMtilde_L=pkL, bimean=0.5 * (pkR + pkL),
        seam_gap=s["seam_gap"],
        TS_peak_lMtilde=float(lMt[m].max()) if m.sum() else np.nan,
        peak_MTU_len_m=float(s["lMT"].max()), MTU_excursion_m=float(s["lMT"].max() - s["lMT"].min()),
        peak_active_force_N=float(fce.max()), peak_passive_force_N=float(fpa.max()),
        peak_tendon_force_N=float(ft.max()), peak_Fpetilde=float(fpet.max()),
        peak_leng_vel_mps=float(np.clip(vM, 0, None).max()),
        neg_fiber_work_J=trap(act_pow, t),
        TS_neg_fiber_work_J=trap(np.clip(fce * vM, 0, None)[m], t[m]) if m.sum() else np.nan,
        peak_act_ecc_power_W=float(act_pow.max()),
    )


def fit(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    A = np.vstack([x, np.ones_like(x)]).T
    sl, ic = np.linalg.lstsq(A, y, rcond=None)[0]
    yh = sl * x + ic
    r2 = 1 - np.sum((y - yh) ** 2) / (np.sum((y - y.mean()) ** 2) + 1e-15)
    return sl, ic, r2


def loo_slopes(x, y):
    out = []
    for i in range(len(x)):
        xx = np.delete(x, i); yy = np.delete(y, i)
        out.append(fit(xx, yy)[0])
    return min(out), max(out)


def speed_adj_coef(anterior, speed, y):
    X = np.vstack([anterior, speed, np.ones_like(anterior)]).T
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    return beta[0]  # coefficient on anterior tilt


def main():
    conds = []
    for off, fn in SELECTED:
        d = load(os.path.join(RESULTS, fn))
        row = dict(offset=off, file=fn, sha256=sha256(os.path.join(RESULTS, fn))[:16],
                   status=d["status"], inf_pr=d["inf_pr"], N=d["N"],
                   td_signed=round(d["td"], 4), anterior=round(-d["td"], 4),
                   speed=round(d["speed"], 6))
        c, pkbw, tdc = contact_s(d)
        row["contact_s"] = round(c, 5); row["peakVGRF_BW"] = round(pkbw, 3); row["td_is_contact"] = tdc
        row["m"] = {nm: metrics(d, nm, c) for nm in MUS}
        conds.append(row)

    conds.sort(key=lambda r: r["anterior"])   # 1.987 -> 15.987

    # ---- primary CSV (lengths + timing) ----
    p1 = os.path.join(HERE, "raw_mat_recalculated_primary_N100.csv")
    with open(p1, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["offset", "source_file", "sha256_16", "solver_status", "final_inf_pr",
                    "mesh_N", "td_tilt_signed_deg", "anterior_tilt_deg", "speed_mps",
                    "contact_s", "peakVGRF_BW", "muscle", "is_biarticular",
                    "peak_lMtilde", "tPeak_pct_stride", "peak_lMtilde_R", "peak_lMtilde_L",
                    "bimean_peak_lMtilde", "seam_gap_lMtilde", "TS_peak_lMtilde"])
        for r in conds:
            for nm in MUS:
                mm = r["m"][nm]
                w.writerow([r["offset"], r["file"], r["sha256"], r["status"],
                            f"{r['inf_pr']:.3e}", r["N"], r["td_signed"], r["anterior"],
                            r["speed"], r["contact_s"], r["peakVGRF_BW"], nm, nm in BIARTIC,
                            f"{mm['peak_lMtilde']:.5f}", f"{mm['tPeak_pct']:.2f}",
                            f"{mm['peak_lMtilde_R']:.5f}", f"{mm['peak_lMtilde_L']:.5f}",
                            f"{mm['bimean']:.5f}", f"{mm['seam_gap']:.2e}",
                            f"{mm['TS_peak_lMtilde']:.5f}"])

    # ---- secondary CSV (forces + work) ----
    p2 = os.path.join(HERE, "raw_mat_recalculated_secondary_N100.csv")
    with open(p2, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["offset", "anterior_tilt_deg", "speed_mps", "muscle", "is_biarticular",
                    "peak_active_force_N", "peak_passive_force_N", "peak_tendon_force_N",
                    "peak_Fpetilde", "peak_leng_vel_mps", "peak_act_ecc_power_W",
                    "neg_fiber_work_J", "TS_neg_fiber_work_J", "peak_MTU_len_m", "MTU_excursion_m"])
        for r in conds:
            for nm in MUS:
                mm = r["m"][nm]
                w.writerow([r["offset"], r["anterior"], r["speed"], nm, nm in BIARTIC,
                            f"{mm['peak_active_force_N']:.1f}", f"{mm['peak_passive_force_N']:.1f}",
                            f"{mm['peak_tendon_force_N']:.1f}", f"{mm['peak_Fpetilde']:.4f}",
                            f"{mm['peak_leng_vel_mps']:.4f}", f"{mm['peak_act_ecc_power_W']:.1f}",
                            f"{mm['neg_fiber_work_J']:.4f}", f"{mm['TS_neg_fiber_work_J']:.4f}",
                            f"{mm['peak_MTU_len_m']:.5f}", f"{mm['MTU_excursion_m']:.5f}"])

    # ---- regression summary ----
    anterior = np.array([r["anterior"] for r in conds])
    speed = np.array([r["speed"] for r in conds])
    EXP_SLOPE = {"semimem": 0.00678, "semiten": 0.00374, "bifemlh": 0.00538, "bifemsh": None}
    EXP_ADJ = {"semimem": 0.00640, "semiten": 0.00351, "bifemlh": 0.00504, "bifemsh": None}
    p3 = os.path.join(HERE, "regression_summary_N100.csv")
    print("\n=== N=100 dose-response: peak_lMtilde vs anterior tilt (per muscle) ===")
    print(f"anterior tilt (deg): {anterior}")
    print(f"speeds (m/s):        {speed}")
    with open(p3, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["muscle", "is_biarticular", "slope_per_deg_anterior", "intercept", "R2",
                    "LOO_slope_min", "LOO_slope_max", "speed_adj_coef_per_deg",
                    "pct_change_min_to_max_tilt", "expected_slope", "expected_speed_adj",
                    "peak_lMtilde_at_min_tilt(p6)", "peak_lMtilde_at_max_tilt(m8)"])
        for nm in MUS:
            y = np.array([r["m"][nm]["peak_lMtilde"] for r in conds])
            sl, ic, r2 = fit(anterior, y)
            lo, hi = loo_slopes(anterior, y)
            adj = speed_adj_coef(anterior, speed, y)
            pct = 100.0 * (y[-1] - y[0]) / y[0]   # p6(min tilt) -> m8(max tilt)
            print(f"{nm:9s} slope={sl:+.5f}/deg (exp {EXP_SLOPE[nm]}) R2={r2:.4f} "
                  f"LOO[{lo:+.5f},{hi:+.5f}] adj={adj:+.5f} (exp {EXP_ADJ[nm]}) "
                  f"min->max={pct:+.2f}%  y[min={y[0]:.4f},max={y[-1]:.4f}]")
            w.writerow([nm, nm in BIARTIC, f"{sl:.6f}", f"{ic:.6f}", f"{r2:.5f}",
                        f"{lo:.6f}", f"{hi:.6f}", f"{adj:.6f}", f"{pct:.3f}",
                        EXP_SLOPE[nm] if EXP_SLOPE[nm] else "", EXP_ADJ[nm] if EXP_ADJ[nm] else "",
                        f"{y[0]:.5f}", f"{y[-1]:.5f}"])
    # biarticular timing + seam
    print("\n=== biarticular peak-lMtilde timing (%stride) and seam gap ===")
    for r in conds:
        tp = [r["m"][nm]["tPeak_pct"] for nm in BIARTIC]
        sg = max(r["m"][nm]["seam_gap"] for nm in MUS)
        print(f"  {r['offset']} ant={r['anterior']:6.3f}: tPeak%={['%.1f'%x for x in tp]} "
              f"contact={r['contact_s']*1000:.1f}ms td_is_contact={r['td_is_contact']} seam_gap<={sg:.1e}")
    print(f"\nwrote:\n  {p1}\n  {p2}\n  {p3}")


if __name__ == "__main__":
    main()
