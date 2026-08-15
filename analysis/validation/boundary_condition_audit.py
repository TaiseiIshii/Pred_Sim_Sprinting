"""
boundary_condition_audit.py  (opencap / OpenSim 4.4 env)  --  Step 4.

Tests whether the "direct effect of pelvic tilt is zero" statement is a real biomechanical
null or an artefact of the tree-rigid boundary condition, by comparing THREE counterfactuals
for the hip-crossing (biarticular) hamstrings, with OpenSim EXACT muscle-tendon lengths:

  A tree-rigid  : change pelvis_tilt only; pelvis-relative hip & knee angles held fixed.
                  (== the current opt-OFF in analyze_opt_on_off_pelvis.py.)
  B femur-fixed : change pelvis_tilt but compensate hip_flexion so the femur keeps its world
                  orientation (knee held, so tibia world also fixed).  This exposes the
                  geometric hip-angle effect that tree-rigid hides.
  C adaptive    : the actual re-optimized predictive-simulation dose-response (referenced
                  from the strict TDPT motion results, motion-peak MTU).

Static pose (audit spec): hip_flexion_l = +30 deg, knee_angle_l = -20 deg (20 deg flexion;
knee flexion is NEGATIVE in this model, verified).  Anterior pelvic tilt swept 0..25 deg.
World transforms are checked so the intended boundary condition is provably realised before
the muscle results are interpreted.

Outputs (Results/Validation_Master/):
  boundary_condition_static.csv,  fig_b1_boundary_static.png

Run:
  & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\envs\\opencap\\python.exe" \
      analysis/validation/boundary_condition_audit.py
"""
import csv
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

BASE_HIP = 30.0     # deg (hip flexion)
BASE_KNEE = -20.0   # deg (knee flexion is NEGATIVE in this model -> 20 deg flexion)
TILTS = [0, 5, 10, 15, 20, 25]   # anterior tilt magnitudes (deg)


class Rig:
    def __init__(self):
        self.m = osim.Model(MODEL)
        self.s = self.m.initSystem()
        self.cs = self.m.getCoordinateSet()

    def set(self, **coords_deg):
        for i in range(self.cs.getSize()):
            self.cs.get(i).setValue(self.s, self.cs.get(i).getDefaultValue(), False)
        for nm, val in coords_deg.items():
            unit_m = nm.startswith("pelvis_t") and nm[-1] in "xyz"
            self.cs.get(nm).setValue(self.s, val if unit_m else math.radians(val), False)
        self.m.assemble(self.s)
        self.m.realizePosition(self.s)

    def mtu(self, name):
        return float(self.m.getMuscles().get(name).getLength(self.s)) * 100.0   # cm

    def body_sagittal(self, name):
        """(rot_deg about ground Z, x_m, y_m) of a body origin in ground."""
        b = self.m.getBodySet().get(name)
        T = b.getTransformInGround(self.s)
        R = T.R()
        r10 = R.asMat33().get(1, 0)
        r00 = R.asMat33().get(0, 0)
        ang = math.degrees(math.atan2(r10, r00))
        p = T.p()
        return ang, float(p.get(0)), float(p.get(1))


def femur_fixed_hip(rig, pelvis_tilt_deg, target_femur_rot):
    """Solve hip_flexion so femur_l world sagittal orientation == target (linear, 1 step)."""
    rig.set(pelvis_tilt=pelvis_tilt_deg, hip_flexion_l=BASE_HIP, knee_angle_l=BASE_KNEE)
    f0, _, _ = rig.body_sagittal("femur_l")
    rig.set(pelvis_tilt=pelvis_tilt_deg, hip_flexion_l=BASE_HIP + 1.0, knee_angle_l=BASE_KNEE)
    f1, _, _ = rig.body_sagittal("femur_l")
    slope = (f1 - f0) / 1.0
    if abs(slope) < 1e-6:
        return BASE_HIP
    return BASE_HIP + (target_femur_rot - f0) / slope


def determine_anterior_sign(rig, base_femur_rot):
    """Return +1 or -1 for the pelvis_tilt sign that = anterior (lengthens biarticular ham
    at the hip under femur-fixed)."""
    lens = {}
    for sgn in (+1, -1):
        hip = femur_fixed_hip(rig, sgn * 15.0, base_femur_rot)
        rig.set(pelvis_tilt=sgn * 15.0, hip_flexion_l=hip, knee_angle_l=BASE_KNEE)
        lens[sgn] = np.mean([rig.mtu(m) for m in BIARTIC])
    return +1 if lens[+1] >= lens[-1] else -1


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    rig = Rig()

    # base pose (0 tilt) reference
    rig.set(pelvis_tilt=0.0, hip_flexion_l=BASE_HIP, knee_angle_l=BASE_KNEE)
    base_femur_rot, base_fx, base_fy = rig.body_sagittal("femur_l")
    base_tibia_rot, base_tx, base_ty = rig.body_sagittal("tibia_l")
    base_mtu = {m: rig.mtu(m) for m in HAM}
    a_sign = determine_anterior_sign(rig, base_femur_rot)
    print(f"anterior pelvic tilt = pelvis_tilt sign {a_sign:+d} "
          f"(base femur rot={base_femur_rot:.2f} deg)")
    print(f"base MTU (cm): " + "  ".join(f"{m}={base_mtu[m]:.2f}" for m in HAM))

    rows = []
    for tilt in TILTS:
        pt = a_sign * tilt          # signed pelvis_tilt for 'anterior' tilt
        # A tree-rigid: hip/knee fixed, pelvis_tilt changes
        rig.set(pelvis_tilt=pt, hip_flexion_l=BASE_HIP, knee_angle_l=BASE_KNEE)
        A_mtu = {m: rig.mtu(m) for m in HAM}
        A_fr, A_fx, A_fy = rig.body_sagittal("femur_l")
        A_tr, _, _ = rig.body_sagittal("tibia_l")
        # B femur-fixed: hip compensates to hold femur world orientation
        hip_c = femur_fixed_hip(rig, pt, base_femur_rot)
        rig.set(pelvis_tilt=pt, hip_flexion_l=hip_c, knee_angle_l=BASE_KNEE)
        B_mtu = {m: rig.mtu(m) for m in HAM}
        B_fr, B_fx, B_fy = rig.body_sagittal("femur_l")
        B_tr, B_tx, B_ty = rig.body_sagittal("tibia_l")
        for cond, mt, fr, fx, fy, tr, hip in (
                ("tree_rigid", A_mtu, A_fr, A_fx, A_fy, A_tr, BASE_HIP),
                ("femur_fixed", B_mtu, B_fr, B_fx, B_fy, B_tr, hip_c)):
            row = {
                "boundary_condition": cond, "anterior_tilt_deg": tilt,
                "pelvis_tilt_deg": round(pt, 3), "hip_flexion_deg": round(hip, 3),
                "knee_angle_deg": BASE_KNEE,
                "femur_world_rot_err_deg": round(fr - base_femur_rot, 4),
                "femur_world_pos_err_mm": round(1000 * math.hypot(fx - base_fx, fy - base_fy), 3),
                "tibia_world_rot_err_deg": round(tr - base_tibia_rot, 4),
            }
            for m in HAM:
                row[f"{m}_MTU_cm"] = round(mt[m], 4)
                row[f"{m}_dMTU_mm"] = round(10.0 * (mt[m] - base_mtu[m]), 3)
            rows.append(row)

    # write CSV
    cols = ["boundary_condition", "anterior_tilt_deg", "pelvis_tilt_deg", "hip_flexion_deg",
            "knee_angle_deg", "femur_world_rot_err_deg", "femur_world_pos_err_mm",
            "tibia_world_rot_err_deg"]
    for m in HAM:
        cols += [f"{m}_MTU_cm", f"{m}_dMTU_mm"]
    out_csv = os.path.join(OUTDIR, "boundary_condition_static.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print("wrote", os.path.basename(out_csv))

    # verification summary
    tr_rows = [r for r in rows if r["boundary_condition"] == "tree_rigid"]
    ff_rows = [r for r in rows if r["boundary_condition"] == "femur_fixed"]
    print("\n--- world-transform verification ---")
    print(f"  tree-rigid  femur rot err (deg): "
          f"[{min(r['femur_world_rot_err_deg'] for r in tr_rows):.2f},"
          f"{max(r['femur_world_rot_err_deg'] for r in tr_rows):.2f}]  "
          f"(EXPECTED: femur rotates WITH pelvis, ~= tilt)")
    print(f"  femur-fixed femur rot err (deg): "
          f"[{min(r['femur_world_rot_err_deg'] for r in ff_rows):.3f},"
          f"{max(r['femur_world_rot_err_deg'] for r in ff_rows):.3f}]  (EXPECTED ~0)")
    print(f"  femur-fixed tibia rot err (deg): "
          f"[{min(r['tibia_world_rot_err_deg'] for r in ff_rows):.3f},"
          f"{max(r['tibia_world_rot_err_deg'] for r in ff_rows):.3f}]  (EXPECTED ~0)")
    print("\n--- MTU range across 0..25 deg anterior tilt (mm) ---")
    for m in HAM:
        tr = [r[f"{m}_dMTU_mm"] for r in tr_rows]
        ff = [r[f"{m}_dMTU_mm"] for r in ff_rows]
        tag = "biarticular" if m in BIARTIC else "MONO control"
        print(f"  {m:11s} ({tag:11s})  tree-rigid Δ=[{min(tr):+.2f},{max(tr):+.2f}]  "
              f"femur-fixed Δ=[{min(ff):+.2f},{max(ff):+.2f}]")

    # figure
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.2))
    for ax, m in zip(axes, HAM):
        ax.plot([r["anterior_tilt_deg"] for r in tr_rows],
                [r[f"{m}_dMTU_mm"] for r in tr_rows], "--s", color=COLORS[m],
                label="A tree-rigid", ms=5)
        ax.plot([r["anterior_tilt_deg"] for r in ff_rows],
                [r[f"{m}_dMTU_mm"] for r in ff_rows], "-o", color=COLORS[m],
                label="B femur-fixed", ms=5)
        ax.axhline(0, color="grey", lw=0.8, ls=":")
        ax.set_title(m + ("" if m in BIARTIC else "  (mono control)"))
        ax.set_xlabel("anterior pelvic tilt (deg)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Δ MTU length from 0 deg (mm)")
    fig.suptitle("Step 4 boundary-condition audit: pelvic-tilt 'direct effect' is boundary-"
                 "condition dependent\n(tree-rigid holds hip angle -> ~0; femur-fixed changes "
                 "hip angle -> monotonic geometric effect)", fontsize=10)
    fig.tight_layout()
    out_png = os.path.join(OUTDIR, "fig_b1_boundary_static.png")
    fig.savefig(out_png, dpi=140)
    plt.close(fig)
    print("wrote", os.path.basename(out_png))


if __name__ == "__main__":
    main()
