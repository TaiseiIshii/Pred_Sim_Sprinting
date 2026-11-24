"""
overlay_N50_vs_N100.py
N=50 vs N=100 走動作オーバーレイ比較アニメーション

Compares running form between N=50 and N=100 mesh resolution simulations
using stick figure visualization with overlay animation.

Output:
  - Snapshot comparison images (sagittal view)
  - Ghost overlay (progressive opacity)
  - MP4/GIF animation (side-by-side + overlay)

Usage:
    python overlay_N50_vs_N100.py
    python overlay_N50_vs_N100.py --fps 30
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ═══════════════════════════════════════════════════════════════════════════
# FK Engine (from visualize_motion_comparison.py)
# ═══════════════════════════════════════════════════════════════════════════

def _rot_axis_angle(axis, angle_rad):
    axis = np.asarray(axis, dtype=float)
    axis = axis / (np.linalg.norm(axis) + 1e-30)
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
        ("pelvis_tilt", [0, 0, 1], "rot"), ("pelvis_list", [1, 0, 0], "rot"),
        ("pelvis_rotation", [0, 1, 0], "rot"), ("pelvis_tx", [1, 0, 0], "trans"),
        ("pelvis_ty", [0, 1, 0], "trans"), ("pelvis_tz", [0, 0, 1], "trans"),
    ]),
    ("femur_r", "pelvis", [-0.0623853, -0.0583263, 0.0728399], [
        ("hip_flexion_r", [0, 0, 1], "rot"), ("hip_adduction_r", [1, 0, 0], "rot"),
        ("hip_rotation_r", [0, 1, 0], "rot"),
    ]),
    ("tibia_r", "femur_r", [0.0041, -0.41, 0], [("knee_angle_r", [0, 0, 1], "rot")]),
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
        ("hip_flexion_l", [0, 0, 1], "rot"), ("hip_adduction_l", [-1, 0, 0], "rot"),
        ("hip_rotation_l", [0, -1, 0], "rot"),
    ]),
    ("tibia_l", "femur_l", [0.0041, -0.41, 0], [("knee_angle_l", [0, 0, 1], "rot")]),
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
        ("lumbar_extension", [0, 0, 1], "rot"), ("lumbar_bending", [1, 0, 0], "rot"),
        ("lumbar_rotation", [0, 1, 0], "rot"),
    ]),
    ("humerus_r", "torso", [0.003672, 0.359390, 0.183537], [
        ("arm_flex_r", [0, 0, 1], "rot"), ("arm_add_r", [1, 0, 0], "rot"),
        ("arm_rot_r", [0, 1, 0], "rot"),
    ]),
    ("ulna_r", "humerus_r", [0.011167, -0.342102, -0.008152], [
        ("elbow_flex_r", [0.22604696, 0.022269, 0.97386183], "rot"),
    ]),
    ("radius_r", "ulna_r", [-0.005088, -0.013896, 0.019727], [
        ("pro_sup_r", [0.05639803, 0.99840646, 0.001952], "rot"),
    ]),
    ("hand_r", "radius_r", [-0.006653, -0.251965, 0.010293], [
        ("wrist_flex_r", [0, 0, 1], "rot"), ("wrist_dev_r", [1, 0, 0], "rot"),
    ]),
    ("humerus_l", "torso", [0.003672, 0.359390, -0.183537], [
        ("arm_flex_l", [0, 0, 1], "rot"), ("arm_add_l", [-1, 0, 0], "rot"),
        ("arm_rot_l", [0, -1, 0], "rot"),
    ]),
    ("ulna_l", "humerus_l", [0.011167, -0.342102, 0.008152], [
        ("elbow_flex_l", [-0.22604696, -0.022269, 0.97386183], "rot"),
    ]),
    ("radius_l", "ulna_l", [-0.005088, -0.013896, -0.019727], [
        ("pro_sup_l", [-0.05639803, -0.99840646, 0.001952], "rot"),
    ]),
    ("hand_l", "radius_l", [-0.006653, -0.251965, -0.010293], [
        ("wrist_flex_l", [0, 0, 1], "rot"), ("wrist_dev_l", [-1, 0, 0], "rot"),
    ]),
]

STICK_SEGMENTS = [
    ("pelvis", "torso"),
    ("pelvis", "femur_r"), ("femur_r", "tibia_r"), ("tibia_r", "talus_r"),
    ("talus_r", "calcn_r"), ("calcn_r", "toes_r"),
    ("pelvis", "femur_l"), ("femur_l", "tibia_l"), ("tibia_l", "talus_l"),
    ("talus_l", "calcn_l"), ("calcn_l", "toes_l"),
    ("torso", "humerus_r"), ("humerus_r", "ulna_r"),
    ("ulna_r", "radius_r"), ("radius_r", "hand_r"),
    ("torso", "humerus_l"), ("humerus_l", "ulna_l"),
    ("ulna_l", "radius_l"), ("radius_l", "hand_l"),
]

HEAD_OFFSET_FROM_TORSO = np.array([0.0, 0.22, 0.0])


def compute_body_positions(q_dict):
    transforms = {"ground": np.eye(4)}
    positions = {"ground": np.zeros(3)}
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
        T_joint = _homogeneous(R_joint, t_joint)
        T_loc = _homogeneous(np.eye(3), np.array(loc_in_parent, dtype=float))
        T_body = T_parent @ T_loc @ T_joint
        transforms[body] = T_body
        positions[body] = T_body[:3, 3].copy()
    T_torso = transforms["torso"]
    positions["head"] = (T_torso @ np.append(HEAD_OFFSET_FROM_TORSO, 1.0))[:3]
    return positions, transforms


# ═══════════════════════════════════════════════════════════════════════════
# .mot reader
# ═══════════════════════════════════════════════════════════════════════════

def read_mot(filepath):
    filepath = Path(filepath)
    with open(filepath, "r", encoding="latin-1") as f:
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


# ═══════════════════════════════════════════════════════════════════════════
# Drawing
# ═══════════════════════════════════════════════════════════════════════════

def draw_stick_figure(ax, positions, color, alpha=1.0, lw=2.5, label=None,
                      marker_size=5, z_offset=0.0):
    """Draw sagittal (X-Y) stick figure."""
    drawn_label = False
    for seg_a, seg_b in STICK_SEGMENTS:
        if seg_a not in positions or seg_b not in positions:
            continue
        pa = positions[seg_a]
        pb = positions[seg_b]
        lbl = label if not drawn_label else None
        ax.plot([pa[0] + z_offset, pb[0] + z_offset], [pa[1], pb[1]],
                color=color, linewidth=lw, alpha=alpha, solid_capstyle="round",
                label=lbl)
        drawn_label = True
    if "head" in positions and "torso" in positions:
        ph = positions["head"]
        pt = positions["torso"]
        ax.plot([pt[0] + z_offset, ph[0] + z_offset], [pt[1], ph[1]],
                color=color, linewidth=lw, alpha=alpha, solid_capstyle="round")
        ax.plot(ph[0] + z_offset, ph[1], "o", color=color,
                markersize=marker_size + 2, alpha=alpha)
    for name, pos in positions.items():
        if name in ("ground", "head"):
            continue
        ax.plot(pos[0] + z_offset, pos[1], "o", color=color,
                markersize=marker_size, alpha=alpha)


# ═══════════════════════════════════════════════════════════════════════════
# Snapshot comparison
# ═══════════════════════════════════════════════════════════════════════════

def create_snapshot_comparison(series_a, series_b, snapshot_times, output_path):
    n = len(snapshot_times)
    fig, axes = plt.subplots(1, n, figsize=(4.5 * n, 8), squeeze=False)
    axes = axes[0]
    times_a = np.array([s[0] for s in series_a])
    times_b = np.array([s[0] for s in series_b])

    for col_idx, t_snap in enumerate(snapshot_times):
        ax = axes[col_idx]
        idx_a = np.argmin(np.abs(times_a - t_snap))
        idx_b = np.argmin(np.abs(times_b - t_snap))
        pos_a, _ = compute_body_positions(series_a[idx_a][1])
        pos_b, _ = compute_body_positions(series_b[idx_b][1])
        # Align pelvis x
        dx = pos_a["pelvis"][0] - pos_b["pelvis"][0]
        pos_b_aligned = {k: v + np.array([dx, 0, 0]) for k, v in pos_b.items()}

        draw_stick_figure(ax, pos_a, color="#2979FF", alpha=0.9, lw=3,
                          label="N=50", marker_size=4)
        draw_stick_figure(ax, pos_b_aligned, color="#FF5252", alpha=0.7, lw=3,
                          label="N=100", marker_size=4)

        ax.set_title(f"t = {t_snap:.3f} s", fontsize=12, fontweight="bold")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.2)
        ax.axhline(y=0, color="brown", linewidth=1, linestyle="--", alpha=0.5)
        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")
        if col_idx == 0:
            ax.legend(loc="upper left", fontsize=9)

    fig.suptitle("Running Form Comparison: N=50 vs N=100 (Mesh Convergence)",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(str(output_path), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] Snapshots: {output_path.name}")


# ═══════════════════════════════════════════════════════════════════════════
# Ghost overlay
# ═══════════════════════════════════════════════════════════════════════════

def create_ghost_overlay(series_a, series_b, n_ghosts=10, output_path=None):
    times_a = np.array([s[0] for s in series_a])
    times_b = np.array([s[0] for s in series_b])
    t_start = max(times_a[0], times_b[0])
    t_end = min(times_a[-1], times_b[-1])
    ghost_times = np.linspace(t_start, t_end, n_ghosts)

    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    for panel_idx, (series, label, color) in enumerate([
        (series_a, "N=50", "#2979FF"),
        (series_b, "N=100", "#FF5252"),
    ]):
        ax = axes[panel_idx]
        times_arr = times_a if panel_idx == 0 else times_b

        for gi, t_g in enumerate(ghost_times):
            idx = np.argmin(np.abs(times_arr - t_g))
            pos, _ = compute_body_positions(series[idx][1])
            alpha = 0.15 + 0.85 * (gi / (n_ghosts - 1))
            draw_stick_figure(ax, pos, color=color, alpha=alpha, lw=2.5, marker_size=3)

        ax.set_title(label, fontsize=13, fontweight="bold")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.2)
        ax.axhline(y=0, color="brown", linewidth=1, linestyle="--", alpha=0.5)
        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")

    fig.suptitle("Ghost Trail: N=50 vs N=100",
                 fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    if output_path:
        fig.savefig(str(output_path), dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"  [OK] Ghost overlay: {output_path.name}")
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# Animation
# ═══════════════════════════════════════════════════════════════════════════

def create_overlay_animation(series_a, series_b, output_path, fps=24, loops=2):
    """Create overlay animation: Left=N50, Center=N100, Right=Overlay."""
    times_a = np.array([s[0] for s in series_a])
    times_b = np.array([s[0] for s in series_b])
    t_start = max(times_a[0], times_b[0])
    t_end = min(times_a[-1], times_b[-1])
    duration = t_end - t_start

    # Generate enough frames for smooth animation (loop the motion)
    total_duration = duration * loops
    n_frames = max(int(total_duration * fps), 60)
    frame_times_raw = np.linspace(0, total_duration, n_frames)
    # Wrap around for looping
    frame_times = t_start + np.mod(frame_times_raw, duration)

    fig, axes = plt.subplots(1, 3, figsize=(20, 7),
                             gridspec_kw={"width_ratios": [1, 1, 1]})

    # Precompute global axis limits
    all_pts = []
    for series in (series_a, series_b):
        for i in range(0, len(series), max(1, len(series) // 20)):
            pos, _ = compute_body_positions(series[i][1])
            for v in pos.values():
                all_pts.append(v)
    all_pts = np.array(all_pts)
    x_min, x_max = all_pts[:, 0].min() - 0.3, all_pts[:, 0].max() + 0.3
    y_min, y_max = -0.1, all_pts[:, 1].max() + 0.3

    def _update(frame_idx):
        t = frame_times[frame_idx]
        for ax in axes:
            ax.cla()
            ax.grid(True, alpha=0.2)
            ax.axhline(y=0, color="brown", linewidth=1, linestyle="--", alpha=0.5)

        idx_a = np.argmin(np.abs(times_a - t))
        idx_b = np.argmin(np.abs(times_b - t))
        pos_a, _ = compute_body_positions(series_a[idx_a][1])
        pos_b, _ = compute_body_positions(series_b[idx_b][1])

        # Overlay: align pelvis
        dx = pos_a["pelvis"][0] - pos_b["pelvis"][0]
        pos_b_aligned = {k: v + np.array([dx, 0, 0]) for k, v in pos_b.items()}

        # Left: N=50
        draw_stick_figure(axes[0], pos_a, "#2979FF", lw=3, label="N=50", marker_size=4)
        axes[0].set_title("N=50", fontsize=13, fontweight="bold", color="#2979FF")

        # Center: N=100
        draw_stick_figure(axes[1], pos_b, "#FF5252", lw=3, label="N=100", marker_size=4)
        axes[1].set_title("N=100", fontsize=13, fontweight="bold", color="#FF5252")

        # Right: Overlay
        draw_stick_figure(axes[2], pos_a, "#2979FF", alpha=0.8, lw=3,
                          label="N=50", marker_size=4)
        draw_stick_figure(axes[2], pos_b_aligned, "#FF5252", alpha=0.7, lw=3,
                          label="N=100", marker_size=4)
        axes[2].set_title("Overlay", fontsize=13, fontweight="bold")
        axes[2].legend(loc="upper right", fontsize=9, framealpha=0.8)

        for ax in axes:
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
            ax.set_aspect("equal")
            ax.set_xlabel("X [m]")
        axes[0].set_ylabel("Y [m]")

        phase = (t - t_start) / duration * 100
        fig.suptitle(f"N=50 vs N=100 Running Form   |   t = {t:.4f} s   "
                     f"({phase:.0f}% gait cycle)",
                     fontsize=14, fontweight="bold")
        return axes

    print(f"  Generating animation: {n_frames} frames, {fps} fps, "
          f"{loops} loops ({n_frames/fps:.1f}s playback)...")

    ani = animation.FuncAnimation(fig, _update, frames=n_frames,
                                  interval=1000 / fps, blit=False)

    suffix = Path(output_path).suffix.lower()
    if suffix == ".gif":
        writer = animation.PillowWriter(fps=fps)
    else:
        try:
            writer = animation.FFMpegWriter(fps=fps, bitrate=3000,
                                            extra_args=["-pix_fmt", "yuv420p"])
        except Exception:
            print("  [WARN] ffmpeg not found, saving as GIF instead")
            output_path = str(output_path).replace(suffix, ".gif")
            writer = animation.PillowWriter(fps=fps)

    ani.save(str(output_path), writer=writer, dpi=120)
    plt.close(fig)
    print(f"  [OK] Animation: {Path(output_path).name}")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = PROJECT_ROOT / "Results"

COORDS_N50 = RESULTS_DIR / "pred_sprinting_coords_04-February-2026__12-27-31___Nominal.mot"
COORDS_N100 = RESULTS_DIR / "pred_sprinting_coords_10-April-2026__16-29-40___Nominal.mot"

OUTPUT_DIR = RESULTS_DIR / "overlay_N50_vs_N100"


def main():
    parser = argparse.ArgumentParser(description="N=50 vs N=100 running overlay animation")
    parser.add_argument("--fps", type=int, default=24, help="Animation FPS")
    parser.add_argument("--loops", type=int, default=2, help="Number of loops")
    parser.add_argument("--format", type=str, default="gif",
                        choices=["gif", "mp4"], help="Output format")
    args = parser.parse_args()

    print("=" * 60)
    print("Running Form Overlay: N=50 vs N=100")
    print("=" * 60)

    # Load coords
    print(f"\nLoading N=50: {COORDS_N50.name}")
    df_n50 = read_mot(COORDS_N50)
    series_n50 = mot_to_q_series(df_n50)
    print(f"  {len(series_n50)} frames, t={series_n50[0][0]:.4f}-{series_n50[-1][0]:.4f} s")

    print(f"Loading N=100: {COORDS_N100.name}")
    df_n100 = read_mot(COORDS_N100)
    series_n100 = mot_to_q_series(df_n100)
    print(f"  {len(series_n100)} frames, t={series_n100[0][0]:.4f}-{series_n100[-1][0]:.4f} s")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Determine common time range
    t_start = max(series_n50[0][0], series_n100[0][0])
    t_end = min(series_n50[-1][0], series_n100[-1][0])
    snapshot_times = np.linspace(t_start + 0.005, t_end - 0.005, 6).tolist()

    print(f"\n--- Generating outputs ---")

    # 1) Snapshot comparison
    create_snapshot_comparison(series_n50, series_n100, snapshot_times,
                               OUTPUT_DIR / "snapshots_N50_vs_N100.png")

    # 2) Ghost overlay
    create_ghost_overlay(series_n50, series_n100, n_ghosts=10,
                         output_path=OUTPUT_DIR / "ghost_N50_vs_N100.png")

    # 3) Animation
    ext = f".{args.format}"
    create_overlay_animation(series_n50, series_n100,
                             OUTPUT_DIR / f"overlay_N50_vs_N100{ext}",
                             fps=args.fps, loops=args.loops)

    print(f"\n{'=' * 60}")
    print(f"Done! Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
