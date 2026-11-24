"""
animate_ham_pareto.py
=====================
Animated (GIF) explainer for the injury-minimising optimal-technique study.

Produces (in Results/HamPareto_Study/):
  anim_pareto_sweep.gif -- as the injury-penalty weight is dialled up, the
        operating point slides DOWN the speed<->strain Pareto frontier (left
        panel) while a schematic sagittal leg runs the actual re-optimised
        stride (right panel) with the hamstring line colour-coded by fascicle
        strain. The motion barely changes, yet the hamstring cools from red
        (risky) toward green (safe): "almost the same run, much safer".

Schematic leg geometry is illustrative (fixed hip, nominal segment lengths),
NOT exact OpenSim geometry; joint angles and fibre strain are the real data.
Labels are in English to avoid CJK font issues. Reads saved data only.

Usage:
    python animate_ham_pareto.py
"""
import glob
import os
import re

import numpy as np
from scipy.io import loadmat

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import Normalize

from injury_metrics import RESULTS, _get, BIARTIC, HAM_R

OUTDIR = os.path.join(RESULTS, "HamPareto_Study")
BFLH_R = 54                       # biceps femoris long head, right leg (0-based row)
Q_PTILT, Q_HIPFLEX, Q_KNEE = 0, 6, 9
STRAIN_NORM = Normalize(vmin=0.90, vmax=1.30)   # green(safe) -> red(danger)
STRAIN_CMAP = plt.get_cmap("RdYlGn_r")
L_THIGH, L_SHANK, L_FOOT = 0.45, 0.45, 0.18
FRAMES_PER_COND = 22


def _weight(cond):
    m = re.search(r"HamPareto_Nom_w(\d+)", cond)
    return int(m.group(1)) / 1000.0 if m else None


def _interp(arr, F):
    arr = np.asarray(arr, dtype=float)
    xp = np.linspace(0, 1, arr.shape[-1])
    xq = np.linspace(0, 1, F)
    if arr.ndim == 1:
        return np.interp(xq, xp, arr)
    return np.vstack([np.interp(xq, xp, arr[i]) for i in range(arr.shape[0])])


def load_cond(path, F=FRAMES_PER_COND):
    o = loadmat(path, struct_as_record=False, squeeze_me=True)["optimumOutput"]
    q = np.asarray(_get(o, "optVars_nsc", "q"), dtype=float)
    lM = np.asarray(_get(o, "muscleValues", "lMtilde"), dtype=float)
    peak = float(np.mean([np.asarray(_get(o, "muscleValues", "lMtilde"))[r].max()
                          for r in HAM_R[:3]]))  # biarticular-mean peak
    return {
        "hip": _interp(np.degrees(q[Q_HIPFLEX]), F),
        "knee": _interp(np.degrees(q[Q_KNEE]), F),
        "strain": _interp(lM[BFLH_R], F),
        "peak": peak,
        "speed": float(_get(o, "ave_speed")),
    }


def collect_nom():
    """Newest nominal Pareto result per weight, sorted by weight ascending."""
    seen = {}
    for f in glob.glob(os.path.join(RESULTS, "pred_sprinting_data_*HamPareto_Nom_w*.mat")):
        w = _weight(os.path.basename(f))
        if w is None:
            continue
        if w not in seen or os.path.getmtime(f) > os.path.getmtime(seen[w]):
            seen[w] = f
    return [(w, seen[w]) for w in sorted(seen)]


def leg_points(hipflex_deg, knee_deg):
    th = np.radians(hipflex_deg)
    sh = np.radians(hipflex_deg + knee_deg)
    hip = np.array([0.0, 0.0])
    knee = hip + L_THIGH * np.array([np.sin(th), -np.cos(th)])
    ankle = knee + L_SHANK * np.array([np.sin(sh), -np.cos(sh)])
    foot = ankle + L_FOOT * np.array([np.cos(sh), np.sin(sh)])
    ham_o = hip + np.array([-0.05, 0.06])
    shank_dir = np.array([np.sin(sh), -np.cos(sh)])
    ham_i = knee + 0.10 * shank_dir
    return hip, knee, ankle, foot, ham_o, ham_i


def main():
    items = collect_nom()
    if len(items) < 2:
        print("[anim skipped] need >=2 nominal Pareto weights. Run run_ham_pareto.bat nominal.")
        return
    weights = [w for w, _ in items]
    conds = [load_cond(f) for _, f in items]
    speeds = [c["speed"] for c in conds]
    peaks = [c["peak"] for c in conds]

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.5, 5.2))
    # Left: frontier
    axL.plot(peaks, speeds, "o-", color="navy", zorder=2)
    axL.axvline(1.15, ls="--", color="red", lw=1, alpha=0.6)
    axL.axvspan(1.15, max(peaks) + 0.05, color="red", alpha=0.06)
    axL.set_xlabel("peak biarticular fascicle strain")
    axL.set_ylabel("top sprinting speed (m/s)")
    axL.set_title("Pareto frontier (marker = current technique)")
    axL.grid(alpha=0.3)
    marker, = axL.plot([], [], "*", color="gold", markersize=22,
                       markeredgecolor="k", zorder=5)

    axR.set_xlim(-0.6, 0.6)
    axR.set_ylim(-1.05, 0.35)
    axR.set_aspect("equal")
    axR.axis("off")
    axR.set_title("re-optimised stride (hamstring = fascicle strain)")
    (leg_line,) = axR.plot([], [], "-", color="black", lw=4, solid_capstyle="round")
    (ham_line,) = axR.plot([], [], "-", lw=6, solid_capstyle="round")
    txt = axR.text(-0.55, 0.28, "", fontsize=10, va="top")
    sm = plt.cm.ScalarMappable(norm=STRAIN_NORM, cmap=STRAIN_CMAP)
    fig.colorbar(sm, ax=axR, fraction=0.046, pad=0.04, label="fascicle strain (lMtilde)")

    total = len(items) * FRAMES_PER_COND

    def update(fr):
        ci = min(fr // FRAMES_PER_COND, len(conds) - 1)
        fi = fr % FRAMES_PER_COND
        c = conds[ci]
        marker.set_data([peaks[ci]], [speeds[ci]])
        hip, knee, ankle, foot, ham_o, ham_i = leg_points(c["hip"][fi], c["knee"][fi])
        xs = [hip[0], knee[0], ankle[0], foot[0]]
        ys = [hip[1], knee[1], ankle[1], foot[1]]
        leg_line.set_data(xs, ys)
        strain = c["strain"][fi]
        ham_line.set_data([ham_o[0], ham_i[0]], [ham_o[1], ham_i[1]])
        ham_line.set_color(STRAIN_CMAP(STRAIN_NORM(strain)))
        flag = "RISK" if c["peak"] > 1.15 else "safe"
        txt.set_text(f"penalty wJ(13) = {weights[ci]:.2f}\n"
                     f"top speed = {c['speed']:.2f} m/s\n"
                     f"peak fascicle strain = {c['peak']:.3f}  [{flag}]")
        return marker, leg_line, ham_line, txt

    anim = FuncAnimation(fig, update, frames=total, interval=60, blit=True)
    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, "anim_pareto_sweep.gif")
    anim.save(out, writer=PillowWriter(fps=18))
    plt.close(fig)
    print(f"Animation saved: {out}")


if __name__ == "__main__":
    main()
