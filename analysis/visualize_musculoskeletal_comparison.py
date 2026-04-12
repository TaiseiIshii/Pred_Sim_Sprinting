"""
visualize_musculoskeletal_comparison.py
筋骨格モデル（3D骨メッシュ）による走動作ベースライン vs 最適化後の比較可視化

OpenSim 4.5 の Geometry フォルダ内の .vtp ファイルを読み込み、
フォワードキネマティクスで各骨メッシュを配置して
実験IKデータとシミュレーション結果を2体並べて描画します。

出力:
  - 静止画スナップショット (PNG) — 複数時刻
  - GIFアニメーション
  - 連番PNG (動画制作用)

Usage:
    python visualize_musculoskeletal_comparison.py
    python visualize_musculoskeletal_comparison.py --sim_label Nominal
    python visualize_musculoskeletal_comparison.py --snapshot_times 0.08 0.12 0.16 0.20
    python visualize_musculoskeletal_comparison.py --view front

Date: 2026-03-24
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import pyvista as pv

# ═══════════════════════════════════════════════════════════════════════════
# Forward-Kinematics Engine
# ═══════════════════════════════════════════════════════════════════════════

def _rot_axis_angle(axis, angle_rad):
    """Rodrigues rotation matrix for rotation about *axis* by *angle_rad*."""
    axis = np.asarray(axis, dtype=float)
    n = np.linalg.norm(axis)
    if n < 1e-30:
        return np.eye(3)
    axis = axis / n
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    K = np.array([[0, -axis[2], axis[1]],
                  [axis[2], 0, -axis[0]],
                  [-axis[1], axis[0], 0]])
    return np.eye(3) + s * K + (1 - c) * K @ K


def _homogeneous(R, t):
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T


# ───────────────────────────────────────────────────────────────────────────
# Kinematic chain (extracted from .osim)
# ───────────────────────────────────────────────────────────────────────────

KINEMATIC_CHAIN = [
    ("pelvis", "ground", [0, 0, 0], [
        ("pelvis_tilt",     [0, 0, 1], "rot"),
        ("pelvis_list",     [1, 0, 0], "rot"),
        ("pelvis_rotation", [0, 1, 0], "rot"),
        ("pelvis_tx",       [1, 0, 0], "trans"),
        ("pelvis_ty",       [0, 1, 0], "trans"),
        ("pelvis_tz",       [0, 0, 1], "trans"),
    ]),
    ("femur_r", "pelvis", [-0.0623853, -0.0583263, 0.0728399], [
        ("hip_flexion_r",   [0, 0, 1], "rot"),
        ("hip_adduction_r", [1, 0, 0], "rot"),
        ("hip_rotation_r",  [0, 1, 0], "rot"),
    ]),
    ("tibia_r", "femur_r", [0.0041, -0.41, 0], [
        ("knee_angle_r", [0, 0, 1], "rot"),
    ]),
    ("talus_r", "tibia_r", [0, -0.481118, 0], [
        ("ankle_angle_r", [-0.10501355, -0.17402245, 0.97912632], "rot"),
    ]),
    ("calcn_r", "talus_r", [-0.0406989, -0.0368078, 0.0069492], [
        ("subtalar_angle_r", [0.78717961, 0.60474746, -0.12094949], "rot"),
    ]),
    ("toes_r", "calcn_r", [0.149210, -0.001755, 0.000948], [
        ("mtp_angle_r", [-0.5809544, 0, 0.81393611], "rot"),
    ]),
    ("femur_l", "pelvis", [-0.0623853, -0.0583263, -0.0728399], [
        ("hip_flexion_l",   [0, 0, 1], "rot"),
        ("hip_adduction_l", [-1, 0, 0], "rot"),
        ("hip_rotation_l",  [0, -1, 0], "rot"),
    ]),
    ("tibia_l", "femur_l", [0.0041, -0.41, 0], [
        ("knee_angle_l", [0, 0, 1], "rot"),
    ]),
    ("talus_l", "tibia_l", [0, -0.481118, 0], [
        ("ankle_angle_l", [0.10501355, 0.17402245, 0.97912632], "rot"),
    ]),
    ("calcn_l", "talus_l", [-0.0406989, -0.0368078, -0.0069492], [
        ("subtalar_angle_l", [-0.78717961, -0.60474746, -0.12094949], "rot"),
    ]),
    ("toes_l", "calcn_l", [0.149210, -0.001755, -0.000948], [
        ("mtp_angle_l", [0.5809544, 0, 0.81393611], "rot"),
    ]),
    ("torso", "pelvis", [-0.088857, 0.071915, 0], [
        ("lumbar_extension", [0, 0, 1], "rot"),
        ("lumbar_bending",   [1, 0, 0], "rot"),
        ("lumbar_rotation",  [0, 1, 0], "rot"),
    ]),
    ("humerus_r", "torso", [0.003672, 0.359390, 0.183537], [
        ("arm_flex_r", [0, 0, 1], "rot"),
        ("arm_add_r",  [1, 0, 0], "rot"),
        ("arm_rot_r",  [0, 1, 0], "rot"),
    ]),
    ("ulna_r", "humerus_r", [0.011167, -0.342102, -0.008152], [
        ("elbow_flex_r", [0.22604696, 0.022269, 0.97386183], "rot"),
    ]),
    ("radius_r", "ulna_r", [-0.005088, -0.013896, 0.019727], [
        ("pro_sup_r", [0.05639803, 0.99840646, 0.001952], "rot"),
    ]),
    ("hand_r", "radius_r", [-0.006653, -0.251965, 0.010293], [
        ("wrist_flex_r", [0, 0, 1], "rot"),
        ("wrist_dev_r",  [1, 0, 0], "rot"),
    ]),
    ("humerus_l", "torso", [0.003672, 0.359390, -0.183537], [
        ("arm_flex_l", [0, 0, 1], "rot"),
        ("arm_add_l",  [-1, 0, 0], "rot"),
        ("arm_rot_l",  [0, -1, 0], "rot"),
    ]),
    ("ulna_l", "humerus_l", [0.011167, -0.342102, 0.008152], [
        ("elbow_flex_l", [-0.22604696, -0.022269, 0.97386183], "rot"),
    ]),
    ("radius_l", "ulna_l", [-0.005088, -0.013896, -0.019727], [
        ("pro_sup_l", [-0.05639803, -0.99840646, 0.001952], "rot"),
    ]),
    ("hand_l", "radius_l", [-0.006653, -0.251965, -0.010293], [
        ("wrist_flex_l", [0, 0, 1], "rot"),
        ("wrist_dev_l",  [-1, 0, 0], "rot"),
    ]),
]


# ───────────────────────────────────────────────────────────────────────────
# Body → Geometry mapping (extracted from .osim VisibleObject)
# ───────────────────────────────────────────────────────────────────────────

BODY_GEOMETRY = {
    "pelvis": {
        "files": ["sacrum.vtp", "pelvis.vtp", "l_pelvis.vtp"],
        "scale": (0.882394, 0.882394, 0.872334),
    },
    "femur_r": {
        "files": ["femur_r.vtp"],
        "scale": (0.857849, 1.06805, 0.857849),
    },
    "femur_l": {
        "files": ["femur_l.vtp"],
        "scale": (0.857849, 1.06805, 0.857849),
    },
    "tibia_r": {
        "files": ["tibia_r.vtp", "fibula_r.vtp"],
        "scale": (0.823052, 1.11888, 0.823052),
    },
    "tibia_l": {
        "files": ["tibia_l.vtp", "fibula_l.vtp"],
        "scale": (0.823052, 1.11888, 0.823052),
    },
    "talus_r": {
        "files": ["talus_rv.vtp"],
        "scale": (0.834506, 0.877421, 0.877421),
    },
    "talus_l": {
        "files": ["talus_lv.vtp"],
        "scale": (0.834506, 0.877421, 0.877421),
    },
    "calcn_r": {
        "files": ["foot.vtp"],
        "scale": (0.834506, 0.877421, 0.877421),
    },
    "calcn_l": {
        "files": ["l_foot.vtp"],
        "scale": (0.834506, 0.877421, 0.877421),
    },
    "toes_r": {
        "files": ["bofoot.vtp"],
        "scale": (0.834506, 0.877421, 0.877421),
    },
    "toes_l": {
        "files": ["l_bofoot.vtp"],
        "scale": (0.834506, 0.877421, 0.877421),
    },
    "torso": {
        "files": ["hat_spine.vtp", "hat_jaw.vtp", "hat_skull.vtp", "hat_ribs_scap.vtp"],
        "scale": (1.16398, 0.967402, 1.07963),
    },
    "humerus_r": {
        "files": ["humerus_rv.vtp"],
        "scale": (0.849592, 1.19502, 0.849592),
    },
    "humerus_l": {
        "files": ["humerus_lv.vtp"],
        "scale": (0.849592, 1.19502, 0.849592),
    },
    "ulna_r": {
        "files": ["ulna_rv.vtp"],
        "scale": (0.756302, 1.06837, 0.756302),
    },
    "ulna_l": {
        "files": ["ulna_lv.vtp"],
        "scale": (0.756302, 1.06837, 0.756302),
    },
    "radius_r": {
        "files": ["radius_rv.vtp"],
        "scale": (0.756302, 1.06837, 0.756302),
    },
    "radius_l": {
        "files": ["radius_lv.vtp"],
        "scale": (0.756302, 1.06837, 0.756302),
    },
    "hand_r": {
        "files": [
            "pisiform_rvs.vtp", "lunate_rvs.vtp", "scaphoid_rvs.vtp",
            "triquetrum_rvs.vtp", "hamate_rvs.vtp", "capitate_rvs.vtp",
            "trapezoid_rvs.vtp", "trapezium_rvs.vtp",
            "metacarpal1_rvs.vtp", "metacarpal2_rvs.vtp",
            "metacarpal3_rvs.vtp", "metacarpal4_rvs.vtp",
            "metacarpal5_rvs.vtp",
            "thumb_proximal_rvs.vtp", "thumb_distal_rvs.vtp",
            "index_proximal_rvs.vtp", "index_medial_rvs.vtp", "index_distal_rvs.vtp",
            "middle_proximal_rvs.vtp", "middle_medial_rvs.vtp", "middle_distal_rvs.vtp",
            "ring_proximal_rvs.vtp", "ring_medial_rvs.vtp", "ring_distal_rvs.vtp",
            "little_proximal_rvs.vtp", "little_medial_rvs.vtp", "little_distal_rvs.vtp",
        ],
        "scale": (0.871418, 0.871418, 0.871418),
    },
    "hand_l": {
        "files": [
            "pisiform_lvs.vtp", "lunate_lvs.vtp", "scaphoid_lvs.vtp",
            "triquetrum_lvs.vtp", "hamate_lvs.vtp", "capitate_lvs.vtp",
            "trapezoid_lvs.vtp", "trapezium_lvs.vtp",
            "metacarpal1_lvs.vtp", "metacarpal2_lvs.vtp",
            "metacarpal3_lvs.vtp", "metacarpal4_lvs.vtp",
            "metacarpal5_lvs.vtp",
            "thumb_proximal_lvs.vtp", "thumb_distal_lvs.vtp",
            "index_proximal_lvs.vtp", "index_medial_lvs.vtp", "index_distal_lvs.vtp",
            "middle_proximal_lvs.vtp", "middle_medial_lvs.vtp", "middle_distal_lvs.vtp",
            "ring_proximal_lvs.vtp", "ring_medial_lvs.vtp", "ring_distal_lvs.vtp",
            "little_proximal_lvs.vtp", "little_medial_lvs.vtp", "little_distal_lvs.vtp",
        ],
        "scale": (0.871418, 0.871418, 0.871418),
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# FK computation
# ═══════════════════════════════════════════════════════════════════════════

def compute_body_transforms(q_dict):
    """
    Given q_dict {coord_name: value_in_deg_or_m}, compute 4x4 world
    transforms for every body. Returns dict {body_name: 4x4 ndarray}.
    """
    transforms = {"ground": np.eye(4)}

    for body, parent, loc_in_parent, coords in KINEMATIC_CHAIN:
        T_parent = transforms[parent]

        R_joint = np.eye(3)
        t_joint = np.zeros(3)

        for coord_name, axis, mode in coords:
            val = q_dict.get(coord_name, 0.0)
            if mode == "rot":
                R_joint = _rot_axis_angle(axis, np.deg2rad(val)) @ R_joint
            else:
                t_joint += np.array(axis, dtype=float) * val

        T_loc = _homogeneous(np.eye(3), np.array(loc_in_parent, dtype=float))
        T_joint = _homogeneous(R_joint, t_joint)
        transforms[body] = T_parent @ T_loc @ T_joint

    return transforms


# ═══════════════════════════════════════════════════════════════════════════
# .mot reader
# ═══════════════════════════════════════════════════════════════════════════

def read_mot(filepath):
    filepath = Path(filepath)
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    header_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("time") or stripped.startswith("/jointset"):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(f"Cannot find header in {filepath}")
    headers = [h.strip() for h in lines[header_idx].strip().split("\t") if h.strip()]
    data_rows = []
    for line in lines[header_idx + 1:]:
        s = line.strip()
        if s and not s.startswith("#"):
            vals = s.split()
            if len(vals) == len(headers):
                data_rows.append([float(v) for v in vals])
    return pd.DataFrame(data_rows, columns=headers)


def simplify_column(col):
    parts = col.strip("/").split("/")
    if len(parts) >= 3:
        return parts[-2]
    return col


def mot_to_q_series(df):
    col_map = {}
    for c in df.columns:
        if c == "time":
            continue
        col_map[simplify_column(c)] = c
    times = df["time"].values
    series = []
    for i in range(len(times)):
        q = {}
        for simple_name, orig_col in col_map.items():
            q[simple_name] = df[orig_col].iloc[i]
        series.append((times[i], q))
    return series


# ═══════════════════════════════════════════════════════════════════════════
# Geometry loading and mesh management
# ═══════════════════════════════════════════════════════════════════════════

# Search order for OpenSim Geometry folder
GEOMETRY_SEARCH_PATHS = [
    Path(r"C:\OpenSim 4.5\Geometry"),
    Path(r"C:\OpenSim 4.4\Geometry"),
    Path(r"C:\OpenSim 4.3\Geometry"),
    Path(r"C:\OpenSim 4.2\Geometry"),
    Path(r"C:\OpenSim 4.1\Geometry"),
    Path(r"C:\Program Files\OpenSim 4.5\Geometry"),
    Path(r"C:\Program Files\OpenSim 4.4\Geometry"),
]


def find_geometry_dir():
    """Find the OpenSim Geometry directory."""
    import os
    # Check OPENSIM_HOME env
    opensim_home = os.environ.get("OPENSIM_HOME", "")
    if opensim_home:
        p = Path(opensim_home) / "Geometry"
        if p.exists():
            return p

    for p in GEOMETRY_SEARCH_PATHS:
        if p.exists():
            return p

    raise FileNotFoundError(
        "OpenSim Geometry folder not found.\n"
        "Set OPENSIM_HOME env or install OpenSim."
    )


def load_body_meshes(geometry_dir: Path):
    """
    Load all body meshes from VTP files. Returns dict {body_name: pv.PolyData}
    where each PolyData is the merged mesh of all geometry files for that body,
    with scale_factors already applied (in the body's local frame).
    """
    meshes = {}
    for body_name, info in BODY_GEOMETRY.items():
        parts = []
        sx, sy, sz = info["scale"]

        for fname in info["files"]:
            fpath = geometry_dir / fname
            if not fpath.exists():
                continue
            try:
                mesh = pv.read(str(fpath))
                # Apply body-level scale
                pts = mesh.points.copy()
                pts[:, 0] *= sx
                pts[:, 1] *= sy
                pts[:, 2] *= sz
                mesh.points = pts
                parts.append(mesh)
            except Exception as e:
                print(f"  [WARN] {fname} load failed: {e}")

        if parts:
            merged = parts[0]
            for p in parts[1:]:
                merged = merged.merge(p)
            meshes[body_name] = merged

    return meshes


def transform_mesh(mesh: pv.PolyData, T: np.ndarray) -> pv.PolyData:
    """Apply a 4x4 homogeneous transform to a mesh (returns new copy)."""
    m = mesh.copy()
    pts = m.points.copy()
    pts_h = np.hstack([pts, np.ones((len(pts), 1))])
    pts_t = (T @ pts_h.T).T[:, :3]
    m.points = pts_t
    return m


def build_posed_model(body_meshes, transforms, z_offset=0.0):
    """
    Given body meshes (in local frame) and world transforms,
    return a single merged mesh with all bodies transformed.
    """
    parts = []
    for body_name, mesh in body_meshes.items():
        if body_name not in transforms:
            continue
        T = transforms[body_name].copy()
        T[2, 3] += z_offset  # Z offset for side-by-side display
        posed = transform_mesh(mesh, T)
        parts.append(posed)

    if not parts:
        return pv.PolyData()
    merged = parts[0]
    for p in parts[1:]:
        merged = merged.merge(p)
    return merged


# ═══════════════════════════════════════════════════════════════════════════
# Rendering functions
# ═══════════════════════════════════════════════════════════════════════════

def setup_camera(pl, view="side", center_x=0.0):
    """Set camera position for a given view."""
    if view == "side":
        # Sagittal view (looking from +Z toward -Z)
        pl.camera_position = [
            (center_x, 0.6, 3.5),    # camera position
            (center_x, 0.6, 0.0),    # focal point
            (0, 1, 0),                # up vector
        ]
    elif view == "front":
        # Frontal view (looking from +X toward -X)
        pl.camera_position = [
            (center_x + 4.0, 0.6, 0.0),
            (center_x, 0.6, 0.0),
            (0, 1, 0),
        ]
    elif view == "three_quarter":
        # 3/4 view
        pl.camera_position = [
            (center_x + 2.5, 1.2, 2.5),
            (center_x, 0.5, 0.0),
            (0, 1, 0),
        ]


def add_ground_plane(pl, x_range=(-2, 3), z_range=(-1.5, 1.5)):
    """Add a ground plane at y=0."""
    ground = pv.Plane(
        center=((x_range[0]+x_range[1])/2, 0.0, (z_range[0]+z_range[1])/2),
        direction=(0, 1, 0),
        i_size=x_range[1]-x_range[0],
        j_size=z_range[1]-z_range[0],
        i_resolution=10,
        j_resolution=10,
    )
    pl.add_mesh(ground, color="#8B7355", opacity=0.3, style="wireframe",
                line_width=1)


def render_snapshot(body_meshes, exp_q, sim_q, output_path, time_val,
                     view="side", title_label=""):
    """
    Render a single snapshot with experimental (blue) and simulation (red)
    models side by side.
    """
    pv.global_theme.background = "white"

    exp_transforms = compute_body_transforms(exp_q)
    sim_transforms = compute_body_transforms(sim_q)

    # Place sim model offset in Z for clarity
    z_sep = 0.6  # separation distance in Z

    exp_mesh = build_posed_model(body_meshes, exp_transforms, z_offset=z_sep / 2)
    sim_mesh = build_posed_model(body_meshes, sim_transforms, z_offset=-z_sep / 2)

    pl = pv.Plotter(off_screen=True, window_size=[1600, 900])

    # Experimental in blue
    if exp_mesh.n_points > 0:
        pl.add_mesh(exp_mesh, color="#4FC3F7", opacity=0.85,
                    smooth_shading=True, label="Experimental (IK)")

    # Simulation in red/orange
    if sim_mesh.n_points > 0:
        pl.add_mesh(sim_mesh, color="#EF5350", opacity=0.75,
                    smooth_shading=True, label="Simulation")

    add_ground_plane(pl)

    # Center on experimental pelvis
    cx = exp_transforms.get("pelvis", np.eye(4))[0, 3]
    setup_camera(pl, view=view, center_x=cx)

    pl.add_text(f"t = {time_val:.4f} s    {title_label}",
                position="upper_left", font_size=14, color="black")
    pl.add_text("Blue: Experimental (IK)  |  Red: Simulation",
                position="upper_right", font_size=11, color="black")

    pl.add_light(pv.Light(position=(cx + 2, 3, 3), intensity=0.7))
    pl.add_light(pv.Light(position=(cx - 2, 3, -3), intensity=0.4))

    pl.screenshot(str(output_path))
    pl.close()
    print(f"  [OK] Snapshot: {output_path}")


def render_overlay_snapshot(body_meshes, exp_q, sim_q, output_path, time_val,
                              view="side", title_label=""):
    """
    Render overlay (same position) — semi-transparent to see differences.
    """
    pv.global_theme.background = "white"

    exp_transforms = compute_body_transforms(exp_q)
    sim_transforms = compute_body_transforms(sim_q)

    # Align pelvis X position for posture comparison
    dx = exp_transforms["pelvis"][0, 3] - sim_transforms["pelvis"][0, 3]
    for body in sim_transforms:
        sim_transforms[body][0, 3] += dx

    exp_mesh = build_posed_model(body_meshes, exp_transforms)
    sim_mesh = build_posed_model(body_meshes, sim_transforms)

    pl = pv.Plotter(off_screen=True, window_size=[1400, 900])

    if exp_mesh.n_points > 0:
        pl.add_mesh(exp_mesh, color="#2196F3", opacity=0.5,
                    smooth_shading=True)
    if sim_mesh.n_points > 0:
        pl.add_mesh(sim_mesh, color="#F44336", opacity=0.5,
                    smooth_shading=True)

    add_ground_plane(pl)

    cx = exp_transforms.get("pelvis", np.eye(4))[0, 3]
    setup_camera(pl, view=view, center_x=cx)

    pl.add_text(f"Overlay  t = {time_val:.4f} s    {title_label}",
                position="upper_left", font_size=14, color="black")
    pl.add_text("Blue: Experimental  |  Red: Simulation",
                position="upper_right", font_size=11, color="black")

    pl.add_light(pv.Light(position=(cx + 2, 3, 3), intensity=0.7))
    pl.add_light(pv.Light(position=(cx - 2, 3, -3), intensity=0.4))

    pl.screenshot(str(output_path))
    pl.close()
    print(f"  [OK] Overlay: {output_path}")


def render_multi_view_snapshot(body_meshes, exp_q, sim_q, output_path,
                                 time_val, title_label=""):
    """
    Render a 2x2 multi-view panel: side|front × exp+sim|overlay
    """
    pv.global_theme.background = "white"

    exp_transforms = compute_body_transforms(exp_q)
    sim_transforms = compute_body_transforms(sim_q)

    z_sep = 0.6
    exp_mesh_sep = build_posed_model(body_meshes, exp_transforms, z_offset=z_sep / 2)
    sim_mesh_sep = build_posed_model(body_meshes, sim_transforms, z_offset=-z_sep / 2)

    # Overlay (aligned)
    sim_transforms_al = {}
    dx = exp_transforms["pelvis"][0, 3] - sim_transforms["pelvis"][0, 3]
    for body in sim_transforms:
        sim_transforms_al[body] = sim_transforms[body].copy()
        sim_transforms_al[body][0, 3] += dx
    exp_mesh_ov = build_posed_model(body_meshes, exp_transforms)
    sim_mesh_ov = build_posed_model(body_meshes, sim_transforms_al)

    cx = exp_transforms.get("pelvis", np.eye(4))[0, 3]

    pl = pv.Plotter(off_screen=True, shape=(2, 2), window_size=[2000, 1400])

    titles = [
        ("Sagittal (Side-by-side)", "side"),
        ("Frontal (Side-by-side)", "front"),
        ("Sagittal (Overlay)", "side"),
        ("Frontal (Overlay)", "front"),
    ]

    for idx, (title, view) in enumerate(titles):
        row, col = divmod(idx, 2)
        pl.subplot(row, col)

        if idx < 2:  # side-by-side
            if exp_mesh_sep.n_points > 0:
                pl.add_mesh(exp_mesh_sep, color="#4FC3F7", opacity=0.85,
                            smooth_shading=True)
            if sim_mesh_sep.n_points > 0:
                pl.add_mesh(sim_mesh_sep, color="#EF5350", opacity=0.75,
                            smooth_shading=True)
        else:  # overlay
            if exp_mesh_ov.n_points > 0:
                pl.add_mesh(exp_mesh_ov, color="#2196F3", opacity=0.5,
                            smooth_shading=True)
            if sim_mesh_ov.n_points > 0:
                pl.add_mesh(sim_mesh_ov, color="#F44336", opacity=0.5,
                            smooth_shading=True)

        add_ground_plane(pl)
        setup_camera(pl, view=view, center_x=cx)
        pl.add_text(title, position="upper_left", font_size=12, color="black")
        pl.add_light(pv.Light(position=(cx + 2, 3, 3), intensity=0.7))

    pl.screenshot(str(output_path))
    pl.close()
    print(f"  [OK] Multi-view: {output_path}")


def _render_single_frame(body_meshes, exp_q, sim_q, time_val,
                          view="side", title_label="",
                          window_size=(1920, 1080), z_sep=0.6,
                          mode="side_by_side"):
    """
    Render a single frame and return the image as numpy array (H, W, 3).
    mode: "side_by_side" | "overlay"
    """
    exp_transforms = compute_body_transforms(exp_q)
    sim_transforms = compute_body_transforms(sim_q)

    pv.global_theme.background = "white"
    pl = pv.Plotter(off_screen=True, window_size=list(window_size))

    if mode == "overlay":
        # Align pelvis X for posture comparison
        dx = exp_transforms["pelvis"][0, 3] - sim_transforms["pelvis"][0, 3]
        sim_transforms_al = {}
        for body in sim_transforms:
            sim_transforms_al[body] = sim_transforms[body].copy()
            sim_transforms_al[body][0, 3] += dx
        exp_mesh = build_posed_model(body_meshes, exp_transforms)
        sim_mesh = build_posed_model(body_meshes, sim_transforms_al)
        exp_opacity, sim_opacity = 0.55, 0.50
    else:
        exp_mesh = build_posed_model(body_meshes, exp_transforms,
                                     z_offset=z_sep / 2)
        sim_mesh = build_posed_model(body_meshes, sim_transforms,
                                     z_offset=-z_sep / 2)
        exp_opacity, sim_opacity = 0.85, 0.75

    if exp_mesh.n_points > 0:
        pl.add_mesh(exp_mesh, color="#4FC3F7", opacity=exp_opacity,
                    smooth_shading=True)
    if sim_mesh.n_points > 0:
        pl.add_mesh(sim_mesh, color="#EF5350", opacity=sim_opacity,
                    smooth_shading=True)

    add_ground_plane(pl)

    cx = exp_transforms.get("pelvis", np.eye(4))[0, 3]
    setup_camera(pl, view=view, center_x=cx)

    pl.add_text(f"t = {time_val:.4f} s    {title_label}",
                position="upper_left", font_size=14, color="black")
    label_text = ("Blue: Experimental  |  Red: Simulation"
                  if mode == "overlay"
                  else "Blue: Experimental (IK)  |  Red: Simulation")
    pl.add_text(label_text, position="upper_right", font_size=11, color="black")
    pl.add_light(pv.Light(position=(cx + 2, 3, 3), intensity=0.7))
    pl.add_light(pv.Light(position=(cx - 2, 3, -3), intensity=0.4))

    img = pl.screenshot(return_img=True)
    pl.close()
    return img


def render_animation_mp4(body_meshes, exp_series, sim_series,
                          output_dir, view="side", title_label="",
                          fps=30, n_loops=3, mode="side_by_side",
                          window_size=(1920, 1080)):
    """
    Render animation and save as MP4 (H.264).

    Parameters
    ----------
    n_loops : int
        Number of times to loop the motion in the video.
    mode : str
        "side_by_side" or "overlay"
    """
    import imageio

    exp_times = np.array([s[0] for s in exp_series])
    sim_times = np.array([s[0] for s in sim_series])
    t_start = max(exp_times[0], sim_times[0])
    t_end = min(exp_times[-1], sim_times[-1])
    duration = t_end - t_start

    # Compute frames: target fps-based count per loop
    frames_per_loop = max(int(duration * fps), 30)
    total_frames = frames_per_loop * n_loops
    # Time sequence: loop forward n_loops times
    single_times = np.linspace(t_start, t_end, frames_per_loop)
    all_times = np.tile(single_times, n_loops)

    safe_label = title_label.strip("[] ").replace(" ", "_")
    mp4_path = output_dir / f"musculoskeletal_{mode}_{safe_label}.mp4"

    print(f"  Generating MP4 ({mode}, {total_frames} frames, "
          f"{fps} fps, {n_loops} loops)...")

    writer = imageio.get_writer(str(mp4_path), fps=fps, codec="libx264",
                                 quality=8,
                                 output_params=["-pix_fmt", "yuv420p"])

    for fi, t in enumerate(all_times):
        exp_idx = np.argmin(np.abs(exp_times - t))
        sim_idx = np.argmin(np.abs(sim_times - t))

        loop_num = fi // frames_per_loop + 1
        lbl = f"{title_label}  Loop {loop_num}/{n_loops}" if n_loops > 1 else title_label

        img = _render_single_frame(
            body_meshes, exp_series[exp_idx][1], sim_series[sim_idx][1],
            t, view=view, title_label=lbl,
            window_size=window_size, mode=mode,
        )
        writer.append_data(img)

        if (fi + 1) % 20 == 0 or fi == total_frames - 1:
            print(f"    Frame {fi + 1}/{total_frames} done")

    writer.close()
    file_size_mb = mp4_path.stat().st_size / (1024 * 1024)
    print(f"  [OK] MP4: {mp4_path}  ({file_size_mb:.1f} MB)")
    return mp4_path


def render_animation_frames(body_meshes, exp_series, sim_series,
                              output_dir, view="side", title_label=""):
    """
    Render all frames as sequential PNGs and generate a GIF.
    """
    import imageio

    exp_times = np.array([s[0] for s in exp_series])
    sim_times = np.array([s[0] for s in sim_series])
    t_start = max(exp_times[0], sim_times[0])
    t_end = min(exp_times[-1], sim_times[-1])

    # Use ~80 frames for a smooth animation
    n_frames = 80
    frame_times = np.linspace(t_start, t_end, n_frames)

    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Generating animation frames ({n_frames} frames)...")

    image_files = []
    for fi, t in enumerate(frame_times):
        exp_idx = np.argmin(np.abs(exp_times - t))
        sim_idx = np.argmin(np.abs(sim_times - t))

        img = _render_single_frame(
            body_meshes, exp_series[exp_idx][1], sim_series[sim_idx][1],
            t, view=view, title_label=title_label,
            window_size=(1400, 800),
        )
        frame_path = frames_dir / f"frame_{fi:04d}.png"
        imageio.v3.imwrite(str(frame_path), img)
        image_files.append(frame_path)

        if (fi + 1) % 20 == 0 or fi == n_frames - 1:
            print(f"    Frame {fi + 1}/{n_frames} done")

    # Build GIF
    gif_path = output_dir / f"musculoskeletal_animation_{title_label.strip('[] ')}.gif"
    images = [imageio.v3.imread(str(f)) for f in image_files]
    imageio.mimsave(str(gif_path), images, duration=100, loop=0)  # ~10fps
    print(f"  [OK] GIF animation: {gif_path}")
    return gif_path


# ═══════════════════════════════════════════════════════════════════════════
# File discovery
# ═══════════════════════════════════════════════════════════════════════════

def find_experimental_ik(project_root):
    ik_dir = project_root / "MainFunctions" / "ExperimentalData" / "IK_Splined"
    candidates = list(ik_dir.glob("*.mot"))
    if not candidates:
        raise FileNotFoundError(f"IK .mot not found in {ik_dir}")
    return candidates[0]


def find_simulation_coords(project_root, label=None):
    results_dir = project_root / "Results"
    all_coords = sorted(results_dir.glob("pred_sprinting_coords_*.mot"))
    if label:
        filtered = [p for p in all_coords if label.lower() in p.name.lower()]
        return filtered if filtered else all_coords[:1]
    return all_coords[:1]


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="筋骨格モデルによる走動作比較 (実験IK vs シミュレーション)")
    parser.add_argument("--sim_label", type=str, default="Nominal",
                        help="Simulation condition label (例: Nominal, HTD_Plus_4)")
    parser.add_argument("--snapshot_times", type=float, nargs="+", default=None,
                        help="Snapshot times [s]")
    parser.add_argument("--view", type=str, default="side",
                        choices=["side", "front", "three_quarter"],
                        help="Camera view: side(矢状面) / front(前額面) / three_quarter")
    parser.add_argument("--no_animation", action="store_true",
                        help="Skip animation generation")
    parser.add_argument("--mp4", action="store_true",
                        help="Generate MP4 video (H.264)")
    parser.add_argument("--mp4_only", action="store_true",
                        help="Generate MP4 only (skip snapshots & GIF)")
    parser.add_argument("--fps", type=int, default=30,
                        help="Video frame rate (default: 30)")
    parser.add_argument("--loops", type=int, default=3,
                        help="Number of loop repetitions in video (default: 3)")
    parser.add_argument("--overlay", action="store_true",
                        help="Use overlay mode instead of side-by-side")
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--geometry_dir", type=str, default=None,
                        help="Path to OpenSim Geometry folder")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent

    print("=" * 60)
    print("  Musculoskeletal Model - Running Motion Comparison")
    print("=" * 60)

    # Find geometry directory
    if args.geometry_dir:
        geom_dir = Path(args.geometry_dir)
    else:
        geom_dir = find_geometry_dir()
    print(f"\n[Geometry]  {geom_dir}")

    # Load meshes
    print("  Loading bone meshes...")
    body_meshes = load_body_meshes(geom_dir)
    print(f"  {len(body_meshes)} body meshes loaded")
    total_faces = sum(m.n_cells for m in body_meshes.values())
    print(f"  Total polygons: {total_faces:,}")

    # Load experimental data
    exp_path = find_experimental_ik(project_root)
    print(f"\n[Experimental]  {exp_path.name}")
    df_exp = read_mot(exp_path)
    exp_series = mot_to_q_series(df_exp)
    print(f"  Frames: {len(exp_series)}, "
          f"Time: {exp_series[0][0]:.4f}-{exp_series[-1][0]:.4f} s")

    # Load simulation
    sim_files = find_simulation_coords(project_root, args.sim_label)
    if not sim_files:
        print("ERROR: No simulation results found")
        return 1

    sim_path = sim_files[0]
    match = re.search(r"___(.+)\.mot$", sim_path.name)
    label = match.group(1) if match else "Sim"

    print(f"[Simulation]  {sim_path.name}")
    df_sim = read_mot(sim_path)
    sim_series = mot_to_q_series(df_sim)
    print(f"  Frames: {len(sim_series)}, "
          f"Time: {sim_series[0][0]:.4f}-{sim_series[-1][0]:.4f} s")

    # Output directory
    out_dir = Path(args.output_dir) if args.output_dir else \
        project_root / "Results" / "musculoskeletal_comparison"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine snapshot times
    t_start = max(exp_series[0][0], sim_series[0][0])
    t_end = min(exp_series[-1][0], sim_series[-1][0])

    if args.snapshot_times is None:
        snapshot_times = np.linspace(t_start + 0.005, t_end - 0.005, 5).tolist()
    else:
        snapshot_times = args.snapshot_times

    exp_times = np.array([s[0] for s in exp_series])
    sim_times = np.array([s[0] for s in sim_series])

    print(f"\n--- Rendering ---")

    anim_mode = "overlay" if args.overlay else "side_by_side"

    # If --mp4_only, skip snapshots
    if not args.mp4_only:
        # 1) Side-by-side snapshots
        for t_snap in snapshot_times:
            exp_idx = np.argmin(np.abs(exp_times - t_snap))
            sim_idx = np.argmin(np.abs(sim_times - t_snap))
            exp_q = exp_series[exp_idx][1]
            sim_q = sim_series[sim_idx][1]

            render_snapshot(
                body_meshes, exp_q, sim_q,
                out_dir / f"side_t{t_snap:.3f}_{label}.png",
                t_snap, view=args.view, title_label=f"[{label}]"
            )

        # 2) Overlay snapshots at key moments
        key_times = [snapshot_times[0], snapshot_times[len(snapshot_times) // 2],
                     snapshot_times[-1]]
        for t_snap in key_times:
            exp_idx = np.argmin(np.abs(exp_times - t_snap))
            sim_idx = np.argmin(np.abs(sim_times - t_snap))
            exp_q = exp_series[exp_idx][1]
            sim_q = sim_series[sim_idx][1]

            render_overlay_snapshot(
                body_meshes, exp_q, sim_q,
                out_dir / f"overlay_t{t_snap:.3f}_{label}.png",
                t_snap, view=args.view, title_label=f"[{label}]"
            )

        # 3) Multi-view panel at mid-point
        t_mid = (t_start + t_end) / 2
        exp_idx = np.argmin(np.abs(exp_times - t_mid))
        sim_idx = np.argmin(np.abs(sim_times - t_mid))
        render_multi_view_snapshot(
            body_meshes, exp_series[exp_idx][1], sim_series[sim_idx][1],
            out_dir / f"multiview_t{t_mid:.3f}_{label}.png",
            t_mid, title_label=f"[{label}]"
        )

    # 4) Animation (GIF)
    if not args.no_animation and not args.mp4_only:
        render_animation_frames(
            body_meshes, exp_series, sim_series,
            out_dir, view=args.view, title_label=f"[{label}]"
        )

    # 5) MP4 video
    if args.mp4 or args.mp4_only:
        render_animation_mp4(
            body_meshes, exp_series, sim_series,
            out_dir, view=args.view, title_label=f"[{label}]",
            fps=args.fps, n_loops=args.loops, mode=anim_mode,
        )

    print(f"\n{'=' * 60}")
    print(f"  Done! Output: {out_dir}")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
