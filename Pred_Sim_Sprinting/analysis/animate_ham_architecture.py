"""
animate_ham_architecture.py
===========================
Animated (GIF) explainers for the hamstring fascicle-architecture study.
Turns the static findings into motion so the mechanism is obvious at a glance.

Produces (in Results/HamArch_Study/):
  anim_forcelength_sweep.gif   -- MECHANISM: as the fascicle-length factor sweeps
        from long (safe) to short (risky), the muscle's peak operating point
        slides off the force-length plateau; active capacity (green) collapses
        while passive force (red) climbs.
  anim_stride_stretch.gif      -- WHEN: a cursor sweeps the stride while the
        biceps femoris long-head fibre length rises to its peak, for short /
        nominal / long fascicle athletes; the marker turns red on the
        descending limb (>1.15).
  anim_leg_hamstring.gif       -- BIOMECHANICS: two schematic sagittal legs
        (short vs long fascicle) run through the stride with (near) identical
        motion, but the hamstring line is colour-coded by fascicle strain --
        the short-fascicle leg flushes red, the long one stays green.

Schematic leg geometry is illustrative (fixed hip, nominal segment lengths),
NOT exact OpenSim geometry; joint angles and fibre strain are the real data.
Labels are in English to avoid CJK font issues.
"""
import glob
import os

import numpy as np
from scipy.io import loadmat

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import Normalize

from injury_metrics import RESULTS, _get

OUTDIR = os.path.join(RESULTS, "HamArch_Study")
BFLH_R = 54                       # biceps femoris long head, right leg (0-based row)
Q_PTILT, Q_HIPFLEX, Q_KNEE = 0, 6, 9
STRAIN_NORM = Normalize(vmin=0.90, vmax=1.60)   # green(safe) -> red(danger)
STRAIN_CMAP = plt.get_cmap("RdYlGn_r")
FAC_CMAP = plt.get_cmap("RdYlBu")
FAC_NORM = Normalize(0.70, 1.20)


def _newest(sub):
    fs = sorted(glob.glob(os.path.join(RESULTS, f"pred_sprinting_data_*{sub}.mat")),
                key=os.path.getmtime)
    return fs[-1] if fs else None


def _interp(arr, F):
    arr = np.asarray(arr, dtype=float)
    xp = np.linspace(0, 1, arr.shape[-1])
    xq = np.linspace(0, 1, F)
    if arr.ndim == 1:
        return np.interp(xq, xp, arr)
    return np.vstack([np.interp(xq, xp, arr[i]) for i in range(arr.shape[0])])


def load_cond(sub, F=60):
    f = _newest(sub)
    if f is None:
        return None
    o = loadmat(f, struct_as_record=False, squeeze_me=True)["optimumOutput"]
    q = np.asarray(_get(o, "optVars_nsc", "q"), dtype=float)
    lM = np.asarray(_get(o, "muscleValues", "lMtilde"), dtype=float)
    fiso = np.asarray(_get(o, "muscleValues", "Fiso"), dtype=float)[BFLH_R]
    fpe = np.asarray(_get(o, "muscleValues", "Fpetilde"), dtype=float)[BFLH_R]
    return {
        "ptilt": _interp(q[Q_PTILT], F),
        "hip": _interp(q[Q_HIPFLEX], F),
        "knee": _interp(q[Q_KNEE], F),
        "strain": _interp(lM[BFLH_R], F),
        "lM_raw": lM[BFLH_R], "fiso_raw": fiso, "fpe_raw": fpe,
        "speed": float(_get(o, "ave_speed")),
    }


# --------------------------------------------------------------------------- #
#  Schematic sagittal-leg forward kinematics (illustrative)
# --------------------------------------------------------------------------- #
L_THIGH, L_SHANK, L_FOOT = 0.45, 0.45, 0.18


def leg_points(hipflex_deg, knee_deg):
    th = np.radians(hipflex_deg)                 # thigh angle from straight-down, +forward
    sh = np.radians(hipflex_deg + knee_deg)      # shank global angle (knee_deg<0 = flexion)
    hip = np.array([0.0, 0.0])
    knee = hip + L_THIGH * np.array([np.sin(th), -np.cos(th)])
    ankle = knee + L_SHANK * np.array([np.sin(sh), -np.cos(sh)])
    foot = ankle + L_FOOT * np.array([np.cos(sh), np.sin(sh)])   # ~forward
    ham_o = hip + np.array([-0.05, 0.06])        # ischial tuberosity (behind/above hip)
    shank_dir = np.array([np.sin(sh), -np.cos(sh)])
    ham_i = knee + 0.10 * shank_dir              # proximal posterior shank
    return hip, knee, ankle, foot, ham_o, ham_i


# --------------------------------------------------------------------------- #
#  Animation 1: force-length operating-point sweep
# --------------------------------------------------------------------------- #
def anim_forcelength():
    subs = ["HamFascicle_p20", "HamFascicle_p10", "HamFascicle_p00",
            "HamFascicle_m10", "HamFascicle_m20", "HamFascicle_m30"]
    facs = [1.20, 1.10, 1.00, 0.90, 0.80, 0.70]
    conds = [load_cond(s) for s in subs]
    conds = [(f, c) for f, c in zip(facs, conds) if c]
    # pooled FL curves
    allx = np.concatenate([c["lM_raw"] for _, c in conds])
    fiso = np.concatenate([c["fiso_raw"] for _, c in conds])
    fpe = np.concatenate([c["fpe_raw"] for _, c in conds])
    order = np.argsort(allx)
    gx = allx[order]
    gi = fiso[order]
    gp = fpe[order]
    peak_of_fac = {f: float(c["lM_raw"].max()) for f, c in conds}

    fac_grid = np.concatenate([np.linspace(1.20, 0.70, 40), np.linspace(0.70, 1.20, 40)])

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(gx, gi, color="seagreen", lw=2.5, label="active capacity (force-length)")
    ax.plot(gx, gp, color="firebrick", lw=2.5, label="passive force")
    ax.axvspan(0.9, 1.1, color="seagreen", alpha=0.08)
    ax.text(1.0, 1.02, "plateau (safe)", color="seagreen", ha="center", fontsize=8)
    ax.set_xlabel("normalised fibre length lMtilde")
    ax.set_ylabel("normalised force")
    ax.set_ylim(-0.05, 1.7)
    ax.set_xlim(float(gx.min()) - 0.02, float(gx.max()) + 0.05)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.25)
    vline = ax.axvline(1.0, color="k", lw=2, ls="--")
    dot_a, = ax.plot([], [], "o", color="seagreen", ms=12, mec="k", zorder=5)
    dot_p, = ax.plot([], [], "o", color="firebrick", ms=12, mec="k", zorder=5)
    txt = ax.text(0.98, 0.60, "", transform=ax.transAxes, ha="right", va="top",
                  fontsize=11, bbox=dict(boxstyle="round", fc="white", ec="0.7"))

    facs_sorted = np.array(sorted(peak_of_fac))
    peaks_sorted = np.array([peak_of_fac[f] for f in facs_sorted])

    def op_lm(fac):
        return float(np.interp(fac, facs_sorted, peaks_sorted))

    def update(i):
        fac = fac_grid[i]
        lm = op_lm(fac)
        a = float(np.interp(lm, gx, gi))
        p = float(np.interp(lm, gx, gp))
        vline.set_xdata([lm, lm])
        col = FAC_CMAP(FAC_NORM(fac))
        vline.set_color(col)
        dot_a.set_data([lm], [a])
        dot_p.set_data([lm], [p])
        flag = "RISK" if lm > 1.15 else "safe"
        txt.set_text(f"fibre-length x{fac:.2f}\noperating lMtilde = {lm:.2f}\n"
                     f"active capacity = {a:.2f}\npassive force = {p:.2f}\n[{flag}]")
        txt.set_color("firebrick" if lm > 1.15 else "seagreen")
        ax.set_title(f"Why short fascicles are dangerous  (fibre-length x{fac:.2f})")
        return vline, dot_a, dot_p, txt

    ani = FuncAnimation(fig, update, frames=len(fac_grid), blit=False)
    out = os.path.join(OUTDIR, "anim_forcelength_sweep.gif")
    ani.save(out, writer=PillowWriter(fps=18))
    plt.close(fig)
    return out


# --------------------------------------------------------------------------- #
#  Animation 2: stride stretch timeline
# --------------------------------------------------------------------------- #
def anim_stride():
    F = 80
    reps = [("HamFascicle_m30", 0.70), ("HamFascicle_p00", 1.00),
            ("HamFascicle_p20", 1.20)]
    data = [(fac, load_cond(sub, F)) for sub, fac in reps]
    data = [(fac, c) for fac, c in data if c]
    phase = np.linspace(0, 100, F)

    COLORS = {0.70: "crimson", 1.00: "0.25", 1.20: "navy"}
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axhspan(1.15, 1.7, color="red", alpha=0.06)
    lines = {}
    for fac, c in data:
        col = COLORS.get(round(fac, 2), "purple")
        ax.plot(phase, c["strain"], color=col, lw=2.5, alpha=0.85)
        lines[fac] = ax.plot([], [], "o", color=col, ms=13, mec="k", zorder=5)[0]
    ax.axhline(1.15, ls=":", color="firebrick", lw=1.2)
    ax.text(2, 1.17, "descending limb = injury-risk zone", color="firebrick", fontsize=8)
    ax.axhline(1.0, ls=":", color="grey", lw=1)
    cursor = ax.axvline(0, color="0.4", lw=1)
    ax.set_xlabel("stride (% from touchdown)")
    ax.set_ylabel("biceps femoris long head\nfibre length lMtilde")
    ax.set_title("Hamstring fibre length through the stride")
    ax.grid(alpha=0.25)
    ax.set_ylim(0.8, 1.65)
    leg = [plt.Line2D([], [], color=COLORS.get(round(f, 2), "purple"), lw=3,
                      label=f"fibre x{f:.2f}") for f, _ in data]
    ax.legend(handles=leg, loc="upper right", fontsize=8)

    def update(i):
        cursor.set_xdata([phase[i], phase[i]])
        arts = [cursor]
        for fac, c in data:
            y = c["strain"][i]
            ln = lines[fac]
            ln.set_data([phase[i]], [y])
            ln.set_markersize(18 if y > 1.15 else 11)
            arts.append(ln)
        return arts

    ani = FuncAnimation(fig, update, frames=F, blit=False)
    out = os.path.join(OUTDIR, "anim_stride_stretch.gif")
    ani.save(out, writer=PillowWriter(fps=18))
    plt.close(fig)
    return out


# --------------------------------------------------------------------------- #
#  Animation 3: schematic legs, hamstring coloured by strain
# --------------------------------------------------------------------------- #
def anim_leg():
    F = 60
    short = load_cond("HamFascicle_m30", F)
    long_ = load_cond("HamFascicle_p20", F)
    if not short or not long_:
        return None
    panels = [("short fascicle (x0.70)", short), ("long fascicle (x1.20)", long_)]

    fig, axes = plt.subplots(1, 2, figsize=(9, 5.5))
    sm = plt.cm.ScalarMappable(norm=STRAIN_NORM, cmap=STRAIN_CMAP)
    cbar = fig.colorbar(sm, ax=axes, fraction=0.046, pad=0.04)
    cbar.set_label("hamstring fascicle strain (lMtilde)")

    art = []
    for ax, (title, c) in zip(axes, panels):
        ax.set_xlim(-0.5, 0.6)
        ax.set_ylim(-0.98, 0.18)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=11)
        thigh, = ax.plot([], [], "-", color="0.25", lw=8, solid_capstyle="round")
        shank, = ax.plot([], [], "-", color="0.25", lw=8, solid_capstyle="round")
        ham, = ax.plot([], [], "-", lw=8, solid_capstyle="round")
        joints, = ax.plot([], [], "o", color="k", ms=8)
        lbl = ax.text(0.5, 0.03, "", transform=ax.transAxes, ha="center",
                      fontsize=12, bbox=dict(boxstyle="round", fc="white", ec="0.7"))
        art.append(dict(c=c, thigh=thigh, shank=shank, ham=ham,
                        joints=joints, lbl=lbl))
    sup = fig.suptitle("", fontsize=12)

    def update(i):
        arts = [sup]
        for a in art:
            c = a["c"]
            hip, knee, ankle, foot, ho, hi = leg_points(c["hip"][i], c["knee"][i])
            a["thigh"].set_data([hip[0], knee[0]], [hip[1], knee[1]])
            a["shank"].set_data([knee[0], ankle[0]], [knee[1], ankle[1]])
            a["ham"].set_data([ho[0], hi[0]], [ho[1], hi[1]])
            a["ham"].set_color(STRAIN_CMAP(STRAIN_NORM(c["strain"][i])))
            a["joints"].set_data([hip[0], knee[0], ankle[0]], [hip[1], knee[1], ankle[1]])
            flag = "RISK" if c["strain"][i] > 1.15 else "safe"
            a["lbl"].set_text(f"strain {c['strain'][i]:.2f}  [{flag}]")
            arts += [a["thigh"], a["shank"], a["ham"], a["joints"], a["lbl"]]
        sup.set_text(f"Same sprinting motion, different internal danger   "
                     f"(stride {100*i/(F-1):.0f}%)")
        return arts

    ani = FuncAnimation(fig, update, frames=F, blit=False)
    out = os.path.join(OUTDIR, "anim_leg_hamstring.gif")
    ani.save(out, writer=PillowWriter(fps=15))
    plt.close(fig)
    return out


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    for fn in (anim_forcelength, anim_stride, anim_leg):
        out = fn()
        print("saved", out)


if __name__ == "__main__":
    main()
