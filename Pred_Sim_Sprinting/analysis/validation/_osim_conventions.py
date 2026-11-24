"""Print OpenSim model coordinate conventions + body names (Step-4 prep).

Determines the sign of knee flexion, hip flexion, pelvis_tilt, and lists femur/tibia
body names, so the boundary-condition audit uses correct signs.

Run (opencap env):
  & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\envs\\opencap\\python.exe" \
      analysis/validation/_osim_conventions.py
"""
import os
import numpy as np
import opensim as osim

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "..", "..", "OpenSimModel",
                     "Scaled_FullBody_HamnerModel_Muscle_withContact.osim")


def main():
    m = osim.Model(MODEL)
    s = m.initSystem()
    cs = m.getCoordinateSet()
    print("=== coordinates of interest (rad -> deg range) ===")
    for i in range(cs.getSize()):
        c = cs.get(i)
        nm = c.getName()
        if any(k in nm for k in ("pelvis_tilt", "hip_flexion", "knee_angle", "knee_flex",
                                 "pelvis_tx", "pelvis_ty")):
            lo, hi = c.getRangeMin(), c.getRangeMax()
            dv = c.getDefaultValue()
            mo = c.getMotionType() if hasattr(c, "getMotionType") else "?"
            unit = "m" if nm.startswith("pelvis_t") and nm[-1] in "xyz" else "deg"
            conv = (lo, hi, dv) if unit == "m" else (np.degrees(lo), np.degrees(hi), np.degrees(dv))
            print(f"  {nm:18s} range=[{conv[0]:8.2f},{conv[1]:8.2f}] default={conv[2]:8.2f} {unit}")
    print("\n=== bodies (look for femur/tibia/pelvis) ===")
    bs = m.getBodySet()
    names = [bs.get(i).getName() for i in range(bs.getSize())]
    print("  ", [n for n in names if any(k in n for k in ("femur", "tibia", "pelvis", "calcn"))])
    print("\n=== left hamstring muscles present? ===")
    ms = m.getMuscles()
    mus = {ms.get(i).getName() for i in range(ms.getSize())}
    for want in ("semimem_l", "semiten_l", "bifemlh_l", "bifemsh_l"):
        print(f"  {want}: {'yes' if want in mus else 'NO'}")

    # baseline MTU at a neutral pose and at hip 30/knee sign test
    def set_pose(hipflex_deg, knee_deg, tilt_deg):
        for i in range(cs.getSize()):
            cs.get(i).setValue(s, cs.get(i).getDefaultValue(), False)
        for nm, val in (("pelvis_tilt", np.radians(tilt_deg)),
                        ("hip_flexion_l", np.radians(hipflex_deg)),
                        ("knee_angle_l", np.radians(knee_deg))):
            try:
                cs.get(nm).setValue(s, val, False)
            except Exception as e:
                print("   set fail", nm, e)
        m.assemble(s)
        m.realizePosition(s)
    print("\n=== knee sign test: MTU of bifemsh_l (knee-only) at knee +20 vs -20 ===")
    for kn in (20, -20):
        set_pose(0, kn, 0)
        L = m.getMuscles().get("bifemsh_l").getLength(s)
        print(f"  knee_angle_l={kn:+3d} deg -> bifemsh_l MTU={L*100:.2f} cm "
              f"(longer = more knee flexion stretches the knee flexor? check)")


if __name__ == "__main__":
    main()
