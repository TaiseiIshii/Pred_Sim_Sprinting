"""
analyze_com_vertical.py
Center of Mass (pelvis) vertical oscillation analysis.

1) Time-series plot of pelvis_ty (vertical) for Exp vs Sim
2) Additional pelvis_tx, pelvis_tz plots
3) Overlay MP4 animation with COM trajectory line and current-height marker

Usage:
    python analyze_com_vertical.py
    python analyze_com_vertical.py --sim_label Nominal --fps 24 --loops 2
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
    return parts[-2] if len(parts) >= 3 else col


def get_col(df, keyword):
    """Find column containing keyword."""
    for c in df.columns:
        if keyword in c:
            return c
    return None


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
# Time-series plots
# ═══════════════════════════════════════════════════════════════════════════

def plot_pelvis_timeseries(df_exp, df_sim, out_dir, label="Nominal"):
    """
    Create comprehensive pelvis position time-series plots:
    - pelvis_ty (vertical / COM height)
    - pelvis_tx (forward)
    - pelvis_tz (lateral)
    - pelvis_tilt (trunk forward lean)
    """
    exp_time = df_exp["time"].values
    sim_time = df_sim["time"].values

    # Common overlap
    t_start = max(exp_time[0], sim_time[0])
    t_end = min(exp_time[-1], sim_time[-1])
    common_t = np.linspace(t_start, t_end, 300)

    dofs = [
        ("pelvis_ty", "Pelvis Height (COM Vertical)", "m", True),
        ("pelvis_tx", "Forward Position", "m", False),
        ("pelvis_tz", "Lateral Position", "m", False),
        ("pelvis_tilt", "Pelvis Tilt (Forward Lean)", "deg", False),
    ]

    # --- Individual plots ---
    for keyword, title, unit, is_main in dofs:
        exp_col = get_col(df_exp, keyword)
        sim_col = get_col(df_sim, keyword)
        if exp_col is None or sim_col is None:
            continue

        exp_vals = np.interp(common_t, exp_time, df_exp[exp_col].values)
        sim_vals = np.interp(common_t, sim_time, df_sim[sim_col].values)
        diff = sim_vals - exp_vals

        fig, axes = plt.subplots(2, 1, figsize=(12, 7), height_ratios=[3, 1],
                                  sharex=True, gridspec_kw={"hspace": 0.08})

        # Top: overlay
        ax = axes[0]
        ax.plot(common_t, exp_vals, color="#2979FF", linewidth=2.5,
                label="Experimental (IK)")
        ax.plot(common_t, sim_vals, color="#FF5252", linewidth=2.5,
                label="Simulation", linestyle="--")
        ax.set_ylabel(f"{title} [{unit}]", fontsize=12)
        ax.set_title(f"{title}: Experimental vs Simulation [{label}]",
                      fontsize=14, fontweight="bold")
        ax.legend(fontsize=11, loc="best")
        ax.grid(True, alpha=0.3)

        if is_main:
            # Annotate statistics
            exp_range = exp_vals.max() - exp_vals.min()
            sim_range = sim_vals.max() - sim_vals.min()
            rmse = np.sqrt(np.mean(diff ** 2))
            ax.annotate(
                f"Exp range: {exp_range:.4f} {unit}\n"
                f"Sim range: {sim_range:.4f} {unit}\n"
                f"RMSE: {rmse:.4f} {unit}",
                xy=(0.02, 0.02), xycoords="axes fraction",
                fontsize=10, fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow",
                          alpha=0.9),
                verticalalignment="bottom",
            )

        # Bottom: difference
        ax2 = axes[1]
        ax2.fill_between(common_t, diff, alpha=0.4, color="#9C27B0")
        ax2.plot(common_t, diff, color="#9C27B0", linewidth=1.5)
        ax2.axhline(0, color="gray", linewidth=0.8, linestyle=":")
        ax2.set_xlabel("Time [s]", fontsize=12)
        ax2.set_ylabel(f"Diff [{unit}]", fontsize=12)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        fname = f"com_{keyword}_{label}.png"
        fig.savefig(str(out_dir / fname), dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  [OK] {fname}")

    # --- Combined pelvis position plot (3 translational DOFs) ---
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True,
                              gridspec_kw={"hspace": 0.12})

    for i, (keyword, title, unit, _) in enumerate(dofs[:3]):
        exp_col = get_col(df_exp, keyword)
        sim_col = get_col(df_sim, keyword)
        exp_vals = np.interp(common_t, exp_time, df_exp[exp_col].values)
        sim_vals = np.interp(common_t, sim_time, df_sim[sim_col].values)

        ax = axes[i]
        ax.plot(common_t, exp_vals, color="#2979FF", linewidth=2.2,
                label="Experimental (IK)")
        ax.plot(common_t, sim_vals, color="#FF5252", linewidth=2.2,
                label="Simulation", linestyle="--")
        ax.set_ylabel(f"{title} [{unit}]", fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=10, loc="best")

        # Mark min/max for pelvis_ty
        if keyword == "pelvis_ty":
            for vals, color, lbl in [(exp_vals, "#2979FF", "Exp"),
                                      (sim_vals, "#FF5252", "Sim")]:
                i_max = np.argmax(vals)
                i_min = np.argmin(vals)
                ax.annotate(f"{lbl} max: {vals[i_max]:.4f}m",
                            xy=(common_t[i_max], vals[i_max]),
                            fontsize=8, color=color,
                            xytext=(5, 8), textcoords="offset points")
                ax.annotate(f"{lbl} min: {vals[i_min]:.4f}m",
                            xy=(common_t[i_min], vals[i_min]),
                            fontsize=8, color=color,
                            xytext=(5, -12), textcoords="offset points")

    axes[0].set_title(
        f"Pelvis (COM) Position: Experimental vs Simulation [{label}]",
        fontsize=14, fontweight="bold")
    axes[-1].set_xlabel("Time [s]", fontsize=12)

    plt.tight_layout()
    fname = f"com_pelvis_positions_{label}.png"
    fig.savefig(str(out_dir / fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {fname}")

    # --- Phase plot: pelvis_ty vs gait phase (%) ---
    phase_exp = (common_t - t_start) / (t_end - t_start) * 100
    exp_ty = np.interp(common_t, exp_time,
                       df_exp[get_col(df_exp, "pelvis_ty")].values)
    sim_ty = np.interp(common_t, sim_time,
                       df_sim[get_col(df_sim, "pelvis_ty")].values)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(phase_exp, exp_ty * 100, color="#2979FF", linewidth=2.5,
            label="Experimental (IK)")
    ax.plot(phase_exp, sim_ty * 100, color="#FF5252", linewidth=2.5,
            label="Simulation", linestyle="--")
    ax.fill_between(phase_exp, exp_ty * 100, sim_ty * 100,
                     alpha=0.15, color="#9C27B0", label="Difference")
    ax.set_xlabel("Gait Cycle Phase [%]", fontsize=12)
    ax.set_ylabel("COM Height [cm]", fontsize=12)
    ax.set_title(f"COM Vertical Oscillation vs Gait Phase [{label}]",
                  fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    # Statistics annotation
    exp_osc = (exp_ty.max() - exp_ty.min()) * 100
    sim_osc = (sim_ty.max() - sim_ty.min()) * 100
    rmse_cm = np.sqrt(np.mean((exp_ty - sim_ty) ** 2)) * 100
    ax.annotate(
        f"Exp oscillation: {exp_osc:.2f} cm\n"
        f"Sim oscillation: {sim_osc:.2f} cm\n"
        f"RMSE: {rmse_cm:.2f} cm",
        xy=(0.98, 0.02), xycoords="axes fraction",
        fontsize=11, fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", alpha=0.9),
        horizontalalignment="right", verticalalignment="bottom",
    )

    plt.tight_layout()
    fname = f"com_vertical_oscillation_phase_{label}.png"
    fig.savefig(str(out_dir / fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {fname}")

    return common_t, exp_ty, sim_ty


# ═══════════════════════════════════════════════════════════════════════════
# Overlay animation with COM height indicator
# ═══════════════════════════════════════════════════════════════════════════

def generate_com_overlay_video(df_exp, df_sim, common_t, exp_ty, sim_ty,
                                out_dir, label="Nominal",
                                fps=24, n_loops=2, same_start=True):
    """
    Create an overlay MP4 animation:
    - Left panel: 3D musculoskeletal overlay (experimental blue + simulation red)
    - Right panel: real-time pelvis_ty time-series with moving cursor

    This uses matplotlib for the combined layout to ensure proper framing.
    """
    import pyvista as pv

    # Import FK/geometry from the existing v2 script
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from visualize_form_comparison_v2 import (
        compute_body_transforms, build_posed_model, build_stick_figure,
        load_body_meshes, find_geometry_dir, mot_to_q_series,
        compute_tracking_camera, add_ground_plane, align_to_same_start,
        EXP_COLOR, SIM_COLOR, BG_COLOR,
    )

    geom_dir = find_geometry_dir()
    body_meshes = load_body_meshes(geom_dir)
    print(f"  Loaded {len(body_meshes)} body meshes")

    exp_series = mot_to_q_series(df_exp)
    sim_series = mot_to_q_series(df_sim)

    if same_start:
        print("  Applying same-start alignment (sim initial posture -> exp initial posture)")
        sim_series = align_to_same_start(exp_series, sim_series)
    exp_times_arr = np.array([s[0] for s in exp_series])
    sim_times_arr = np.array([s[0] for s in sim_series])

    t_start = common_t[0]
    t_end = common_t[-1]
    duration = t_end - t_start

    frames_per_loop = max(int(duration * fps), 20)
    single_times = np.linspace(t_start, t_end, frames_per_loop)
    total_frames = frames_per_loop * n_loops
    all_times = np.tile(single_times, n_loops)

    # Pre-render all 3D frames
    print(f"  Rendering {total_frames} composite frames ({fps} fps, {n_loops} loops)...")

    import imageio
    mp4_path = out_dir / f"com_overlay_animation_{label}.mp4"
    gif_path = out_dir / f"com_overlay_animation_{label}.gif"

    writer = imageio.get_writer(str(mp4_path), fps=fps, codec="libx264",
                                quality=8,
                                output_params=["-pix_fmt", "yuv420p"])

    from PIL import Image
    gif_frames = []
    gif_step = max(1, frames_per_loop // 40)

    for fi, t in enumerate(all_times):
        loop_num = fi // frames_per_loop + 1

        # --- 3D rendering ---
        exp_idx = np.argmin(np.abs(exp_times_arr - t))
        sim_idx = np.argmin(np.abs(sim_times_arr - t))

        exp_q = exp_series[exp_idx][1]
        sim_q = sim_series[sim_idx][1]

        exp_tf = compute_body_transforms(exp_q)
        sim_tf = compute_body_transforms(sim_q)

        # Align at pelvis X
        dx = exp_tf["pelvis"][0, 3] - sim_tf["pelvis"][0, 3]
        for body in sim_tf:
            sim_tf[body][0, 3] += dx

        exp_mesh = build_posed_model(body_meshes, exp_tf)
        sim_mesh = build_posed_model(body_meshes, sim_tf)
        exp_stick = build_stick_figure(exp_tf)
        sim_stick = build_stick_figure(sim_tf)

        pv.global_theme.background = "white"
        pl = pv.Plotter(off_screen=True, window_size=[1000, 900])

        if exp_mesh.n_points > 0:
            pl.add_mesh(exp_mesh, color=EXP_COLOR, opacity=0.45,
                        smooth_shading=True)
        if sim_mesh.n_points > 0:
            pl.add_mesh(sim_mesh, color=SIM_COLOR, opacity=0.40,
                        smooth_shading=True)
        if exp_stick is not None:
            pl.add_mesh(exp_stick, color=EXP_COLOR, line_width=3, opacity=0.9)
        if sim_stick is not None:
            pl.add_mesh(sim_stick, color=SIM_COLOR, line_width=3, opacity=0.9)

        # COM height markers (horizontal lines at pelvis_ty)
        exp_py = exp_tf["pelvis"][1, 3]
        sim_py = sim_tf["pelvis"][1, 3]
        cx = exp_tf["pelvis"][0, 3]

        # Horizontal dashed line for each COM height
        for py, color in [(exp_py, EXP_COLOR), (sim_py, SIM_COLOR)]:
            line = pv.Line((cx - 0.3, py, 0), (cx + 0.3, py, 0))
            pl.add_mesh(line, color=color, line_width=3)

        add_ground_plane(pl, center_x=cx)
        cam_pos, focal, up = compute_tracking_camera(exp_tf, view="side",
                                                       cam_dist=2.8)
        pl.camera_position = [cam_pos, focal, up]
        pl.add_light(pv.Light(position=(cx + 3, 4, 4), intensity=0.6))
        pl.add_light(pv.Light(position=(cx - 2, 3, -3), intensity=0.3))

        img_3d = pl.screenshot(return_img=True)
        pl.close()

        # --- Matplotlib composite ---
        fig = plt.figure(figsize=(19.2, 10.8), dpi=100)

        # Left: 3D view
        ax_3d = fig.add_axes([0.01, 0.05, 0.52, 0.88])
        ax_3d.imshow(img_3d)
        ax_3d.axis("off")
        ss_tag = " [Same Start]" if same_start else ""
        ax_3d.set_title(f"Overlay: Blue=Experimental  Red=Simulation{ss_tag}",
                         fontsize=13, color="#333333", pad=5)

        # Right top: pelvis_ty relative displacement (zero = initial height)
        exp_ty_rel = (exp_ty - exp_ty[0]) * 100  # cm from start
        sim_ty_rel = (sim_ty - sim_ty[0]) * 100
        ax_ty = fig.add_axes([0.58, 0.55, 0.38, 0.38])
        ax_ty.plot(common_t, exp_ty_rel, color="#2979FF", linewidth=2,
                   label="Experimental")
        ax_ty.plot(common_t, sim_ty_rel, color="#FF5252", linewidth=2,
                   linestyle="--", label="Simulation")
        ax_ty.fill_between(common_t, exp_ty_rel, sim_ty_rel,
                            alpha=0.12, color="#9C27B0")
        ax_ty.axhline(0, color="gray", linewidth=0.8, linestyle=":")
        # Current time cursor
        cur_exp_rel = np.interp(t, common_t, exp_ty_rel)
        cur_sim_rel = np.interp(t, common_t, sim_ty_rel)
        ax_ty.axvline(t, color="#333333", linewidth=1.5, linestyle=":",
                       alpha=0.7)
        ax_ty.plot(t, cur_exp_rel, "o", color="#2979FF", markersize=8,
                   zorder=5)
        ax_ty.plot(t, cur_sim_rel, "o", color="#FF5252", markersize=8,
                   zorder=5)
        ax_ty.set_ylabel("Displacement from start [cm]", fontsize=11)
        ax_ty.set_title("COM Vertical Displacement (0 = initial height)",
                         fontsize=12, fontweight="bold")
        ax_ty.legend(fontsize=9, loc="upper right")
        ax_ty.grid(True, alpha=0.3)

        # Right bottom: difference
        diff_ty = (sim_ty - exp_ty) * 100  # cm
        cur_diff = np.interp(t, common_t, diff_ty)
        ax_diff = fig.add_axes([0.58, 0.10, 0.38, 0.35])
        ax_diff.fill_between(common_t, diff_ty, alpha=0.4, color="#9C27B0")
        ax_diff.plot(common_t, diff_ty, color="#9C27B0", linewidth=1.5)
        ax_diff.axhline(0, color="gray", linewidth=0.8, linestyle=":")
        ax_diff.axvline(t, color="#333333", linewidth=1.5, linestyle=":",
                         alpha=0.7)
        ax_diff.plot(t, cur_diff, "o", color="#9C27B0", markersize=8,
                     zorder=5)
        ax_diff.set_xlabel("Time [s]", fontsize=11)
        ax_diff.set_ylabel("Diff (Sim-Exp) [cm]", fontsize=11)
        ax_diff.set_title("Height Difference", fontsize=12, fontweight="bold")
        ax_diff.grid(True, alpha=0.3)

        # Time & loop info
        fig.text(0.27, 0.01,
                 f"t = {t:.4f} s    Loop {loop_num}/{n_loops}",
                 fontsize=12, ha="center", color="#555555")

        # Render to array
        fig.canvas.draw()
        buf = fig.canvas.buffer_rgba()
        w, h = fig.canvas.get_width_height()
        img_composite = np.asarray(buf).reshape(h, w, 4)[:, :, :3].copy()
        plt.close(fig)

        writer.append_data(img_composite)

        # GIF frames (first loop, downsampled)
        if loop_num == 1 and fi % gif_step == 0:
            pil_img = Image.fromarray(img_composite)
            pil_img = pil_img.resize((960, 540), Image.LANCZOS)
            gif_frames.append(np.array(pil_img))

        if (fi + 1) % 10 == 0 or fi == total_frames - 1:
            pct = (fi + 1) / total_frames * 100
            print(f"    Frame {fi + 1}/{total_frames} ({pct:.0f}%)")

    writer.close()
    file_size_mb = mp4_path.stat().st_size / (1024 * 1024)
    print(f"  [OK] MP4: {mp4_path}  ({file_size_mb:.1f} MB)")

    if gif_frames:
        imageio.mimsave(str(gif_path), gif_frames, duration=120, loop=0)
        gif_size_mb = gif_path.stat().st_size / (1024 * 1024)
        print(f"  [OK] GIF: {gif_path}  ({gif_size_mb:.1f} MB)")

    return mp4_path


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="COM Vertical Oscillation Analysis")
    parser.add_argument("--sim_label", type=str, default="Nominal")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--loops", type=int, default=5)
    parser.add_argument("--plots_only", action="store_true",
                        help="Generate plots only, skip video")
    parser.add_argument("--same_start", action="store_true", default=True,
                        help="Align simulation initial posture to experimental (default: on)")
    parser.add_argument("--no_same_start", dest="same_start", action="store_false",
                        help="Disable same-start alignment")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent

    print("=" * 65)
    print("  COM Vertical Oscillation Analysis")
    print("=" * 65)

    # Load data
    exp_path = find_experimental_ik(project_root)
    print(f"\n[Experimental] {exp_path.name}")
    df_exp = read_mot(exp_path)

    sim_files = find_simulation_coords(project_root, args.sim_label)
    if not sim_files:
        print("ERROR: No simulation file found")
        return 1
    sim_path = sim_files[0]
    match = re.search(r"___(.+)\.mot$", sim_path.name)
    label = match.group(1) if match else "Sim"
    print(f"[Simulation] {sim_path.name}")
    df_sim = read_mot(sim_path)

    out_dir = project_root / "Results" / "com_analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Quick summary ---
    exp_ty_col = get_col(df_exp, "pelvis_ty")
    sim_ty_col = get_col(df_sim, "pelvis_ty")
    print(f"\n--- Pelvis Height (COM Vertical) Summary ---")
    print(f"  Experimental: min={df_exp[exp_ty_col].min():.4f} m, "
          f"max={df_exp[exp_ty_col].max():.4f} m, "
          f"range={df_exp[exp_ty_col].max() - df_exp[exp_ty_col].min():.4f} m "
          f"({(df_exp[exp_ty_col].max() - df_exp[exp_ty_col].min())*100:.2f} cm)")
    print(f"  Simulation:   min={df_sim[sim_ty_col].min():.4f} m, "
          f"max={df_sim[sim_ty_col].max():.4f} m, "
          f"range={df_sim[sim_ty_col].max() - df_sim[sim_ty_col].min():.4f} m "
          f"({(df_sim[sim_ty_col].max() - df_sim[sim_ty_col].min())*100:.2f} cm)")

    # --- Plots ---
    print("\n--- Time-series Plots ---")
    common_t, exp_ty, sim_ty = plot_pelvis_timeseries(df_exp, df_sim, out_dir,
                                                       label=label)

    if args.plots_only:
        print(f"\n  Done (plots only). Output: {out_dir}")
        return 0

    # --- Animation ---
    suffix = "_sameStart" if args.same_start else ""
    vid_label = label + suffix
    print(f"\n--- Overlay Animation (same_start={args.same_start}) ---")
    generate_com_overlay_video(df_exp, df_sim, common_t, exp_ty, sim_ty,
                                out_dir, label=vid_label,
                                fps=args.fps, n_loops=args.loops,
                                same_start=args.same_start)

    print(f"\n{'=' * 65}")
    print(f"  Done! Output: {out_dir}")
    print(f"{'=' * 65}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
