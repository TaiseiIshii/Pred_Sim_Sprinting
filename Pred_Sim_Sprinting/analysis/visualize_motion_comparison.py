"""
visualize_motion_comparison.py
OpenSimモデルのフォワードキネマティクスによるスティックフィギュアアニメーション

ベースライン（実験IK）と最適化後（シミュレーション）の走動作を
同一画面上で直接比較するアニメーションを生成します。

Usage:
    python visualize_motion_comparison.py
    python visualize_motion_comparison.py --sim_label Nominal
    python visualize_motion_comparison.py --snapshot_times 0.08 0.12 0.16 0.20
    python visualize_motion_comparison.py --fps 30 --output sprint_compare.mp4

Date: 2026-03-24
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d
import matplotlib.animation as animation

# ═══════════════════════════════════════════════════════════════════════════
# Forward-Kinematics Engine  (from the extracted .osim kinematic chain)
# ═══════════════════════════════════════════════════════════════════════════

def _rot_axis_angle(axis, angle_rad):
    """Rodrigues rotation matrix for rotation about *axis* by *angle_rad*."""
    axis = np.asarray(axis, dtype=float)
    axis = axis / (np.linalg.norm(axis) + 1e-30)
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    K = np.array([[0, -axis[2], axis[1]],
                  [axis[2], 0, -axis[0]],
                  [-axis[1], axis[0], 0]])
    return np.eye(3) + s * K + (1 - c) * K @ K


def _homogeneous(R, t):
    """Build 4×4 homogeneous matrix from 3×3 rotation and 3-vector."""
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T


# ---------------------------------------------------------------------------
# Kinematic chain definition  (from OpenSim model)
# ---------------------------------------------------------------------------
# Each entry: (body_name, parent_name, location_in_parent,
#              [(coord_name, axis, 'rot'|'trans'), ...])

KINEMATIC_CHAIN = [
    # --- pelvis (root) ---
    ("pelvis", "ground", [0, 0, 0], [
        ("pelvis_tilt",     [0, 0, 1], "rot"),
        ("pelvis_list",     [1, 0, 0], "rot"),
        ("pelvis_rotation", [0, 1, 0], "rot"),
        ("pelvis_tx",       [1, 0, 0], "trans"),
        ("pelvis_ty",       [0, 1, 0], "trans"),
        ("pelvis_tz",       [0, 0, 1], "trans"),
    ]),
    # --- right leg ---
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
    # --- left leg ---
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
    # --- torso ---
    ("torso", "pelvis", [-0.088857, 0.071915, 0], [
        ("lumbar_extension", [0, 0, 1], "rot"),
        ("lumbar_bending",   [1, 0, 0], "rot"),
        ("lumbar_rotation",  [0, 1, 0], "rot"),
    ]),
    # --- right arm ---
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
    # --- left arm ---
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

# Connections to draw as stick segments (body_a, body_b)
STICK_SEGMENTS = [
    # trunk
    ("pelvis", "torso"),
    # right leg
    ("pelvis", "femur_r"), ("femur_r", "tibia_r"), ("tibia_r", "talus_r"),
    ("talus_r", "calcn_r"), ("calcn_r", "toes_r"),
    # left leg
    ("pelvis", "femur_l"), ("femur_l", "tibia_l"), ("tibia_l", "talus_l"),
    ("talus_l", "calcn_l"), ("calcn_l", "toes_l"),
    # right arm
    ("torso", "humerus_r"), ("humerus_r", "ulna_r"),
    ("ulna_r", "radius_r"), ("radius_r", "hand_r"),
    # left arm
    ("torso", "humerus_l"), ("humerus_l", "ulna_l"),
    ("ulna_l", "radius_l"), ("radius_l", "hand_l"),
]

# A virtual "head" point offset from torso origin (for visualisation)
HEAD_OFFSET_FROM_TORSO = np.array([0.0, 0.22, 0.0])  # approximate


def compute_body_positions(q_dict):
    """
    Given a dict {coord_name: value_in_deg_or_m}, compute world positions
    for every body origin.  Angles in DEGREES, translations in METERS.
    Returns dict {body_name: 3-vector}.
    """
    transforms = {"ground": np.eye(4)}
    positions  = {"ground": np.zeros(3)}

    for body, parent, loc_in_parent, coords in KINEMATIC_CHAIN:
        T_parent = transforms[parent]

        # 1) translate to joint in parent frame
        R_joint = np.eye(3)
        t_joint = np.zeros(3)

        for coord_name, axis, mode in coords:
            val = q_dict.get(coord_name, 0.0)
            if mode == "rot":
                val_rad = np.deg2rad(val)
                R_joint = _rot_axis_angle(axis, val_rad) @ R_joint
            else:  # trans
                t_joint += np.array(axis, dtype=float) * val

        T_joint = _homogeneous(R_joint, t_joint)
        T_loc = _homogeneous(np.eye(3), np.array(loc_in_parent, dtype=float))

        T_body = T_parent @ T_loc @ T_joint
        transforms[body] = T_body
        positions[body] = T_body[:3, 3].copy()

    # virtual head
    T_torso = transforms["torso"]
    head_world = (T_torso @ np.append(HEAD_OFFSET_FROM_TORSO, 1.0))[:3]
    positions["head"] = head_world

    return positions, transforms


# ═══════════════════════════════════════════════════════════════════════════
# .mot reader  (reused from comparison script)
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
    """Convert a .mot DataFrame into a list of (time, q_dict) pairs."""
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
# Drawing helpers
# ═══════════════════════════════════════════════════════════════════════════

def draw_stick_figure_2d(ax, positions, color, alpha=1.0, lw=2.5, label=None,
                         view="sagittal", marker_size=5, z_offset=0.0):
    """
    Draw a 2D stick figure on *ax*.
    view: 'sagittal' (X-Y), 'frontal' (Z-Y), 'top' (X-Z)
    """
    def _proj(p):
        if view == "sagittal":
            return (p[0] + z_offset, p[1])
        elif view == "frontal":
            return (p[2] + z_offset, p[1])
        else:  # top
            return (p[0] + z_offset, p[2])

    drawn_label = False
    for seg_a, seg_b in STICK_SEGMENTS:
        if seg_a not in positions or seg_b not in positions:
            continue
        pa, pb = _proj(positions[seg_a]), _proj(positions[seg_b])
        lbl = label if not drawn_label else None
        ax.plot([pa[0], pb[0]], [pa[1], pb[1]],
                color=color, linewidth=lw, alpha=alpha, solid_capstyle="round",
                label=lbl)
        drawn_label = True

    # draw head
    if "head" in positions and "torso" in positions:
        ph = _proj(positions["head"])
        pt = _proj(positions["torso"])
        ax.plot([pt[0], ph[0]], [pt[1], ph[1]],
                color=color, linewidth=lw, alpha=alpha, solid_capstyle="round")
        ax.plot(ph[0], ph[1], "o", color=color, markersize=marker_size + 2, alpha=alpha)

    # joints
    for name, pos in positions.items():
        if name in ("ground", "head"):
            continue
        pp = _proj(pos)
        ax.plot(pp[0], pp[1], "o", color=color, markersize=marker_size, alpha=alpha)


def draw_stick_figure_3d(ax, positions, color, alpha=1.0, lw=2.5, label=None,
                         marker_size=4):
    """Draw a 3D stick figure on a 3D axes."""
    drawn_label = False
    for seg_a, seg_b in STICK_SEGMENTS:
        if seg_a not in positions or seg_b not in positions:
            continue
        pa = positions[seg_a]
        pb = positions[seg_b]
        lbl = label if not drawn_label else None
        ax.plot([pa[0], pb[0]], [pa[2], pb[2]], [pa[1], pb[1]],
                color=color, linewidth=lw, alpha=alpha, label=lbl)
        drawn_label = True

    if "head" in positions and "torso" in positions:
        ph = positions["head"]
        pt = positions["torso"]
        ax.plot([pt[0], ph[0]], [pt[2], ph[2]], [pt[1], ph[1]],
                color=color, linewidth=lw, alpha=alpha)
        ax.plot([ph[0]], [ph[2]], [ph[1]], "o",
                color=color, markersize=marker_size + 2, alpha=alpha)

    for name, pos in positions.items():
        if name in ("ground", "head"):
            continue
        ax.plot([pos[0]], [pos[2]], [pos[1]], "o",
                color=color, markersize=marker_size, alpha=alpha)


# ═══════════════════════════════════════════════════════════════════════════
# Snapshot comparison (multi-frame static figure)
# ═══════════════════════════════════════════════════════════════════════════

def create_snapshot_comparison(exp_series, sim_series, snapshot_times,
                               output_path, title="", view="sagittal"):
    """
    Create a static figure with side-by-side snapshots at specified times.
    Both motions are overlaid in each panel.
    """
    n = len(snapshot_times)
    fig, axes = plt.subplots(1, n, figsize=(4.5 * n, 8), squeeze=False)
    axes = axes[0]

    exp_times = np.array([s[0] for s in exp_series])
    sim_times = np.array([s[0] for s in sim_series])

    for col_idx, t_snap in enumerate(snapshot_times):
        ax = axes[col_idx]

        # find nearest frames
        exp_idx = np.argmin(np.abs(exp_times - t_snap))
        sim_idx = np.argmin(np.abs(sim_times - t_snap))

        exp_pos, _ = compute_body_positions(exp_series[exp_idx][1])
        sim_pos, _ = compute_body_positions(sim_series[sim_idx][1])

        # Use the pelvis_tx from experimental as reference to align horizontally
        # so we compare posture, not absolute position
        dx = exp_pos["pelvis"][0] - sim_pos["pelvis"][0]

        # draw experimental in blue, simulation in red
        draw_stick_figure_2d(ax, exp_pos, color="#2196F3", alpha=0.9, lw=3,
                             label="実験 (IK)", view=view, marker_size=4)
        # shift sim to align pelvis x
        sim_pos_aligned = {k: v + np.array([dx, 0, 0]) for k, v in sim_pos.items()}
        draw_stick_figure_2d(ax, sim_pos_aligned, color="#F44336", alpha=0.7, lw=3,
                             label="シミュレーション", view=view, marker_size=4)

        ax.set_title(f"t = {t_snap:.3f} s", fontsize=12, fontweight="bold")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.2)

        if view == "sagittal":
            ax.set_xlabel("X (前方) [m]")
            ax.set_ylabel("Y (鉛直) [m]")
        elif view == "frontal":
            ax.set_xlabel("Z (側方) [m]")
            ax.set_ylabel("Y (鉛直) [m]")

        # draw ground line
        ax.axhline(y=0, color="brown", linewidth=1, linestyle="--", alpha=0.5)

        if col_idx == 0:
            ax.legend(loc="upper left", fontsize=9)

    fig.suptitle(f"走動作フォーム比較 ({view}) {title}",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] スナップショット保存: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════
# Overlay ghosting plot (overlapping silhouettes at regular intervals)
# ═══════════════════════════════════════════════════════════════════════════

def create_ghost_overlay(exp_series, sim_series, n_ghosts=8,
                          output_path=None, title="", view="sagittal"):
    """
    Draw ghosted stick figures at evenly-spaced time points.
    Each figure is drawn with decreasing opacity, showing motion progression.
    """
    exp_times = np.array([s[0] for s in exp_series])
    sim_times = np.array([s[0] for s in sim_series])
    t_start = max(exp_times[0], sim_times[0])
    t_end = min(exp_times[-1], sim_times[-1])
    ghost_times = np.linspace(t_start, t_end, n_ghosts)

    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    for panel_idx, (series, label, color) in enumerate([
        (exp_series, "実験 (IK)", "#2196F3"),
        (sim_series, "シミュレーション", "#F44336"),
    ]):
        ax = axes[panel_idx]
        times_arr = exp_times if panel_idx == 0 else sim_times

        for gi, t_g in enumerate(ghost_times):
            idx = np.argmin(np.abs(times_arr - t_g))
            pos, _ = compute_body_positions(series[idx][1])
            alpha = 0.2 + 0.8 * (gi / (n_ghosts - 1))
            draw_stick_figure_2d(ax, pos, color=color, alpha=alpha, lw=2.5,
                                 view=view, marker_size=3)

        ax.set_title(label, fontsize=13, fontweight="bold")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.2)
        ax.axhline(y=0, color="brown", linewidth=1, linestyle="--", alpha=0.5)
        if view == "sagittal":
            ax.set_xlabel("X (前方) [m]")
            ax.set_ylabel("Y (鉛直) [m]")

    fig.suptitle(f"走動作ゴースト表示 ({view}) {title}",
                 fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"  [OK] ゴースト表示保存: {output_path}")
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# Animation (MP4 / GIF)
# ═══════════════════════════════════════════════════════════════════════════

def create_animation(exp_series, sim_series, output_path, fps=25, title="",
                      view="sagittal"):
    """
    Create a side-by-side (or overlay) animation comparing both motions.
    """
    exp_times = np.array([s[0] for s in exp_series])
    sim_times = np.array([s[0] for s in sim_series])
    t_start = max(exp_times[0], sim_times[0])
    t_end = min(exp_times[-1], sim_times[-1])

    duration = t_end - t_start
    # Use at least as many frames as the data has, or fps-based, whichever larger
    n_frames_from_fps = max(int(duration * fps), 2)
    n_frames = max(n_frames_from_fps, min(len(exp_series), len(sim_series)), 60)
    if n_frames < 2:
        print("  [WARN] 動画フレーム数が少なすぎます")
        return
    # actual playback fps = slow-motion since real duration is very short
    playback_fps = fps

    frame_times = np.linspace(t_start, t_end, n_frames)

    fig, axes = plt.subplots(1, 3, figsize=(20, 7),
                              gridspec_kw={"width_ratios": [1, 1, 1]})

    def _update(frame_idx):
        t = frame_times[frame_idx]
        for ax in axes:
            ax.cla()
            ax.grid(True, alpha=0.2)
            ax.axhline(y=0, color="brown", linewidth=1, linestyle="--", alpha=0.5)

        exp_idx = np.argmin(np.abs(exp_times - t))
        sim_idx = np.argmin(np.abs(sim_times - t))

        exp_pos, _ = compute_body_positions(exp_series[exp_idx][1])
        sim_pos, _ = compute_body_positions(sim_series[sim_idx][1])

        # align pelvis horizontally for overlay
        dx = exp_pos["pelvis"][0] - sim_pos["pelvis"][0]
        sim_pos_aligned = {k: v + np.array([dx, 0, 0]) for k, v in sim_pos.items()}

        # panel 1: experimental only
        draw_stick_figure_2d(axes[0], exp_pos, "#2196F3", lw=3,
                             label="実験 (IK)", view=view, marker_size=4)
        axes[0].set_title("実験 (IK)", fontsize=12, fontweight="bold")

        # panel 2: simulation only
        draw_stick_figure_2d(axes[1], sim_pos, "#F44336", lw=3,
                             label="シミュレーション", view=view, marker_size=4)
        axes[1].set_title("シミュレーション", fontsize=12, fontweight="bold")

        # panel 3: overlay
        draw_stick_figure_2d(axes[2], exp_pos, "#2196F3", alpha=0.8, lw=3,
                             label="実験", view=view, marker_size=4)
        draw_stick_figure_2d(axes[2], sim_pos_aligned, "#F44336", alpha=0.7, lw=3,
                             label="シミュレーション", view=view, marker_size=4)
        axes[2].set_title("重ね合わせ", fontsize=12, fontweight="bold")

        # consistent axis limits
        all_pts = []
        for pos in (exp_pos, sim_pos):
            for v in pos.values():
                all_pts.append(v)
        all_pts = np.array(all_pts)

        for ax in axes:
            if view == "sagittal":
                ax.set_xlim(all_pts[:, 0].min() - 0.2, all_pts[:, 0].max() + 0.2)
                ax.set_ylim(-0.15, all_pts[:, 1].max() + 0.25)
                ax.set_xlabel("X [m]")
                ax.set_ylabel("Y [m]")
            elif view == "frontal":
                ax.set_xlim(all_pts[:, 2].min() - 0.3, all_pts[:, 2].max() + 0.3)
                ax.set_ylim(-0.15, all_pts[:, 1].max() + 0.25)
                ax.set_xlabel("Z [m]")
                ax.set_ylabel("Y [m]")
            ax.set_aspect("equal")
        axes[2].legend(loc="upper right", fontsize=8)

        fig.suptitle(f"t = {t:.4f} s   {title}", fontsize=13, fontweight="bold")
        return axes

    print(f"  アニメーション生成中 ({n_frames} フレーム, {playback_fps} fps, "
          f"再生時間 {n_frames/playback_fps:.1f}s) ...")
    ani = animation.FuncAnimation(fig, _update, frames=n_frames,
                                   interval=1000 / playback_fps, blit=False)

    suffix = Path(output_path).suffix.lower()
    if suffix == ".gif":
        writer = animation.PillowWriter(fps=playback_fps)
    else:
        try:
            writer = animation.FFMpegWriter(fps=playback_fps, bitrate=2000)
        except Exception:
            print("  [WARN] ffmpeg未検出。GIF形式で保存します。")
            output_path = str(output_path).replace(suffix, ".gif")
            writer = animation.PillowWriter(fps=playback_fps)

    ani.save(str(output_path), writer=writer, dpi=120)
    plt.close(fig)
    print(f"  [OK] アニメーション保存: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════
# 3D snapshot comparison
# ═══════════════════════════════════════════════════════════════════════════

def create_3d_snapshot(exp_series, sim_series, t_snap, output_path, title=""):
    """Single 3D snapshot at time t_snap."""
    exp_times = np.array([s[0] for s in exp_series])
    sim_times = np.array([s[0] for s in sim_series])

    exp_idx = np.argmin(np.abs(exp_times - t_snap))
    sim_idx = np.argmin(np.abs(sim_times - t_snap))

    exp_pos, _ = compute_body_positions(exp_series[exp_idx][1])
    sim_pos, _ = compute_body_positions(sim_series[sim_idx][1])

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    # offset sim slightly in z for visibility
    sim_pos_offset = {k: v + np.array([0, 0, 0.3]) for k, v in sim_pos.items()}

    draw_stick_figure_3d(ax, exp_pos, "#2196F3", lw=3, alpha=0.9,
                         label="実験 (IK)", marker_size=4)
    draw_stick_figure_3d(ax, sim_pos_offset, "#F44336", lw=3, alpha=0.8,
                         label="シミュレーション", marker_size=4)

    ax.set_xlabel("X (前方) [m]")
    ax.set_ylabel("Z (側方) [m]")
    ax.set_zlabel("Y (鉛直) [m]")
    ax.set_title(f"3D比較  t = {t_snap:.3f} s  {title}", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)

    # Set reasonable viewing angle
    ax.view_init(elev=15, azim=-70)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] 3D スナップショット保存: {output_path}")


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
    return all_coords[:1]  # default: first one


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="走動作スティックフィギュア比較 (実験 vs シミュレーション)")
    parser.add_argument("--sim_label", type=str, default="Nominal",
                        help="シミュレーションファイルのラベル (例: Nominal)")
    parser.add_argument("--snapshot_times", type=float, nargs="+", default=None,
                        help="スナップショット時刻 [s] (例: 0.08 0.12 0.16 0.20)")
    parser.add_argument("--fps", type=int, default=25, help="動画FPS")
    parser.add_argument("--output", type=str, default=None,
                        help="動画出力パス (例: compare.mp4 or compare.gif)")
    parser.add_argument("--no_animation", action="store_true",
                        help="アニメーションを生成しない (静止画のみ)")
    parser.add_argument("--view", type=str, default="sagittal",
                        choices=["sagittal", "frontal"],
                        help="表示ビュー: sagittal(矢状面) or frontal(前額面)")
    parser.add_argument("--output_dir", type=str, default=None)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent

    # Japanese font
    try:
        import matplotlib.font_manager as fm
        jp_fonts = [f.name for f in fm.fontManager.ttflist
                    if "Gothic" in f.name or "Meiryo" in f.name or "Hiragino" in f.name]
        if jp_fonts:
            plt.rcParams["font.family"] = jp_fonts[0]
    except Exception:
        pass

    print("=" * 60)
    print("  走動作スティックフィギュア比較ツール")
    print("=" * 60)

    # Load experimental
    exp_path = find_experimental_ik(project_root)
    print(f"\n[実験データ]  {exp_path.name}")
    df_exp = read_mot(exp_path)
    exp_series = mot_to_q_series(df_exp)
    print(f"  フレーム数: {len(exp_series)}, 時間: {exp_series[0][0]:.4f}-{exp_series[-1][0]:.4f} s")

    # Load simulation
    sim_files = find_simulation_coords(project_root, args.sim_label)
    if not sim_files:
        print("ERROR: シミュレーション結果が見つかりません")
        return 1

    sim_path = sim_files[0]
    match = re.search(r"___(.+)\.mot$", sim_path.name)
    label = match.group(1) if match else "Sim"

    print(f"[シミュレーション]  {sim_path.name}")
    df_sim = read_mot(sim_path)
    sim_series = mot_to_q_series(df_sim)
    print(f"  フレーム数: {len(sim_series)}, 時間: {sim_series[0][0]:.4f}-{sim_series[-1][0]:.4f} s")

    # Output directory
    out_dir = Path(args.output_dir) if args.output_dir else project_root / "Results" / "motion_comparison"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine snapshot times
    t_start = max(exp_series[0][0], sim_series[0][0])
    t_end = min(exp_series[-1][0], sim_series[-1][0])

    if args.snapshot_times is None:
        # auto: 6 evenly spaced snapshots
        snapshot_times = np.linspace(t_start + 0.005, t_end - 0.005, 6).tolist()
    else:
        snapshot_times = args.snapshot_times

    print(f"\n--- 出力生成中 ---")

    # 1) Multi-frame snapshot comparison (sagittal)
    create_snapshot_comparison(
        exp_series, sim_series, snapshot_times,
        out_dir / f"snapshots_sagittal_{label}.png",
        title=f"[{label}]", view="sagittal"
    )

    # 2) Multi-frame snapshot comparison (frontal)
    create_snapshot_comparison(
        exp_series, sim_series, snapshot_times,
        out_dir / f"snapshots_frontal_{label}.png",
        title=f"[{label}]", view="frontal"
    )

    # 3) Ghost overlay
    create_ghost_overlay(
        exp_series, sim_series, n_ghosts=10,
        output_path=out_dir / f"ghost_overlay_{label}.png",
        title=f"[{label}]", view="sagittal"
    )

    # 4) 3D snapshots at key moments
    t_mid = (t_start + t_end) / 2
    for t3d in [t_start + 0.01, t_mid, t_end - 0.01]:
        create_3d_snapshot(
            exp_series, sim_series, t3d,
            out_dir / f"3d_t{t3d:.3f}_{label}.png",
            title=f"[{label}]"
        )

    # 5) Animation
    if not args.no_animation:
        anim_path = args.output if args.output else out_dir / f"animation_{label}.gif"
        create_animation(
            exp_series, sim_series, anim_path,
            fps=args.fps, title=f"[{label}]", view=args.view
        )

    print(f"\n{'=' * 60}")
    print(f"  完了! 出力先: {out_dir}")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
