"""
Fig5_compute_mtu.py -- RUN WITH THE opencap PYTHON (OpenSim 4.4).

Recomputes the phase-normalized boundary decomposition of biarticular-hamstring MTU
length for Figure 5, saving the FULL waveforms (not just peaks).  Mirrors
Results/Independent_Audit_20260819/audit_boundary_opensim.py exactly and cross-checks
the terminal-swing peaks against boundary_phase_corrected_opensim.csv.

  A tree-rigid : nominal .mot + constant pelvis_tilt offset delta; hip/knee held
                 (pelvis & femur co-rotate, hip relative angle preserved -> dMTU ~ 0)
  B femur-fixed: nominal .mot + delta, hip_flexion_l solved per frame to hold femur world rot
  C adaptive   : re-optimized PelvisTDwide_m8 (N=100) .mot; baseline = nominal MTU at same phase

Writes source_data/Fig5_mtu_waveforms_source.csv  (muscle, series, phase_pct, dMTU_mm)
   and source_data/Fig5_mtu_peaks_source.csv       (muscle, series, TS_peak_mm, ratios)
"""
import csv
import glob
import math
import os

import numpy as np
import opensim as osim

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.abspath(os.path.join(HERE, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(OUTDIR, "..", ".."))
RESULTS = os.path.join(PROJECT_ROOT, "Results")
AUDIT = os.path.join(RESULTS, "Independent_Audit_20260819")
SRC = os.path.join(OUTDIR, "source_data")
MODEL = os.path.join(PROJECT_ROOT, "OpenSimModel",
                     "Scaled_FullBody_HamnerModel_Muscle_withContact.osim")
HAM = ["semimem_l", "semiten_l", "bifemlh_l", "bifemsh_l"]
BIARTIC = ["semimem_l", "semiten_l", "bifemlh_l"]
MAX_FRAMES = 120
TS_PCT = 85.0   # terminal swing = last 15% of the step (matches the audit)


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

    mtu_nom = {m: [] for m in HAM}; femrot_nom = []
    for f in fr_n:
        rig.apply(h_n, d_n, f, 0.0)
        femrot_nom.append(rig.femrot())
        for m in HAM:
            mtu_nom[m].append(rig.mtu(m))
    mtu_nom = {m: np.array(v) for m, v in mtu_nom.items()}
    femrot_nom = np.array(femrot_nom)

    mtu_A = {m: [] for m in HAM}; mtu_B = {m: [] for m in HAM}
    for i, f in enumerate(fr_n):
        rig.apply(h_n, d_n, f, tilt_off=delta, hip_off_l=0.0, hip_off_r=0.0)
        for m in HAM:
            mtu_A[m].append(rig.mtu(m))
        hoff = femur_fixed_hip(rig, h_n, d_n, f, delta, femrot_nom[i])
        rig.apply(h_n, d_n, f, tilt_off=delta, hip_off_l=hoff, hip_off_r=hoff)
        for m in HAM:
            mtu_B[m].append(rig.mtu(m))
    mtu_A = {m: np.array(v) for m, v in mtu_A.items()}
    mtu_B = {m: np.array(v) for m, v in mtu_B.items()}

    mtu_C = {m: [] for m in HAM}
    for f in fr_a:
        rig.apply(h_a, d_a, f, 0.0)
        for m in HAM:
            mtu_C[m].append(rig.mtu(m))
    mtu_C = {m: np.array(v) for m, v in mtu_C.items()}

    # waveforms + peaks
    wrows, prows = [], []
    print(f"\n{'muscle':11s} {'A_pk':>7s} {'B_pk':>7s} {'C_pk':>7s} {'B/C%':>7s}")
    for m in HAM:
        dA = 10.0 * (mtu_A[m] - mtu_nom[m])
        dB = 10.0 * (mtu_B[m] - mtu_nom[m])
        nom_interp = np.interp(ph_a, ph_n, mtu_nom[m])
        dC = 10.0 * (mtu_C[m] - nom_interp)
        for ph, v in zip(ph_n, dA):
            wrows.append([m, "tree_rigid", f"{ph:.3f}", f"{v:.4f}"])
        for ph, v in zip(ph_n, dB):
            wrows.append([m, "femur_fixed", f"{ph:.3f}", f"{v:.4f}"])
        for ph, v in zip(ph_a, dC):
            wrows.append([m, "adaptive", f"{ph:.3f}", f"{v:.4f}"])
        A_pk = float(dA[ph_n >= TS_PCT].max())
        B_pk = float(dB[ph_n >= TS_PCT].max())
        C_pk = float(dC[ph_a >= TS_PCT].max())
        ratio = 100.0 * B_pk / C_pk if abs(C_pk) > 1e-9 else float("nan")
        prows.append([m, m in BIARTIC, round(delta, 3), round(A_pk, 3), round(B_pk, 3),
                      round(C_pk, 3), round(ratio, 2)])
        print(f"{m:11s} {A_pk:7.3f} {B_pk:7.3f} {C_pk:7.3f} {ratio:7.1f}")

    os.makedirs(SRC, exist_ok=True)
    with open(os.path.join(SRC, "Fig5_mtu_waveforms_source.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["muscle", "series", "phase_pct", "dMTU_mm"]); w.writerows(wrows)
    with open(os.path.join(SRC, "Fig5_mtu_peaks_source.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["muscle", "is_biarticular", "delta_pelvis_deg", "A_tree_rigid_TSpeak_mm",
                    "B_femur_fixed_TSpeak_mm", "C_adaptive_TSpeak_mm", "fixed_over_adaptive_pct"])
        w.writerows(prows)

    # cross-check vs audit
    exp = {r["muscle"]: r for r in csv.DictReader(
        open(os.path.join(AUDIT, "boundary_phase_corrected_opensim.csv"), encoding="utf-8"))}
    print("\ncross-check vs audit (C adaptive TS peak mm / ratio):")
    ok = True
    for r in prows:
        m = r[0]
        if m in exp:
            ec = float(exp[m]["C_adaptive_peak_phaseNorm_mm"]); er = float(exp[m]["fixed_over_adaptive_pct"])
            dC = abs(r[5] - ec); dr = abs(r[6] - er) if not math.isnan(r[6]) else 0
            flag = "OK" if (dC < 0.02 and dr < 0.5) else "CHECK"
            ok = ok and flag == "OK"
            print(f"  {m:11s} C={r[5]:.3f} (audit {ec:.3f} d={dC:.3f})  ratio={r[6]:.1f} (audit {er:.1f}) {flag}")
    print("ALL MATCH" if ok else "MISMATCH - investigate")


if __name__ == "__main__":
    main()
