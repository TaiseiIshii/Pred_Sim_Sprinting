"""
visualize_pelvic_tilt_motion.py
骨盤前後傾条件ごとの走動作（筋骨格モデル）を比較するアニメーション生成。

`visualize_motion_comparison.py` のフォワードキネマティクス・エンジンと
描画ヘルパーを再利用し、収束した骨盤傾斜条件
(Nominal, _PelvisTilt_m07, _PelvisTilt_m10) のスティックフィギュアを

  1) 横並びアニメーション (条件ごと, トレッドミル視点)
  2) 重ね合わせアニメーション (骨盤を揃えて姿勢を直接比較)
  3) ストライド連続スナップショット (静止画)

として出力する。

各条件の半ストライドは継続時間がわずかに異なるため、ストライド位相 [0,1]
に正規化して同一位相で比較する。

Usage:
    python visualize_pelvic_tilt_motion.py
    python visualize_pelvic_tilt_motion.py --fps 25 --frames 80 --cycles 2
    python visualize_pelvic_tilt_motion.py --gif        # GIFで出力

Date: 2026-06-05
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# フォワードキネマティクス・エンジンと描画ヘルパーを再利用
from visualize_motion_comparison import (
    read_mot,
    simplify_column,
    compute_body_positions,
    draw_stick_figure_2d,
)

# ─────────────────────────────────────────────────────────────────────────
# 設定: 比較する骨盤傾斜条件 (収束/許容解のみ)
#   label, ファイル名に含まれる識別子, 色
# ─────────────────────────────────────────────────────────────────────────
CONDITION_SPECS = [
    ("Nominal",  "04-February-2026__12-27-31___Nominal",        "#2196F3"),
    ("-7 deg",   "PelvisTilt_m07",                              "#4CAF50"),
    ("-10 deg",  "PelvisTilt_m10",                              "#F44336"),
]

# 描画範囲 (トレッドミル / 重ね合わせ視点, 骨盤を原点付近に固定)
XLIM = (-1.0, 1.0)
YLIM = (-0.15, 1.95)


# ─────────────────────────────────────────────────────────────────────────
# 位相補間データの構築
# ─────────────────────────────────────────────────────────────────────────
def build_phase_data(df):
    """`.mot` DataFrame からストライド位相 [0,1] で補間できるデータを作る。

    コロケーション境界で重複する時刻行を除去し、時刻を単調増加に整える。
    戻り値: (phases, col_map, mean_tilt)
      phases : 正規化位相 (昇順, 0..1)
      col_map: {coord_name: values_array}
      mean_tilt: pelvis_tilt の平均 [deg]
    """
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
    """位相 p における関節角 dict を返す。

    treadmill=True のとき pelvis_tx/tz を 0 にして図を原点付近に固定する
    (鉛直方向 pelvis_ty は残すので上下動は再現される)。
    """
    p = float(np.clip(p, 0.0, 1.0))
    q = {}
    for name, vals in col_map.items():
        q[name] = float(np.interp(p, phases, vals))
    if treadmill:
        q["pelvis_tx"] = 0.0
        q["pelvis_tz"] = 0.0
    return q


def load_conditions(results_dir):
    """CONDITION_SPECS に対応する coords .mot を読み込む。見つからない条件は除外。"""
    conditions = []
    for label, ident, color in CONDITION_SPECS:
        matches = sorted(results_dir.glob(f"pred_sprinting_coords_*{ident}*.mot"))
        if not matches:
            print(f"  [WARN] 条件 '{label}' (識別子 {ident}) の coords が見つかりません。除外します。")
            continue
        path = matches[-1]  # 最新を採用
        df = read_mot(path)
        phases, col_map, mean_tilt = build_phase_data(df)
        conditions.append({
            "label": label,
            "color": color,
            "path": path,
            "phases": phases,
            "col_map": col_map,
            "mean_tilt": mean_tilt,
        })
        print(f"  [OK] {label:8s}  mean pelvis_tilt = {mean_tilt:6.2f} deg  ({path.name})")
    return conditions


# ─────────────────────────────────────────────────────────────────────────
# 描画ユーティリティ
# ─────────────────────────────────────────────────────────────────────────
def _style_axis(ax):
    ax.set_aspect("equal")
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.grid(True, alpha=0.2)
    ax.axhline(y=0, color="brown", linewidth=1.2, linestyle="--", alpha=0.5)
    ax.set_xlabel("X (前後) [m]")
    ax.set_ylabel("Y (鉛直) [m]")


def _phase_sequence(n_frames, cycles):
    """0..1 の位相を cycles 回ループした配列を返す。"""
    one = np.linspace(0.0, 1.0, n_frames, endpoint=False)
    return np.tile(one, cycles)


# ─────────────────────────────────────────────────────────────────────────
# 1) 横並びアニメーション
# ─────────────────────────────────────────────────────────────────────────
def render_side_by_side(conditions, out_path, n_frames=80, cycles=2, fps=25):
    n = len(conditions)
    fig, axes = plt.subplots(1, n, figsize=(5.0 * n, 7.5), squeeze=False)
    axes = axes[0]
    seq = _phase_sequence(n_frames, cycles)

    def _update(fi):
        p = seq[fi]
        for ax, cond in zip(axes, conditions):
            ax.cla()
            q = q_at_phase(cond["phases"], cond["col_map"], p, treadmill=True)
            pos, _ = compute_body_positions(q)
            draw_stick_figure_2d(ax, pos, cond["color"], lw=3.0,
                                 view="sagittal", marker_size=4)
            _style_axis(ax)
            ax.set_title(f"{cond['label']}\n(mean pelvis_tilt {cond['mean_tilt']:.1f}°)",
                         fontsize=12, fontweight="bold")
        fig.suptitle(f"骨盤前後傾ごとの走動作比較   ストライド位相 {p*100:4.0f}%",
                     fontsize=14, fontweight="bold")
        return axes

    print(f"  横並びアニメ生成中 ({len(seq)} フレーム, {fps} fps) ...")
    ani = animation.FuncAnimation(fig, _update, frames=len(seq),
                                  interval=1000 / fps, blit=False)
    _save_animation(ani, out_path, fps)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────
# 2) 重ね合わせアニメーション
# ─────────────────────────────────────────────────────────────────────────
def render_overlay(conditions, out_path, n_frames=80, cycles=2, fps=25):
    fig, ax = plt.subplots(figsize=(8.5, 8.5))
    seq = _phase_sequence(n_frames, cycles)

    # 凡例用ハンドル
    legend_handles = [
        plt.Line2D([0], [0], color=c["color"], lw=3,
                   label=f"{c['label']} ({c['mean_tilt']:.1f}°)")
        for c in conditions
    ]

    def _update(fi):
        p = seq[fi]
        ax.cla()
        for cond in conditions:
            q = q_at_phase(cond["phases"], cond["col_map"], p, treadmill=True)
            pos, _ = compute_body_positions(q)
            draw_stick_figure_2d(ax, pos, cond["color"], lw=3.0, alpha=0.75,
                                 view="sagittal", marker_size=3)
        _style_axis(ax)
        ax.legend(handles=legend_handles, loc="upper right", fontsize=10)
        ax.set_title(f"骨盤前後傾の重ね合わせ比較   ストライド位相 {p*100:4.0f}%",
                     fontsize=13, fontweight="bold")
        return [ax]

    print(f"  重ね合わせアニメ生成中 ({len(seq)} フレーム, {fps} fps) ...")
    ani = animation.FuncAnimation(fig, _update, frames=len(seq),
                                  interval=1000 / fps, blit=False)
    _save_animation(ani, out_path, fps)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────
# 3) ストライド連続スナップショット (静止画, 前進を残す)
# ─────────────────────────────────────────────────────────────────────────
def render_ghost_sequence(conditions, out_path, n_ghosts=9):
    n = len(conditions)
    fig, axes = plt.subplots(n, 1, figsize=(15, 4.0 * n), squeeze=False)
    axes = axes[:, 0]
    ghost_phases = np.linspace(0.0, 1.0, n_ghosts)

    for ax, cond in zip(axes, conditions):
        xs_all = []
        ys_all = []
        for gi, p in enumerate(ghost_phases):
            # 前進を残すため tx を保持
            q = q_at_phase(cond["phases"], cond["col_map"], p, treadmill=False)
            pos, _ = compute_body_positions(q)
            alpha = 0.25 + 0.75 * (gi / (n_ghosts - 1))
            draw_stick_figure_2d(ax, pos, cond["color"], lw=2.5, alpha=alpha,
                                 view="sagittal", marker_size=3)
            for v in pos.values():
                xs_all.append(v[0])
                ys_all.append(v[1])
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.2)
        ax.axhline(y=0, color="brown", linewidth=1.2, linestyle="--", alpha=0.5)
        ax.set_xlim(min(xs_all) - 0.2, max(xs_all) + 0.2)
        ax.set_ylim(-0.15, max(ys_all) + 0.25)
        ax.set_xlabel("X (前方) [m]")
        ax.set_ylabel("Y (鉛直) [m]")
        ax.set_title(f"{cond['label']}  (mean pelvis_tilt {cond['mean_tilt']:.1f}°)  "
                     f"半ストライド進行 →", fontsize=12, fontweight="bold")

    fig.suptitle("骨盤前後傾ごとの走動作シーケンス (半ストライド)",
                 fontsize=15, fontweight="bold", y=1.0)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] 連続スナップショット保存: {out_path}")


# ─────────────────────────────────────────────────────────────────────────
# アニメーション保存 (MP4優先, 失敗時GIF)
# ─────────────────────────────────────────────────────────────────────────
def _save_animation(ani, out_path, fps):
    out_path = Path(out_path)
    suffix = out_path.suffix.lower()

    if suffix != ".gif":
        # imageio-ffmpeg 同梱のバイナリを利用
        try:
            import imageio_ffmpeg
            matplotlib.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass
        try:
            writer = animation.FFMpegWriter(fps=fps, bitrate=2600,
                                            extra_args=["-pix_fmt", "yuv420p"])
            ani.save(str(out_path), writer=writer, dpi=120)
            print(f"  [OK] 動画保存: {out_path}")
            return
        except Exception as exc:
            print(f"  [WARN] MP4保存に失敗 ({exc}). GIFにフォールバックします。")
            out_path = out_path.with_suffix(".gif")

    writer = animation.PillowWriter(fps=fps)
    ani.save(str(out_path), writer=writer, dpi=110)
    print(f"  [OK] 動画保存: {out_path}")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="骨盤前後傾ごとの走動作スティックフィギュア比較アニメーション")
    parser.add_argument("--fps", type=int, default=25, help="動画FPS")
    parser.add_argument("--frames", type=int, default=80,
                        help="半ストライドあたりのフレーム数")
    parser.add_argument("--cycles", type=int, default=2,
                        help="ループ回数 (半ストライドを何回繰り返すか)")
    parser.add_argument("--gif", action="store_true", help="GIF形式で出力")
    parser.add_argument("--output_dir", type=str, default=None)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent  # Pred_Sim_Sprinting
    results_dir = project_root / "Results"
    out_dir = (Path(args.output_dir) if args.output_dir
               else results_dir / "PelvicTilt_Study")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 日本語フォント
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
    print("  骨盤前後傾 × 走動作 可視化ツール")
    print("=" * 64)

    conditions = load_conditions(results_dir)
    if len(conditions) < 2:
        print("ERROR: 比較できる条件が不足しています (2条件以上必要)。")
        return 1

    ext = ".gif" if args.gif else ".mp4"

    print("\n--- 出力生成 ---")
    render_ghost_sequence(conditions, out_dir / "pelvic_tilt_motion_sequence.png",
                          n_ghosts=9)
    render_side_by_side(conditions, out_dir / f"pelvic_tilt_motion_sidebyside{ext}",
                        n_frames=args.frames, cycles=args.cycles, fps=args.fps)
    render_overlay(conditions, out_dir / f"pelvic_tilt_motion_overlay{ext}",
                   n_frames=args.frames, cycles=args.cycles, fps=args.fps)

    print(f"\n{'=' * 64}")
    print(f"  完了! 出力先: {out_dir}")
    print(f"{'=' * 64}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
