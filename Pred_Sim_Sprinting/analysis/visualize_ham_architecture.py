"""
visualize_ham_architecture.py
=============================
Advanced, publication-quality visualisations of the hamstring muscle-architecture
study (RQ2). Turns the numbers into intuition with four figures:

  1. viz_speed_injury_landscape.png   -- the "two orthogonal levers" trade-off map:
        every virtual athlete plotted in (top speed, peak fascicle strain) space.
        Fascicle length moves you vertically (strain) at ~constant speed; strength
        moves you horizontally (speed) at ~constant strain.
  2. viz_forcelength_operating_points.png -- WHY short fascicles are dangerous:
        the muscle's active force-length multiplier (Fiso) and passive force
        (Fpetilde) vs normalised fibre length, with each condition's PEAK operating
        point overlaid. Shows the operating point sliding off the plateau onto the
        descending limb / passive wall as fascicles shorten (active->passive shift).
  3. viz_stride_waveforms.png         -- WHEN it happens: fibre length, passive
        force and active eccentric power over the stride for short/nominal/long
        fascicle athletes, with stance shading and peak markers.
  4. viz_permuscle_heatmap.png        -- per-muscle pattern: peak strain & peak
        passive force across the fascicle sweep, showing the biarticular escalation
        vs the flat monoarticular (bifemsh) control.
  + viz_dashboard.png                 -- a 2x2 one-glance summary.

All labels are in English to avoid CJK font issues. Figures saved under
Results/HamArch_Study/. Requires matplotlib. Representative muscle: biceps femoris
long head (bifemlh) -- the most commonly injured hamstring and the one whose
fascicle length is the epidemiological risk factor (Timmins 2016).
"""
import glob
import os
import re

import numpy as np
from scipy.io import loadmat

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib import cm

from injury_metrics import (BIARTIC, HAM, HAM_L, HAM_R, RESULTS, _get,
                            _stance_mask_R, compute_injury_metrics)

if not hasattr(cm, "get_cmap"):          # matplotlib >= 3.9 removed cm.get_cmap
    cm.get_cmap = lambda n: matplotlib.colormaps[n]
else:                                    # <3.9: override to silence deprecation warning
    cm.get_cmap = lambda n: matplotlib.colormaps[n]

OUTDIR = os.path.join(RESULTS, "HamArch_Study")
MUSC_ROW = {nm: (HAM_L[i], HAM_R[i]) for i, nm in enumerate(HAM)}
FASC_CMAP = "RdYlBu"           # low factor (short/weak) -> red (danger)
FNORM = TwoSlopeNorm(vcenter=1.0, vmin=0.70, vmax=1.20)


def _factor(cond):
    m = re.search(r"([mp])(\d+)", cond)
    if not m:
        return 1.0
    return 1.0 + (-1 if m.group(1) == "m" else 1) * int(m.group(2)) / 100.0


def _newest(patterns):
    files = {}
    for pat in patterns:
        for f in glob.glob(os.path.join(RESULTS, pat)):
            tok = re.search(r"___(.+)\.mat$", os.path.basename(f))
            tok = tok.group(1) if tok else os.path.basename(f)
            if tok not in files or os.path.getmtime(f) > os.path.getmtime(files[tok]):
                files[tok] = f
    return files


def collect_scalars(mode, include_nominal):
    pats = [f"pred_sprinting_data_*Ham{mode}*.mat"]
    if include_nominal:
        pats.append("pred_sprinting_data_*Nominal.mat")
    rows = []
    for cond, f in _newest(pats).items():
        d = compute_injury_metrics(f)
        if d.get("N") != 50:
            continue
        d["cond"] = cond
        d["factor"] = _factor(cond)
        d["biartic_peak"] = float(np.mean([d[m + "_peak_lMtilde"] for m in BIARTIC]))
        d["biartic_passive"] = float(np.mean([d[m + "_peak_Fpetilde"] for m in BIARTIC]))
        rows.append(d)
    rows.sort(key=lambda r: r["factor"])
    return rows


def load_series(path, musc="bifemlh", leg="R"):
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    mv = _get(o, "muscleValues")
    row = MUSC_ROW[musc][1 if leg == "R" else 0]

    def a(n):
        return np.asarray(_get(mv, n), dtype=float)[row]

    lMtilde, Fpe, Fce, Fiso = a("lMtilde"), a("Fpetilde"), a("Fce"), a("Fiso")
    lM = a("lM")
    vMtilde, vMax = a("vMtilde"), a("vMax")
    T = lMtilde.shape[0]
    try:
        tt = float(_get(o, "optVars_nsc", "totalTime"))
    except Exception:
        tt = 1.0
    t = np.linspace(0.0, tt, T)
    dlmdt = np.gradient(lM, t)
    ecc_power = Fce * np.clip(dlmdt, 0.0, None)
    stance = _stance_mask_R(o, T)
    return {
        "factor": _factor(os.path.basename(path)),
        "t_pct": 100.0 * t / (t[-1] + 1e-9),
        "lMtilde": lMtilde, "Fpe": Fpe, "Fiso": Fiso,
        "ecc_power": ecc_power, "stance": stance,
    }


# --------------------------------------------------------------------------- #
#  Figure 1: speed-injury landscape
# --------------------------------------------------------------------------- #
def plot_landscape(ax):
    fasc = collect_scalars("Fascicle", include_nominal=False)   # p00 is the 1.0 point
    stre = collect_scalars("Strength", include_nominal=True)    # Nominal is the 1.0 point

    fx = [r["speed"] for r in fasc]; fy = [r["biartic_peak"] for r in fasc]
    sx = [r["speed"] for r in stre]; sy = [r["biartic_peak"] for r in stre]

    ax.axhspan(1.15, 1.75, color="red", alpha=0.06)
    ax.text(11.98, 1.45, "high strain-injury risk\n(descending limb)",
            color="firebrick", fontsize=8, ha="right", va="center")
    ax.axhline(1.0, ls=":", color="grey", lw=1)

    ax.plot(fx, fy, "-", color="0.6", lw=1, zorder=1)
    ax.scatter(fx, fy, c=[r["factor"] for r in fasc], cmap=FASC_CMAP, norm=FNORM,
               s=170, marker="o", edgecolor="k", zorder=3, label="fibre-length sweep")
    ax.plot(sx, sy, "-", color="0.6", lw=1, zorder=1)
    ax.scatter(sx, sy, c=[r["factor"] for r in stre], cmap="PuOr", norm=FNORM,
               s=150, marker="s", edgecolor="k", zorder=3, label="strength sweep")

    # annotate the two orthogonal effect directions
    ax.annotate("", xy=(11.70, 1.55), xytext=(11.70, 1.02),
                arrowprops=dict(arrowstyle="-|>", color="crimson", lw=2))
    ax.text(11.72, 1.30, "shorter\nfascicle", color="crimson", fontsize=9, va="center")
    ax.annotate("", xy=(11.50, 0.95), xytext=(11.92, 0.95),
                arrowprops=dict(arrowstyle="-|>", color="navy", lw=2))
    ax.text(11.71, 0.90, "weaker", color="navy", fontsize=9, ha="center")

    for r in fasc:
        if abs(r["factor"] - 0.70) < 1e-6 or abs(r["factor"] - 1.20) < 1e-6:
            ax.annotate(f"x{r['factor']:.2f}", (r["speed"], r["biartic_peak"]),
                        textcoords="offset points", xytext=(6, 6), fontsize=8)
    ax.set_xlabel("top sprinting speed (m/s)")
    ax.set_ylabel("peak fascicle strain (norm. fibre length)")
    ax.set_title("A  Speed-injury landscape: two orthogonal levers")
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(alpha=0.25)


# --------------------------------------------------------------------------- #
#  Figure 2: force-length operating points
# --------------------------------------------------------------------------- #
def plot_forcelength(ax, series):
    # Pool (lMtilde, Fiso) and (lMtilde, Fpetilde); both are functions of lMtilde.
    allx = np.concatenate([s["lMtilde"] for s in series])
    fiso = np.concatenate([s["Fiso"] for s in series])
    fpe = np.concatenate([s["Fpe"] for s in series])
    order = np.argsort(allx)
    ax.plot(allx[order], fiso[order], color="seagreen", lw=2.5,
            label="active force-length (capacity)")
    ax.plot(allx[order], fpe[order], color="firebrick", lw=2.5,
            label="passive force")
    ax.axvspan(0.9, 1.1, color="seagreen", alpha=0.08)
    ax.text(1.0, 1.05, "plateau\n(safe)", color="seagreen", fontsize=8, ha="center")

    for s in series:
        pk = float(s["lMtilde"].max())
        col = cm.get_cmap(FASC_CMAP)(FNORM(s["factor"]))
        ax.axvline(pk, color=col, lw=2, ls="--", alpha=0.9)
        ax.plot(pk, float(s["Fpe"][np.argmax(s["lMtilde"])]), "o", color=col,
                markeredgecolor="k", markersize=9, zorder=5)
    ax.annotate("short fascicle:\nactive collapses,\npassive explodes",
                xy=(1.55, 1.0), xytext=(1.28, 1.35), fontsize=8, color="firebrick",
                arrowprops=dict(arrowstyle="-|>", color="firebrick"))
    ax.set_xlabel("normalised fibre length lMtilde  (peak operating point per athlete)")
    ax.set_ylabel("normalised force")
    ax.set_title("B  Why short fascicles are dangerous (operating point)")
    ax.set_ylim(-0.05, 1.75)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.25)


# --------------------------------------------------------------------------- #
#  Figure 3: stride waveforms
# --------------------------------------------------------------------------- #
def plot_waveforms(axes, series3):
    titles = ["fibre length lMtilde", "passive force Fpetilde",
              "active eccentric power (W)"]
    keys = ["lMtilde", "Fpe", "ecc_power"]
    for ax, key, title in zip(axes, keys, titles):
        for s in series3:
            col = cm.get_cmap(FASC_CMAP)(FNORM(s["factor"]))
            ax.plot(s["t_pct"], s[key], color=col, lw=2,
                    label=f"x{s['factor']:.2f}")
            ip = int(np.argmax(s["lMtilde"]))
            if key == "lMtilde":
                ax.plot(s["t_pct"][ip], s[key][ip], "v", color=col,
                        markeredgecolor="k", zorder=5)
        # stance shading from the nominal-ish middle athlete
        st = series3[len(series3) // 2]["stance"]
        if st is not None:
            tp = series3[len(series3) // 2]["t_pct"]
            ax.fill_between(tp, *ax.get_ylim(), where=st, color="grey",
                            alpha=0.12, step="mid")
        if key == "lMtilde":
            ax.axhline(1.0, ls=":", color="grey", lw=1)
        ax.set_ylabel(title)
        ax.grid(alpha=0.25)
    axes[0].set_title("C  Stride dynamics (biceps femoris long head, right leg)")
    axes[0].legend(loc="upper right", fontsize=8, ncol=3, title="fibre-length factor")
    axes[-1].set_xlabel("stride (% from touchdown);  grey = right-foot stance")


# --------------------------------------------------------------------------- #
#  Figure 4: per-muscle heatmaps
# --------------------------------------------------------------------------- #
def plot_single_heatmap(ax, metric="strain", tag="D"):
    rows = collect_scalars("Fascicle", include_nominal=False)
    factors = [r["factor"] for r in rows]
    if metric == "strain":
        M = np.array([[r[m + "_peak_lMtilde"] for r in rows] for m in HAM])
        title = f"{tag}  peak fascicle strain (lMtilde)"
    else:
        M = np.array([[r[m + "_peak_Fpetilde"] for r in rows] for m in HAM])
        title = f"{tag}  peak passive force (/Fmax)"
    labels = ["semimem\n(bi)", "semiten\n(bi)", "bifemlh\n(bi)", "bifemsh\n(mono)"]
    im = ax.imshow(M, aspect="auto", cmap="YlOrRd", origin="upper")
    ax.set_xticks(range(len(factors)))
    ax.set_xticklabels([f"{f:.2f}" for f in factors])
    ax.set_yticks(range(len(HAM)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("fibre-length factor")
    ax.set_title(title, fontsize=10)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center",
                    fontsize=7, color="black")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


def _rep_series():
    """Short / nominal / long fascicle representative waveforms."""
    want = ["HamFascicle_m30", "HamFascicle_p00", "HamFascicle_p20"]
    out = []
    for w in want:
        fs = sorted(glob.glob(os.path.join(RESULTS, f"pred_sprinting_data_*{w}.mat")))
        if fs:
            out.append(load_series(fs[-1]))
    return out


def _all_fascicle_series():
    files = _newest(["pred_sprinting_data_*HamFascicle*.mat"])
    return [load_series(f) for f in files.values()]


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    all_series = sorted(_all_fascicle_series(), key=lambda s: s["factor"])
    rep = _rep_series()

    # Fig 1
    fig, ax = plt.subplots(figsize=(8, 6))
    plot_landscape(ax)
    fig.tight_layout(); fig.savefig(os.path.join(OUTDIR, "viz_speed_injury_landscape.png"), dpi=150)
    plt.close(fig)

    # Fig 2
    fig, ax = plt.subplots(figsize=(8, 6))
    plot_forcelength(ax, all_series)
    fig.tight_layout(); fig.savefig(os.path.join(OUTDIR, "viz_forcelength_operating_points.png"), dpi=150)
    plt.close(fig)

    # Fig 3
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    plot_waveforms(axes, rep)
    fig.tight_layout(); fig.savefig(os.path.join(OUTDIR, "viz_stride_waveforms.png"), dpi=150)
    plt.close(fig)

    # Fig 4
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4))
    plot_single_heatmap(a1, "strain", "D")
    plot_single_heatmap(a2, "passive", "E")
    fig.tight_layout(); fig.savefig(os.path.join(OUTDIR, "viz_permuscle_heatmap.png"), dpi=150)
    plt.close(fig)

    # Dashboard
    fig = plt.figure(figsize=(15, 11))
    gs = fig.add_gridspec(2, 2)
    plot_landscape(fig.add_subplot(gs[0, 0]))
    plot_forcelength(fig.add_subplot(gs[0, 1]), all_series)
    ax_wave = fig.add_subplot(gs[1, 0])
    for s in rep:
        col = cm.get_cmap(FASC_CMAP)(FNORM(s["factor"]))
        ax_wave.plot(s["t_pct"], s["lMtilde"], color=col, lw=2, label=f"x{s['factor']:.2f}")
    ax_wave.axhline(1.0, ls=":", color="grey")
    ax_wave.set_title("C  fibre length over the stride (bifemlh)")
    ax_wave.set_xlabel("stride (%)"); ax_wave.set_ylabel("lMtilde")
    ax_wave.legend(fontsize=8, title="fibre factor"); ax_wave.grid(alpha=0.25)
    plot_single_heatmap(fig.add_subplot(gs[1, 1]), "strain", "D")
    fig.suptitle("Hamstring fascicle architecture and sprint injury risk - visual summary",
                 fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(os.path.join(OUTDIR, "viz_dashboard.png"), dpi=140)
    plt.close(fig)

    print("Saved figures to", OUTDIR)
    for f in ["viz_speed_injury_landscape.png", "viz_forcelength_operating_points.png",
              "viz_stride_waveforms.png", "viz_permuscle_heatmap.png", "viz_dashboard.png"]:
        print("  -", f)


if __name__ == "__main__":
    main()
