"""
prepare_opensim_comparison.py
OpenSim GUIで動作比較するためのファイルを準備するスクリプト

主な機能:
  1) 実験IK と シミュレーション結果 の .mot ファイルを
     OpenSim GUIで読み込みやすい「簡易カラム名」形式に変換
  2) pelvis_tz をオフセットして2体を並べて表示できるペアファイル生成

Usage:
    python prepare_opensim_comparison.py
    python prepare_opensim_comparison.py --sim_label Nominal --offset 0.6
"""

import argparse
import re
from pathlib import Path
import numpy as np


def read_mot_raw(filepath):
    """Read .mot file and return header lines, column names, data array."""
    filepath = Path(filepath)
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    header_lines = []
    data_start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("time") or stripped.startswith("/jointset"):
            data_start = i
            break
        header_lines.append(line)

    if data_start is None:
        raise ValueError(f"Cannot find header in {filepath}")

    col_line = lines[data_start].strip()
    columns = [c.strip() for c in col_line.split("\t") if c.strip()]

    data_rows = []
    for line in lines[data_start + 1:]:
        s = line.strip()
        if s and not s.startswith("#"):
            vals = s.split()
            if len(vals) == len(columns):
                data_rows.append([float(v) for v in vals])

    return header_lines, columns, np.array(data_rows)


def simplify_column_name(col):
    """
    /jointset/ground_pelvis/pelvis_tilt/value -> pelvis_tilt
    /jointset/hip_r/hip_flexion_r/value       -> hip_flexion_r
    """
    if col == "time":
        return "time"
    parts = col.strip("/").split("/")
    if len(parts) >= 3:
        return parts[-2]  # e.g., pelvis_tilt, hip_flexion_r
    return col


def write_mot(filepath, columns, data, name="motion"):
    """Write OpenSim .mot file with standard header."""
    filepath = Path(filepath)
    n_rows, n_cols = data.shape

    t_min = data[0, 0]
    t_max = data[-1, 0]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"{name}\n")
        f.write("version=1\n")
        f.write(f"nRows={n_rows}\n")
        f.write(f"nColumns={n_cols}\n")
        f.write("inDegrees=yes\n")
        f.write(f"range {t_min:.6f} {t_max:.6f}\n")
        f.write("endheader\n")
        f.write("\t".join(columns) + "\n")
        for row in data:
            f.write("\t".join(f"{v:.8f}" for v in row) + "\n")


def find_column_index(columns, name):
    """Find column index by simplified name."""
    for i, col in enumerate(columns):
        if simplify_column_name(col) == name:
            return i
    return None


def main():
    parser = argparse.ArgumentParser(
        description="OpenSim GUI comparison file preparation")
    parser.add_argument("--sim_label", type=str, default="Nominal")
    parser.add_argument("--offset", type=float, default=0.6,
                        help="Z-axis offset for side-by-side display (meters)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    out_dir = project_root / "Results" / "opensim_gui_comparison"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Find files ──
    ik_dir = project_root / "MainFunctions" / "ExperimentalData" / "IK_Splined"
    ik_files = sorted(ik_dir.glob("*.mot"))
    if not ik_files:
        print("ERROR: No IK .mot files found")
        return 1
    ik_path = ik_files[0]

    results_dir = project_root / "Results"
    sim_files = sorted(results_dir.glob("pred_sprinting_coords_*.mot"))
    sim_files = [f for f in sim_files
                 if args.sim_label.lower() in f.name.lower()]
    if not sim_files:
        print("ERROR: No simulation .mot files found")
        return 1
    sim_path = sim_files[0]

    print("=" * 60)
    print("  OpenSim GUI Comparison File Preparation")
    print("=" * 60)
    print(f"\n  Experimental IK: {ik_path.name}")
    print(f"  Simulation:      {sim_path.name}")
    print(f"  Z offset:        {args.offset} m")

    # ── Read data ──
    _, ik_cols, ik_data = read_mot_raw(ik_path)
    _, sim_cols, sim_data = read_mot_raw(sim_path)

    # ── Simplify column names ──
    ik_simple = [simplify_column_name(c) for c in ik_cols]
    sim_simple = [simplify_column_name(c) for c in sim_cols]

    # ── 1) Write simplified .mot files (no offset) ──
    exp_out = out_dir / "experimental_ik.mot"
    write_mot(exp_out, ik_simple, ik_data, name="Experimental_IK")
    print(f"\n  [1] Experimental .mot: {exp_out.name}")

    sim_out = out_dir / f"simulation_{args.sim_label}.mot"
    write_mot(sim_out, sim_simple, sim_data, name=f"Simulation_{args.sim_label}")
    print(f"  [2] Simulation .mot:   {sim_out.name}")

    # ── 2) Write offset versions for side-by-side ──
    tz_idx_ik = find_column_index(ik_cols, "pelvis_tz")
    tz_idx_sim = find_column_index(sim_cols, "pelvis_tz")

    if tz_idx_ik is not None:
        ik_offset_data = ik_data.copy()
        ik_offset_data[:, tz_idx_ik] += args.offset / 2
        exp_offset_out = out_dir / "experimental_ik_offset.mot"
        write_mot(exp_offset_out, ik_simple, ik_offset_data,
                  name="Experimental_IK_Offset")
        print(f"  [3] Exp offset .mot:   {exp_offset_out.name}  "
              f"(pelvis_tz +{args.offset/2:.2f})")

    if tz_idx_sim is not None:
        sim_offset_data = sim_data.copy()
        sim_offset_data[:, tz_idx_sim] -= args.offset / 2
        sim_offset_out = out_dir / f"simulation_{args.sim_label}_offset.mot"
        write_mot(sim_offset_out, sim_simple, sim_offset_data,
                  name=f"Simulation_{args.sim_label}_Offset")
        print(f"  [4] Sim offset .mot:   {sim_offset_out.name}  "
              f"(pelvis_tz -{args.offset/2:.2f})")

    # ── 3) Trim to common time range ──
    t_start = max(ik_data[0, 0], sim_data[0, 0])
    t_end = min(ik_data[-1, 0], sim_data[-1, 0])

    # Resample both to the same time vector
    n_points = 200
    common_time = np.linspace(t_start, t_end, n_points)

    def interpolate_to_common(data, columns):
        """Interpolate data to common time vector."""
        result = np.zeros((n_points, data.shape[1]))
        result[:, 0] = common_time
        for j in range(1, data.shape[1]):
            result[:, j] = np.interp(common_time, data[:, 0], data[:, j])
        return result

    ik_resampled = interpolate_to_common(ik_data, ik_cols)
    sim_resampled = interpolate_to_common(sim_data, sim_cols)

    # Write time-matched versions
    exp_sync = out_dir / "experimental_ik_synced.mot"
    write_mot(exp_sync, ik_simple, ik_resampled, name="Experimental_IK_Synced")

    sim_sync = out_dir / f"simulation_{args.sim_label}_synced.mot"
    write_mot(sim_sync, sim_simple, sim_resampled,
              name=f"Simulation_{args.sim_label}_Synced")

    print(f"\n  [5] Time-synced Exp:   {exp_sync.name}")
    print(f"  [6] Time-synced Sim:   {sim_sync.name}")
    print(f"      Common time range: {t_start:.4f} - {t_end:.4f} s "
          f"({n_points} points)")

    # == Print Instructions ==
    print(f"""
{'='*60}
  Files generated in: {out_dir}
{'='*60}

  ===== OpenSim GUI Comparison Instructions =====

  --- Method A: Same model, switch between motions ---
  1. File > Open Model >
     OpenSimModel\\Scaled_FullBody_HamnerModel_Muscle_withContact.osim
  2. File > Load Motion > experimental_ik_synced.mot
  3. File > Load Motion > simulation_{args.sim_label}_synced.mot
  4. Use the Motions dropdown (toolbar) to switch between them
  5. Move the time slider to compare postures at the same time

  --- Method B: Two models side-by-side (RECOMMENDED) ---
  1. File > Open Model > ...osim  (1st instance)
  2. In Navigator: select this model
  3. File > Load Motion > experimental_ik_offset.mot
  4. File > Open Model > ...osim  (2nd instance - will get a suffix)
  5. In Navigator: select the 2nd model
  6. File > Load Motion > simulation_{args.sim_label}_offset.mot
  7. Both models appear Z-offset ({args.offset}m apart) in the 3D view
  8. Move time slider - both motions advance together

  --- Method C: Tools > Plot for quantitative comparison ---
  1. Load model + both synced motions
  2. Tools > Plot
  3. Select coordinate (e.g., hip_flexion_r) on Y-axis
  4. Select "time" on X-axis
  5. Add curves from both motions to compare

  TIP: If motions don't advance together, make sure both
  motions are "Current" (check the Motions panel, bold = current).
  Click on a motion name to make it current.
""")

    return 0


if __name__ == "__main__":
    main()
