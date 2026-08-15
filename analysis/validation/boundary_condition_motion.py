"""
boundary_condition_motion.py  (opencap / OpenSim 4.4)  --  Step 4, full-motion A/B/C.

Extends the static boundary-condition audit to the WHOLE nominal sprint step: computes
left-hamstring MTU length at every phase under three counterfactuals for one representative
touchdown-pelvic-tilt offset (the strict N=100 m8 condition), with per-frame world-transform
verification.

  A tree-rigid  : nominal pose + constant pelvis_tilt offset (delta); hip/knee held.
  B femur-fixed : nominal pose + pelvis_tilt offset, hip_flexion solved per frame so femur_l
                  keeps its nominal world orientation (knee held -> tibia world also held).
  C adaptive    : the actual re-optimized PelvisTDwide_m8 (N=100) coordinates.

delta_pelvis = achieved touchdown pelvic tilt (m8) - nominal, applied to A and B.

Outputs (Results/Validation_Master/):
  boundary_condition_motion.csv   (long: boundary x phase x muscle)
  fig_b2_boundary_motion.png

Run:
  & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\envs\\opencap\\python.exe" \
      analysis/validation/boundary_condition_motion.py
"""
import csv
import glob
import math
import os

import numpy as np
import opensim as osim
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, "..", "..", "Results"))
MODEL = os.path.join(HERE, "..", "..", "OpenSimModel",
                     "Scaled_FullBody_HamnerModel_Muscle_withContact.osim")
OUTDIR = os.path.join(RESULTS, "Validation_Master")
HAM = ["semimem_l", "semiten_l", "bifemlh_l", "bifemsh_l"]
BIARTIC = ["semimem_l", "semiten_l", "bifemlh_l"]
COLORS = {"semimem_l": "#1b7837", "semiten_l": "#762a83", "bifemlh_l": "#2166ac",
          "bifemsh_l": "#b2182b"}
MAX_FRAMES = 120


def read_mot(path):
    lines = open(path, "r", errors="replace").read().splitlines()
    hi = next(i for i, l in enumerate(lines) if l.strip().lower() == "endheader")
    header = [h.strip() for h in lines[hi + 1].split("\t") if h.strip()]
    rows = [[float(v) for v in l.split()] for l in lines[hi + 2:] if len(l.split()) == len(header)]
    return header, np.asarray(rows, float)


def coord_name(h):
    parts = [p for p in h.split("/") if p]
    return parts[-2] if parts and parts[-1] == "value" and len(parts) >= 2 else h


def latest(pattern, tag=None):
    fs = sorted(glob.glob(os.path.join(RESULTS, pattern)), key=os.path.getmtime, reverse=True)
    return fs[0] if fs else None


class Rig:
    def __init__(self):
        self.m = osim.Model(MODEL)
        self.s = self.m.initSystem()
        self.cs = self.m.getCoordinateSet()
        self.names = {self.cs.get(i).getName() for i in range(self.cs.getSize())}

    def apply(self, header, data, frame, tilt_off=0.0, hip_off_l=0.0, hip_off_r=0.0):
        for c, h in enumerate(header):
            if c == 0:
                continue
            cn = coord_name(h)
            if cn not in self.names:
                continue
            val = data[frame, c]
            if cn in ("pelvis_tx", "pelvis_ty", "pelvis_tz"):
                self.cs.get(cn).setValue(self.s, val, False)
                continue
            if cn == "pelvis_tilt":
                val += tilt_off
            elif cn == "hip_flexion_l":
                val += hip_off_l
            elif cn == "hip_flexion_r":
                val += hip_off_r
            self.cs.get(cn).setValue(self.s, math.radians(val), False)
        self.m.assemble(self.s)
        self.m.realizePosition(self.s)

    def mtu(self, name):
        return float(self.m.getMuscles().get(name).getLength(self.s)) * 100.0

    def sagittal(self, body):
        T = self.m.getBodySet().get(body).getTransformInGround(self.s)
        R = T.R().asMat33()
        p = T.p()
        return math.degrees(math.atan2(R.get(1, 0), R.get(0, 0))), float(p.get(0)), float(p.get(1))

    def col(self, header, name):
        for c, h in enumerate(header):
            if coord_name(h) == name:
                return c
        return None


def femur_fixed_hip(rig, header, data, frame, tilt_off, target_rot):
    """hip_flexion_l offset that restores femur_l world orientation at this frame (1-step)."""
    rig.apply(header, data, frame, tilt_off=tilt_off, hip_off_l=0.0)
    f0, _, _ = rig.sagittal("femur_l")
    rig.apply(header, data, frame, tilt_off=tilt_off, hip_off_l=1.0)
    f1, _, _ = rig.sagittal("femur_l")
    slope = f1 - f0
    return 0.0 if abs(slope) < 1e-6 else (target_rot - f0) / slope


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    rig = Rig()
    nom_mot = latest("pred_sprinting_coords_*10-April-2026*Nominal.mot")
    adp_mot = latest("pred_sprinting_coords_*24-June-2026__23-17-49*PelvisTDwide_m8.mot")
    print("nominal:", os.path.basename(nom_mot))
    print("adaptive:", os.path.basename(adp_mot))
    h_n, d_n = read_mot(nom_mot)
    h_a, d_a = read_mot(adp_mot)

    pt_col_n = rig.col(h_n, "pelvis_tilt")
    hip_col_n = rig.col(h_n, "hip_flexion_l")
    knee_col_n = rig.col(h_n, "knee_angle_l")
    pt_col_a = rig.col(h_a, "pelvis_tilt")
    delta = float(d_a[0, pt_col_a] - d_n[0, pt_col_n])   # touchdown tilt offset (deg)
    print(f"delta_pelvis (touchdown, m8 - nominal) = {delta:+.2f} deg")

    def frames(n):
        step = max(1, n // MAX_FRAMES)
        return list(range(0, n, step))
    fr_n = frames(len(d_n))
    fr_a = frames(len(d_a))
    t_n = d_n[:, 0]
    t_a = d_a[:, 0]

    # nominal reference femur/tibia world orientation per frame (for femur-fixed target + errors)
    nom_ref = {}
    for f in fr_n:
        rig.apply(h_n, d_n, f, 0.0)
        fr, fx, fy = rig.sagittal("femur_l")
        tr, tx, ty = rig.sagittal("tibia_l")
        nom_ref[f] = (fr, fx, fy, tr, tx, ty, {m: rig.mtu(m) for m in HAM})

    rows = []

    def record(cond, f, header, data, phase_pct, tilt_off, hip_off_l):
        rig.apply(header, data, f if header is h_a else f, tilt_off=tilt_off, hip_off_l=hip_off_l,
                  hip_off_r=hip_off_l)
        fr, fx, fy = rig.sagittal("femur_l")
        tr, tx, ty = rig.sagittal("tibia_l")
        pt = math.degrees(0) + data[f, pt_col_a if header is h_a else pt_col_n] + (tilt_off if header is not h_a else 0)
        hip = data[f, (rig.col(header, "hip_flexion_l"))] + (hip_off_l if header is not h_a else 0)
        knee = data[f, rig.col(header, "knee_angle_l")]
        # nearest nominal ref frame for world-error + dMTU baseline
        fref = min(nom_ref, key=lambda k: abs(t_n[k] - (t_a[f] if header is h_a else t_n[f])))
        rfr, rfx, rfy, rtr, rtx, rty, rmtu = nom_ref[fref]
        for m in HAM:
            L = rig.mtu(m)
            rows.append({
                "boundary_condition": cond, "delta_pelvis_deg": round(delta, 3),
                "phase_pct": round(phase_pct, 2), "achieved_pelvis_tilt_deg": round(pt, 3),
                "hip_flexion_deg": round(hip, 3), "knee_angle_deg": round(knee, 3),
                "femur_world_rot_err_deg": round(fr - rfr, 4),
                "femur_world_pos_err_mm": round(1000 * math.hypot(fx - rfx, fy - rfy), 3),
                "tibia_world_rot_err_deg": round(tr - rtr, 4),
                "tibia_world_pos_err_mm": round(1000 * math.hypot(tx - rtx, ty - rty), 3),
                "muscle": m, "lMT_cm": round(L, 4),
                "dMTU_from_nominal_mm": round(10.0 * (L - rmtu[m]), 3),
            })

    for f in fr_n:
        ph = 100.0 * (t_n[f] - t_n[0]) / (t_n[-1] - t_n[0])
        record("A_tree_rigid", f, h_n, d_n, ph, delta, 0.0)
        tgt = nom_ref[f][0]
        hoff = femur_fixed_hip(rig, h_n, d_n, f, delta, tgt)
        record("B_femur_fixed", f, h_n, d_n, ph, delta, hoff)
    for f in fr_a:
        ph = 100.0 * (t_a[f] - t_a[0]) / (t_a[-1] - t_a[0])
        record("C_adaptive", f, h_a, d_a, ph, 0.0, 0.0)

    cols = ["boundary_condition", "delta_pelvis_deg", "phase_pct", "achieved_pelvis_tilt_deg",
            "hip_flexion_deg", "knee_angle_deg", "femur_world_rot_err_deg",
            "femur_world_pos_err_mm", "tibia_world_rot_err_deg", "tibia_world_pos_err_mm",
            "muscle", "lMT_cm", "dMTU_from_nominal_mm"]
    out_csv = os.path.join(OUTDIR, "boundary_condition_motion.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as fp:
        w = csv.DictWriter(fp, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print("wrote", os.path.basename(out_csv), f"({len(rows)} rows)")

    # verification + terminal-swing peak per condition/muscle
    def sub(cond, m):
        return [r for r in rows if r["boundary_condition"] == cond and r["muscle"] == m]
    print("\n--- world-transform verification (femur_l rotation error, deg) ---")
    for cond in ("A_tree_rigid", "B_femur_fixed", "C_adaptive"):
        errs = [r["femur_world_rot_err_deg"] for r in rows if r["boundary_condition"] == cond]
        print(f"  {cond:14s} femur rot err range [{min(errs):+.2f},{max(errs):+.2f}] "
              f"(A~=delta, B~=0, C=re-optimized)")
    print("\n--- terminal-swing (last 15% phase) peak MTU vs nominal (mm) ---")
    for m in HAM:
        line = f"  {m:11s}"
        for cond in ("A_tree_rigid", "B_femur_fixed", "C_adaptive"):
            ts = [r["dMTU_from_nominal_mm"] for r in sub(cond, m) if r["phase_pct"] >= 85]
            line += f"  {cond.split('_')[0]}={max(ts, default=float('nan')):+6.2f}"
        print(line)

    # figure: MTU(phase) for biarticular + control, 3 conditions
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.2))
    ls = {"A_tree_rigid": ("--", "A tree-rigid"), "B_femur_fixed": ("-", "B femur-fixed"),
          "C_adaptive": ("-.", "C adaptive")}
    for ax, m in zip(axes, HAM):
        for cond, (style, lab) in ls.items():
            s = sub(cond, m)
            ax.plot([r["phase_pct"] for r in s], [r["lMT_cm"] for r in s], style,
                    color=COLORS[m], label=lab, lw=1.8)
        ax.axvspan(85, 100, color="#fddbc7", alpha=0.4)
        ax.set_title(m + ("" if m in BIARTIC else "  (mono control)"))
        ax.set_xlabel("phase (% of step)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("MTU length (cm)")
    fig.suptitle(f"Step 4 full-motion boundary comparison (delta touchdown tilt {delta:+.1f} deg; "
                 "shaded = terminal swing)", fontsize=10)
    fig.tight_layout()
    out_png = os.path.join(OUTDIR, "fig_b2_boundary_motion.png")
    fig.savefig(out_png, dpi=140)
    plt.close(fig)
    print("wrote", os.path.basename(out_png))


if __name__ == "__main__":
    main()
