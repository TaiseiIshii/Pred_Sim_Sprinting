"""
compute_osim_muscle_paths_td.py
v3 (TDPT) 用の wrapping 込み筋経路キャッシュを OpenSim API で生成する。

v2 版 compute_osim_muscle_paths.py との違いは **ポーズの入力源だけ**:
TDPT 条件には .mot が無いので、最適化結果 .mat の optVars_nsc.q（37自由度の関節角
軌道, rad/m）を直接読み、モデルの座標名にマッピングしてポーズする。あとは同じ
（getCurrentPath で wrapping 済み筋経路、getTransformInGround で body 変換を抽出）。

実行環境: **opensim を import できる env**（このマシンでは conda `opencap`）。
  & 'C:\\Users\\...\\envs\\opencap\\python.exe' compute_osim_muscle_paths_td.py --frames 60

出力: Results/PelvicTD_Study/_muscle_cache.pkl
  形式は v2 と同一（レンダラ visualize_pelvic_*_musculoskeletal.py がそのまま読める）。
"""
import argparse
import glob
import os
import pickle
from pathlib import Path

import numpy as np
from scipy.io import loadmat
import opensim as osim

from compute_osim_muscle_paths import (
    set_pose, body_transform, muscle_path_ground, load_muscle_dynamics,
    RENDER_BODIES, HAM_BASES, base_name, TRANS_COORDS,
)

# (offset_deg, cache_ident). ident = .mat ファイル名の `___<ident>.mat` 部分。
CONDITION_SPECS = [
    (-8, "PelvisTDwide_m8"),
    (0,  "PelvisTDwide_p0"),
    (6,  "PelvisTD_p6"),
]

# q の行順 (1-based 1..37) に対応する OpenSim 座標名（KINEMATIC_CHAIN を平坦化した順）。
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


def _get(o, *names):
    for n in names:
        o = getattr(o, n) if hasattr(o, n) else o[n]
    return o


def _mat_N(path):
    try:
        m = loadmat(path, struct_as_record=False, squeeze_me=True,
                    variable_names=["optimumOutput"])
        return int(np.asarray(_get(m["optimumOutput"], "options", "N")).ravel()[0])
    except Exception:
        return None


def pick_mat(results_dir, ident, target_n=50):
    fs = sorted(glob.glob(os.path.join(results_dir,
                f"pred_sprinting_data_*{ident}.mat")), key=os.path.getmtime,
                reverse=True)
    for p in fs:
        if _mat_N(p) == target_n:
            return p
    return fs[0] if fs else None


def cols_from_mat(mat_path, frames):
    """.mat の q(37×ncol, rad/m) を {coord_name: values(frames,)} に。回転は度に
    変換（set_pose が deg2rad するため）、並進はそのまま m。"""
    m = loadmat(str(mat_path), struct_as_record=False, squeeze_me=True)
    q = np.asarray(_get(m["optimumOutput"], "optVars_nsc", "q"), dtype=float)
    ncol = q.shape[1]
    ph_src = np.linspace(0.0, 1.0, ncol)
    ph_tgt = np.linspace(0.0, 1.0, frames, endpoint=False)
    cols = {}
    for i, name in enumerate(COORD_ORDER):
        v = np.interp(ph_tgt, ph_src, q[i, :])
        if name not in TRANS_COORDS:
            v = np.degrees(v)
        cols[name] = v
    mean_tilt = float(np.degrees(np.mean(q[0, :])))
    td_tilt = float(np.degrees(q[0, 0]))
    return ph_tgt, cols, mean_tilt, td_tilt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--mesh", type=int, default=50)
    ap.add_argument("--osim", type=str, default=None)
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    root = here.parent
    osim_path = Path(args.osim) if args.osim else (
        root / "OpenSimModel" / "Scaled_FullBody_HamnerModel_Muscle_withContact.osim")
    results_dir = str(root / "Results")
    out = root / "Results" / "PelvicTD_Study" / "_muscle_cache.pkl"
    out.parent.mkdir(parents=True, exist_ok=True)

    print("OpenSim", osim.GetVersion())
    model = osim.Model(str(osim_path))
    state = model.initSystem()
    cs = model.getCoordinateSet()

    # 全筋を描画（ハムは半径を強調）。muscle_order は muscleValues 行と対応。
    muscles, muscle_order, radius, is_ham = {}, [], {}, {}
    mset = model.getMuscles()
    for i in range(mset.getSize()):
        mm = mset.get(i)
        nm = mm.getName()
        muscle_order.append(nm)
        muscles[nm] = mm
        f = float(mm.getMaxIsometricForce())
        r = 0.0030 + 0.0040 * np.sqrt(max(f, 1.0) / 1500.0)
        if base_name(nm) in HAM_BASES:
            r = max(r, 0.009)
        radius[nm] = float(min(r, 0.013))
        is_ham[nm] = base_name(nm) in HAM_BASES
    print(f"描画筋数: {len(muscles)} (うちハム {sum(is_ham.values())})")

    cache = {}
    for off, ident in CONDITION_SPECS:
        mat = pick_mat(results_dir, ident, args.mesh)
        if not mat:
            print(f"  [WARN] {ident} (N={args.mesh}) の .mat なし。スキップ")
            continue
        phases, cols, mean_tilt, td_tilt = cols_from_mat(mat, args.frames)
        F = args.frames
        bodies = {b: np.zeros((F, 4, 4), dtype=np.float32) for b in RENDER_BODIES}
        mus = {nm: [None] * F for nm in muscles}
        for fi in range(F):
            set_pose(model, state, cs, cols, fi)
            for b in RENDER_BODIES:
                bodies[b][fi] = body_transform(model, state, b)
            for nm, mm in muscles.items():
                mus[nm][fi] = muscle_path_ground(state, mm)
        dyn = load_muscle_dynamics(mat, muscle_order)
        cache[ident] = {
            "offset": off, "mean_tilt": mean_tilt, "td_tilt": td_tilt,
            "phases": phases, "bodies": bodies, "muscles": mus,
            "is_ham": is_ham, "radius": radius, "dyn": dyn,
            "grf_force": None, "grf_point": None,
        }
        print(f"  [OK] {ident:18s} TD {td_tilt:6.2f} / mean {mean_tilt:6.2f} deg, "
              f"{F} frames  ({os.path.basename(mat)})")

    with open(out, "wb") as f:
        pickle.dump(cache, f, protocol=4)
    print(f"[OK] cache -> {out}  ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
