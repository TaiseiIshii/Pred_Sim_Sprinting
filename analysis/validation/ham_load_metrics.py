"""
ham_load_metrics.py  --  corrected single-source-of-truth hamstring load-surrogate
metrics for the saved predictive-sprinting results.

WHY THIS MODULE (Step-0 audit fixes)
------------------------------------
The legacy analysis (injury_metrics.py, plot_pelvic_td_figs.py) computed metrics on a
UNIFORM time grid (np.linspace / scalar dt) and used the NORMALISED fibre velocity
`vMtilde` inside an "eccWork" that is therefore NOT in joules.  Empirically:
  * saved `timeNodes` are NON-uniform (Radau collocation), dt in [0.32, 1.02] ms, and
    start at t0=0.056 s (not 0);  `muscleValues` are sampled on `timeNodes`.
  * `Fce`, `Fpass`, `FT` are in NEWTONS;  `Fpetilde`,`Fiso`,`vMtilde` are normalised.
  * physical fibre velocity = `vMtilde * vMax`  [m/s]  (EXACT model quantity; verified
    to equal d(lM)/dt on the real grid), with vMtilde>0 == LENGTHENING (eccentric).

This module therefore:
  * integrates / differentiates ONLY on the saved non-uniform `timeNodes`;
  * uses physical forces (N) and physical fibre velocity (m/s) so negative fibre work is
    a genuine energy in JOULES;
  * expresses peak timing as a TRUE-TIME fraction of the step, and provides
    terminal-swing / early-stance aggregates from GRF-detected gait events.

Gait / phase convention (single symmetric step = half stride)
-------------------------------------------------------------
The step spans [t0, tE] with t0 = right-foot touchdown (verified: GRFs.R vertical is
high at t0) and tE = left-foot touchdown (half a stride later, by L<->R symmetry).
  * EARLY STANCE  -> reference = RIGHT leg, window [t0, t0 + es_frac*contact].
  * TERMINAL SWING-> reference = LEFT leg, window [tE - ts_frac*T, tE] (left limb is the
    one approaching touchdown at tE).  By mirror symmetry this equals the right limb's
    own terminal swing one step later, so no periodic wrap-around artefact is introduced.

Hamstring rows (0-based) in the 92-row muscle arrays:
  LEFT  semimem,semiten,bifemlh,bifemsh = 6,7,8,9
  RIGHT                                 = 52,53,54,55
Biarticular (stretch-relevant) group = semimem,semiten,bifemlh; bifemsh = mono-articular
control (does not cross the hip).
"""
from __future__ import annotations

import glob
import hashlib
import os
import re

import numpy as np
from scipy.io import loadmat

__version__ = "1.0.0"

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, "..", "..", "Results"))

BODY_MASS = 72.17                 # kg (subject)
BW = BODY_MASS * 9.80665          # N (body weight = 707.75 N)

HAM = ["semimem", "semiten", "bifemlh", "bifemsh"]
HAM_L = {"semimem": 6, "semiten": 7, "bifemlh": 8, "bifemsh": 9}
HAM_R = {"semimem": 52, "semiten": 53, "bifemlh": 54, "bifemsh": 55}
BIARTIC = ["semimem", "semiten", "bifemlh"]

# phase-window fractions (documented, adjustable), applied on the reconstructed stride
ES_FRAC = 0.50        # early stance    = first 50% of ground contact
TS_SWING_FRAC = 0.25  # terminal swing  = last 25% of the swing phase (pre-touchdown)


# --------------------------------------------------------------------------- io
def _get(o, *names):
    for n in names:
        o = getattr(o, n) if hasattr(o, n) else o[n]
    return o


def sha256(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def _trap(y, x):
    """Trapezoidal integral on a possibly non-uniform grid x."""
    y = np.asarray(y, float)
    x = np.asarray(x, float)
    if y.size < 2:
        return 0.0
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x)))


def load_optimum(path):
    """Load one result .mat into a plain dict of arrays + metadata.

    Time vector policy: use saved non-uniform `timeNodes` (length == muscleValues cols).
    Raises if the two are inconsistent (never silently fall back to linspace)."""
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    mv = _get(o, "muscleValues")

    def arr(name):
        return np.asarray(_get(mv, name), float)

    lMtilde = arr("lMtilde")
    ncol = lMtilde.shape[1]
    t = np.asarray(_get(o, "timeNodes"), float).ravel()
    if t.size != ncol:
        raise ValueError(f"{os.path.basename(path)}: timeNodes({t.size}) != "
                         f"muscleValues cols({ncol}); refusing linspace fallback.")

    vMax = np.asarray(_get(mv, "vMax"), float)
    if vMax.ndim == 1:                       # per-muscle constant -> broadcast to (92,ncol)
        vMax = np.repeat(vMax[:, None], ncol, axis=1)

    d = {
        "path": path,
        "name": os.path.basename(path),
        "t": t,                              # s, non-uniform
        "lM": arr("lM"),                     # m  (fibre length)
        "lMtilde": lMtilde,                  # -  (fibre length / lMo)
        "lMT": arr("lMTk_lr"),               # m  (MTU length)
        "Fce": arr("Fce"),                   # N  (active contractile force)
        "Fpass": arr("Fpass"),               # N  (passive fibre force)
        "FT": arr("FT"),                     # N  (tendon force)
        "vMtilde": arr("vMtilde"),           # -  (normalised fibre velocity, >0 lengthening)
        "vMax": vMax,                        # m/s (max shortening velocity, per muscle)
        "Fpetilde": arr("Fpetilde"),         # -  (normalised passive force)
    }
    # metadata
    d["N"] = int(np.asarray(_get(o, "options", "N")).ravel()[0])
    try:
        d["return_status"] = str(_get(o, "stats", "return_status"))
        d["success"] = bool(int(np.asarray(_get(o, "stats", "success")).ravel()[0]))
        d["iter_count"] = int(np.asarray(_get(o, "stats", "iter_count")).ravel()[0])
    except Exception:
        d["return_status"], d["success"], d["iter_count"] = "unknown", False, -1
    try:
        d["speed"] = float(np.asarray(_get(o, "ave_speed")).ravel()[0])
    except Exception:
        d["speed"] = np.nan
    q = np.asarray(_get(o, "optVars_nsc", "q"), float)          # 37 x (N*4) rad
    d["q"] = q
    d["pelvis_tilt_deg"] = np.degrees(q[0])
    d["td_tilt_deg"] = float(np.degrees(q[0, 0]))
    d["mean_tilt_deg"] = float(np.degrees(q[0].mean()))
    try:
        d["totalTime"] = float(np.asarray(_get(o, "optVars_nsc", "totalTime")).ravel()[0])
    except Exception:
        d["totalTime"] = float(t[-1] - t[0])
    try:
        d["GRF_R"] = np.asarray(_get(o, "GRFs", "R"), float)    # (ncol,3) [AP,vert,ML] N
    except Exception:
        d["GRF_R"] = None
    return d


# ----------------------------------------------------------------- gait events
def gait_events(d, thr_frac=0.05):
    """Right-foot stance window + step bounds from GRFs.R vertical (N).

    Returns dict with indices/times of touchdown (td), toe-off (to), contact, and the
    early-stance and terminal-swing boolean masks (see module docstring)."""
    t = d["t"]
    n = t.size
    g = d["GRF_R"]
    out = {"t0": float(t[0]), "tE": float(t[-1]), "T": float(t[-1] - t[0])}
    if g is None or g.ndim != 2:
        out.update(td=0, to=n // 3, contact_s=np.nan, es_mask=None, ts_mask=None,
                   grf_ok=False)
        return out
    if g.shape[0] != n and g.shape[1] == n:
        g = g.T
    vert = g[:, int(np.argmax(np.ptp(g, axis=0)))]
    thr = thr_frac * BW
    stance = vert > thr
    # right stance is the contiguous contact bout starting at t0 (touchdown)
    td = 0
    to = td
    while to + 1 < n and stance[to + 1]:
        to += 1
    contact_s = float(t[to] - t[td])
    out.update(td=td, to=to, contact_s=contact_s,
               peakVertBW=float(vert.max() / BW), grf_ok=True,
               td_is_contact=bool(stance[0]))
    return out


# ------------------------------------------------- reference-limb full-stride metrics
def reference_stride(d, nm):
    """One full stride of the reference (right) limb.

    Concatenate the simulated right-leg step [0,T] with the left-leg step mapped to
    [T,2T].  This is valid because the model enforces left<->right mirror symmetry with a
    half-stride offset, so the right limb over [T,2T] equals the left limb over [0,T];
    the seam is continuous (|Δ lMtilde| < 1e-3, verified).  The reconstructed stride runs
    stance -> mid-swing -> TERMINAL swing -> next touchdown, so terminal-swing peaks are
    represented on a single continuous limb (no bilateral-timing averaging artefact)."""
    t = d["t"]
    T = float(t[-1] - t[0])
    rR, rL = HAM_R[nm], HAM_L[nm]

    def cat(field):
        return np.concatenate([d[field][rR], d[field][rL]])

    vM = np.concatenate([d["vMtilde"][rR] * d["vMax"][rR],
                         d["vMtilde"][rL] * d["vMax"][rL]])
    return {
        "t": np.concatenate([t - t[0], (t - t[0]) + T]), "T": T,
        "lMtilde": cat("lMtilde"), "lM": cat("lM"), "lMT": cat("lMT"),
        "Fce": cat("Fce"), "Fpass": cat("Fpass"), "FT": cat("FT"),
        "Fpetilde": cat("Fpetilde"), "vM": vM,
    }


def stride_metrics(s):
    """Load surrogates over one reconstructed reference-limb full stride (physical units)."""
    t = s["t"]
    lMt, lm, lmt = s["lMtilde"], s["lM"], s["lMT"]
    fce, fpa, ft, vM, fpet = s["Fce"], s["Fpass"], s["FT"], s["vM"], s["Fpetilde"]
    ratio = np.divide(lm, lMt, out=np.full_like(lm, np.nan), where=lMt > 0)
    lMo = float(np.nanmedian(ratio))
    leng = np.clip(vM, 0.0, None)
    act_pow = np.clip(fce * vM, 0.0, None)
    tot_pow = np.clip((fce + fpa) * vM, 0.0, None)
    i_pL, i_pF = int(np.argmax(lMt)), int(np.argmax(fce))
    stride = 2.0 * s["T"] if s["T"] > 0 else 1.0
    return {
        "peak_lMtilde": float(lMt.max()),
        "min_lMtilde": float(lMt.min()),
        "peak_MTU_len_m": float(lmt.max()),
        "MTU_excursion_m": float(lmt.max() - lmt.min()),
        "peak_leng_vel_mps": float(leng.max()),
        "peak_leng_rate_hz": float((leng / (lMo + 1e-12)).max()),
        "peak_active_force_N": float(fce.max()),
        "peak_passive_force_N": float(fpa.max()),
        "peak_tendon_force_N": float(ft.max()),
        "peak_Fpetilde": float(fpet.max()),
        "peak_act_ecc_power_W": float(act_pow.max()),
        "neg_fiber_work_J": _trap(act_pow, t),            # active eccentric energy / stride
        "neg_fiber_work_tot_J": _trap(tot_pow, t),        # + passive
        "lMo_m": lMo,
        "tPeak_lMtilde_pct": 100.0 * float(t[i_pL]) / stride,
        "tPeak_Fce_pct": 100.0 * float(t[i_pF]) / stride,
        "leng_at_peak_Fce": bool(vM[i_pF] > 0),
        "cotiming_lMt_Fce_pct": abs(100.0 * float(t[i_pL] - t[i_pF]) / stride),
    }


def _stride_window(s, mask):
    """Peak / integral load surrogates within a phase window of the reconstructed stride."""
    keys = ("peak_lMtilde", "peak_active_force_N", "peak_passive_force_N",
            "peak_tendon_force_N", "peak_leng_vel_mps", "neg_fiber_work_J")
    if mask is None or mask.sum() < 2:
        return {k: np.nan for k in keys}
    lMt = s["lMtilde"][mask]
    fce = s["Fce"][mask]
    fpa = s["Fpass"][mask]
    ft = s["FT"][mask]
    vM = s["vM"][mask]
    tw = s["t"][mask]
    return {
        "peak_lMtilde": float(lMt.max()),
        "peak_active_force_N": float(fce.max()),
        "peak_passive_force_N": float(fpa.max()),
        "peak_tendon_force_N": float(ft.max()),
        "peak_leng_vel_mps": float(np.clip(vM, 0, None).max()),
        "neg_fiber_work_J": _trap(np.clip(fce * vM, 0, None), tw),
    }


def condition_metrics(path):
    """Flat dict of all load surrogates for one condition .mat.

    Primary per-muscle metrics are computed on the RECONSTRUCTED reference-limb full
    stride (see reference_stride).  Naming:
       <muscle>_<metric>       = reference-limb full stride
       <muscle>_ES_<metric>    = early-stance window   (first ES_FRAC of ground contact)
       <muscle>_TS_<metric>    = terminal-swing window (last TS_FRAC of a step pre-touchdown)
       <muscle>_R/L_peak_lMtilde, <muscle>_bimean_peak_lMtilde = per-leg cross-checks
    Plus provenance / convergence / achieved kinematics."""
    d = load_optimum(path)
    ev = gait_events(d)
    contact = ev.get("contact_s", np.nan)
    out = {
        "name": d["name"], "N": d["N"], "return_status": d["return_status"],
        "success": d["success"], "iter_count": d["iter_count"],
        "speed_mps": d["speed"], "td_tilt_deg": d["td_tilt_deg"],
        "mean_tilt_deg": d["mean_tilt_deg"], "totalTime_s": d["totalTime"],
        "contact_s": contact, "peakVertGRF_BW": ev.get("peakVertBW", np.nan),
        "td_is_contact": ev.get("td_is_contact", None),
        "time_grid_type": "radau_timeNodes_nonuniform",
    }
    T = d["totalTime"]
    for nm in HAM:
        s = reference_stride(d, nm)
        ts_t = s["t"]
        # phase windows on the stride timeline [0, 2T]: early stance = first ES_FRAC of
        # ground contact; terminal swing = last TS_SWING_FRAC of the swing phase.
        stride = 2.0 * T
        es_mask = ts_t <= (ES_FRAC * contact) if np.isfinite(contact) else None
        tsw_start = stride - TS_SWING_FRAC * (stride - contact) if np.isfinite(contact) \
            else stride * 0.80
        tsw_mask = ts_t >= tsw_start
        for k, v in stride_metrics(s).items():
            out[f"{nm}_{k}"] = v
        for k, v in _stride_window(s, es_mask).items():
            out[f"{nm}_ES_{k}"] = v
        for k, v in _stride_window(s, tsw_mask).items():
            out[f"{nm}_TS_{k}"] = v
        # per-leg cross-checks (should be ~equal under symmetry; timing not averaged)
        pkR = float(d["lMtilde"][HAM_R[nm]].max())
        pkL = float(d["lMtilde"][HAM_L[nm]].max())
        out[f"{nm}_R_peak_lMtilde"] = pkR
        out[f"{nm}_L_peak_lMtilde"] = pkL
        out[f"{nm}_bimean_peak_lMtilde"] = 0.5 * (pkR + pkL)
    return out


# --------------------------------------------------------------- file selection
def find_latest(token, mesh_N=None):
    """Newest *.mat whose condition token matches, optionally filtered to mesh_N."""
    fs = sorted(glob.glob(os.path.join(RESULTS, f"pred_sprinting_data_*{token}.mat")),
                key=os.path.getmtime, reverse=True)
    for p in fs:
        if mesh_N is None:
            return p
        try:
            m = loadmat(p, struct_as_record=False, squeeze_me=True,
                        variable_names=["optimumOutput"])
            if int(np.asarray(_get(m["optimumOutput"], "options", "N")).ravel()[0]) == mesh_N:
                return p
        except Exception:
            continue
    return None


if __name__ == "__main__":
    # quick smoke print on the nominal condition
    p = find_latest("Nominal")
    m = condition_metrics(p)
    print(f"{m['name']}  N={m['N']}  status={m['return_status']}  speed={m['speed_mps']:.3f}")
    print(f"contact={m['contact_s']*1000:.1f} ms  peakVertGRF={m['peakVertGRF_BW']:.2f} BW  "
          f"td_is_contact={m['td_is_contact']}")
    print(f"{'muscle':9s} {'pkLMt':>6s} {'MTUm':>6s} {'vLeng':>7s} {'Fce_N':>7s} "
          f"{'Fpa_N':>6s} {'FT_N':>7s} {'negWJ':>7s} {'tLMt%':>6s} {'tFce%':>6s} lengF")
    for nm in HAM:
        print(f"{nm:9s} {m[nm+'_peak_lMtilde']:6.3f} {m[nm+'_peak_MTU_len_m']:6.3f} "
              f"{m[nm+'_peak_leng_vel_mps']:7.3f} {m[nm+'_peak_active_force_N']:7.0f} "
              f"{m[nm+'_peak_passive_force_N']:6.0f} {m[nm+'_peak_tendon_force_N']:7.0f} "
              f"{m[nm+'_neg_fiber_work_J']:7.2f} {m[nm+'_tPeak_lMtilde_pct']:6.1f} "
              f"{m[nm+'_tPeak_Fce_pct']:6.1f} {m[nm+'_leng_at_peak_Fce']}")
