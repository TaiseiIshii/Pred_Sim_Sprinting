"""
visualize_pelvic_shift_motion.py
骨盤前後傾オフセット条件 (_PelvisShift_*) ごとの走動作を比較するアニメーション。

`visualize_motion_comparison.py` のフォワードキネマティクス・エンジンと描画
ヘルパーを再利用し、Method B (剛体波形シフト) で得た各オフセット条件 +
Nominal (offset 0) のスティックフィギュアを

  1) 横並びアニメーション (条件ごと, トレッドミル視点)
  2) 重ね合わせアニメーション (骨盤を揃えて姿勢を直接比較)
  3) ストライド連続スナップショット (静止画)

として出力する。今回は角度を強制的にずらしているため、前回と違い姿勢差が
明確に現れる想定。各条件はストライド位相 [0,1] に正規化して同一位相で比較。

Usage:
    python visualize_pelvic_shift_motion.py
    python visualize_pelvic_shift_motion.py --fps 25 --frames 80 --cycles 2 --gif

Date: 2026-06-05
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from visualize_motion_comparison import (
    read_mot,
    simplify_column,
    compute_body_positions,
    draw_stick_figure_2d,
)

XLIM = (-1.0, 1.0)
YLIM = (-0.15, 1.95)


def build_phase_data(df):
    times = df["time"].values.astype(float)
    order = np.argsort(times, kind="stable")
    times = times[order]
    keep = np.concatenate(([True], np.diff(times) > 1e-12))
    times = times[keep]
    span = times[-1] - times[0]
    if span <= 0:
        raise ValueError("時刻範囲がゼロです")
    phases = (times - times[0]) / span
    col_map = {}
    for c in df.columns:
        if c == "time":
            continue
        vals = df[c].values.astype(float)[order][keep]
        col_map[simplify_column(c)] = vals
    mean_tilt = float(np.mean(col_map.get("pelvis_tilt", np.array([np.nan]))))
    return phases, col_map, mean_tilt


def q_at_phase(phases, col_map, p, treadmill=True):
    p = float(np.clip(p, 0.0, 1.0))
    q = {name: float(np.interp(p, phases, vals)) for name, vals in col_map.items()}
    if treadmill:
        q["pelvis_tx"] = 0.0
        q["pelvis_tz"] = 0.0
    return q


def _offset_from_name(name):
    m = re.search(r"PelvisShift_([mp])(\d+)", name)
    if not m:
        return None
    sgn = -1 if m.group(1) == "m" else 1
    return sgn * int(m.group(2))


def load_conditions(results_dir):
    """Collect Nominal (offset 0) + all _PelvisShift_* coords, newest per offset."""
    conditions = {}

    # Nominal reference (newest N=50-style coords); offset 0
    noms = sorted(results_dir.glob("pred_sprinting_coords_*Nominal.mot"))
    if noms:
        # prefer the 04-February-2026 N=50 nominal if present (matches study mesh)
        pref = [p for p in noms if "04-February-2026" in p.name]
        nom = pref[-1] if pref else noms[-1]
        conditions[0] = ("Nominal(0)", nom)

    # PelvisShift conditions
    best_time = {}
    for p in results_dir.glob("pred_sprinting_coords_*PelvisShift_*.mot"):
        off = _offset_from_name(p.name)
        if off is None:
            continue
        t = p.stat().st_mtime
        if off not in best_time or t > best_time[off]:
            best_time[off] = t
            conditions[off] = (f"{off:+d}°", p)

    # order by offset (anterior negative -> posterior positive)
    out = []
    cmap = plt.get_cmap("coolwarm")
    offs_sorted = sorted(conditions.keys())
    span = max(1, (max(offs_sorted) - min(offs_sorted))) if offs_sorted else 1
    for off in offs_sorted:
        label, path = conditions[off]
        df = read_mot(path)
        phases, col_map, mean_tilt = build_phase_data(df)
        frac = (off - min(offs_sorted)) / span
        out.append({
            "offset": off, "label": label, "path": path,
            "phases": phases, "col_map": col_map, "mean_tilt": mean_tilt,
            "color": cmap(frac),
        })
        print(f"  [OK] offset {off:+d}  mean pelvis_tilt = {mean_tilt:6.2f} deg  ({path.name})")
    return out


def _style_axis(ax):
    ax.set_aspect("equal"); ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.grid(True, alpha=0.2)
    ax.axhline(y=0, color="brown", linewidth=1.2, linestyle="--", alpha=0.5)
    ax.set_xlabel("X (前後) [m]"); ax.set_ylabel("Y (鉛直) [m]")


def _phase_sequence(n_frames, cycles):
    one = np.linspace(0.0, 1.0, n_frames, endpoint=False)
    return np.tile(one, cycles)


def render_side_by_side(conds, out_path, n_frames=80, cycles=2, fps=25):
    n = len(conds)
    fig, axes = plt.subplots(1, n, figsize=(3.4 * n, 7.2), squeeze=False)
    axes = axes[0]
    seq = _phase_sequence(n_frames, cycles)

    def _update(fi):
        p = seq[fi]
        for ax, c in zip(axes, conds):
            ax.cla()
            pos, _ = compute_body_positions(q_at_phase(c["phases"], c["col_map"], p, True))
            draw_stick_figure_2d(ax, pos, c["color"], lw=2.6, view="sagittal", marker_size=3)
            _style_axis(ax)
            ax.set_title(f"{c['label']}\n(mean {c['mean_tilt']:.1f}°)", fontsize=11, fontweight="bold")
        fig.suptitle(f"骨盤前後傾オフセットごとの走動作   位相 {p*100:4.0f}%", fontsize=14, fontweight="bold")
        return axes

    print(f"  横並びアニメ生成中 ({len(seq)} フレーム, {fps} fps) ...")
    ani = animation.FuncAnimation(fig, _update, frames=len(seq), interval=1000/fps, blit=False)
    _save_animation(ani, out_path, fps); plt.close(fig)


def render_overlay(conds, out_path, n_frames=80, cycles=2, fps=25):
    fig, ax = plt.subplots(figsize=(8.5, 8.5))
    seq = _phase_sequence(n_frames, cycles)
    handles = [plt.Line2D([0],[0], color=c["color"], lw=3,
                          label=f"{c['label']} ({c['mean_tilt']:.1f}°)") for c in conds]

    def _update(fi):
        p = seq[fi]; ax.cla()
        for c in conds:
            pos, _ = compute_body_positions(q_at_phase(c["phases"], c["col_map"], p, True))
            draw_stick_figure_2d(ax, pos, c["color"], lw=2.6, alpha=0.7, view="sagittal", marker_size=2)
        _style_axis(ax)
        ax.legend(handles=handles, loc="upper right", fontsize=9)
        ax.set_title(f"骨盤前後傾オフセットの重ね合わせ   位相 {p*100:4.0f}%", fontsize=13, fontweight="bold")
        return [ax]

    print(f"  重ね合わせアニメ生成中 ({len(seq)} フレーム, {fps} fps) ...")
    ani = animation.FuncAnimation(fig, _update, frames=len(seq), interval=1000/fps, blit=False)
    _save_animation(ani, out_path, fps); plt.close(fig)


def render_ghost_sequence(conds, out_path, n_ghosts=9):
    n = len(conds)
    fig, axes = plt.subplots(n, 1, figsize=(15, 3.4 * n), squeeze=False)
    axes = axes[:, 0]
    gph = np.linspace(0.0, 1.0, n_ghosts)
    for ax, c in zip(axes, conds):
        xs, ys = [], []
        for gi, p in enumerate(gph):
            pos, _ = compute_body_positions(q_at_phase(c["phases"], c["col_map"], p, False))
            a = 0.25 + 0.75 * (gi / (n_ghosts - 1))
            draw_stick_figure_2d(ax, pos, c["color"], lw=2.4, alpha=a, view="sagittal", marker_size=3)
            for v in pos.values():
                xs.append(v[0]); ys.append(v[1])
        ax.set_aspect("equal"); ax.grid(True, alpha=0.2)
        ax.axhline(y=0, color="brown", linewidth=1.2, linestyle="--", alpha=0.5)
        ax.set_xlim(min(xs)-0.2, max(xs)+0.2); ax.set_ylim(-0.15, max(ys)+0.25)
        ax.set_xlabel("X (前方) [m]"); ax.set_ylabel("Y (鉛直) [m]")
        ax.set_title(f"{c['label']}  (mean {c['mean_tilt']:.1f}°)  半ストライド進行 →",
                     fontsize=12, fontweight="bold")
    fig.suptitle("骨盤前後傾オフセットごとの走動作シーケンス (半ストライド)",
                 fontsize=15, fontweight="bold", y=1.0)
    fig.tight_layout()
    fig.savefig(out_path, dpi=170, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] 連続スナップショット保存: {out_path}")


def _save_animation(ani, out_path, fps):
    out_path = Path(out_path); suffix = out_path.suffix.lower()
    if suffix != ".gif":
        try:
            import imageio_ffmpeg
            matplotlib.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass
        try:
            writer = animation.FFMpegWriter(fps=fps, bitrate=2600, extra_args=["-pix_fmt", "yuv420p"])
            ani.save(str(out_path), writer=writer, dpi=120)
            print(f"  [OK] 動画保存: {out_path}"); return
        except Exception as exc:
            print(f"  [WARN] MP4保存に失敗 ({exc}). GIFにフォールバック。")
            out_path = out_path.with_suffix(".gif")
    writer = animation.PillowWriter(fps=fps)
    ani.save(str(out_path), writer=writer, dpi=110)
    print(f"  [OK] 動画保存: {out_path}")


def main():
    ap = argparse.ArgumentParser(description="骨盤前後傾オフセットごとの走動作比較")
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--frames", type=int, default=80)
    ap.add_argument("--cycles", type=int, default=2)
    ap.add_argument("--gif", action="store_true")
    ap.add_argument("--output_dir", type=str, default=None)
    args = ap.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    results_dir = project_root / "Results"
    out_dir = Path(args.output_dir) if args.output_dir else results_dir / "PelvicShift_Study"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib.font_manager as fm
        jp = [f.name for f in fm.fontManager.ttflist
              if any(k in f.name for k in ("Gothic", "Meiryo", "Yu Gothic", "MS Gothic"))]
        if jp:
            plt.rcParams["font.family"] = jp[0]
    except Exception:
        pass
    plt.rcParams["axes.unicode_minus"] = False

    print("=" * 64)
    print("  骨盤前後傾オフセット × 走動作 可視化ツール")
    print("=" * 64)

    conds = load_conditions(results_dir)
    if len(conds) < 2:
        print("ERROR: 比較できる条件が不足しています (2条件以上必要)。")
        return 1

    ext = ".gif" if args.gif else ".mp4"
    print("\n--- 出力生成 ---")
    render_ghost_sequence(conds, out_dir / "pelvic_shift_motion_sequence.png", n_ghosts=9)
    render_side_by_side(conds, out_dir / f"pelvic_shift_motion_sidebyside{ext}",
                        n_frames=args.frames, cycles=args.cycles, fps=args.fps)
    render_overlay(conds, out_dir / f"pelvic_shift_motion_overlay{ext}",
                   n_frames=args.frames, cycles=args.cycles, fps=args.fps)
    print(f"\n{'=' * 64}\n  完了! 出力先: {out_dir}\n{'=' * 64}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
