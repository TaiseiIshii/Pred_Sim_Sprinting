"""
compare_GRF_N50_vs_N100.py
N=50 と N=100 メッシュ解像度における地面反力（GRF）の比較

Compares ground reaction forces between N=50 and N=100 mesh resolution
simulations to assess mesh convergence.

Output:
  - GRF time-series comparison (vertical, horizontal, resultant)
  - Phase-normalized comparison (% gait cycle)
  - Peak/impulse statistics table
  - Difference metrics (RMSE, peak error, correlation)

Usage:
    python compare_GRF_N50_vs_N100.py
"""

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# ───────────────────────────────────────────────────────────────────────────
# Configuration
# ───────────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = PROJECT_ROOT / "Results"

# N=50 result (04-Feb-2026, total GRF in first 9 columns of full _GRF.mot)
GRF_N50_PATH = RESULTS_DIR / "pred_sprinting_04-February-2026__12-27-31___Nominal_GRF.mot"

# N=100 result (10-Apr-2026, _GRF_Single.mot has summed totals)
GRF_N100_PATH = RESULTS_DIR / "pred_sprinting_10-April-2026__16-29-40___Nominal_GRF_Single.mot"

BODY_MASS = 72.17  # kg (subject mass)
BW = BODY_MASS * 9.80665  # N

OUTPUT_DIR = RESULTS_DIR / "GRF_comparison_N50_N100"

# ───────────────────────────────────────────────────────────────────────────
# .mot reader
# ───────────────────────────────────────────────────────────────────────────

def read_mot(filepath):
    """Read an OpenSim .mot file and return (labels, data_array)."""
    filepath = Path(filepath)
    with open(filepath, "r", encoding="latin-1") as f:
        lines = f.readlines()

    header_idx = None
    for i, line in enumerate(lines):
        toks = line.strip().split()
        if len(toks) > 1 and toks[0].lower() == "time":
            header_idx = i
            break

    if header_idx is None:
        raise ValueError(f"Cannot find header in {filepath}")

    labels = lines[header_idx].strip().split("\t")
    labels = [l.strip() for l in labels if l.strip()]

    data_rows = []
    for line in lines[header_idx + 1:]:
        s = line.strip()
        if s and not s.startswith("#"):
            vals = s.split()
            if len(vals) >= len(labels):
                data_rows.append([float(v) for v in vals[:len(labels)]])

    data = np.array(data_rows)
    return labels, data


def extract_total_grf(labels, data, use_per_sphere_sum=False):
    """Extract time and total GRF components (vx, vy, vz) from .mot data.
    
    If use_per_sphere_sum=True, sums per-sphere columns instead of using
    the total columns (needed when total columns are incorrect).
    """
    time = data[:, labels.index("time")]

    if use_per_sphere_sum:
        # Sum all per-sphere force columns (N_ground_force_vx/vy/vz)
        per_vx_idx = [i for i, l in enumerate(labels)
                      if l.endswith("_ground_force_vx") and l != "ground_force_vx"]
        per_vy_idx = [i for i, l in enumerate(labels)
                      if l.endswith("_ground_force_vy") and l != "ground_force_vy"]
        per_vz_idx = [i for i, l in enumerate(labels)
                      if l.endswith("_ground_force_vz") and l != "ground_force_vz"]
        vx = np.sum(data[:, per_vx_idx], axis=1)
        vy = np.sum(data[:, per_vy_idx], axis=1)
        vz = np.sum(data[:, per_vz_idx], axis=1)
    else:
        vx = data[:, labels.index("ground_force_vx")]
        vy = data[:, labels.index("ground_force_vy")]
        vz = data[:, labels.index("ground_force_vz")]
    return time, vx, vy, vz


def detect_needs_per_sphere_sum(labels, data):
    """Detect if total GRF columns are incorrect by comparing with per-sphere sum."""
    per_vy_idx = [i for i, l in enumerate(labels)
                  if l.endswith("_ground_force_vy") and l != "ground_force_vy"]
    if not per_vy_idx:
        return False
    total_vy = data[:, labels.index("ground_force_vy")]
    per_vy_sum = np.sum(data[:, per_vy_idx], axis=1)
    # If per-sphere sum peak is >2x the total column peak, total is likely broken
    ratio = np.max(np.abs(per_vy_sum)) / max(np.max(np.abs(total_vy)), 1e-10)
    return ratio > 2.0


def normalize_sign(vy, vx, vz):
    """
    Ensure vertical GRF is positive (upward = push on body).
    Some files store action force (body-on-ground, vy negative for upward push),
    others store reaction force (ground-on-body, vy positive for upward push).
    """
    if np.max(np.abs(vy)) > 10:  # significant force present
        peak_idx = np.argmax(np.abs(vy))
        if vy[peak_idx] < 0:
            # action force convention → negate all to get reaction force
            return -vy, -vx, -vz
    return vy, vx, vz


# ───────────────────────────────────────────────────────────────────────────
# Statistics
# ───────────────────────────────────────────────────────────────────────────

def compute_comparison_stats(t50, v50, t100, v100, label=""):
    """Compute RMSE, correlation, peak difference on common time base."""
    t_start = max(t50[0], t100[0])
    t_end = min(t50[-1], t100[-1])
    t_common = np.linspace(t_start, t_end, 500)

    v50_i = np.interp(t_common, t50, v50)
    v100_i = np.interp(t_common, t100, v100)

    diff = v100_i - v50_i
    rmse = np.sqrt(np.mean(diff ** 2))
    max_diff = np.max(np.abs(diff))
    peak50 = np.max(np.abs(v50_i))
    peak100 = np.max(np.abs(v100_i))

    if np.std(v50_i) > 1e-10 and np.std(v100_i) > 1e-10:
        corr = np.corrcoef(v50_i, v100_i)[0, 1]
    else:
        corr = np.nan

    # Impulse (integral)
    dt = t_common[1] - t_common[0]
    impulse50 = np.trapezoid(v50_i, t_common)
    impulse100 = np.trapezoid(v100_i, t_common)

    return {
        "Component": label,
        "Peak_N50 (N)": f"{peak50:.1f}",
        "Peak_N100 (N)": f"{peak100:.1f}",
        "Peak_diff (%)": f"{abs(peak100 - peak50) / peak50 * 100:.2f}" if peak50 > 0 else "N/A",
        "RMSE (N)": f"{rmse:.2f}",
        "RMSE (BW)": f"{rmse / BW:.4f}",
        "MaxDiff (N)": f"{max_diff:.2f}",
        "Correlation": f"{corr:.6f}",
        "Impulse_N50 (Ns)": f"{impulse50:.3f}",
        "Impulse_N100 (Ns)": f"{impulse100:.3f}",
    }


# ───────────────────────────────────────────────────────────────────────────
# Plotting
# ───────────────────────────────────────────────────────────────────────────

def plot_grf_comparison(t50, vx50, vy50, vz50, t100, vx100, vy100, vz100):
    """Main GRF comparison figure: 3 components + resultant + difference."""
    fig = plt.figure(figsize=(16, 14))
    gs = GridSpec(4, 2, figure=fig, hspace=0.35, wspace=0.3)

    components = [
        ("Vertical GRF", vy50, vy100, "ground_force_vy"),
        ("Anterior-Posterior GRF", vx50, vx100, "ground_force_vx"),
        ("Medial-Lateral GRF", vz50, vz100, "ground_force_vz"),
    ]

    # Resultant
    res50 = np.sqrt(vx50**2 + vy50**2 + vz50**2)
    res100 = np.sqrt(vx100**2 + vy100**2 + vz100**2)

    for i, (title, c50, c100, _) in enumerate(components):
        ax = fig.add_subplot(gs[i, 0])
        ax.plot(t50, c50, color="#2979FF", linewidth=2, label="N=50")
        ax.plot(t100, c100, color="#FF5252", linewidth=2, linestyle="--", label="N=100")
        ax.set_ylabel("Force [N]", fontsize=10)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        if i == 0:
            # Add BW axis
            ax2 = ax.twinx()
            ax2.set_ylim(np.array(ax.get_ylim()) / BW)
            ax2.set_ylabel("Force [BW]", fontsize=10, color="gray")
            ax2.tick_params(axis="y", labelcolor="gray")

        # Difference subplot on right
        ax_diff = fig.add_subplot(gs[i, 1])
        t_start = max(t50[0], t100[0])
        t_end = min(t50[-1], t100[-1])
        t_common = np.linspace(t_start, t_end, 500)
        c50_i = np.interp(t_common, t50, c50)
        c100_i = np.interp(t_common, t100, c100)
        diff = c100_i - c50_i

        ax_diff.fill_between(t_common, diff, alpha=0.4, color="#9C27B0")
        ax_diff.plot(t_common, diff, color="#9C27B0", linewidth=1.5)
        ax_diff.axhline(0, color="gray", linewidth=0.8, linestyle=":")
        ax_diff.set_ylabel("Diff (N100−N50) [N]", fontsize=10)
        ax_diff.set_title(f"{title} — Difference", fontsize=11)
        ax_diff.grid(True, alpha=0.3)

        rmse = np.sqrt(np.mean(diff ** 2))
        ax_diff.annotate(f"RMSE: {rmse:.1f} N ({rmse/BW:.3f} BW)",
                         xy=(0.02, 0.95), xycoords="axes fraction",
                         fontsize=9, fontfamily="monospace",
                         bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.9),
                         verticalalignment="top")

    # Resultant row
    ax_res = fig.add_subplot(gs[3, 0])
    ax_res.plot(t50, res50, color="#2979FF", linewidth=2, label="N=50")
    ax_res.plot(t100, res100, color="#FF5252", linewidth=2, linestyle="--", label="N=100")
    ax_res.set_xlabel("Time [s]", fontsize=11)
    ax_res.set_ylabel("Force [N]", fontsize=10)
    ax_res.set_title("Resultant GRF", fontsize=12, fontweight="bold")
    ax_res.legend(fontsize=9)
    ax_res.grid(True, alpha=0.3)

    ax_res_diff = fig.add_subplot(gs[3, 1])
    t_common = np.linspace(max(t50[0], t100[0]), min(t50[-1], t100[-1]), 500)
    res50_i = np.interp(t_common, t50, res50)
    res100_i = np.interp(t_common, t100, res100)
    res_diff = res100_i - res50_i
    ax_res_diff.fill_between(t_common, res_diff, alpha=0.4, color="#9C27B0")
    ax_res_diff.plot(t_common, res_diff, color="#9C27B0", linewidth=1.5)
    ax_res_diff.axhline(0, color="gray", linewidth=0.8, linestyle=":")
    ax_res_diff.set_xlabel("Time [s]", fontsize=11)
    ax_res_diff.set_ylabel("Diff [N]", fontsize=10)
    ax_res_diff.set_title("Resultant GRF — Difference", fontsize=11)
    ax_res_diff.grid(True, alpha=0.3)

    fig.suptitle("GRF Comparison: N=50 vs N=100 Mesh Resolution\n(Mesh Convergence Analysis)",
                 fontsize=15, fontweight="bold", y=0.98)

    return fig


def plot_phase_normalized(t50, vx50, vy50, vz50, t100, vx100, vy100, vz100):
    """Phase-normalized comparison (0-100% gait cycle)."""
    phase50 = np.linspace(0, 100, len(t50))
    phase100 = np.linspace(0, 100, len(t100))

    phase_common = np.linspace(0, 100, 200)

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True,
                             gridspec_kw={"hspace": 0.15})

    components = [
        ("Vertical GRF", vy50, vy100),
        ("Anterior-Posterior GRF", vx50, vx100),
        ("Medial-Lateral GRF", vz50, vz100),
    ]

    for i, (title, c50, c100) in enumerate(components):
        ax = axes[i]
        c50_i = np.interp(phase_common, phase50, c50)
        c100_i = np.interp(phase_common, phase100, c100)

        ax.plot(phase_common, c50_i / BW, color="#2979FF", linewidth=2.5, label="N=50")
        ax.plot(phase_common, c100_i / BW, color="#FF5252", linewidth=2.5, linestyle="--", label="N=100")
        ax.fill_between(phase_common, c50_i / BW, c100_i / BW,
                        alpha=0.15, color="gray")

        ax.set_ylabel(f"{title} [BW]", fontsize=11)
        ax.legend(fontsize=10, loc="best")
        ax.grid(True, alpha=0.3)

        if i == 0:
            ax.set_title("Phase-Normalized GRF: N=50 vs N=100", fontsize=14, fontweight="bold")

    axes[-1].set_xlabel("Gait Cycle [%]", fontsize=12)

    plt.tight_layout()
    return fig


def plot_peak_comparison_bar(stats_list):
    """Bar chart comparing peak values."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    labels = ["Vertical", "Anter-Post", "Med-Lat"]
    peaks_50 = [float(s["Peak_N50 (N)"]) for s in stats_list[:3]]
    peaks_100 = [float(s["Peak_N100 (N)"]) for s in stats_list[:3]]

    x = np.arange(len(labels))
    width = 0.35

    axes[0].bar(x - width / 2, peaks_50, width, label="N=50", color="#2979FF", alpha=0.8)
    axes[0].bar(x + width / 2, peaks_100, width, label="N=100", color="#FF5252", alpha=0.8)
    axes[0].set_ylabel("Peak Force [N]", fontsize=11)
    axes[0].set_title("Peak GRF Comparison", fontsize=12, fontweight="bold")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3, axis="y")

    # Peak in BW
    axes[1].bar(x - width / 2, [p / BW for p in peaks_50], width, label="N=50", color="#2979FF", alpha=0.8)
    axes[1].bar(x + width / 2, [p / BW for p in peaks_100], width, label="N=100", color="#FF5252", alpha=0.8)
    axes[1].set_ylabel("Peak Force [BW]", fontsize=11)
    axes[1].set_title("Peak GRF (Body Weight)", fontsize=12, fontweight="bold")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis="y")

    # RMSE
    rmse_vals = [float(s["RMSE (N)"]) for s in stats_list[:3]]
    axes[2].bar(labels, rmse_vals, color="#9C27B0", alpha=0.8)
    axes[2].set_ylabel("RMSE [N]", fontsize=11)
    axes[2].set_title("RMSE (N=100 vs N=50)", fontsize=12, fontweight="bold")
    axes[2].grid(True, alpha=0.3, axis="y")

    for ax_idx, ax in enumerate(axes[:2]):
        for j, (v50, v100) in enumerate(zip(
            [peaks_50, [p / BW for p in peaks_50]][ax_idx],
            [peaks_100, [p / BW for p in peaks_100]][ax_idx]
        )):
            pass  # skip annotation clutter

    plt.tight_layout()
    fig.suptitle("", y=1.02)
    return fig


# ───────────────────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("GRF Comparison: N=50 vs N=100 (Mesh Convergence)")
    print("=" * 60)

    # Load data
    print(f"\nLoading N=50 GRF: {GRF_N50_PATH.name}")
    labels50, data50 = read_mot(GRF_N50_PATH)
    needs_sum = detect_needs_per_sphere_sum(labels50, data50)
    if needs_sum:
        print("  [!] Total GRF columns appear incorrect — using per-sphere sum")
    t50, vx50, vy50, vz50 = extract_total_grf(labels50, data50, use_per_sphere_sum=needs_sum)
    print(f"  Time: {t50[0]:.4f} - {t50[-1]:.4f} s, {len(t50)} points")

    print(f"\nLoading N=100 GRF: {GRF_N100_PATH.name}")
    labels100, data100 = read_mot(GRF_N100_PATH)
    t100, vx100, vy100, vz100 = extract_total_grf(labels100, data100)
    print(f"  Time: {t100[0]:.4f} - {t100[-1]:.4f} s, {len(t100)} points")

    # Normalize sign conventions (both should have positive vertical = upward)
    vy50, vx50, vz50 = normalize_sign(vy50, vx50, vz50)
    vy100, vx100, vz100 = normalize_sign(vy100, vx100, vz100)

    print(f"\n  N=50  peak vertical GRF: {np.max(vy50):.1f} N ({np.max(vy50)/BW:.2f} BW)")
    print(f"  N=100 peak vertical GRF: {np.max(vy100):.1f} N ({np.max(vy100)/BW:.2f} BW)")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Compute statistics
    stats = []
    stats.append(compute_comparison_stats(t50, vy50, t100, vy100, "Vertical (vy)"))
    stats.append(compute_comparison_stats(t50, vx50, t100, vx100, "Anterior-Posterior (vx)"))
    stats.append(compute_comparison_stats(t50, vz50, t100, vz100, "Medial-Lateral (vz)"))

    res50 = np.sqrt(vx50**2 + vy50**2 + vz50**2)
    res100 = np.sqrt(vx100**2 + vy100**2 + vz100**2)
    stats.append(compute_comparison_stats(t50, res50, t100, res100, "Resultant"))

    # Print statistics
    print("\n" + "=" * 60)
    print("Comparison Statistics")
    print("=" * 60)
    stats_df = pd.DataFrame(stats)
    print(stats_df.to_string(index=False))

    # Save statistics
    csv_path = OUTPUT_DIR / "GRF_comparison_stats.csv"
    stats_df.to_csv(csv_path, index=False)
    print(f"\n  [OK] Stats saved: {csv_path.name}")

    # Plot 1: Time-series comparison
    fig1 = plot_grf_comparison(t50, vx50, vy50, vz50, t100, vx100, vy100, vz100)
    p1 = OUTPUT_DIR / "GRF_timeseries_N50_vs_N100.png"
    fig1.savefig(str(p1), dpi=200, bbox_inches="tight")
    plt.close(fig1)
    print(f"  [OK] {p1.name}")

    # Plot 2: Phase-normalized
    fig2 = plot_phase_normalized(t50, vx50, vy50, vz50, t100, vx100, vy100, vz100)
    p2 = OUTPUT_DIR / "GRF_phase_normalized_N50_vs_N100.png"
    fig2.savefig(str(p2), dpi=200, bbox_inches="tight")
    plt.close(fig2)
    print(f"  [OK] {p2.name}")

    # Plot 3: Peak bar chart
    fig3 = plot_peak_comparison_bar(stats)
    p3 = OUTPUT_DIR / "GRF_peak_comparison_N50_vs_N100.png"
    fig3.savefig(str(p3), dpi=200, bbox_inches="tight")
    plt.close(fig3)
    print(f"  [OK] {p3.name}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Body mass: {BODY_MASS} kg, 1 BW = {BW:.2f} N")
    print(f"  N=50:  {len(t50)} time points, dt_avg = {np.mean(np.diff(t50))*1000:.3f} ms")
    print(f"  N=100: {len(t100)} time points, dt_avg = {np.mean(np.diff(t100))*1000:.3f} ms")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"\n  Vertical GRF RMSE: {stats[0]['RMSE (N)']} N ({stats[0]['RMSE (BW)']} BW)")
    print(f"  Vertical GRF peak diff: {stats[0]['Peak_diff (%)']}%")
    print(f"  Vertical GRF correlation: {stats[0]['Correlation']}")
    print()


if __name__ == "__main__":
    main()
