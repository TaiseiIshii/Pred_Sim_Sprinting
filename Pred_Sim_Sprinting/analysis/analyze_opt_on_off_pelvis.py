"""
analyze_opt_on_off_pelvis.py   (opencap / OpenSim 4.x env)
STEP 2 (supervisor remark #3): separate the DIRECT effect of the imposed pelvic
tilt from the effect of the whole-body RE-OPTIMIZATION.

Definitions
-----------
opt-OFF : take the Nominal optimal kinematics and rigidly add the pelvic-tilt
          offset to the pelvis_tilt coordinate ONLY (every other joint stays at
          Nominal). No re-optimization. Compute hamstring MTU length via OpenSim.
opt-ON  : the actual re-optimized _PelvisShift_ solution for the same offset
          (whole motion re-solved with pelvis_tilt pinned). Compute the same.

Because the hamstrings span hip & knee (in the pelvis frame) and NOT the
pelvis-ground pelvis_tilt DOF, opt-OFF hamstring MTU length is expected to equal
Nominal exactly (direct tilt effect = 0). Any dose-response therefore comes
entirely from the re-optimized coordination (chiefly hip flexion). This script
quantifies that and writes Figure 4 + a CSV.

Run:
  & '...\\envs\\opencap\\python.exe' analysis\\analyze_opt_on_off_pelvis.py
"""
import csv
import glob
import os
import re

import numpy as np
import opensim as osim
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "Results")
MODEL = os.path.join(HERE, "..", "OpenSimModel",
                     "Scaled_FullBody_HamnerModel_Muscle_withContact.osim")
OUTDIR = os.path.join(RESULTS, "PelvicShift_Study")
HAM_L = ["semimem_l", "semiten_l", "bifemlh_l"]      # biarticular, left (terminal-swing peak in-window)
ALL_HAM_L = HAM_L + ["bifemsh_l"]


def read_mot(path):
    """Return (time(F,), colnames[list], data(F,C)) for an OpenSim .mot (deg)."""
    lines = open(path, "r", errors="replace").read().splitlines()
    hi = next(i for i, l in enumerate(lines) if l.strip().lower() == "endheader")
    header = lines[hi + 1].split("\t")
    header = [h.strip() for h in header if h.strip()]
    rows = []
    for l in lines[hi + 2:]:
        s = l.split()
        if len(s) == len(header):
            rows.append([float(v) for v in s])
    arr = np.asarray(rows, float)
    return arr[:, 0], header, arr


def coord_name(colheader):
    """'/jointset/hip_l/hip_flexion_l/value' -> 'hip_flexion_l'."""
    parts = [p for p in colheader.split("/") if p]
    if parts and parts[-1] == "value" and len(parts) >= 2:
        return parts[-2]
    return colheader


def ham_mtu_trajectory(model, state, time, header, data, tilt_offset_deg=0.0):
    """Compute left-hamstring MTU length trajectory for the given .mot pose set.

    tilt_offset_deg is ADDED to the pelvis_tilt column (opt-OFF manipulation).
    Returns dict[muscle] -> (F,) MTU length in metres.
    """
    cset = model.getCoordinateSet()
    coord_names = {cset.get(i).getName(): cset.get(i)
                   for i in range(cset.getSize())}
    colmap = []
    for c, h in enumerate(header):
        if c == 0:
            continue
        cn = coord_name(h)
        if cn in coord_names:
            colmap.append((c, cn))
    out = {m: np.zeros(len(time)) for m in ALL_HAM_L}
    for f in range(len(time)):
        for c, cn in colmap:
            val = data[f, c]
            if cn == "pelvis_tilt":
                val = val + tilt_offset_deg
            # translations (pelvis_tx/ty/tz) are in metres, not degrees
            if cn in ("pelvis_tx", "pelvis_ty", "pelvis_tz"):
                coord_names[cn].setValue(state, val, False)
            else:
                coord_names[cn].setValue(state, np.radians(val), False)
        model.assemble(state)
        model.realizePosition(state)
        for m in ALL_HAM_L:
            out[m][f] = model.getMuscles().get(m).getLength(state)
    return out


def peak_swing(traj):
    """Peak (max) MTU length over the step for each muscle (terminal-swing peak)."""
    return {m: float(v.max()) for m, v in traj.items()}


def load_meta():
    """offset -> (speed, ptMean, hipR_TD) from the P0 CSV (plain csv, no scipy)."""
    p = os.path.join(OUTDIR, "pelvic_force_eccentric.csv")
    meta = {}
    if not os.path.exists(p):
        return meta
    for row in csv.DictReader(open(p, encoding="utf-8")):
        try:
            off = int(float(row["offset"]))
        except Exception:
            continue
        meta[off] = (float(row["speed"]), float(row["ptMean"]), float(row["hipR_TD"]))
    return meta


def main():
    model = osim.Model(MODEL)
    state = model.initSystem()

    nom = sorted(glob.glob(os.path.join(RESULTS, "pred_sprinting_coords_*04-February-2026*Nominal.mot")))[-1]
    t_n, h_n, d_n = read_mot(nom)
    nominal_traj = ham_mtu_trajectory(model, state, t_n, h_n, d_n, 0.0)
    nominal_peak = peak_swing(nominal_traj)

    shift_files = {}
    for f in glob.glob(os.path.join(RESULTS, "pred_sprinting_coords_*PelvisShift_*.mot")):
        mobj = re.search(r"PelvisShift_([mp])(\d+)", f)
        if not mobj:
            continue
        off = (-1 if mobj.group(1) == "m" else 1) * int(mobj.group(2))
        if off not in shift_files or os.path.getmtime(f) > os.path.getmtime(shift_files[off]):
            shift_files[off] = f

    meta = load_meta()
    offsets = sorted(shift_files)
    rows = []
    print("=" * 96)
    print("STEP 2  peak LEFT-hamstring MTU length (mm): Nominal vs opt-OFF(tilt only) vs opt-ON(re-optimized)")
    print(f"{'off':>4s}{'ptMean':>8s}{'speed':>7s} | "
          + " ".join(f"{m.split('_')[0][:6]+' OFF/ON':>16s}" for m in HAM_L))
    for off in offsets:
        # opt-OFF: Nominal kinematics + rigid pelvis_tilt offset
        off_traj = ham_mtu_trajectory(model, state, t_n, h_n, d_n, float(off))
        off_peak = peak_swing(off_traj)
        # opt-ON: re-optimized trajectory
        t_s, h_s, d_s = read_mot(shift_files[off])
        on_traj = ham_mtu_trajectory(model, state, t_s, h_s, d_s, 0.0)
        on_peak = peak_swing(on_traj)
        spd, ptm, hip = meta.get(off, (np.nan, np.nan, np.nan))
        cells = []
        for m in HAM_L:
            cells.append(f"{1000*off_peak[m]:7.1f}/{1000*on_peak[m]:7.1f}")
        print(f"{off:4d}{ptm:8.2f}{spd:7.2f} | " + " ".join(f"{c:>16s}" for c in cells))
        row = {"offset": off, "ptMean": ptm, "speed": spd, "hipR_TD": hip}
        for m in ALL_HAM_L:
            row[f"{m}_nominal_mm"] = 1000 * nominal_peak[m]
            row[f"{m}_optOFF_mm"] = 1000 * off_peak[m]
            row[f"{m}_optON_mm"] = 1000 * on_peak[m]
        rows.append(row)

    # sanity print: max |opt-OFF - Nominal| across all conditions/muscles
    dev = max(abs(r[f"{m}_optOFF_mm"] - r[f"{m}_nominal_mm"])
              for r in rows for m in ALL_HAM_L)
    print("-" * 96)
    print(f"max |opt-OFF - Nominal| peak MTU over all conditions/muscles = {dev:.4f} mm "
          f"({'INVARIANT: direct pelvis-tilt effect = 0' if dev < 0.05 else 'NON-ZERO'})")

    # ---- Figure 4 ----------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharex=True)
    offs = [r["offset"] for r in rows]
    for ax, m in zip(axes, HAM_L):
        nomv = rows[0][f"{m}_nominal_mm"]
        ax.axhline(nomv, color="0.6", ls=":", lw=1, label="Nominal")
        ax.plot(offs, [r[f"{m}_optOFF_mm"] for r in rows], "s--", color="#1f77b4",
                label="opt-OFF (tilt only)")
        ax.plot(offs, [r[f"{m}_optON_mm"] for r in rows], "o-", color="#d62728",
                label="opt-ON (re-optimized)")
        ax.set_title(m.replace("_l", " (L)"))
        ax.set_xlabel("pelvic-tilt offset (deg)\n(- = more anterior)")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("peak swing MTU length (mm)")
    axes[0].legend(fontsize=8, loc="best")
    fig.suptitle("STEP 2  Imposed pelvic tilt alone (opt-OFF) does NOT stretch the hamstrings; "
                 "only re-optimization (opt-ON) does", fontsize=11)
    fig.tight_layout()
    figpath = os.path.join(OUTDIR, "fig4_opt_on_vs_off.png")
    fig.savefig(figpath, dpi=150)
    print("wrote", os.path.relpath(figpath, HERE))

    # ---- CSV ---------------------------------------------------------------
    cols = ["offset", "ptMean", "speed", "hipR_TD"]
    for m in ALL_HAM_L:
        cols += [f"{m}_nominal_mm", f"{m}_optOFF_mm", f"{m}_optON_mm"]
    outcsv = os.path.join(OUTDIR, "opt_on_off_pelvis.csv")
    with open(outcsv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})
    print("wrote", os.path.relpath(outcsv, HERE))


if __name__ == "__main__":
    main()
