"""
_common.py -- single source of truth for the thesis additional-figure set.

Clean-room re-implementation of the raw-.mat data path, kept byte-for-byte
consistent with Results/Independent_Audit_20260819/audit_recalc_N100.py so that
every figure is recomputed straight from the source MAT / .mot / .sto files and
never hard-codes a manuscript number.  Every figure script imports THIS module.

Definitions (identical to the audit):
  * lMtilde = lM / lMo                          (normalized muscle fibre length)
  * A = -pelvis_tilt_deg                        (anterior tilt amount, deg)
  * physical fibre velocity vM = vMtilde*vMax   (m/s, >0 = lengthening)
  * one full stride = right-leg step [0,T] concatenated with the mirror-symmetric
    left-leg step mapped to [T,2T]
  * peak_lMtilde = max over the FULL reconstructed stride (NOT the terminal-swing window)
  * terminal swing (muscle-metric window) = last 25% of swing = [2T-0.25(2T-contact), 2T]
  * Fce here = contractile-element force INCLUDING the damping term (De Groote 2016),
    reported as "Fce (収縮要素力, 減衰項含む)"; it is NOT a pure active force.
"""
from __future__ import annotations

import csv
import hashlib
import os

import numpy as np
from scipy.io import loadmat

# --------------------------------------------------------------------------- paths
HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.abspath(os.path.join(HERE, ".."))            # thesis_figures_final_<ts>/
PROJECT_ROOT = os.path.abspath(os.path.join(OUTDIR, "..", ".."))
RESULTS = os.path.join(PROJECT_ROOT, "Results")
AUDIT = os.path.join(RESULTS, "Independent_Audit_20260819")
EXP_IK_DIR = os.path.join(PROJECT_ROOT, "MainFunctions", "ExperimentalData", "IK_Splined")
MODEL = os.path.join(PROJECT_ROOT, "OpenSimModel",
                     "Scaled_FullBody_HamnerModel_Muscle_withContact.osim")

FIG_PDF = os.path.join(OUTDIR, "figures", "pdf")
FIG_SVG = os.path.join(OUTDIR, "figures", "svg")
FIG_PNG = os.path.join(OUTDIR, "figures", "png")
SRC = os.path.join(OUTDIR, "source_data")
QA = os.path.join(OUTDIR, "qa")
for _d in (FIG_PDF, FIG_SVG, FIG_PNG, SRC, QA):
    os.makedirs(_d, exist_ok=True)

# --------------------------------------------------------------------------- muscles
MUS = ["semimem", "semiten", "bifemlh", "bifemsh"]
BIARTIC = ["semimem", "semiten", "bifemlh"]
L = {"semimem": 6, "semiten": 7, "bifemlh": 8, "bifemsh": 9}       # 0-based MAT rows
R = {"semimem": 52, "semiten": 53, "bifemlh": 54, "bifemsh": 55}
BODY_MASS = 72.17                                                   # kg (=sum of 20 segments)
BW = BODY_MASS * 9.80665                                            # N
TS_SWING_FRAC = 0.25

# fixed, colour-blind-aware muscle identity (used in EVERY figure)
COLORS = {"semimem": "#1b7837",   # deep green
          "semiten": "#762a83",   # purple
          "bifemlh": "#2166ac",   # blue
          "bifemsh": "#7f7f7f"}   # grey / open
MARKERS = {"semimem": "o", "semiten": "s", "bifemlh": "^", "bifemsh": "D"}
LINESTYLES = {"semimem": "-", "semiten": "-", "bifemlh": "-", "bifemsh": "--"}
LABELS_EN = {"semimem": "semimembranosus", "semiten": "semitendinosus",
             "bifemlh": "biceps femoris LH", "bifemsh": "biceps femoris SH"}
LABELS_JP = {"semimem": "半膜様筋", "semiten": "半腱様筋",
             "bifemlh": "大腿二頭筋長頭", "bifemsh": "大腿二頭筋短頭"}
SHORT = {"semimem": "SM", "semiten": "ST", "bifemlh": "BFlh", "bifemsh": "BFsh"}

# strict Solve_Succeeded N=100 8-condition primary set (from final_source_manifest.csv)
SELECTED_N100 = [
    ("m8", "pred_sprinting_data_24-June-2026__23-17-49___PelvisTDwide_m8.mat"),
    ("m6", "pred_sprinting_data_25-June-2026__00-01-41___PelvisTDwide_m6.mat"),
    ("m4", "pred_sprinting_data_25-June-2026__01-05-16___PelvisTDwide_m4.mat"),
    ("m2", "pred_sprinting_data_25-June-2026__02-31-10___PelvisTDwide_m2.mat"),
    ("p0", "pred_sprinting_data_25-June-2026__03-15-59___PelvisTDwide_p0.mat"),
    ("p2", "pred_sprinting_data_25-June-2026__04-33-19___PelvisTDwide_p2.mat"),
    ("p4", "pred_sprinting_data_25-June-2026__05-43-11___PelvisTDwide_p4.mat"),
    ("p6", "pred_sprinting_data_25-June-2026__07-24-05___PelvisTDwide_p6.mat"),
]
NOMINAL_N100 = "pred_sprinting_data_10-April-2026__16-29-40___Nominal.mat"
NOMINAL_COORDS = "pred_sprinting_coords_10-April-2026__16-29-40___Nominal.mot"
NOMINAL_ACTS = "pred_sprinting_acts_10-April-2026__16-29-40___Nominal.sto"
EXP_IK = os.path.join(EXP_IK_DIR, "Splined_100_meshInts_p02_maxVel_01.mot")


# --------------------------------------------------------------------------- io helpers
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
    y = np.asarray(y, float)
    x = np.asarray(x, float)
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x))) if y.size > 1 else 0.0


def load(path):
    """Load one optimumOutput MAT into the fields every figure needs."""
    if not os.path.isabs(path):
        path = os.path.join(RESULTS, path)
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    mv = _g(o, "muscleValues")
    A = lambda k: np.asarray(_g(mv, k), float)
    t = np.asarray(_g(o, "timeNodes"), float).ravel()
    lMtilde = A("lMtilde")
    ncol = lMtilde.shape[1]
    assert t.size == ncol, f"timeNodes {t.size} != cols {ncol}"
    vMax = A("vMax")
    if vMax.ndim == 1:
        vMax = np.repeat(vMax[:, None], ncol, axis=1)
    q = np.asarray(_g(o, "optVars_nsc", "q"), float)
    return dict(
        path=path, name=os.path.basename(path), t=t,
        lMtilde=lMtilde, lM=A("lM"), lMT=A("lMTk_lr"), Fce=A("Fce"),
        Fpass=A("Fpass"), FT=A("FT"), vMtilde=A("vMtilde"), vMax=vMax,
        Fpetilde=A("Fpetilde"),
        N=int(np.asarray(_g(o, "options", "N")).ravel()[0]),
        status=str(_g(o, "stats", "return_status")),
        inf_pr=float(np.asarray(_g(o, "stats", "iterations", "inf_pr"), float).ravel()[-1]),
        speed=float(np.asarray(_g(o, "ave_speed")).ravel()[0]),
        td=float(np.degrees(q[0, 0])),
        totalTime=float(np.asarray(_g(o, "optVars_nsc", "totalTime")).ravel()[0]),
        GRF_R=np.asarray(_g(o, "GRFs", "R"), float),
    )


def contact_s(d):
    """Ground-contact duration (s), peak vertical GRF (BW), and td_is_contact flag."""
    g = d["GRF_R"]
    t = d["t"]
    n = t.size
    if g.shape[0] != n and g.shape[1] == n:
        g = g.T
    vert = g[:, int(np.argmax(np.ptp(g, axis=0)))]   # vertical = largest peak-to-peak column
    stance = vert > 0.05 * BW
    to = 0
    while to + 1 < n and stance[to + 1]:
        to += 1
    return float(t[to] - t[0]), float(vert.max() / BW), bool(stance[0])


def stride(d, nm):
    """Reconstructed reference (right)-limb FULL stride for muscle nm."""
    t = d["t"]
    T = float(t[-1] - t[0])
    rR, rL = R[nm], L[nm]
    cat = lambda f: np.concatenate([d[f][rR], d[f][rL]])
    vM = np.concatenate([d["vMtilde"][rR] * d["vMax"][rR], d["vMtilde"][rL] * d["vMax"][rL]])
    ts = np.concatenate([t - t[0], (t - t[0]) + T])
    seam_gap = abs(float(d["lMtilde"][rR][-1] - d["lMtilde"][rL][0]))
    return dict(t=ts, T=T, strideT=2.0 * T, lMtilde=cat("lMtilde"), lMT=cat("lMT"),
                Fce=cat("Fce"), Fpass=cat("Fpass"), FT=cat("FT"),
                Fpetilde=cat("Fpetilde"), vM=vM, seam_gap=seam_gap)


def metrics(d, nm, contact):
    """Per-muscle scalar metrics on the reconstructed stride (matches audit)."""
    s = stride(d, nm)
    t = s["t"]
    lMt = s["lMtilde"]
    fce, fpa, ft, vM, fpet = s["Fce"], s["Fpass"], s["FT"], s["vM"], s["Fpetilde"]
    strideT = s["strideT"]
    ip = int(np.argmax(lMt))
    tpk = 100.0 * t[ip] / strideT
    tsw_start = strideT - TS_SWING_FRAC * (strideT - contact) if np.isfinite(contact) else 0.8 * strideT
    mwin = t >= tsw_start
    act_pow = np.clip(fce * vM, 0.0, None)
    pkR = float(d["lMtilde"][R[nm]].max())
    pkL = float(d["lMtilde"][L[nm]].max())
    return dict(
        peak_lMtilde=float(lMt.max()), tPeak_pct=tpk,
        peak_lMtilde_R=pkR, peak_lMtilde_L=pkL, bimean=0.5 * (pkR + pkL),
        seam_gap=s["seam_gap"],
        TS_peak_lMtilde=float(lMt[mwin].max()) if mwin.sum() else np.nan,
        peak_Fce_N=float(fce.max()), peak_Fpass_N=float(fpa.max()),
        peak_FT_N=float(ft.max()), peak_Fpetilde=float(fpet.max()),
        peak_leng_vel_mps=float(np.clip(vM, 0, None).max()),
        neg_fiber_work_J=trap(act_pow, t),
        peak_MTU_len_m=float(s["lMT"].max()), MTU_excursion_m=float(s["lMT"].max() - s["lMT"].min()),
        tsw_start_pct=100.0 * tsw_start / strideT,
    )


def stride_waveform(d, nm, grid):
    """lMtilde (and Fce, Fpass, vM) resampled onto a common %-stride grid for display.

    Peaks are always read from metrics() on the NATIVE nodes; the resampled curve
    is for plotting only.
    """
    s = stride(d, nm)
    pct = 100.0 * s["t"] / s["strideT"]
    out = {"pct": grid}
    for k in ("lMtilde", "Fce", "Fpass", "FT", "vM"):
        out[k] = np.interp(grid, pct, s[k])
    return out


# --------------------------------------------------------------------------- regression
def fit(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    Amat = np.vstack([x, np.ones_like(x)]).T
    sl, ic = np.linalg.lstsq(Amat, y, rcond=None)[0]
    yh = sl * x + ic
    r2 = 1 - np.sum((y - yh) ** 2) / (np.sum((y - y.mean()) ** 2) + 1e-15)
    return sl, ic, r2


def loo_slopes(x, y):
    out = []
    for i in range(len(x)):
        out.append(fit(np.delete(x, i), np.delete(y, i))[0])
    return min(out), max(out)


def speed_adj_coef(anterior, speed, y):
    X = np.vstack([anterior, speed, np.ones_like(anterior)]).T
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    return float(beta[0])


# --------------------------------------------------------------------------- .mot / .sto
def read_mot(path):
    """Return (columns_simplified, ndata) for an OpenSim .mot/.sto; angles in deg."""
    lines = open(path, "r", errors="replace").read().splitlines()
    hi = next(i for i, l in enumerate(lines) if l.strip().lower() == "endheader")
    header = [h.strip() for h in lines[hi + 1].split("\t") if h.strip()]
    rows = [[float(v) for v in l.split()] for l in lines[hi + 2:]
            if len(l.split()) == len(header)]
    simp = []
    for h in header:
        parts = [p for p in h.split("/") if p]
        simp.append(parts[-2] if parts and parts[-1] == "value" and len(parts) >= 2 else h)
    return simp, np.asarray(rows, float)


# --------------------------------------------------------------------------- primary loader
def load_primary_N100():
    """Return the 8 selected N=100 conditions, sorted by anterior tilt ascending."""
    conds = []
    for off, fn in SELECTED_N100:
        d = load(fn)
        c, pkbw, tdc = contact_s(d)
        conds.append(dict(offset=off, file=fn, d=d, contact=c, peakVGRF_BW=pkbw,
                          td_is_contact=tdc, anterior=round(-d["td"], 4),
                          speed=d["speed"], status=d["status"], inf_pr=d["inf_pr"],
                          m={nm: metrics(d, nm, c) for nm in MUS}))
    conds.sort(key=lambda r: r["anterior"])
    return conds


# --------------------------------------------------------------------------- matplotlib
def setup_mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm
    # register Meiryo so any stray JP renders (figures are kept English for portability)
    for p in (r"C:\Windows\Fonts\meiryo.ttc",):
        if os.path.exists(p):
            try:
                fm.fontManager.addfont(p)
            except Exception:
                pass
    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "svg.fonttype": "none",          # keep SVG text editable
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "font.family": "DejaVu Sans", "font.size": 9,
        "axes.titlesize": 10, "axes.labelsize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
        "axes.linewidth": 0.8, "lines.linewidth": 1.6,
        "figure.dpi": 120, "savefig.dpi": 600, "savefig.bbox": "tight",
    })
    return plt


def tilt_cmap():
    """Sequential map: darker = larger anterior tilt, both ends visible on white."""
    import matplotlib.pyplot as plt
    base = plt.get_cmap("Blues")
    return lambda norm: base(0.28 + 0.68 * float(np.clip(norm, 0, 1)))


def save_fig(fig, stem):
    """Write PDF + SVG + 600-dpi PNG; return the three paths (relative to OUTDIR)."""
    import matplotlib.pyplot as plt
    pdf = os.path.join(FIG_PDF, stem + ".pdf")
    svg = os.path.join(FIG_SVG, stem + ".svg")
    png = os.path.join(FIG_PNG, stem + ".png")
    fig.savefig(pdf)
    fig.savefig(svg)
    fig.savefig(png, dpi=600)
    plt.close(fig)
    rel = lambda p: os.path.relpath(p, OUTDIR).replace("\\", "/")
    return rel(pdf), rel(svg), rel(png)


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return os.path.relpath(path, OUTDIR).replace("\\", "/")


def write_manifest_fragment(fig_id, rows):
    """rows: list of dicts. Written to qa/manifest_<fig_id>.csv for later aggregation."""
    cols = ["figure_id", "panel_id", "analytical_question", "takeaway", "input_path",
            "input_sha256", "source_commit", "simulation_commit", "analysis_commit",
            "mesh", "condition_family", "solver_acceptance_rule",
            "muscle_names_and_indices", "phase_window", "metric_formula", "source_csv",
            "plotting_script", "pdf_path", "svg_path", "png_path", "generated_at", "qa_status"]
    p = os.path.join(QA, f"manifest_{fig_id}.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return p
