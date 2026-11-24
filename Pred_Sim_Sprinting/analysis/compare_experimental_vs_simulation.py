"""
compare_experimental_vs_simulation.py
最適化前の実験データ（IK）と最適化後のシミュレーションデータのフォーム比較

This script loads:
  - Experimental IK data  (ExperimentalData/IK_Splined/*.mot)
  - Simulation coords      (Results/pred_sprinting_coords_*.mot)
and produces overlay plots of joint angles, RMSE statistics, and
optional stick-figure snapshots.

Usage:
    python compare_experimental_vs_simulation.py
    python compare_experimental_vs_simulation.py --sim_label Nominal
    python compare_experimental_vs_simulation.py --list   # show available sim files

Date: 2026-03-24
"""

import argparse
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend so it works headless
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# ---------------------------------------------------------------------------
# .mot file reader
# ---------------------------------------------------------------------------

def read_mot(filepath: str | Path) -> pd.DataFrame:
    """Read an OpenSim .mot file and return a pandas DataFrame."""
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
        raise ValueError(f"Cannot find header row in {filepath}")

    headers = lines[header_idx].strip().split("\t")
    headers = [h.strip() for h in headers if h.strip()]

    data_rows = []
    for line in lines[header_idx + 1:]:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            vals = stripped.split()
            if len(vals) == len(headers):
                data_rows.append([float(v) for v in vals])

    df = pd.DataFrame(data_rows, columns=headers)
    return df


def simplify_column(col: str) -> str:
    """'/jointset/hip_r/hip_flexion_r/value' -> 'hip_flexion_r'"""
    parts = col.strip("/").split("/")
    # OpenSim convention: .../joint_name/coord_name/value
    if len(parts) >= 3:
        return parts[-2]  # the coordinate name
    return col


# ---------------------------------------------------------------------------
# Joint grouping for tidy subplots
# ---------------------------------------------------------------------------

JOINT_GROUPS = {
    "Pelvis": [
        "pelvis_tilt", "pelvis_list", "pelvis_rotation",
        "pelvis_tx", "pelvis_ty", "pelvis_tz",
    ],
    "Hip (R)": [
        "hip_flexion_r", "hip_adduction_r", "hip_rotation_r",
    ],
    "Knee & Ankle (R)": [
        "knee_angle_r", "ankle_angle_r", "subtalar_angle_r", "mtp_angle_r",
    ],
    "Hip (L)": [
        "hip_flexion_l", "hip_adduction_l", "hip_rotation_l",
    ],
    "Knee & Ankle (L)": [
        "knee_angle_l", "ankle_angle_l", "subtalar_angle_l", "mtp_angle_l",
    ],
    "Trunk": [
        "lumbar_extension", "lumbar_bending", "lumbar_rotation",
    ],
    "Arm (R)": [
        "arm_flex_r", "arm_add_r", "arm_rot_r",
        "elbow_flex_r", "pro_sup_r", "wrist_flex_r", "wrist_dev_r",
    ],
    "Arm (L)": [
        "arm_flex_l", "arm_add_l", "arm_rot_l",
        "elbow_flex_l", "pro_sup_l", "wrist_flex_l", "wrist_dev_l",
    ],
}

# Key joints to always highlight in the summary plot
KEY_JOINTS = [
    "hip_flexion_r", "knee_angle_r", "ankle_angle_r",
    "hip_flexion_l", "knee_angle_l", "ankle_angle_l",
    "pelvis_tilt", "pelvis_ty", "lumbar_extension",
]


# ---------------------------------------------------------------------------
# Interpolation helper (resample to common time base)
# ---------------------------------------------------------------------------

def resample_to_common_time(df_exp: pd.DataFrame, df_sim: pd.DataFrame):
    """
    Resample both DataFrames onto a common time grid (using the overlapping
    time range) so they can be compared element-wise.
    Returns (time, exp_resampled, sim_resampled).
    """
    t_exp = df_exp["time"].values
    t_sim = df_sim["time"].values

    t_start = max(t_exp[0], t_sim[0])
    t_end = min(t_exp[-1], t_sim[-1])

    n_pts = 200
    t_common = np.linspace(t_start, t_end, n_pts)

    # Build column mapping: simplified name -> original column for each DF
    exp_map = {simplify_column(c): c for c in df_exp.columns if c != "time"}
    sim_map = {simplify_column(c): c for c in df_sim.columns if c != "time"}
    common_joints = sorted(set(exp_map.keys()) & set(sim_map.keys()))

    exp_resampled = pd.DataFrame({"time": t_common})
    sim_resampled = pd.DataFrame({"time": t_common})

    for joint in common_joints:
        exp_resampled[joint] = np.interp(t_common, t_exp, df_exp[exp_map[joint]].values)
        sim_resampled[joint] = np.interp(t_common, t_sim, df_sim[sim_map[joint]].values)

    return t_common, exp_resampled, sim_resampled, common_joints


# ---------------------------------------------------------------------------
# RMSE / statistics
# ---------------------------------------------------------------------------

def compute_rmse(exp_vals: np.ndarray, sim_vals: np.ndarray) -> float:
    return float(np.sqrt(np.mean((exp_vals - sim_vals) ** 2)))


def compute_statistics(t, exp_df, sim_df, joints):
    """Return a DataFrame with RMSE, max error, correlation for each joint."""
    rows = []
    for j in joints:
        e = exp_df[j].values
        s = sim_df[j].values
        rmse = compute_rmse(e, s)
        max_err = float(np.max(np.abs(e - s)))
        corr = float(np.corrcoef(e, s)[0, 1]) if np.std(e) > 1e-10 and np.std(s) > 1e-10 else np.nan
        rows.append({"joint": j, "RMSE_deg": rmse, "MaxError_deg": max_err, "Correlation": corr})
    return pd.DataFrame(rows).sort_values("RMSE_deg", ascending=False)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_joint_group(ax, t, exp_vals, sim_vals, joint_name, ylabel="Angle [deg]"):
    """Plot a single joint comparison on given axes."""
    ax.plot(t, exp_vals, "b-", linewidth=1.5, label="実験データ (IK)")
    ax.plot(t, sim_vals, "r--", linewidth=1.5, label="シミュレーション")

    # shade difference
    ax.fill_between(t, exp_vals, sim_vals, alpha=0.15, color="gray")

    ax.set_title(joint_name, fontsize=10, fontweight="bold")
    ax.set_xlabel("Time [s]", fontsize=8)
    ax.set_ylabel(ylabel, fontsize=8)
    ax.tick_params(labelsize=7)
    ax.grid(True, alpha=0.3)


def create_summary_plot(t, exp_df, sim_df, key_joints, title_suffix=""):
    """Create a summary figure with key joints overlaid."""
    available = [j for j in key_joints if j in exp_df.columns]
    n = len(available)
    ncols = 3
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 4 * nrows))
    axes = np.atleast_2d(axes).flatten()

    for idx, joint in enumerate(available):
        plot_joint_group(axes[idx], t, exp_df[joint].values, sim_df[joint].values, joint)

    # single legend at top
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, fontsize=11, frameon=True)

    for idx in range(len(available), len(axes)):
        axes[idx].set_visible(False)

    fig.suptitle(f"実験 vs シミュレーション: 主要関節角度 {title_suffix}",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    return fig


def create_all_joints_pdf(t, exp_df, sim_df, common_joints, pdf_path, title_suffix=""):
    """Write a multi-page PDF with all joint groups."""
    with PdfPages(pdf_path) as pdf:
        for group_name, group_joints in JOINT_GROUPS.items():
            available = [j for j in group_joints if j in common_joints]
            if not available:
                continue

            n = len(available)
            ncols = min(n, 3)
            nrows = int(np.ceil(n / ncols))
            fig, axes = plt.subplots(nrows, ncols, figsize=(5.5 * ncols, 4 * nrows))
            axes = np.atleast_2d(axes).flatten()

            for idx, joint in enumerate(available):
                ylabel = "Position [m]" if joint in ("pelvis_tx", "pelvis_ty", "pelvis_tz") else "Angle [deg]"
                plot_joint_group(axes[idx], t, exp_df[joint].values, sim_df[joint].values, joint, ylabel=ylabel)

            for idx in range(len(available), len(axes)):
                axes[idx].set_visible(False)

            handles, labels = axes[0].get_legend_handles_labels()
            fig.legend(handles, labels, loc="upper center", ncol=2, fontsize=10, frameon=True)
            fig.suptitle(f"{group_name} {title_suffix}", fontsize=13, fontweight="bold", y=1.01)
            fig.tight_layout()
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)

    print(f"  [OK] 全関節PDFを保存: {pdf_path}")


def create_rmse_bar_chart(stats_df, output_path, title_suffix=""):
    """Horizontal bar chart of RMSE per joint."""
    fig, ax = plt.subplots(figsize=(10, max(6, len(stats_df) * 0.35)))
    colors = ["#d62728" if j in KEY_JOINTS else "#1f77b4" for j in stats_df["joint"]]
    ax.barh(stats_df["joint"], stats_df["RMSE_deg"], color=colors, edgecolor="white")
    ax.set_xlabel("RMSE [deg]", fontsize=11)
    ax.set_title(f"関節角度 RMSE: 実験 vs シミュレーション {title_suffix}",
                 fontsize=13, fontweight="bold")
    ax.invert_yaxis()
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] RMSE棒グラフを保存: {output_path}")


def create_difference_heatmap(t, exp_df, sim_df, common_joints, output_path, title_suffix=""):
    """Heatmap of angular difference (exp - sim) over time for all joints."""
    diff_matrix = np.zeros((len(common_joints), len(t)))
    for i, j in enumerate(common_joints):
        diff_matrix[i, :] = exp_df[j].values - sim_df[j].values

    fig, ax = plt.subplots(figsize=(14, max(6, len(common_joints) * 0.3)))
    cmap = plt.cm.RdBu_r
    vmax = np.percentile(np.abs(diff_matrix), 95)
    im = ax.imshow(diff_matrix, aspect="auto", cmap=cmap, vmin=-vmax, vmax=vmax,
                   extent=[t[0], t[-1], len(common_joints) - 0.5, -0.5])
    ax.set_yticks(range(len(common_joints)))
    ax.set_yticklabels(common_joints, fontsize=7)
    ax.set_xlabel("Time [s]", fontsize=11)
    ax.set_title(f"角度差 (実験 − シミュレーション) ヒートマップ {title_suffix}",
                 fontsize=13, fontweight="bold")
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Difference [deg]", fontsize=10)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] ヒートマップを保存: {output_path}")


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def find_experimental_ik(project_root: Path) -> Path:
    """Return path to the splined IK .mot file."""
    ik_dir = project_root / "MainFunctions" / "ExperimentalData" / "IK_Splined"
    candidates = list(ik_dir.glob("*.mot"))
    if not candidates:
        raise FileNotFoundError(f"IK Splined .mot file not found in {ik_dir}")
    return candidates[0]


def find_simulation_coords(project_root: Path, label: str | None = None) -> list[Path]:
    """Return list of simulation coords .mot files, optionally filtered by label."""
    results_dir = project_root / "Results"
    all_coords = sorted(results_dir.glob("pred_sprinting_coords_*.mot"))
    if label:
        filtered = [p for p in all_coords if label.lower() in p.name.lower()]
        return filtered if filtered else all_coords
    return all_coords


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="実験データとシミュレーション結果のフォーム比較")
    parser.add_argument("--sim_label", type=str, default=None,
                        help="シミュレーションファイルをフィルタするラベル (例: Nominal, HTD_Plus_4)")
    parser.add_argument("--list", action="store_true",
                        help="利用可能なシミュレーション結果一覧を表示")
    parser.add_argument("--output_dir", type=str, default=None,
                        help="出力ディレクトリ (デフォルト: Results/comparison_plots)")
    args = parser.parse_args()

    # Locate project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir  # script is in project root

    # Japanese-compatible font (use default if not available)
    try:
        import matplotlib.font_manager as fm
        jp_fonts = [f.name for f in fm.fontManager.ttflist
                    if "Gothic" in f.name or "Meiryo" in f.name or "Hiragino" in f.name]
        if jp_fonts:
            plt.rcParams["font.family"] = jp_fonts[0]
        else:
            plt.rcParams["font.family"] = "sans-serif"
    except Exception:
        pass

    print("=" * 60)
    print("  実験データ vs シミュレーション フォーム比較ツール")
    print("=" * 60)

    # List mode
    sim_files = find_simulation_coords(project_root, args.sim_label)
    if args.list:
        print(f"\n利用可能なシミュレーション結果 ({len(sim_files)} 件):")
        for f in sim_files:
            print(f"  - {f.name}")
        return 0

    # Load experimental data
    exp_path = find_experimental_ik(project_root)
    print(f"\n[実験データ]    {exp_path.name}")
    df_exp = read_mot(exp_path)
    print(f"  時間範囲: {df_exp['time'].iloc[0]:.4f} - {df_exp['time'].iloc[-1]:.4f} s")
    print(f"  データ点数: {len(df_exp)}")

    if not sim_files:
        print("ERROR: シミュレーション結果が見つかりません")
        return 1

    # Output directory
    out_dir = Path(args.output_dir) if args.output_dir else project_root / "Results" / "comparison_plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Process each simulation file
    for sim_path in sim_files:
        # Extract label from filename
        match = re.search(r"___(.+)\.mot$", sim_path.name)
        label = match.group(1) if match else sim_path.stem
        label_clean = label.replace(" ", "_")

        print(f"\n{'─' * 50}")
        print(f"[シミュレーション] {sim_path.name}")
        df_sim = read_mot(sim_path)
        print(f"  時間範囲: {df_sim['time'].iloc[0]:.4f} - {df_sim['time'].iloc[-1]:.4f} s")
        print(f"  データ点数: {len(df_sim)}")

        # Resample to common time
        t, exp_r, sim_r, common_joints = resample_to_common_time(df_exp, df_sim)
        print(f"  共通関節数: {len(common_joints)}")
        print(f"  共通時間範囲: {t[0]:.4f} - {t[-1]:.4f} s")

        # 1) Summary plot (key joints)
        fig = create_summary_plot(t, exp_r, sim_r, KEY_JOINTS, title_suffix=f"[{label}]")
        summary_path = out_dir / f"summary_{label_clean}.png"
        fig.savefig(summary_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  [OK] サマリープロットを保存: {summary_path}")

        # 2) All-joints PDF
        pdf_path = out_dir / f"all_joints_{label_clean}.pdf"
        create_all_joints_pdf(t, exp_r, sim_r, common_joints, pdf_path,
                              title_suffix=f"[{label}]")

        # 3) Statistics
        stats = compute_statistics(t, exp_r, sim_r, common_joints)
        stats_path = out_dir / f"rmse_stats_{label_clean}.csv"
        stats.to_csv(stats_path, index=False, encoding="utf-8-sig")
        print(f"  [OK] RMSE統計をCSV保存: {stats_path}")

        # Print top-10 worst joints
        print(f"\n  RMSE上位10関節 [{label}]:")
        for _, row in stats.head(10).iterrows():
            print(f"    {row['joint']:25s}  RMSE={row['RMSE_deg']:7.2f}°  "
                  f"MaxErr={row['MaxError_deg']:7.2f}°  r={row['Correlation']:.3f}")

        # 4) RMSE bar chart
        bar_path = out_dir / f"rmse_bar_{label_clean}.png"
        create_rmse_bar_chart(stats, bar_path, title_suffix=f"[{label}]")

        # 5) Difference heatmap
        heatmap_path = out_dir / f"diff_heatmap_{label_clean}.png"
        create_difference_heatmap(t, exp_r, sim_r, common_joints, heatmap_path,
                                  title_suffix=f"[{label}]")

    print(f"\n{'=' * 60}")
    print(f"  完了! 出力先: {out_dir}")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
