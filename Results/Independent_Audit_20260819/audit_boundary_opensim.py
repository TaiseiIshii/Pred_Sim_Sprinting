"""
audit_boundary_opensim.py -- INDEPENDENT Phase-5 reproduction of the phase-normalized
boundary decomposition using OpenSim-exact MTU length (opencap env, OpenSim 4.4).

Fixes the absolute-time frame correspondence in boundary_condition_motion.py: the adaptive
(C) step and the nominal step have different durations, so the adaptive dMTU baseline must be
the nominal MTU at the SAME normalized phase (0-100%), not the nearest absolute time.

  A tree-rigid : nominal .mot + constant pelvis_tilt offset delta; hip/knee held.
  B femur-fixed: nominal .mot + delta, hip_flexion_l solved per frame to keep femur_l world rot.
  C adaptive   : the re-optimized PelvisTDwide_m8 (N=100) .mot; baseline = nominal MTU at same phase.

Reports terminal-swing (last 15% phase) peak dMTU per muscle and femur-fixed/adaptive ratio,
to reproduce the manuscript's 7.666/9.727/8.435 mm and 89.6-95.8%.
Run with the opencap python (OpenSim 4.4).
"""
import glob
import math
import os
import csv
import numpy as np
import opensim as osim

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, ".."))
MODEL = os.path.join(RESULTS, "..", "OpenSimModel",
                     "Scaled_FullBody_HamnerModel_Muscle_withContact.osim")
HAM = ["semimem_l", "semiten_l", "bifemlh_l", "bifemsh_l"]
BIARTIC = ["semimem_l", "semiten_l", "bifemlh_l"]
MAX_FRAMES = 120
TS_PCT = 85.0   # terminal swing = last 15% of the step (matches boundary_condition_motion.py)


def read_mot(path):
    lines = open(path, "r", errors="replace").read().splitlines()
    hi = next(i for i, l in enumerate(lines) if l.strip().lower() == "endheader")
    header = [h.strip() for h in lines[hi + 1].split("\t") if h.strip()]
    rows = [[float(v) for v in l.split()] for l in lines[hi + 2:] if len(l.split()) == len(header)]
    return header, np.asarray(rows, float)


def coord_name(h):
    parts = [p for p in h.split("/") if p]
    return parts[-2] if parts and parts[-1] == "value" and len(parts) >= 2 else h


def latest(pattern):
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
                self.cs.get(cn).setValue(self.s, val, False); continue
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
        return float(self.m.getMuscles().get(name).getLength(self.s)) * 100.0   # cm

    def femrot(self):
        T = self.m.getBodySet().get("femur_l").getTransformInGround(self.s)
        R = T.R().asMat33()
        return math.degrees(math.atan2(R.get(1, 0), R.get(0, 0)))

    def col(self, header, name):
        for c, h in enumerate(header):
            if coord_name(h) == name:
                return c
        return None


def femur_fixed_hip(rig, header, data, frame, tilt_off, target_rot):
    rig.apply(header, data, frame, tilt_off=tilt_off, hip_off_l=0.0)
    f0 = rig.femrot()
    rig.apply(header, data, frame, tilt_off=tilt_off, hip_off_l=1.0)
    f1 = rig.femrot()
    slope = f1 - f0
    return 0.0 if abs(slope) < 1e-6 else (target_rot - f0) / slope


def frames(n):
    step = max(1, n // MAX_FRAMES)
    return list(range(0, n, step))


def main():
    rig = Rig()
    nom = latest("pred_sprinting_coords_*10-April-2026*Nominal.mot")
    adp = latest("pred_sprinting_coords_*24-June-2026__23-17-49*PelvisTDwide_m8.mot")
    print("nominal :", os.path.basename(nom))
    print("adaptive:", os.path.basename(adp))
    h_n, d_n = read_mot(nom); h_a, d_a = read_mot(adp)
    pt_n = rig.col(h_n, "pelvis_tilt"); pt_a = rig.col(h_a, "pelvis_tilt")
    delta = float(d_a[0, pt_a] - d_n[0, pt_n])
    print(f"delta_pelvis (touchdown m8-nominal) = {delta:+.3f} deg")

    fr_n = frames(len(d_n)); fr_a = frames(len(d_a))
    ph_n = np.array([100.0 * (d_n[f, 0] - d_n[fr_n[0], 0]) / (d_n[fr_n[-1], 0] - d_n[fr_n[0], 0]) for f in fr_n])
    ph_a = np.array([100.0 * (d_a[f, 0] - d_a[fr_a[0], 0]) / (d_a[fr_a[-1], 0] - d_a[fr_a[0], 0]) for f in fr_a])

    # nominal MTU + femur world-rot per nominal frame
    mtu_nom = {m: [] for m in HAM}; femrot_nom = []
    for f in fr_n:
        rig.apply(h_n, d_n, f, 0.0)
        femrot_nom.append(rig.femrot())
        for m in HAM:
            mtu_nom[m].append(rig.mtu(m))
    mtu_nom = {m: np.array(v) for m, v in mtu_nom.items()}
    femrot_nom = np.array(femrot_nom)

    # A tree-rigid + B femur-fixed on nominal frames
    mtu_A = {m: [] for m in HAM}; mtu_B = {m: [] for m in HAM}; ferr_B = []
    for i, f in enumerate(fr_n):
        rig.apply(h_n, d_n, f, tilt_off=delta, hip_off_l=0.0, hip_off_r=0.0)
        for m in HAM:
            mtu_A[m].append(rig.mtu(m))
        hoff = femur_fixed_hip(rig, h_n, d_n, f, delta, femrot_nom[i])
        rig.apply(h_n, d_n, f, tilt_off=delta, hip_off_l=hoff, hip_off_r=hoff)
        ferr_B.append(rig.femrot() - femrot_nom[i])
        for m in HAM:
            mtu_B[m].append(rig.mtu(m))
    mtu_A = {m: np.array(v) for m, v in mtu_A.items()}
    mtu_B = {m: np.array(v) for m, v in mtu_B.items()}

    # C adaptive on adaptive frames
    mtu_C = {m: [] for m in HAM}
    for f in fr_a:
        rig.apply(h_a, d_a, f, 0.0)
        for m in HAM:
            mtu_C[m].append(rig.mtu(m))
    mtu_C = {m: np.array(v) for m, v in mtu_C.items()}

    print(f"\nfemur world-rot err: A(tree-rigid)~delta={delta:+.2f}  B(femur-fixed) max|err|={np.abs(ferr_B).max():.3f} deg")
    print(f"\n{'muscle':11s} {'A_peak':>8s} {'B_peak':>8s} {'C_peak(phaseNorm)':>18s} {'B/C %':>8s}")
    out_rows = []
    for m in HAM:
        # dMTU in mm, terminal swing (phase>=85)
        dA = 10.0 * (mtu_A[m] - mtu_nom[m])           # same nominal frames
        dB = 10.0 * (mtu_B[m] - mtu_nom[m])
        # adaptive: baseline = nominal MTU interpolated at adaptive PHASE
        nom_interp = np.interp(ph_a, ph_n, mtu_nom[m])
        dC = 10.0 * (mtu_C[m] - nom_interp)
        A_pk = dA[ph_n >= TS_PCT].max()
        B_pk = dB[ph_n >= TS_PCT].max()
        C_pk = dC[ph_a >= TS_PCT].max()
        ratio = 100.0 * B_pk / C_pk if abs(C_pk) > 1e-9 else float("nan")
        print(f"{m:11s} {A_pk:8.3f} {B_pk:8.3f} {C_pk:18.3f} {ratio:8.1f}")
        out_rows.append(dict(muscle=m, is_biarticular=m in BIARTIC, delta_pelvis_deg=round(delta, 3),
                             A_tree_rigid_peak_mm=round(A_pk, 3), B_femur_fixed_peak_mm=round(B_pk, 3),
                             C_adaptive_peak_phaseNorm_mm=round(C_pk, 3),
                             fixed_over_adaptive_pct=round(ratio, 2)))
    out = os.path.join(HERE, "boundary_phase_corrected_opensim.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys())); w.writeheader(); w.writerows(out_rows)
    print("\nExpected (manuscript phase-norm re-audit): adaptive SM 7.666 ST 9.727 BFlh 8.435 mm; ratio 89.6-95.8%")
    print("wrote", out)


if __name__ == "__main__":
    main()
