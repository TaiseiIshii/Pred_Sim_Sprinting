"""
_probe_osim_ham.py  (opencap / OpenSim 4.x env)
Verify the core STEP-2 hypothesis: is hamstring musculotendon (MTU) length a
function of hip flexion & knee angle ONLY, i.e. INVARIANT to pelvis_tilt (the
pelvis-ground DOF) when hip/knee are held fixed?

If MTU length is flat while sweeping pelvis_tilt (hip/knee fixed at the Nominal
terminal-swing pose), then the "optimization-OFF" direct effect of pelvic tilt
on hamstring stretch is ~zero, and the Experiment-1 lengthening must be an
emergent re-optimization (hip-flexion) response.

Run:
  & 'C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\envs\\opencap\\python.exe' analysis\\_probe_osim_ham.py
"""
import os
import numpy as np
import opensim as osim

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "..", "OpenSimModel",
                     "Scaled_FullBody_HamnerModel_Muscle_withContact.osim")

HAM_KEYS = ("semimem", "semiten", "bifemlh", "bifemsh")


def main():
    model = osim.Model(MODEL)
    state = model.initSystem()

    coords = [model.getCoordinateSet().get(i).getName()
              for i in range(model.getCoordinateSet().getSize())]
    muscles = [model.getMuscles().get(i).getName()
               for i in range(model.getMuscles().getSize())]
    print("n coords =", len(coords), "| n muscles =", len(muscles))
    ham = [m for m in muscles if any(k in m.lower() for k in HAM_KEYS)]
    print("hamstring muscles:", ham)
    print("has pelvis_tilt coord:", "pelvis_tilt" in coords,
          "| hip_flexion_l:", "hip_flexion_l" in coords,
          "| knee_angle_l:", "knee_angle_l" in coords)

    def set_coord(name, val_rad):
        model.getCoordinateSet().get(name).setValue(state, val_rad)

    # Nominal-like terminal-swing pose for the LEFT leg (approx): hip flexed,
    # knee extending. Use representative values; the TEST is invariance to tilt,
    # not the absolute pose.
    base = {
        "hip_flexion_l": np.radians(45.0),
        "knee_angle_l": np.radians(-20.0),
        "hip_flexion_r": np.radians(-10.0),
        "knee_angle_r": np.radians(-30.0),
    }
    for k, v in base.items():
        if k in coords:
            set_coord(k, v)

    print("\nSweep pelvis_tilt with hip/knee FIXED -> left hamstring MTU length (m):")
    print(f"{'pelvis_tilt_deg':>15s} | "
          + " ".join(f"{m.split('_')[0][:8]:>9s}" for m in ham if m.endswith("_l")))
    lengths = {m: [] for m in ham if m.endswith("_l")}
    tilts = np.arange(-14, 3, 2.0)
    for td in tilts:
        if "pelvis_tilt" in coords:
            set_coord("pelvis_tilt", np.radians(td))
        model.realizePosition(state)
        vals = []
        for m in ham:
            if not m.endswith("_l"):
                continue
            L = model.getMuscles().get(m).getLength(state)
            lengths[m].append(L)
            vals.append(L)
        print(f"{td:15.1f} | " + " ".join(f"{v:9.5f}" for v in vals))

    print("\nRange of MTU length over the pelvis_tilt sweep (max-min, mm):")
    for m, arr in lengths.items():
        arr = np.asarray(arr)
        print(f"  {m:16s} {1000*(arr.max()-arr.min()):8.4f} mm   "
              f"(mean {1000*arr.mean():.1f} mm)")

    # Contrast: sweep hip flexion (fixed tilt) to show ham length DOES depend on it
    print("\nContrast: sweep hip_flexion_l with pelvis_tilt fixed -> MTU length (m):")
    if "pelvis_tilt" in coords:
        set_coord("pelvis_tilt", np.radians(-7.0))
    print(f"{'hip_flexion_deg':>15s} | "
          + " ".join(f"{m.split('_')[0][:8]:>9s}" for m in ham if m.endswith("_l")))
    for hf in np.arange(20, 61, 10.0):
        set_coord("hip_flexion_l", np.radians(hf))
        model.realizePosition(state)
        vals = [model.getMuscles().get(m).getLength(state)
                for m in ham if m.endswith("_l")]
        print(f"{hf:15.1f} | " + " ".join(f"{v:9.5f}" for v in vals))


if __name__ == "__main__":
    main()
