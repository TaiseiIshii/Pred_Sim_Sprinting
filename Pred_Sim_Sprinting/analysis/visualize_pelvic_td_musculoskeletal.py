"""
visualize_pelvic_td_musculoskeletal.py
v3 (TDPT) の「リッチ」3D筋骨格可視化。実 OpenSim 骨メッシュ（posed）＋ wrapping
込みの筋経路を pyvista で描き、ハム4筋を正規化筋線維長 lMtilde で着色する。

v2 版 visualize_pelvic_shift_musculoskeletal.py の描画エンジン（骨/筋/凡例/足跡/
カメラ/MP4 書き出し）を **そのまま再利用**し、TDPT の条件・キャッシュ・出力名だけ
差し替える薄いラッパ。先に `compute_osim_muscle_paths_td.py`（opensim 対応 env）で
Results/PelvicTD_Study/_muscle_cache.pkl を作っておくこと。

実行（conda base python: pyvista/vtk/imageio_ffmpeg が必要）:
  python analysis/visualize_pelvic_td_musculoskeletal.py
  python analysis/visualize_pelvic_td_musculoskeletal.py --only side --skip_video
"""
import argparse
import glob
import os
import pickle
from pathlib import Path

import numpy as np
from scipy.io import loadmat

from visualize_pelvic_shift_musculoskeletal import (
    render_sidebyside_frame,
    render_overlay_frame,
    write_mp4,
    write_hero_still,
    load_hamstring_strain,
    foot_trace_pts,
    _peak_ham_strain,
    setup_japanese_font,
)
from visualize_form_comparison_v2 import find_geometry_dir, load_body_meshes

# (offset_deg, cache_ident, ASCII label) — 代表3条件
CONDITION_SPECS = [
    (-8, "PelvisTDwide_m8", "strong anterior"),
    (0,  "PelvisTDwide_p0", "nominal"),
    (6,  "PelvisTD_p6",     "near-neutral"),
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
    fs = sorted(glob.glob(os.path.join(str(results_dir),
                f"pred_sprinting_data_*{ident}.mat")), key=os.path.getmtime,
                reverse=True)
    for p in fs:
        if _mat_N(p) == target_n:
            return p
    return fs[0] if fs else None


def load_speeds(study_dir):
    """pelvic_td_summary.csv から offset->speed を読む。"""
    import csv
    out = {}
    p = Path(study_dir) / "pelvic_td_summary.csv"
    if not p.exists():
        return out
    with open(p, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            try:
                out[int(round(float(row["offset"])))] = float(row["speed"])
            except (KeyError, ValueError):
                pass
    return out


def load_conditions(results_dir, cache, study_dir):
    speeds = load_speeds(study_dir)
    conds = []
    for off, ident, lab in CONDITION_SPECS:
        if ident not in cache:
            print(f"  [WARN] cache に {ident} なし。スキップ")
            continue
        mat = pick_mat(results_dir, ident)
        if not mat:
            print(f"  [WARN] {ident} の .mat なし。スキップ")
            continue
        entry = cache[ident]
        strain = load_hamstring_strain(mat)
        td = float(entry.get("td_tilt", entry["mean_tilt"]))
        conds.append({
            "offset": off,
            "label": f"TD {td:+.1f}deg ({lab})",
            "mean_tilt": entry["mean_tilt"],
            "cache": entry, "strain": strain,
            "foot_trace": foot_trace_pts(entry),
            "peak_strain": _peak_ham_strain(strain),
            "speed": speeds.get(off),
        })
        print(f"  [OK] {ident:18s} TD {td:6.2f} deg, {len(entry['phases'])} frames")
    return conds


def main():
    ap = argparse.ArgumentParser(description="v3(TDPT) リッチ筋骨格可視化")
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--cycles", type=int, default=2)
    ap.add_argument("--width", type=int, default=1680)
    ap.add_argument("--height", type=int, default=950)
    ap.add_argument("--skip_video", action="store_true")
    ap.add_argument("--only", choices=["both", "side", "overlay"], default="both")
    args = ap.parse_args()

    setup_japanese_font()
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "Results"
    out_dir = results_dir / "PelvicTD_Study"
    cache_path = out_dir / "_muscle_cache.pkl"

    print("=" * 70)
    print("  v3(TDPT) × リッチ筋骨格可視化 (wrapping込み筋経路)")
    print("=" * 70)
    if not cache_path.exists():
        print(f"ERROR: 筋経路キャッシュが見つかりません: {cache_path}")
        print("  先に opensim 対応 env で compute_osim_muscle_paths_td.py を実行:")
        print("  & '<opencap>\\python.exe' analysis/compute_osim_muscle_paths_td.py --frames 60")
        return 1
    with open(cache_path, "rb") as f:
        cache = pickle.load(f)
    print(f"  cache: {cache_path.name}  ({len(cache)} 条件)")

    geom_dir = find_geometry_dir()
    print(f"  Geometry: {geom_dir}")
    body_meshes = load_body_meshes(geom_dir)
    print(f"  body メッシュ数: {len(body_meshes)}")

    print("\n--- 条件読み込み ---")
    conds = load_conditions(results_dir, cache, out_dir)
    if len(conds) < 2:
        print("ERROR: 比較できる条件が不足しています。")
        return 1

    win = (args.width, args.height)
    print("\n--- 出力生成 (color=strain) ---")
    if args.only == "both":
        write_hero_still(conds, body_meshes,
                         out_dir / "pelvic_td_musculoskeletal_hero.png", win)
    if not args.skip_video:
        if args.only in ("both", "side"):
            write_mp4(render_sidebyside_frame, conds, body_meshes,
                      out_dir / "pelvic_td_musculoskeletal_sidebyside.mp4",
                      args.frames, args.cycles, args.fps, win)
        if args.only in ("both", "overlay"):
            write_mp4(render_overlay_frame, conds, body_meshes,
                      out_dir / "pelvic_td_musculoskeletal_overlay.mp4",
                      args.frames, args.cycles, args.fps, win)
    print("\n[done]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
