"""
visualize_form_comparison_v2.py
Improved Running Form Comparison: Experimental IK vs Simulation

Multiple visualization modes for intuitive form difference analysis:
  1) side_by_side  - Two models running side-by-side (sagittal view, camera tracks)
  2) overlay       - Semi-transparent overlay aligned at pelvis (best for posture diff)
  3) ghost_trail   - Overlay with afterimage trail showing past poses
  4) split_screen  - Left=Experimental, Right=Simulation (synced, same camera angle)

Features:
  - Auto-tracking camera that follows the model smoothly
  - Full-body framing with generous margin (no clipping)
  - Ground contact markers
  - Joint angle difference annotations
  - Color-coded difference highlighting on overlay
  - High-quality H.264 MP4 + GIF output

Usage:
    python visualize_form_comparison_v2.py --mode side_by_side
    python visualize_form_comparison_v2.py --mode overlay --fps 24
    python visualize_form_comparison_v2.py --mode ghost_trail
    python visualize_form_comparison_v2.py --mode split_screen
    python visualize_form_comparison_v2.py --mode all

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
# Forward Kinematics Engine (same as original)
# ═══════════════════════════════════════════════════════════════════════════

def _rot_axis_angle(axis, angle_rad):
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

BODY_GEOMETRY = {
    "pelvis":    {"files": ["sacrum.vtp", "pelvis.vtp", "l_pelvis.vtp"], "scale": (0.882394, 0.882394, 0.872334)},
    "femur_r":   {"files": ["femur_r.vtp"], "scale": (0.857849, 1.06805, 0.857849)},
    "femur_l":   {"files": ["femur_l.vtp"], "scale": (0.857849, 1.06805, 0.857849)},
    "tibia_r":   {"files": ["tibia_r.vtp", "fibula_r.vtp"], "scale": (0.823052, 1.11888, 0.823052)},
    "tibia_l":   {"files": ["tibia_l.vtp", "fibula_l.vtp"], "scale": (0.823052, 1.11888, 0.823052)},
    "talus_r":   {"files": ["talus_rv.vtp"], "scale": (0.834506, 0.877421, 0.877421)},
    "talus_l":   {"files": ["talus_lv.vtp"], "scale": (0.834506, 0.877421, 0.877421)},
    "calcn_r":   {"files": ["foot.vtp"], "scale": (0.834506, 0.877421, 0.877421)},
    "calcn_l":   {"files": ["l_foot.vtp"], "scale": (0.834506, 0.877421, 0.877421)},
    "toes_r":    {"files": ["bofoot.vtp"], "scale": (0.834506, 0.877421, 0.877421)},
    "toes_l":    {"files": ["l_bofoot.vtp"], "scale": (0.834506, 0.877421, 0.877421)},
    "torso":     {"files": ["hat_spine.vtp", "hat_jaw.vtp", "hat_skull.vtp", "hat_ribs_scap.vtp"], "scale": (1.16398, 0.967402, 1.07963)},
    "humerus_r": {"files": ["humerus_rv.vtp"], "scale": (0.849592, 1.19502, 0.849592)},
    "humerus_l": {"files": ["humerus_lv.vtp"], "scale": (0.849592, 1.19502, 0.849592)},
    "ulna_r":    {"files": ["ulna_rv.vtp"], "scale": (0.756302, 1.06837, 0.756302)},
    "ulna_l":    {"files": ["ulna_lv.vtp"], "scale": (0.756302, 1.06837, 0.756302)},
    "radius_r":  {"files": ["radius_rv.vtp"], "scale": (0.756302, 1.06837, 0.756302)},
    "radius_l":  {"files": ["radius_lv.vtp"], "scale": (0.756302, 1.06837, 0.756302)},
    "hand_r": {
        "files": ["pisiform_rvs.vtp", "lunate_rvs.vtp", "scaphoid_rvs.vtp",
                  "triquetrum_rvs.vtp", "hamate_rvs.vtp", "capitate_rvs.vtp",
                  "trapezoid_rvs.vtp", "trapezium_rvs.vtp",
                  "metacarpal1_rvs.vtp", "metacarpal2_rvs.vtp",
                  "metacarpal3_rvs.vtp", "metacarpal4_rvs.vtp", "metacarpal5_rvs.vtp",
                  "thumb_proximal_rvs.vtp", "thumb_distal_rvs.vtp",
                  "index_proximal_rvs.vtp", "index_medial_rvs.vtp", "index_distal_rvs.vtp",
                  "middle_proximal_rvs.vtp", "middle_medial_rvs.vtp", "middle_distal_rvs.vtp",
                  "ring_proximal_rvs.vtp", "ring_medial_rvs.vtp", "ring_distal_rvs.vtp",
                  "little_proximal_rvs.vtp", "little_medial_rvs.vtp", "little_distal_rvs.vtp"],
        "scale": (0.871418, 0.871418, 0.871418),
    },
    "hand_l": {
        "files": ["pisiform_lvs.vtp", "lunate_lvs.vtp", "scaphoid_lvs.vtp",
                  "triquetrum_lvs.vtp", "hamate_lvs.vtp", "capitate_lvs.vtp",
                  "trapezoid_lvs.vtp", "trapezium_lvs.vtp",
                  "metacarpal1_lvs.vtp", "metacarpal2_lvs.vtp",
                  "metacarpal3_lvs.vtp", "metacarpal4_lvs.vtp", "metacarpal5_lvs.vtp",
                  "thumb_proximal_lvs.vtp", "thumb_distal_lvs.vtp",
                  "index_proximal_lvs.vtp", "index_medial_lvs.vtp", "index_distal_lvs.vtp",
                  "middle_proximal_lvs.vtp", "middle_medial_lvs.vtp", "middle_distal_lvs.vtp",
                  "ring_proximal_lvs.vtp", "ring_medial_lvs.vtp", "ring_distal_lvs.vtp",
                  "little_proximal_lvs.vtp", "little_medial_lvs.vtp", "little_distal_lvs.vtp"],
        "scale": (0.871418, 0.871418, 0.871418),
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# FK / .mot / Geometry helpers
# ═══════════════════════════════════════════════════════════════════════════

def compute_body_transforms(q_dict):
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
    return parts[-2] if len(parts) >= 3 else col


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


def find_geometry_dir():
    import os
    opensim_home = os.environ.get("OPENSIM_HOME", "")
    if opensim_home:
        p = Path(opensim_home) / "Geometry"
        if p.exists():
            return p
    for ver in ["4.5", "4.4", "4.3", "4.2", "4.1"]:
        for prefix in [r"C:\OpenSim", r"C:\Program Files\OpenSim"]:
            p = Path(f"{prefix} {ver}") / "Geometry"
            if p.exists():
                return p
    raise FileNotFoundError("OpenSim Geometry folder not found")


def load_body_meshes(geometry_dir: Path):
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
                pts = mesh.points.copy()
                pts[:, 0] *= sx
                pts[:, 1] *= sy
                pts[:, 2] *= sz
                mesh.points = pts
                parts.append(mesh)
            except Exception:
                pass
        if parts:
            merged = parts[0]
            for p in parts[1:]:
                merged = merged.merge(p)
            meshes[body_name] = merged
    return meshes


def transform_mesh(mesh, T):
    m = mesh.copy()
    pts = m.points.copy()
    pts_h = np.hstack([pts, np.ones((len(pts), 1))])
    pts_t = (T @ pts_h.T).T[:, :3]
    m.points = pts_t
    return m


def build_posed_model(body_meshes, transforms, z_offset=0.0, x_offset=0.0):
    parts = []
    for body_name, mesh in body_meshes.items():
        if body_name not in transforms:
            continue
        T = transforms[body_name].copy()
        T[0, 3] += x_offset
        T[2, 3] += z_offset
        parts.append(transform_mesh(mesh, T))
    if not parts:
        return pv.PolyData()
    merged = parts[0]
    for p in parts[1:]:
        merged = merged.merge(p)
    return merged


# ═══════════════════════════════════════════════════════════════════════════
# Stick figure (lightweight joint skeleton lines for annotations)
# ═══════════════════════════════════════════════════════════════════════════

STICK_LINKS = [
    # Trunk
    ("pelvis", "torso"),
    # Right leg
    ("pelvis", "femur_r"), ("femur_r", "tibia_r"), ("tibia_r", "talus_r"),
    ("talus_r", "calcn_r"), ("calcn_r", "toes_r"),
    # Left leg
    ("pelvis", "femur_l"), ("femur_l", "tibia_l"), ("tibia_l", "talus_l"),
    ("talus_l", "calcn_l"), ("calcn_l", "toes_l"),
    # Right arm
    ("torso", "humerus_r"), ("humerus_r", "ulna_r"), ("ulna_r", "radius_r"),
    ("radius_r", "hand_r"),
    # Left arm
    ("torso", "humerus_l"), ("humerus_l", "ulna_l"), ("ulna_l", "radius_l"),
    ("radius_l", "hand_l"),
]


def build_stick_figure(transforms, z_offset=0.0, x_offset=0.0):
    """Build a stick figure (lines) from body transforms."""
    points = []
    lines_idx = []
    idx = 0
    for parent_name, child_name in STICK_LINKS:
        if parent_name not in transforms or child_name not in transforms:
            continue
        p1 = transforms[parent_name][:3, 3].copy()
        p2 = transforms[child_name][:3, 3].copy()
        p1[0] += x_offset; p1[2] += z_offset
        p2[0] += x_offset; p2[2] += z_offset
        points.append(p1)
        points.append(p2)
        lines_idx.extend([2, idx, idx + 1])
        idx += 2

    if not points:
        return None
    pts = np.array(points)
    lines = np.array(lines_idx)
    poly = pv.PolyData(pts, lines=lines)
    return poly


# ═══════════════════════════════════════════════════════════════════════════
# Camera helpers — auto-tracking with full-body framing
# ═══════════════════════════════════════════════════════════════════════════

def compute_tracking_camera(transforms, view="side", cam_dist=3.0, cam_height=0.7):
    """
    Compute camera position that tracks the model's pelvis and ensures
    the full body is visible. Returns (position, focal_point, up).
    """
    pelvis_pos = transforms.get("pelvis", np.eye(4))[:3, 3]
    cx, cy = pelvis_pos[0], pelvis_pos[1]
    # Focus slightly above ground, centered on pelvis
    focal = np.array([cx, cam_height, 0.0])

    if view == "side":
        # Sagittal view from +Z
        cam_pos = np.array([cx, cam_height, cam_dist])
    elif view == "front":
        cam_pos = np.array([cx + cam_dist, cam_height, 0.0])
    elif view == "three_quarter":
        cam_pos = np.array([cx + cam_dist * 0.7, cam_height + 0.5, cam_dist * 0.7])
    elif view == "rear_quarter":
        cam_pos = np.array([cx - cam_dist * 0.7, cam_height + 0.5, cam_dist * 0.7])
    else:
        cam_pos = np.array([cx, cam_height, cam_dist])

    return cam_pos, focal, (0, 1, 0)


def add_ground_plane(pl, center_x=0.0, extent_x=4.0, extent_z=2.5):
    """Add a subtle grid ground plane at y=0."""
    ground = pv.Plane(
        center=(center_x, 0.0, 0.0),
        direction=(0, 1, 0),
        i_size=extent_x * 2,
        j_size=extent_z * 2,
        i_resolution=20,
        j_resolution=10,
    )
    pl.add_mesh(ground, color="#9E9E9E", opacity=0.15, style="wireframe",
                line_width=0.5)


def add_phase_bar(pl, t, t_start, t_end, loop_num=0, n_loops=1):
    """Add a progress bar at the bottom of the frame."""
    frac = (t - t_start) / (t_end - t_start) if t_end > t_start else 0.0
    frac = max(0.0, min(1.0, frac))
    pct = frac * 100
    bar_text = f"{'=' * int(pct // 2.5):.<40s}  {pct:.0f}%"
    if n_loops > 1:
        bar_text = f"Loop {loop_num}/{n_loops}  " + bar_text
    pl.add_text(bar_text, position="lower_left", font_size=10, color="#555555")


# ═══════════════════════════════════════════════════════════════════════════
# Key DOFs for annotation
# ═══════════════════════════════════════════════════════════════════════════

KEY_DOFS = [
    "hip_flexion_r", "hip_flexion_l",
    "knee_angle_r", "knee_angle_l",
    "ankle_angle_r", "ankle_angle_l",
    "pelvis_tilt",
    "lumbar_extension",
    "arm_flex_r", "arm_flex_l",
    "elbow_flex_r", "elbow_flex_l",
]

DOF_LABELS = {
    "hip_flexion_r": "R.Hip", "hip_flexion_l": "L.Hip",
    "knee_angle_r": "R.Knee", "knee_angle_l": "L.Knee",
    "ankle_angle_r": "R.Ankle", "ankle_angle_l": "L.Ankle",
    "pelvis_tilt": "Pelvis Tilt",
    "lumbar_extension": "Trunk",
    "arm_flex_r": "R.Arm", "arm_flex_l": "L.Arm",
    "elbow_flex_r": "R.Elbow", "elbow_flex_l": "L.Elbow",
}


def compute_dof_diffs(exp_q, sim_q, dofs=KEY_DOFS):
    """Compute angular differences for key DOFs."""
    diffs = {}
    for dof in dofs:
        ev = exp_q.get(dof, 0.0)
        sv = sim_q.get(dof, 0.0)
        diffs[dof] = sv - ev
    return diffs


# ═══════════════════════════════════════════════════════════════════════════
# Rendering functions for each mode
# ═══════════════════════════════════════════════════════════════════════════

EXP_COLOR = "#2979FF"   # Blue
SIM_COLOR = "#FF5252"   # Red
GHOST_EXP = "#90CAF9"   # Light blue
GHOST_SIM = "#EF9A9A"   # Light red
BG_COLOR = "#F5F5F5"    # Near-white


def _make_plotter(window_size=(1920, 1080)):
    pv.global_theme.background = BG_COLOR
    pl = pv.Plotter(off_screen=True, window_size=list(window_size))
    return pl


def _add_lights(pl, cx=0.0):
    pl.add_light(pv.Light(position=(cx + 3, 4, 4), intensity=0.6))
    pl.add_light(pv.Light(position=(cx - 2, 3, -3), intensity=0.3))
    pl.add_light(pv.Light(position=(cx, 5, 0), intensity=0.2))  # top fill


def _add_legend(pl, mode="side_by_side"):
    if mode == "overlay":
        txt = "Blue: Experimental (IK)  |  Red: Simulation (Overlay)"
    elif mode == "ghost_trail":
        txt = "Blue: Experimental  |  Red: Simulation  (Ghost Trail)"
    else:
        txt = "Blue: Experimental (IK)  |  Red: Simulation"
    pl.add_text(txt, position="upper_right", font_size=10, color="#333333")


def _add_diff_annotation(pl, diffs, position="lower_right"):
    """Add key DOF difference annotation box to the plot."""
    lines = ["Joint Angle Diff (Sim - Exp):"]
    # Show only lower body + trunk (most intuitive for running)
    show_dofs = ["pelvis_tilt", "lumbar_extension",
                 "hip_flexion_r", "knee_angle_r", "ankle_angle_r",
                 "hip_flexion_l", "knee_angle_l", "ankle_angle_l"]
    for dof in show_dofs:
        if dof in diffs:
            label = DOF_LABELS.get(dof, dof)
            d = diffs[dof]
            arrow = "+" if d > 0 else ""
            lines.append(f"  {label:<12s}: {arrow}{d:.1f} deg")
    text = "\n".join(lines)
    pl.add_text(text, position=position, font_size=9, color="#333333")


def render_frame_side_by_side(body_meshes, exp_q, sim_q, t, t_start, t_end,
                               window_size=(1920, 1080), z_sep=0.8,
                               view="side", loop_num=1, n_loops=1, label=""):
    """Side-by-side: two models separated in Z, camera tracks pelvis."""
    exp_tf = compute_body_transforms(exp_q)
    sim_tf = compute_body_transforms(sim_q)

    exp_mesh = build_posed_model(body_meshes, exp_tf, z_offset=z_sep / 2)
    sim_mesh = build_posed_model(body_meshes, sim_tf, z_offset=-z_sep / 2)

    pl = _make_plotter(window_size)

    if exp_mesh.n_points > 0:
        pl.add_mesh(exp_mesh, color=EXP_COLOR, opacity=0.85, smooth_shading=True)
    if sim_mesh.n_points > 0:
        pl.add_mesh(sim_mesh, color=SIM_COLOR, opacity=0.80, smooth_shading=True)

    cx = exp_tf["pelvis"][0, 3]
    add_ground_plane(pl, center_x=cx)

    cam_pos, focal, up = compute_tracking_camera(exp_tf, view=view, cam_dist=3.2)
    pl.camera_position = [cam_pos, focal, up]

    pl.add_text(f"t = {t:.4f} s  {label}", position="upper_left",
                font_size=13, color="#222222")
    _add_legend(pl, "side_by_side")
    add_phase_bar(pl, t, t_start, t_end, loop_num, n_loops)
    _add_lights(pl, cx)

    img = pl.screenshot(return_img=True)
    pl.close()
    return img


def render_frame_overlay(body_meshes, exp_q, sim_q, t, t_start, t_end,
                          window_size=(1920, 1080),
                          view="side", loop_num=1, n_loops=1, label="",
                          show_diffs=True):
    """Overlay: aligned at pelvis, semi-transparent for posture diff."""
    exp_tf = compute_body_transforms(exp_q)
    sim_tf = compute_body_transforms(sim_q)

    # Align simulation pelvis X to experimental pelvis X
    dx = exp_tf["pelvis"][0, 3] - sim_tf["pelvis"][0, 3]
    for body in sim_tf:
        sim_tf[body][0, 3] += dx

    exp_mesh = build_posed_model(body_meshes, exp_tf)
    sim_mesh = build_posed_model(body_meshes, sim_tf)

    # Also build stick figures for clearer structure
    exp_stick = build_stick_figure(exp_tf)
    sim_stick = build_stick_figure(sim_tf)

    pl = _make_plotter(window_size)

    if exp_mesh.n_points > 0:
        pl.add_mesh(exp_mesh, color=EXP_COLOR, opacity=0.45, smooth_shading=True)
    if sim_mesh.n_points > 0:
        pl.add_mesh(sim_mesh, color=SIM_COLOR, opacity=0.40, smooth_shading=True)
    if exp_stick is not None:
        pl.add_mesh(exp_stick, color=EXP_COLOR, line_width=3, opacity=0.9)
    if sim_stick is not None:
        pl.add_mesh(sim_stick, color=SIM_COLOR, line_width=3, opacity=0.9)

    cx = exp_tf["pelvis"][0, 3]
    add_ground_plane(pl, center_x=cx)

    cam_pos, focal, up = compute_tracking_camera(exp_tf, view=view, cam_dist=2.8)
    pl.camera_position = [cam_pos, focal, up]

    pl.add_text(f"t = {t:.4f} s  {label}", position="upper_left",
                font_size=13, color="#222222")
    _add_legend(pl, "overlay")
    add_phase_bar(pl, t, t_start, t_end, loop_num, n_loops)

    if show_diffs:
        diffs = compute_dof_diffs(exp_q, sim_q)
        _add_diff_annotation(pl, diffs)

    _add_lights(pl, cx)
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


def render_frame_ghost_trail(body_meshes, exp_series, sim_series,
                              frame_idx, frame_times, exp_times_arr, sim_times_arr,
                              t_start, t_end,
                              window_size=(1920, 1080), view="side",
                              loop_num=1, n_loops=1, label="",
                              trail_count=3, trail_step=3):
    """
    Ghost trail: current frame solid + past frames as fading ghosts.
    Shows motion trajectory with afterimage trail.
    """
    t = frame_times[frame_idx]
    exp_idx = np.argmin(np.abs(exp_times_arr - t))
    sim_idx = np.argmin(np.abs(sim_times_arr - t))

    exp_tf = compute_body_transforms(exp_series[exp_idx][1])
    sim_tf = compute_body_transforms(sim_series[sim_idx][1])

    pl = _make_plotter(window_size)

    # Draw ghost frames (older = more transparent)
    for gi in range(trail_count, 0, -1):
        ghost_fi = frame_idx - gi * trail_step
        if ghost_fi < 0:
            continue
        gt = frame_times[ghost_fi]
        g_exp_idx = np.argmin(np.abs(exp_times_arr - gt))
        g_sim_idx = np.argmin(np.abs(sim_times_arr - gt))

        g_exp_tf = compute_body_transforms(exp_series[g_exp_idx][1])
        g_sim_tf = compute_body_transforms(sim_series[g_sim_idx][1])

        alpha = 0.08 + 0.07 * (trail_count - gi)  # fade: 0.08 ~ 0.22

        g_exp_mesh = build_posed_model(body_meshes, g_exp_tf)
        g_sim_mesh = build_posed_model(body_meshes, g_sim_tf)

        if g_exp_mesh.n_points > 0:
            pl.add_mesh(g_exp_mesh, color=GHOST_EXP, opacity=alpha,
                        smooth_shading=True)
        if g_sim_mesh.n_points > 0:
            pl.add_mesh(g_sim_mesh, color=GHOST_SIM, opacity=alpha,
                        smooth_shading=True)

    # Current frame (solid)
    exp_mesh = build_posed_model(body_meshes, exp_tf)
    sim_mesh = build_posed_model(body_meshes, sim_tf)

    # Align sim to exp in X for overlay
    dx = exp_tf["pelvis"][0, 3] - sim_tf["pelvis"][0, 3]
    # For ghost trail, keep both at original X position so you can see trajectory

    if exp_mesh.n_points > 0:
        pl.add_mesh(exp_mesh, color=EXP_COLOR, opacity=0.5, smooth_shading=True)
    if sim_mesh.n_points > 0:
        pl.add_mesh(sim_mesh, color=SIM_COLOR, opacity=0.45, smooth_shading=True)

    # Stick figures on current frame
    exp_stick = build_stick_figure(exp_tf)
    sim_stick = build_stick_figure(sim_tf)
    if exp_stick is not None:
        pl.add_mesh(exp_stick, color=EXP_COLOR, line_width=3, opacity=0.9)
    if sim_stick is not None:
        pl.add_mesh(sim_stick, color=SIM_COLOR, line_width=3, opacity=0.9)

    # Camera tracks midpoint between both models
    mid_x = (exp_tf["pelvis"][0, 3] + sim_tf["pelvis"][0, 3]) / 2
    mid_tf = {"pelvis": np.eye(4)}
    mid_tf["pelvis"][0, 3] = mid_x
    cam_pos, focal, up = compute_tracking_camera(mid_tf, view=view, cam_dist=3.5)
    pl.camera_position = [cam_pos, focal, up]

    add_ground_plane(pl, center_x=mid_x, extent_x=5.0)

    pl.add_text(f"t = {t:.4f} s  {label}", position="upper_left",
                font_size=13, color="#222222")
    _add_legend(pl, "ghost_trail")
    add_phase_bar(pl, t, t_start, t_end, loop_num, n_loops)
    _add_lights(pl, mid_x)

    img = pl.screenshot(return_img=True)
    pl.close()
    return img


def render_frame_split_screen(body_meshes, exp_q, sim_q, t, t_start, t_end,
                               window_size=(1920, 1080), view="side",
                               loop_num=1, n_loops=1, label=""):
    """
    Split screen: left subplot = experimental, right subplot = simulation.
    Same camera angle, synced time.
    """
    exp_tf = compute_body_transforms(exp_q)
    sim_tf = compute_body_transforms(sim_q)

    # Align sim to exp pelvis X so camera works the same
    dx = exp_tf["pelvis"][0, 3] - sim_tf["pelvis"][0, 3]
    for body in sim_tf:
        sim_tf[body][0, 3] += dx

    pv.global_theme.background = BG_COLOR
    pl = pv.Plotter(off_screen=True, shape=(1, 2),
                    window_size=list(window_size), border=True)

    cx = exp_tf["pelvis"][0, 3]
    cam_pos, focal, up = compute_tracking_camera(exp_tf, view=view, cam_dist=2.6)

    # Left: Experimental
    pl.subplot(0, 0)
    exp_mesh = build_posed_model(body_meshes, exp_tf)
    if exp_mesh.n_points > 0:
        pl.add_mesh(exp_mesh, color=EXP_COLOR, opacity=0.85, smooth_shading=True)
    add_ground_plane(pl, center_x=cx)
    pl.camera_position = [cam_pos, focal, up]
    pl.add_text("Experimental (IK)", position="upper_left",
                font_size=12, color=EXP_COLOR)
    pl.add_text(f"t = {t:.4f} s", position="lower_left",
                font_size=10, color="#555555")
    _add_lights(pl, cx)

    # Right: Simulation
    pl.subplot(0, 1)
    sim_mesh = build_posed_model(body_meshes, sim_tf)
    if sim_mesh.n_points > 0:
        pl.add_mesh(sim_mesh, color=SIM_COLOR, opacity=0.85, smooth_shading=True)
    add_ground_plane(pl, center_x=cx)
    pl.camera_position = [cam_pos, focal, up]
    pl.add_text("Simulation", position="upper_left",
                font_size=12, color=SIM_COLOR)

    # Add diff annotation on right side
    diffs = compute_dof_diffs(exp_q, sim_q)
    _add_diff_annotation(pl, diffs, position="lower_right")
    _add_lights(pl, cx)

    img = pl.screenshot(return_img=True)
    pl.close()
    return img


# ═══════════════════════════════════════════════════════════════════════════
# Video generation
# ═══════════════════════════════════════════════════════════════════════════

def generate_video(body_meshes, exp_series, sim_series, output_dir,
                   mode="side_by_side", view="side", fps=24, n_loops=2,
                   window_size=(1920, 1080), label="", make_gif=True):
    """Generate MP4 and optionally GIF for the given mode."""
    import imageio

    exp_times_arr = np.array([s[0] for s in exp_series])
    sim_times_arr = np.array([s[0] for s in sim_series])
    t_start = max(exp_times_arr[0], sim_times_arr[0])
    t_end = min(exp_times_arr[-1], sim_times_arr[-1])
    duration = t_end - t_start

    frames_per_loop = max(int(duration * fps), 20)
    total_frames = frames_per_loop * n_loops
    single_times = np.linspace(t_start, t_end, frames_per_loop)
    all_times = np.tile(single_times, n_loops)

    safe_label = label.strip("[] ").replace(" ", "_") if label else "comparison"
    mp4_path = output_dir / f"form_{mode}_{safe_label}.mp4"
    gif_path = output_dir / f"form_{mode}_{safe_label}.gif"

    print(f"\n  [{mode.upper()}] Generating {total_frames} frames "
          f"({fps} fps, {n_loops} loops)...")

    writer = imageio.get_writer(str(mp4_path), fps=fps, codec="libx264",
                                quality=8,
                                output_params=["-pix_fmt", "yuv420p"])

    gif_frames = []
    gif_step = max(1, frames_per_loop // 40)  # ~40 frames for GIF

    for fi, t in enumerate(all_times):
        exp_idx = np.argmin(np.abs(exp_times_arr - t))
        sim_idx = np.argmin(np.abs(sim_times_arr - t))
        loop_num = fi // frames_per_loop + 1

        if mode == "side_by_side":
            img = render_frame_side_by_side(
                body_meshes, exp_series[exp_idx][1], sim_series[sim_idx][1],
                t, t_start, t_end, window_size=window_size,
                view=view, loop_num=loop_num, n_loops=n_loops, label=label)

        elif mode == "overlay":
            img = render_frame_overlay(
                body_meshes, exp_series[exp_idx][1], sim_series[sim_idx][1],
                t, t_start, t_end, window_size=window_size,
                view=view, loop_num=loop_num, n_loops=n_loops, label=label)

        elif mode == "ghost_trail":
            # Use indices within current loop
            fi_in_loop = fi % frames_per_loop
            img = render_frame_ghost_trail(
                body_meshes, exp_series, sim_series,
                fi_in_loop, single_times, exp_times_arr, sim_times_arr,
                t_start, t_end, window_size=window_size,
                view=view, loop_num=loop_num, n_loops=n_loops, label=label)

        elif mode == "split_screen":
            img = render_frame_split_screen(
                body_meshes, exp_series[exp_idx][1], sim_series[sim_idx][1],
                t, t_start, t_end, window_size=window_size,
                view=view, loop_num=loop_num, n_loops=n_loops, label=label)

        writer.append_data(img)

        # Collect GIF frames (first loop only, downsampled)
        if make_gif and loop_num == 1 and fi % gif_step == 0:
            # Downscale for GIF
            from PIL import Image
            pil_img = Image.fromarray(img)
            pil_img = pil_img.resize((960, 540), Image.LANCZOS)
            gif_frames.append(np.array(pil_img))

        if (fi + 1) % 10 == 0 or fi == total_frames - 1:
            pct = (fi + 1) / total_frames * 100
            print(f"    Frame {fi + 1}/{total_frames} ({pct:.0f}%)")

    writer.close()
    file_size_mb = mp4_path.stat().st_size / (1024 * 1024)
    print(f"  [OK] MP4: {mp4_path}  ({file_size_mb:.1f} MB)")

    if make_gif and gif_frames:
        imageio.mimsave(str(gif_path), gif_frames, duration=120, loop=0)
        gif_size_mb = gif_path.stat().st_size / (1024 * 1024)
        print(f"  [OK] GIF: {gif_path}  ({gif_size_mb:.1f} MB)")

    return mp4_path


# ═══════════════════════════════════════════════════════════════════════════
# Composite panel snapshot
# ═══════════════════════════════════════════════════════════════════════════

def render_composite_snapshot(body_meshes, exp_q, sim_q, t, output_path, label=""):
    """
    4-panel composite: side sbs, front sbs, side overlay, 3/4 overlay
    """
    exp_tf = compute_body_transforms(exp_q)
    sim_tf = compute_body_transforms(sim_q)

    pv.global_theme.background = BG_COLOR
    pl = pv.Plotter(off_screen=True, shape=(2, 2), window_size=[2400, 1600])

    configs = [
        ("Side View (Side-by-side)", "side", "sbs"),
        ("Front View (Side-by-side)", "front", "sbs"),
        ("Side View (Overlay)", "side", "overlay"),
        ("3/4 View (Overlay)", "three_quarter", "overlay"),
    ]

    cx = exp_tf["pelvis"][0, 3]

    for idx, (title, view, style) in enumerate(configs):
        row, col = divmod(idx, 2)
        pl.subplot(row, col)

        if style == "sbs":
            z_sep = 0.8
            exp_mesh = build_posed_model(body_meshes, exp_tf, z_offset=z_sep/2)
            sim_mesh = build_posed_model(body_meshes, sim_tf, z_offset=-z_sep/2)
            exp_op, sim_op = 0.85, 0.80
        else:
            sim_tf_al = {}
            dx = exp_tf["pelvis"][0, 3] - sim_tf["pelvis"][0, 3]
            for body in sim_tf:
                sim_tf_al[body] = sim_tf[body].copy()
                sim_tf_al[body][0, 3] += dx
            exp_mesh = build_posed_model(body_meshes, exp_tf)
            sim_mesh = build_posed_model(body_meshes, sim_tf_al)
            exp_op, sim_op = 0.45, 0.40

        if exp_mesh.n_points > 0:
            pl.add_mesh(exp_mesh, color=EXP_COLOR, opacity=exp_op, smooth_shading=True)
        if sim_mesh.n_points > 0:
            pl.add_mesh(sim_mesh, color=SIM_COLOR, opacity=sim_op, smooth_shading=True)

        add_ground_plane(pl, center_x=cx)
        cam_pos, focal, up = compute_tracking_camera(exp_tf, view=view,
                                                       cam_dist=2.8 if style == "overlay" else 3.2)
        pl.camera_position = [cam_pos, focal, up]
        pl.add_text(title, position="upper_left", font_size=11, color="#333333")
        _add_lights(pl, cx)

    pl.screenshot(str(output_path))
    pl.close()
    print(f"  [OK] Composite: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def align_to_same_start(exp_series, sim_series):
    """
    Adjust simulation DOFs so that at t=0 the posture matches
    the experimental initial posture exactly.

    For each DOF:  sim_adjusted[t] = sim[t] + (exp[0] - sim[0])

    At t=0 this gives sim_adjusted = exp[0] (identical pose).
    As t increases, the simulation's own trajectory dynamics
    create growing divergence from experimental—making differences
    emerge naturally and intuitively.

    Translation DOFs (pelvis_tx/ty/tz) are handled the same way
    so both models start from the same world position.
    """
    exp_q0 = exp_series[0][1]   # experimental initial pose
    sim_q0 = sim_series[0][1]   # simulation initial pose

    # Compute per-DOF offset
    offsets = {}
    for dof in sim_q0:
        offsets[dof] = exp_q0.get(dof, 0.0) - sim_q0.get(dof, 0.0)

    # Apply offset to every frame
    adjusted = []
    for t, q in sim_series:
        q_adj = {}
        for dof, val in q.items():
            q_adj[dof] = val + offsets.get(dof, 0.0)
        adjusted.append((t, q_adj))

    return adjusted


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


def main():
    parser = argparse.ArgumentParser(
        description="Improved Running Form Comparison Visualization")
    parser.add_argument("--sim_label", type=str, default="Nominal")
    parser.add_argument("--mode", type=str, default="all",
                        choices=["side_by_side", "overlay", "ghost_trail",
                                 "split_screen", "all"],
                        help="Visualization mode")
    parser.add_argument("--view", type=str, default="side",
                        choices=["side", "front", "three_quarter", "rear_quarter"])
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--loops", type=int, default=2)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--no_gif", action="store_true")
    parser.add_argument("--snapshot_only", action="store_true",
                        help="Generate composite snapshots only (no video)")
    parser.add_argument("--same_start", action="store_true",
                        help="Align simulation initial pose to experimental "
                             "(same start posture, differences grow over time)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    window_size = (args.width, args.height)

    print("=" * 65)
    print("  Running Form Comparison v2 - Improved Visualization")
    print("=" * 65)

    # Load geometry
    geom_dir = find_geometry_dir()
    print(f"\n[Geometry] {geom_dir}")
    print("  Loading bone meshes...")
    body_meshes = load_body_meshes(geom_dir)
    print(f"  {len(body_meshes)} bodies, "
          f"{sum(m.n_cells for m in body_meshes.values()):,} polygons")

    # Load data
    exp_path = find_experimental_ik(project_root)
    print(f"\n[Experimental] {exp_path.name}")
    df_exp = read_mot(exp_path)
    exp_series = mot_to_q_series(df_exp)
    print(f"  {len(exp_series)} frames, "
          f"t = {exp_series[0][0]:.4f} - {exp_series[-1][0]:.4f} s")

    sim_files = find_simulation_coords(project_root, args.sim_label)
    if not sim_files:
        print("ERROR: No simulation file found")
        return 1
    sim_path = sim_files[0]
    match = re.search(r"___(.+)\.mot$", sim_path.name)
    label = match.group(1) if match else "Sim"
    print(f"[Simulation] {sim_path.name}")
    df_sim = read_mot(sim_path)
    sim_series = mot_to_q_series(df_sim)
    print(f"  {len(sim_series)} frames, "
          f"t = {sim_series[0][0]:.4f} - {sim_series[-1][0]:.4f} s")

    # --- Same-start alignment ---
    if args.same_start:
        sim_series = align_to_same_start(exp_series, sim_series)
        label = label + "_sameStart"
        print("  [same_start] Simulation initial pose aligned to experimental.")
        print("  Differences will grow from zero over time.")

    out_dir = project_root / "Results" / "form_comparison_v2"
    out_dir.mkdir(parents=True, exist_ok=True)

    exp_times = np.array([s[0] for s in exp_series])
    sim_times = np.array([s[0] for s in sim_series])
    t_start = max(exp_times[0], sim_times[0])
    t_end = min(exp_times[-1], sim_times[-1])

    # --- Composite snapshots at key times ---
    print("\n--- Composite Snapshots ---")
    snapshot_times = np.linspace(t_start + 0.005, t_end - 0.005, 5)
    for t_snap in snapshot_times:
        exp_idx = np.argmin(np.abs(exp_times - t_snap))
        sim_idx = np.argmin(np.abs(sim_times - t_snap))
        render_composite_snapshot(
            body_meshes, exp_series[exp_idx][1], sim_series[sim_idx][1],
            t_snap, out_dir / f"composite_t{t_snap:.3f}_{label}.png",
            label=label)

    if args.snapshot_only:
        print(f"\n  Done (snapshots only). Output: {out_dir}")
        return 0

    # --- Videos ---
    if args.mode == "all":
        modes = ["side_by_side", "overlay", "ghost_trail", "split_screen"]
    else:
        modes = [args.mode]

    for mode in modes:
        generate_video(
            body_meshes, exp_series, sim_series, out_dir,
            mode=mode, view=args.view, fps=args.fps, n_loops=args.loops,
            window_size=window_size, label=label, make_gif=not args.no_gif)

    print(f"\n{'=' * 65}")
    print(f"  Done! Output: {out_dir}")
    print(f"{'=' * 65}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
