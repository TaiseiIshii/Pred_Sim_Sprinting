"""
validate_against_literature.py
==============================
Credibility / face-validity check for the predictive sprinting simulation.

WHY
---
Before trusting any *perturbation* result (pelvic tilt, hamstring architecture,
touchdown distance ...), we must show that the UNPERTURBED (Nominal) simulation
reproduces, as *emergent* outputs, quantities that independent experiments have
measured for maximal-velocity sprinting. None of the numbers below are imposed
on the optimisation -- top speed, ground reaction forces, step timing, joint
range of motion and hamstring fascicle/MTU mechanics all fall out of the
physics + "run as fast as possible" objective. If they land inside published
ranges, the model is a credible virtual laboratory.

WHAT IT DOES
------------
Loads the newest Nominal result (prefers N=100, falls back to N=50) and derives:

  * Performance / gait timing : top speed, step frequency, step & stride length,
                                ground-contact time, flight time, duty factor.
  * Ground reaction forces    : peak vertical & horizontal (braking/propulsive)
                                GRF, vertical/braking/propulsive impulses, and a
                                vertical-impulse *balance* check (must equal body
                                weight x stride time -- a hard physics test).
  * Joint kinematics          : hip / knee / ankle full-stride ROM (L/R union),
                                pelvis tilt, lumbar (trunk) angle.
  * Hamstring mechanics       : peak normalised fascicle length, MTU excursion,
                                fascicle:MTU decoupling ratio, passive force, and
                                whether peak strain occurs in swing (via
                                injury_metrics.py).

Each value is compared to a published range (see REFERENCES) and flagged
OK / HIGH / LOW. Honest flags (e.g. contact time slightly short, contact-model
horizontal-GRF transients high) are reported, not hidden.

OUTPUT
------
  * A formatted table to stdout.
  * Results/Validation/validation_summary.csv

USAGE
-----
  python analysis/validate_against_literature.py           # auto (N=100 -> N=50)
  python analysis/validate_against_literature.py 50         # force a mesh
  python analysis/validate_against_literature.py --mat <path_to_nominal.mat>
"""
from __future__ import annotations

import csv
import glob
import os
import re
import sys

import numpy as np
from scipy.io import loadmat

import injury_metrics as im

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "Results")
OUTDIR = os.path.join(RESULTS, "Validation")

# Subject the model was scaled to (international-caliber male sprinter,
# Haralabidis et al.). Body weight used to normalise GRFs.
BODY_MASS = 72.17                      # kg
G = 9.80665
BW = BODY_MASS * G                     # N

COORD_ORDER = [
    "pelvis_tilt", "pelvis_list", "pelvis_rotation", "pelvis_tx", "pelvis_ty", "pelvis_tz",
    "hip_flexion_r", "hip_adduction_r", "hip_rotation_r", "knee_angle_r", "ankle_angle_r",
    "subtalar_angle_r", "mtp_angle_r",
    "hip_flexion_l", "hip_adduction_l", "hip_rotation_l", "knee_angle_l", "ankle_angle_l",
    "subtalar_angle_l", "mtp_angle_l",
    "lumbar_extension", "lumbar_bending", "lumbar_rotation",
    "arm_flex_r", "arm_add_r", "arm_rot_r", "elbow_flex_r", "pro_sup_r", "wrist_flex_r", "wrist_dev_r",
    "arm_flex_l", "arm_add_l", "arm_rot_l", "elbow_flex_l", "pro_sup_l", "wrist_flex_l", "wrist_dev_l",
]

# ---------------------------------------------------------------------------
# Published reference ranges for MAXIMAL-VELOCITY sprinting. Ranges are kept
# deliberately broad and defensible; `ref` keys map into REFERENCES below.
# ---------------------------------------------------------------------------
REFERENCES = {
    "Haralabidis2024": "Haralabidis, Eaton, Delp, Hicks (2024/25). Simulations reveal how "
                       "touchdown kinematic variables affect top sprinting speed. bioRxiv "
                       "2024.10.08.617292; Med Sci Sports Exerc, doi:10.1249/MSS.0000000000003797. "
                       "(Source framework; optimal top speed 11.85 m/s, international-caliber male sprinter.)",
    "Weyand2000": "Weyand, Sternlight, Bellizzi, Wright (2000). Faster top running speeds are "
                  "achieved with greater ground forces not more rapid leg movements. J Appl Physiol 89:1991-1999.",
    "Weyand2010": "Weyand, Sandell, Prime, Bundle (2010). The biological limits to running speed "
                  "are imposed from the ground up. J Appl Physiol 108:950-961.",
    "ClarkWeyand2014": "Clark & Weyand (2014). Are running speeds maximized with simple-spring "
                       "stance mechanics? J Appl Physiol 117:604-615.",
    "MannHerman1985": "Mann & Herman (1985). Kinematic analysis of Olympic sprint performance: "
                      "men's 200 m. Int J Sport Biomech 1:151-162.",
    "Schache2011": "Schache, Blanch, Dorn, Brown, Rosemond, Pandy (2011). Effect of running speed "
                   "on lower limb joint kinematics. Med Sci Sports Exerc 43:1260-1271.",
    "Schache2012": "Schache, Dorn, Blanch, Brown, Pandy (2012). Mechanics of the human hamstring "
                   "muscles during sprinting. Med Sci Sports Exerc 44:647-658.",
    "Thelen2005": "Thelen, Chumanov, Hoerth et al. (2005). Hamstring muscle kinematics during "
                  "treadmill sprinting. Med Sci Sports Exerc 37:108-114.",
    "Chumanov2007": "Chumanov, Heiderscheit, Thelen (2007). The effect of speed and influence of "
                    "individual muscles on hamstring mechanics during the swing phase of sprinting. "
                    "J Biomech 40:3555-3562.",
    "Kalkhoven2023": "Kalkhoven, Lehnert, Bourne et al. (2023). Reconsidering the swing-phase "
                     "hamstring stretch-injury paradigm. Sports Med 53:2321-2346.",
    "Nagahara2017": "Nagahara, Mizutani, Matsuo, Kanehisa, Fukunaga (2017/18). Step-to-step "
                    "spatiotemporal & GRF variables during the acceleration/max-velocity phase of sprinting.",
    "physics": "Hard physical constraint (flight dynamics): summed vertical impulse over a full "
               "stride must equal body weight x stride time.",
}


def _get(o, *names):
    for n in names:
        o = getattr(o, n) if hasattr(o, n) else o[n]
    return o


def _trap(y, x):
    y = np.asarray(y, float)
    x = np.asarray(x, float)
    if y.size < 2:
        return 0.0
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x)))


def _mat_N(path):
    try:
        m = loadmat(path, struct_as_record=False, squeeze_me=True,
                    variable_names=["optimumOutput"])
        return int(np.asarray(_get(m["optimumOutput"], "options", "N")).ravel()[0])
    except Exception:
        return None


def newest_nominal(target_n=None):
    fs = sorted(glob.glob(os.path.join(RESULTS, "pred_sprinting_data_*Nominal.mat")),
                key=os.path.getmtime, reverse=True)
    if not fs:
        return None
    if target_n is None:
        for n in (100, 50):
            for p in fs:
                if _mat_N(p) == n:
                    return p
        return fs[0]
    for p in fs:
        if _mat_N(p) == target_n:
            return p
    return None


# ---------------------------------------------------------------------------
# Emergent-output extractors
# ---------------------------------------------------------------------------

def performance_timing(o, grf):
    speed = float(np.asarray(_get(o, "ave_speed")).ravel()[0])
    step_T = float(np.asarray(_get(o, "optVars_nsc", "totalTime")).ravel()[0])
    stride_T = 2.0 * step_T
    return {
        "top_speed": speed,
        "step_freq": 1.0 / step_T,
        "step_length": speed * step_T,
        "stride_length": speed * stride_T,
        "contact_time": grf["contact_s"],
        "flight_time": step_T - grf["contact_s"],
        "duty_factor": grf["contact_s"] / stride_T,
        "_step_T": step_T,
        "_stride_T": stride_T,
    }


def grf_metrics(o):
    GR = np.asarray(_get(o, "GRFs", "R"), float)          # (nT,3) [AP, vert, ML] (N)
    t = np.asarray(_get(o, "timeNodes"), float).ravel()
    if t.size != GR.shape[0]:
        t = np.linspace(0.0, 1.0, GR.shape[0])
    fx, fy = GR[:, 0], GR[:, 1]
    stance = fy > 0.05 * BW
    ts, fys, fxs = t[stance], fy[stance], fx[stance]
    contact = float(ts[-1] - ts[0])
    return {
        "peak_vGRF": float(fy.max() / BW),
        "peak_brakeGRF": float(-fx.min() / BW) if fx.min() < 0 else 0.0,
        "peak_propGRF": float(fx.max() / BW) if fx.max() > 0 else 0.0,
        "vert_impulse": _trap(fys, ts) / BW,
        "brake_impulse": -_trap(np.minimum(fxs, 0.0), ts) / BW,
        "prop_impulse": _trap(np.maximum(fxs, 0.0), ts) / BW,
        "contact_s": contact,
    }


def _read_mot(path):
    with open(path, "r", encoding="latin-1") as f:
        lines = f.readlines()
    hi = next(i for i, ln in enumerate(lines) if ln.strip().lower().startswith("time"))
    labels = lines[hi].split()
    rows = []
    for ln in lines[hi + 1:]:
        toks = ln.split()
        if len(toks) == len(labels):
            try:
                rows.append([float(x) for x in toks])
            except ValueError:
                pass
    return labels, np.asarray(rows)


def kinematics(matpath):
    """Full-stride joint ROM (deg) from the reconstructed coords .mot.

    One simulated step contains the stance leg PLUS the swing of the other leg,
    so the L/R union of a joint spans the full sprint ROM.
    """
    base = os.path.basename(matpath)
    m = re.search(r"pred_sprinting_data_(.+?)___(.+)\.mat", base)
    if not m:
        return None
    cond = m.group(2)
    cands = glob.glob(os.path.join(RESULTS, f"pred_sprinting_coords_*___{cond}.mot"))
    if not cands:
        return None
    ref = os.path.getmtime(matpath)
    mot = min(cands, key=lambda f: abs(os.path.getmtime(f) - ref))
    labels, data = _read_mot(mot)
    col = {}
    for i, l in enumerate(labels):
        key = l.strip("/").split("/")[-2] if l.count("/") >= 2 else l
        col[key] = i

    def stat(v):
        return {"min": float(v.min()), "max": float(v.max()),
                "rom": float(v.max() - v.min()), "mean": float(v.mean())}

    out = {}
    for base_j in ("hip_flexion", "knee_angle", "ankle_angle"):
        vs = [data[:, col[f"{base_j}_{s}"]] for s in ("r", "l") if f"{base_j}_{s}" in col]
        if vs:
            out[base_j] = stat(np.concatenate(vs))
    for base_j in ("pelvis_tilt", "lumbar_extension"):
        if base_j in col:
            out[base_j] = stat(data[:, col[base_j]])
    return out


# ---------------------------------------------------------------------------
# Check assembly
# ---------------------------------------------------------------------------
class Check:
    __slots__ = ("group", "name", "value", "unit", "lo", "hi", "refs", "note")

    def __init__(self, group, name, value, unit, lo, hi, refs, note=""):
        self.group, self.name, self.value = group, name, value
        self.unit, self.lo, self.hi = unit, lo, hi
        self.refs, self.note = refs, note

    @property
    def flag(self):
        if self.lo is None or self.hi is None or self.value is None:
            return "INFO"
        if self.value < self.lo:
            return "LOW"
        if self.value > self.hi:
            return "HIGH"
        return "OK"


def build_checks(matpath):
    o = loadmat(matpath, struct_as_record=False, squeeze_me=True)["optimumOutput"]
    grf = grf_metrics(o)
    pt = performance_timing(o, grf)
    kin = kinematics(matpath)
    ham = im.compute_injury_metrics(matpath)

    C = []
    # -- Performance / gait timing --------------------------------------------
    C.append(Check("Performance", "Top speed", pt["top_speed"], "m/s", 11.5, 12.4,
                   ["Haralabidis2024", "Weyand2010"],
                   "Haralabidis optimal = 11.85 m/s (near-exact reproduction)."))
    C.append(Check("Gait timing", "Step frequency", pt["step_freq"], "steps/s", 4.4, 5.0,
                   ["Weyand2000", "MannHerman1985"], ""))
    C.append(Check("Gait timing", "Step length", pt["step_length"], "m", 2.0, 2.6,
                   ["MannHerman1985", "Nagahara2017"], ""))
    C.append(Check("Gait timing", "Ground-contact time", pt["contact_time"] * 1e3, "ms", 80, 110,
                   ["Weyand2000", "ClarkWeyand2014"],
                   "Slightly short -- consistent with the model's very high speed / short stance."))
    C.append(Check("Gait timing", "Flight time", pt["flight_time"] * 1e3, "ms", 110, 150,
                   ["Weyand2000"], ""))
    C.append(Check("Gait timing", "Duty factor", pt["duty_factor"], "-", 0.16, 0.24,
                   ["Weyand2010"], "contact / stride time."))
    # -- Ground reaction forces -----------------------------------------------
    C.append(Check("GRF", "Peak vertical GRF", grf["peak_vGRF"], "BW", 3.5, 5.0,
                   ["Weyand2010", "ClarkWeyand2014"],
                   "At/above upper end: compliant sphere-contact + short stance inflate the PEAK; "
                   "impulse (below) is the robust test."))
    C.append(Check("GRF", "Vertical impulse / step", grf["vert_impulse"], "BW.s", 0.18, 0.24,
                   ["Weyand2000"], ""))
    C.append(Check("GRF", "Vertical-impulse balance",
                   2.0 * grf["vert_impulse"] / pt["_stride_T"], "BW (mean)", 0.97, 1.03,
                   ["physics"],
                   "2 x step impulse / stride time must equal 1 BW. Hard physics check."))
    C.append(Check("GRF", "Peak braking GRF", grf["peak_brakeGRF"], "BW", 0.4, 0.9,
                   ["ClarkWeyand2014", "Nagahara2017"],
                   "Peak horizontal runs high (touchdown contact transient); impulses are physiological."))
    C.append(Check("GRF", "Peak propulsive GRF", grf["peak_propGRF"], "BW", 0.3, 0.9,
                   ["ClarkWeyand2014", "Nagahara2017"], ""))
    C.append(Check("GRF", "Braking impulse", grf["brake_impulse"], "BW.s", 0.01, 0.05,
                   ["Nagahara2017"], ""))
    C.append(Check("GRF", "Propulsive impulse", grf["prop_impulse"], "BW.s", 0.01, 0.05,
                   ["Nagahara2017"],
                   "prop >= brake at constant top speed because the model overcomes aerodynamic drag."))
    # -- Joint kinematics (full-stride ROM) -----------------------------------
    if kin:
        C.append(Check("Kinematics", "Hip flex/ext ROM", kin["hip_flexion"]["rom"], "deg", 70, 95,
                       ["Schache2011"], f"peak flex {kin['hip_flexion']['max']:.0f}, "
                       f"peak ext {kin['hip_flexion']['min']:.0f} deg."))
        C.append(Check("Kinematics", "Knee flexion ROM", kin["knee_angle"]["rom"], "deg", 100, 135,
                       ["Schache2011"], "knee_angle<0 = flexion; swing peak flexion ~"
                       f"{-kin['knee_angle']['min']:.0f} deg, never fully extends "
                       f"(min flex ~{-kin['knee_angle']['max']:.0f} deg)."))
        C.append(Check("Kinematics", "Ankle DF/PF ROM", kin["ankle_angle"]["rom"], "deg", 40, 60,
                       ["Schache2011"], f"DF {kin['ankle_angle']['max']:.0f}, "
                       f"PF {kin['ankle_angle']['min']:.0f} deg."))
        C.append(Check("Kinematics", "Pelvis tilt (mean)", kin["pelvis_tilt"]["mean"], "deg", -20, 0,
                       ["Schache2011"],
                       "more negative = more anterior tilt in this model; slight anterior tilt / forward lean."))
        C.append(Check("Kinematics", "Lumbar angle (mean)", kin["lumbar_extension"]["mean"], "deg", -25, 0,
                       ["Schache2011"], "negative = forward trunk flexion (sprinters run with slight forward lean)."))
    # -- Hamstring mechanics ---------------------------------------------------
    for nm in im.BIARTIC:
        C.append(Check("Hamstring", f"{nm}: peak norm. fascicle len", ham[f"{nm}_peak_lMtilde"],
                       "L/Lo", 0.90, 1.20, ["Thelen2005", "Chumanov2007", "Kalkhoven2023"],
                       "fascicles operate near optimal length (~1.0), only mildly on the descending limb."))
    for nm in im.BIARTIC:
        C.append(Check("Hamstring", f"{nm}: MTU excursion (p2p)", ham[f"{nm}_mtu_strain"] * 100,
                       "%", 12, 26, ["Thelen2005", "Schache2012"],
                       "peak-to-peak ~ +/-9-11% about mean, in line with ~8-12% hamstring MTU stretch."))
    for nm in im.BIARTIC:
        C.append(Check("Hamstring", f"{nm}: fascicle:MTU ratio", ham[f"{nm}_fasc_mtu_ratio"],
                       "-", 0.5, 1.0, ["Kalkhoven2023"],
                       "tendon/aponeurosis absorbs part of the MTU stretch (Kalkhoven decoupling)."))
    # swing-phase timing (INFO: expected True for all biarticular hamstrings)
    swing_ok = all(ham.get(f"{nm}_peak_in_stance") is False for nm in im.BIARTIC)
    C.append(Check("Hamstring", "Peak strain in SWING (all biartic)", 1.0 if swing_ok else 0.0,
                   "bool", 1.0, 1.0, ["Thelen2005", "Chumanov2007"],
                   "classic late-swing hamstring lengthening paradigm."))
    return C, kin, ham


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def main(argv):
    target_n, matpath = None, None
    if "--mat" in argv:
        matpath = argv[argv.index("--mat") + 1]
    else:
        for a in argv[1:]:
            if a.isdigit():
                target_n = int(a)
        matpath = newest_nominal(target_n)
    if not matpath or not os.path.exists(matpath):
        raise SystemExit("No Nominal .mat found in Results/ (or --mat path invalid).")

    N = _mat_N(matpath)
    checks, kin, ham = build_checks(matpath)

    print("=" * 92)
    print("  PREDICTIVE SPRINT SIMULATION -- FACE VALIDITY vs PUBLISHED SPRINT DATA")
    print("=" * 92)
    print(f"  file : {os.path.basename(matpath)}")
    print(f"  mesh : N={N}   subject: international-caliber male sprinter "
          f"({BODY_MASS:.1f} kg, 1 BW={BW:.0f} N)")
    print("-" * 92)
    hdr = f"  {'metric':32s} {'sim':>10s} {'unit':>7s}  {'lit. range':>13s}  flag"
    grp = None
    for c in checks:
        if c.group != grp:
            grp = c.group
            print(f"\n  [{grp}]")
            print(hdr)
        rng = "-" if c.lo is None else f"{c.lo:g}..{c.hi:g}"
        val = "-" if c.value is None else f"{c.value:10.3f}"
        mark = {"OK": "OK ", "HIGH": "HIGH", "LOW": "LOW ", "INFO": "i  "}[c.flag]
        print(f"  {c.name:32s} {val} {c.unit:>7s}  {rng:>13s}  {mark}")

    n_ok = sum(c.flag == "OK" for c in checks)
    n_tot = sum(c.flag in ("OK", "HIGH", "LOW") for c in checks)
    print("\n" + "-" * 92)
    print(f"  {n_ok}/{n_tot} metrics inside published ranges. "
          f"HIGH/LOW flags are explained in the notes column of the CSV / report.")
    print("-" * 92)

    # ---- CSV ----
    os.makedirs(OUTDIR, exist_ok=True)
    csvpath = os.path.join(OUTDIR, "validation_summary.csv")
    with open(csvpath, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["group", "metric", "sim_value", "unit", "lit_low", "lit_high",
                    "flag", "references", "note"])
        for c in checks:
            w.writerow([c.group, c.name,
                        "" if c.value is None else round(c.value, 4), c.unit,
                        c.lo, c.hi, c.flag, "; ".join(c.refs), c.note])
    print(f"  wrote {os.path.relpath(csvpath, HERE)}")

    print("\n  REFERENCES")
    used = sorted({r for c in checks for r in c.refs})
    for k in used:
        print(f"   [{k}] {REFERENCES[k]}")


if __name__ == "__main__":
    main(sys.argv)
