"""
visualize_pelvic_shift_smpl.py
骨盤前後傾オフセット条件の「3D人体(SMPL風)」可視化。

棒人間/骨格に加え、本スクリプトは滑らかな皮膚付き人体メッシュ(soft-body)を
同じフォワードキネマティクス骨格の上に被せてアニメーションする。各セグメント
(胴・上腕・前腕・大腿・下腿・足・頭)をテーパ付きカプセル状メッシュで近似し、
SMPL風の連続した人体シルエットを生成する。骨盤前後傾による「走りフォーム」の
全身的な見た目の違いを直感的に示すのが目的。

  1) 横並びアニメーション (sidebyside MP4)   — 代表3条件を並置
  2) 重ね合わせアニメーション (overlay MP4)   — 骨盤を揃えシルエットを重ねる

本物の SMPL (skinned multi-person linear) メッシュを使いたい場合:
  - SMPL は研究ライセンスが必要 (https://smpl.is.tue.mpg.de で登録)。
  - smplx + 本体 .pkl/.npz を導入後、--smpl_model <path> を指定すると
    本物の SMPL ボディメッシュを OpenSim 関節角からポーズ付けして描画する
    (retarget 層は load_real_smpl() を参照; モデル未指定時は soft-body 近似)。

依存: pyvista, vtk, imageio (+imageio-ffmpeg), scipy, numpy, matplotlib
推奨実行: conda base python (pyvista/vtk/imageio_ffmpeg 入り)

Date: 2026-06-21
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# FK / .mot / 条件発見 / ひずみは骨格スクリプトから再利用
from visualize_form_comparison_v2 import (
    compute_body_transforms,
    read_mot,
    simplify_column,
)
from visualize_pelvic_shift_musculoskeletal import (
    CONDITION_SPECS,
    build_phase_data,
    q_at_phase,
    load_hamstring_strain,
    strain_at,
)

# ═══════════════════════════════════════════════════════════════════════════
# 設定
# ═══════════════════════════════════════════════════════════════════════════

SKIN_COLOR = (0.93, 0.78, 0.68)       # 肌色
SKIN_COLOR_ALT = (0.80, 0.84, 0.92)   # 重ね合わせ用の淡色
XVIEW = "side"

# セグメント定義: (親body, 子body, 近位半径, 遠位半径)
#   親→子 の world 原点間をテーパ付きカプセルで結ぶ。半径[m]は概略の人体寸法。
SEGMENTS = [
    # 体幹 (骨盤→胴)
    ("pelvis", "torso", 0.13, 0.115),
    # 右脚
    ("pelvis", "femur_r", 0.085, 0.075),   # 殿部→大腿近位 (相対的に太く)
    ("femur_r", "tibia_r", 0.075, 0.050),  # 大腿
    ("tibia_r", "talus_r", 0.050, 0.032),  # 下腿
    ("talus_r", "toes_r", 0.035, 0.025),   # 足
    # 左脚
    ("pelvis", "femur_l", 0.085, 0.075),
    ("femur_l", "tibia_l", 0.075, 0.050),
    ("tibia_l", "talus_l", 0.050, 0.032),
    ("talus_l", "toes_l", 0.035, 0.025),
    # 右腕
    ("torso", "humerus_r", 0.050, 0.040),
    ("humerus_r", "ulna_r", 0.040, 0.030),
    ("ulna_r", "hand_r", 0.030, 0.022),
    # 左腕
    ("torso", "humerus_l", 0.050, 0.040),
    ("humerus_l", "ulna_l", 0.040, 0.030),
    ("ulna_l", "hand_l", 0.030, 0.022),
]

# 頭 (torso 原点から上方オフセットに球)
HEAD_OFFSET_FROM_TORSO = np.array([0.02, 0.30, 0.0])
HEAD_RADIUS = 0.105

# ハム強調オーバーレイ (大腿後面に沿った半透明チューブ; ひずみ着色)
LM_VMIN, LM_VMAX = 0.85, 1.18
STRAIN_CMAP = plt.get_cmap("RdYlGn_r")


# ═══════════════════════════════════════════════════════════════════════════
# soft-body 人体メッシュ生成
# ═══════════════════════════════════════════════════════════════════════════

def tapered_capsule(p0, p1, r0, r1, n_sides=18):
    """p0→p1 を結ぶテーパ付き円柱 + 端球 (近似カプセル) を返す。"""
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    axis = p1 - p0
    length = np.linalg.norm(axis)
    if length < 1e-6:
        return pv.Sphere(radius=max(r0, r1), center=p0)
    direction = axis / length
    center = (p0 + p1) / 2.0
    # テーパ円柱本体
    cyl = pv.Cylinder(center=center, direction=direction, radius=1.0,
                      height=length, resolution=n_sides, capping=False)
    # 半径を軸方向に線形補間してテーパ化
    pts = cyl.points.copy()
    rel = (pts - p0) @ direction          # 軸方向の投影距離 [0,length]
    frac = np.clip(rel / length, 0.0, 1.0)
    radial = pts - (p0 + np.outer(rel, direction))
    rad_norm = np.linalg.norm(radial, axis=1, keepdims=True)
    rad_norm[rad_norm < 1e-9] = 1.0
    target_r = (r0 * (1 - frac) + r1 * frac)[:, None]
    cyl.points = (p0 + np.outer(rel, direction)) + radial / rad_norm * target_r
    # 端球で関節を滑らかに
    s0 = pv.Sphere(radius=r0, center=p0, theta_resolution=n_sides,
                   phi_resolution=n_sides)
    s1 = pv.Sphere(radius=r1, center=p1, theta_resolution=n_sides,
                   phi_resolution=n_sides)
    return cyl + s0 + s1


def build_human_mesh(transforms):
    """FK transforms から soft-body 人体メッシュ(単一 PolyData)を組む。"""
    parts = []
    for parent, child, r0, r1 in SEGMENTS:
        if parent not in transforms or child not in transforms:
            continue
        p0 = transforms[parent][:3, 3]
        p1 = transforms[child][:3, 3]
        parts.append(tapered_capsule(p0, p1, r0, r1))
    # 頭
    if "torso" in transforms:
        T = transforms["torso"]
        head_c = (T @ np.append(HEAD_OFFSET_FROM_TORSO, 1.0))[:3]
        parts.append(pv.Sphere(radius=HEAD_RADIUS, center=head_c,
                               theta_resolution=22, phi_resolution=22))
    if not parts:
        return pv.PolyData()
    merged = parts[0]
    for p in parts[1:]:
        merged = merged + p
    return merged


def strain_color(lm_val):
    if not np.isfinite(lm_val):
        return (0.6, 0.6, 0.6)
    t = float(np.clip((lm_val - LM_VMIN) / (LM_VMAX - LM_VMIN), 0.0, 1.0))
    r, g, b, _ = STRAIN_CMAP(t)
    return (r, g, b)


def hamstring_overlay(transforms, strain, p):
    """大腿後面に沿ったハム強調チューブ (右側; ひずみ着色) を返す。無ければ None。"""
    need = ("pelvis", "tibia_r")
    if any(b not in transforms for b in need):
        return None, None
    ischium = transforms["pelvis"][:3, 3] + (transforms["pelvis"][:3, :3] @
                                             np.array([-0.10, -0.09, 0.06]))
    knee = transforms["tibia_r"][:3, 3]
    mid = (ischium + knee) / 2.0
    try:
        spline = pv.Spline(np.vstack([ischium, mid, knee]), 40)
        tube = spline.tube(radius=0.018, n_sides=12)
    except Exception:
        return None, None
    lm = strain_at(strain, "bifemlh_r", p)
    return tube, strain_color(lm)


# ═══════════════════════════════════════════════════════════════════════════
# 描画
# ═══════════════════════════════════════════════════════════════════════════

def add_ground(pl, cx):
    ground = pv.Plane(center=(cx, 0.0, 0.0), direction=(0, 1, 0),
                      i_size=4.0, j_size=2.4, i_resolution=8, j_resolution=8)
    pl.add_mesh(ground, color="#8B7355", opacity=0.18, style="wireframe",
                line_width=1)


def frame_sagittal(pl, zoom=1.0):
    pl.view_vector((0.0, 0.0, 1.0), viewup=(0.0, 1.0, 0.0))
    pl.reset_camera()
    if zoom != 1.0:
        pl.camera.zoom(zoom)


def add_lights(pl, cx):
    pl.add_light(pv.Light(position=(cx + 2, 3, 3), intensity=0.6))
    pl.add_light(pv.Light(position=(cx - 2, 3, -3), intensity=0.35))


def _draw_human(pl, cond, p, *, skin=SKIN_COLOR, opacity=1.0, align_dx=0.0,
                show_ham=True):
    q = q_at_phase(cond["phases"], cond["col_map"], p, treadmill=True)
    transforms = compute_body_transforms(q)
    if align_dx:
        for b in transforms:
            transforms[b] = transforms[b].copy()
            transforms[b][0, 3] += align_dx
    mesh = build_human_mesh(transforms)
    if mesh.n_points > 0:
        pl.add_mesh(mesh, color=skin, opacity=opacity, smooth_shading=True,
                    specular=0.25, specular_power=12)
    if show_ham:
        tube, col = hamstring_overlay(transforms, cond["strain"], p)
        if tube is not None:
            pl.add_mesh(tube, color=col, opacity=min(1.0, opacity + 0.1),
                        smooth_shading=True, specular=0.3)
    return transforms["pelvis"][0, 3]


def render_sidebyside_frame(conds, p, window_size):
    n = len(conds)
    pv.global_theme.background = "white"
    pl = pv.Plotter(off_screen=True, shape=(1, n), window_size=list(window_size),
                    border=False)
    for i, cond in enumerate(conds):
        pl.subplot(0, i)
        cx = _draw_human(pl, cond, p)
        frame_sagittal(pl, zoom=1.18)
        add_ground(pl, cx)
        add_lights(pl, cx)
        pl.add_text(f"{cond['label']}\n(mean tilt {cond['mean_tilt']:.1f} deg)",
                    position="upper_left", font_size=11, color="black")
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


def render_overlay_frame(conds, p, window_size):
    pv.global_theme.background = "white"
    pl = pv.Plotter(off_screen=True, window_size=list(window_size), border=False)
    skins = [SKIN_COLOR, (0.78, 0.86, 0.78), SKIN_COLOR_ALT]
    base_cx = None
    for i, cond in enumerate(conds):
        q0 = q_at_phase(cond["phases"], cond["col_map"], p, treadmill=True)
        tf0 = compute_body_transforms(q0)
        cx0 = tf0["pelvis"][0, 3]
        if base_cx is None:
            base_cx = cx0
        _draw_human(pl, cond, p, skin=skins[i % len(skins)], opacity=0.45,
                    align_dx=base_cx - cx0, show_ham=True)
    frame_sagittal(pl, zoom=1.18)
    add_ground(pl, base_cx)
    add_lights(pl, base_cx)
    handles = "  |  ".join(f"{c['label']} ({c['mean_tilt']:.1f}deg)" for c in conds)
    pl.add_text("Overlay (pelvis-aligned): " + handles, position="upper_left",
                font_size=11, color="black")
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


# ═══════════════════════════════════════════════════════════════════════════
# 出力
# ═══════════════════════════════════════════════════════════════════════════

def _phase_seq(n_frames, cycles):
    one = np.linspace(0.0, 1.0, n_frames, endpoint=False)
    return np.tile(one, cycles)


def write_mp4(frame_fn, conds, out_path, n_frames, cycles, fps, window_size):
    import imageio
    seq = _phase_seq(n_frames, cycles)
    print(f"  {out_path.name}: {len(seq)} フレーム生成中 ...")
    writer = imageio.get_writer(str(out_path), fps=fps, codec="libx264",
                                quality=8, output_params=["-pix_fmt", "yuv420p"])
    try:
        for fi, p in enumerate(seq):
            writer.append_data(frame_fn(conds, p, window_size))
            if (fi + 1) % 15 == 0 or fi == len(seq) - 1:
                print(f"    {fi + 1}/{len(seq)}")
    finally:
        writer.close()
    mb = out_path.stat().st_size / (1024 * 1024)
    print(f"  [OK] {out_path.name}  ({mb:.1f} MB)")


def write_hero_still(conds, out_path, window_size):
    img = render_sidebyside_frame(conds, 0.8, window_size)
    fig, ax = plt.subplots(figsize=(window_size[0] / 130, window_size[1] / 130))
    ax.imshow(img)
    ax.axis("off")
    ax.set_title("3D人体(SMPL風)による骨盤前後傾フォーム比較",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {out_path.name}")


# ═══════════════════════════════════════════════════════════════════════════
# 本物の SMPL を使う場合のフック (モデル未提供時は未使用)
# ═══════════════════════════════════════════════════════════════════════════

def load_real_smpl(model_path):
    """本物の SMPL モデルを読み込む (smplx 必須)。

    NOTE: SMPL は OpenSim とジョイント定義が異なるため、本格運用には
    OpenSim 関節角 → SMPL pose (axis-angle 72) への retarget が必要。
    本リポジトリでは soft-body 近似をデフォルトとし、この関数は将来の
    licensed SMPL 導入時の拡張ポイントとして用意している。
    """
    try:
        import smplx  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "smplx が見つかりません。本物の SMPL を使うには "
            "`pip install smplx trimesh` と SMPL モデル(.pkl/.npz)が必要です。"
        ) from exc
    raise NotImplementedError(
        "本物の SMPL ポーズ付けは未実装 (retarget 層が必要)。"
        "現状は soft-body 近似を使用してください。"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 条件発見 + main
# ═══════════════════════════════════════════════════════════════════════════

def load_conditions(results_dir):
    conds = []
    for off, ident in CONDITION_SPECS:
        coords = sorted(results_dir.glob(f"pred_sprinting_coords_*{ident}*.mot"))
        data = sorted(results_dir.glob(f"pred_sprinting_data_*{ident}*.mat"))
        if not coords or not data:
            print(f"  [WARN] 条件 {ident} が見つかりません。スキップ。")
            continue
        df = read_mot(coords[-1])
        phases, col_map, mean_tilt = build_phase_data(df)
        strain = load_hamstring_strain(data[-1])
        label = f"{off:+d}deg" if off != 0 else "0deg(nominal)"
        conds.append({
            "offset": off, "label": label, "mean_tilt": mean_tilt,
            "phases": phases, "col_map": col_map, "strain": strain,
        })
        print(f"  [OK] {ident:18s} mean tilt {mean_tilt:6.2f} deg")
    return conds


def setup_japanese_font():
    try:
        import matplotlib.font_manager as fm
        jp = [f.name for f in fm.fontManager.ttflist
              if any(k in f.name for k in ("Gothic", "Meiryo", "Yu Gothic",
                                           "MS Gothic"))]
        if jp:
            plt.rcParams["font.family"] = jp[0]
    except Exception:
        pass
    plt.rcParams["axes.unicode_minus"] = False


def main():
    ap = argparse.ArgumentParser(
        description="骨盤前後傾オフセットの3D人体(SMPL風)可視化")
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--cycles", type=int, default=2)
    ap.add_argument("--width", type=int, default=1680)
    ap.add_argument("--height", type=int, default=950)
    ap.add_argument("--output_dir", type=str, default=None)
    ap.add_argument("--skip_video", action="store_true")
    ap.add_argument("--only", choices=["both", "side", "overlay"], default="both")
    ap.add_argument("--smpl_model", type=str, default=None,
                    help="本物の SMPL モデル(.pkl/.npz)パス (任意; 未指定で soft-body)")
    args = ap.parse_args()

    setup_japanese_font()

    if args.smpl_model:
        load_real_smpl(args.smpl_model)  # 現状は明示的に未実装を通知

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    results_dir = project_root / "Results"
    out_dir = (Path(args.output_dir) if args.output_dir
               else results_dir / "PelvicShift_Study")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("  骨盤前後傾オフセット × 3D人体(SMPL風) 可視化")
    print("=" * 70)
    conds = load_conditions(results_dir)
    if len(conds) < 2:
        print("ERROR: 比較できる条件が不足しています。")
        return 1

    win = (args.width, args.height)
    print("\n--- 出力生成 ---")
    if args.only == "both":
        write_hero_still(conds,
                         out_dir / "pelvic_shift_smpl_hero.png", win)
    if not args.skip_video:
        if args.only in ("both", "side"):
            write_mp4(render_sidebyside_frame, conds,
                      out_dir / "pelvic_shift_smpl_sidebyside.mp4",
                      args.frames, args.cycles, args.fps, win)
        if args.only in ("both", "overlay"):
            write_mp4(render_overlay_frame, conds,
                      out_dir / "pelvic_shift_smpl_overlay.mp4",
                      args.frames, args.cycles, args.fps,
                      (int(win[0] * 0.65), win[1]))

    print(f"\n{'=' * 70}\n  完了! 出力先: {out_dir}\n{'=' * 70}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
