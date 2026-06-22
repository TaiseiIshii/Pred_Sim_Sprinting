"""
visualize_pelvic_shift_musculoskeletal.py
骨盤前後傾オフセット条件の「リッチ」筋骨格可視化 (実OpenSim骨メッシュ + 解剖学的に
正しい wrapping 込みの筋経路)。

従来は .osim の path point 間を直線/スプラインで結んでいたため、股関節などをまたぐ
筋が屈曲時に骨から離れて「垂れ下がる」不自然さがあった。本版は OpenSim 4.x の
Python API で **wrapping 込みの筋経路**と**各 body の ground 変換**を事前計算した
キャッシュ (`_muscle_cache.pkl`, compute_osim_muscle_paths.py が生成) を読み込み、
taut（張った）筋チューブを描く。これにより筋の不自然な緩みを解消する。

ハム4筋 (semimembranosus, semitendinosus, biceps femoris long/short head) は各条件の
最適化結果 (.mat) の正規化筋線維長 lMtilde で着色し、「伸張 = 肉離れリスク」を3D表現。
代表3条件 (-6° / 0° / +6°) を比較する:

  1) 横並びアニメーション (sidebyside MP4)
  2) 重ね合わせアニメーション (overlay MP4)  — 骨盤を揃え骨を半透明、筋を強調
  3) ピーク伸張スチル (hero PNG)             — 最大伸張位相 + ひずみカラーバー

前提: 先に `compute_osim_muscle_paths.py` を opensim 対応 env で実行してキャッシュを作る。

依存: pyvista, vtk, imageio (+imageio-ffmpeg), scipy, numpy, matplotlib
推奨実行: conda base python (pyvista/vtk/imageio_ffmpeg が入っている環境)

Date: 2026-06-21
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import pyvista as pv
from scipy.io import loadmat

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

# 骨メッシュ読込ヘルパを再利用
from visualize_form_comparison_v2 import (
    find_geometry_dir,
    load_body_meshes,
    build_posed_model,
)

# ═══════════════════════════════════════════════════════════════════════════
# 設定
# ═══════════════════════════════════════════════════════════════════════════

CONDITION_SPECS = [
    (-6, "PelvisShift_m06"),
    (0,  "PelvisShift_p00"),
    (6,  "PelvisShift_p06"),
]

# .mat muscleValues.lMtilde の行 (1-based) → ハム基底名
HAM_ROW_1BASED = {
    "semimem_l": 7,  "semiten_l": 8,  "bifemlh_l": 9,  "bifemsh_l": 10,
    "semimem_r": 53, "semiten_r": 54, "bifemlh_r": 55, "bifemsh_r": 56,
}

# ひずみ着色レンジ (固定 = 条件横断で比較可能)。低=緑, 高=赤。
LM_VMIN, LM_VMAX = 0.85, 1.18
STRAIN_CMAP = plt.get_cmap("RdYlGn_r")

# 筋活性化 (0..1) のカラーマップ。低=青灰, 高=赤 (筋電図風)。
ACT_CMAP = plt.get_cmap("turbo")

BONE_COLOR = (0.92, 0.89, 0.82)
NONHAM_COLOR = (0.50, 0.11, 0.11)
GRF_COLOR = (0.10, 0.45, 0.95)
GRF_SCALE = 0.00018          # N -> m (体重~750N で ~0.7m の矢)

CACHE_NAME = "_muscle_cache.pkl"


def base_name(name):
    return name[:-2] if name.endswith(("_r", "_l")) else name


# ═══════════════════════════════════════════════════════════════════════════
# ひずみ loader (.mat)
# ═══════════════════════════════════════════════════════════════════════════

def _get(o, *names):
    for n in names:
        try:
            o = getattr(o, n)
        except AttributeError:
            o = o[n]
    return o


def load_hamstring_strain(mat_path):
    """.mat の muscleValues.lMtilde からハム4筋(L/R)の位相→lMtilde を作る。"""
    m = loadmat(str(mat_path), struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    lM = np.asarray(_get(o, "muscleValues", "lMtilde"), dtype=float)
    ncol = lM.shape[1]
    phases = np.linspace(0.0, 1.0, ncol)
    return {nm: (phases, lM[r - 1, :].copy()) for nm, r in HAM_ROW_1BASED.items()}


def strain_at(strain, muscle_name, p):
    if muscle_name not in strain:
        return np.nan
    ph, vals = strain[muscle_name]
    return float(np.interp(np.clip(p, 0.0, 1.0), ph, vals))


def strain_color(lm_val):
    if not np.isfinite(lm_val):
        return (0.6, 0.6, 0.6)
    t = float(np.clip((lm_val - LM_VMIN) / (LM_VMAX - LM_VMIN), 0.0, 1.0))
    r, g, b, _ = STRAIN_CMAP(t)
    return (r, g, b)


def _series_at(dyn_entry, p, kind):
    """dyn[name] = (ph_a, act, ph_f, forceRatio) から位相 p の値を補間。"""
    ph_a, act, ph_f, fr = dyn_entry
    if kind == "act":
        return float(np.interp(np.clip(p, 0, 1), ph_a, act))
    return float(np.interp(np.clip(p, 0, 1), ph_f, fr))


def act_color(a):
    t = float(np.clip(a, 0.0, 1.0))
    r, g, b, _ = ACT_CMAP(t)
    return (r, g, b)


# ═══════════════════════════════════════════════════════════════════════════
# 描画ヘルパ
# ═══════════════════════════════════════════════════════════════════════════

def muscle_tube(points, radius):
    """wrapping 済みポリラインを taut なチューブに。直線区間を保持し緩みを防ぐ。"""
    pts = np.asarray(points, dtype=float)
    if pts.shape[0] < 2:
        return None
    try:
        poly = pv.lines_from_points(pts)
        return poly.tube(radius=radius, n_sides=12, capping=True)
    except Exception:
        return None


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
    pl.add_light(pv.Light(position=(cx + 2, 3, 3), intensity=0.65))
    pl.add_light(pv.Light(position=(cx - 2, 3, -3), intensity=0.35))


def _bodies_at(entry, fi):
    return {b: entry["bodies"][b][fi] for b in entry["bodies"]}


def _grf_arrow(force, foot_pos, align_dx):
    """GRF ベクトル(N)を接地足(calcn)位置から描く矢印 mesh。小さければ None。

    COP は元の ground 系、骨は treadmill シフト済みで座標系が異なるため、
    作用点には足(calcn)の現在位置を用いて整合させる。
    """
    if force is None or foot_pos is None:
        return None
    mag = float(np.linalg.norm(force))
    if mag < 150.0:                     # 接地していない相は描かない
        return None
    p0 = np.asarray(foot_pos, dtype=float).copy()
    p0[0] += align_dx
    p0[1] = 0.0                          # 地面から立ち上げる
    # .mot の ground_force_v は「地面に働く力」符号。体に働く反力は上向きにするため
    # 鉛直成分が負なら全体を反転して GRF(反力)= 上向きで描く。
    f = np.asarray(force, dtype=float).copy()
    if f[1] < 0:
        f = -f
    vec = f * GRF_SCALE
    length = float(np.linalg.norm(vec))
    try:
        return pv.Arrow(start=p0, direction=vec / (length + 1e-9),
                        scale=length, tip_length=0.2, tip_radius=0.045,
                        shaft_radius=0.02)
    except Exception:
        return None


def _draw_one(pl, cond, fi, body_meshes, *, bone_opacity=1.0,
              muscle_opacity_nonham=0.5, muscle_opacity_ham=0.98, align_dx=0.0,
              color_mode="strain", show_grf=True):
    """1体ぶんの骨+筋(wrapping済)を描く。pelvis world x を返す。

    color_mode: 'strain'(ハムをlMtilde着色, 他はミュート赤) /
                'activation'(全筋を活性度で着色) / 'force'(全筋を力比で着色)。
    """
    entry = cond["cache"]
    transforms = _bodies_at(entry, fi)
    if align_dx:
        transforms = {b: T.copy() for b, T in transforms.items()}
        for b in transforms:
            transforms[b][0, 3] += align_dx

    bones = build_posed_model(body_meshes, transforms)
    if bones.n_points > 0:
        pl.add_mesh(bones, color=BONE_COLOR, opacity=bone_opacity,
                    smooth_shading=True, specular=0.2)

    p = float(entry["phases"][fi])
    radius = entry["radius"]
    is_ham = entry["is_ham"]
    dyn = entry.get("dyn", {})
    strain = cond["strain"]
    for nm, frames in entry["muscles"].items():
        pts = np.asarray(frames[fi], dtype=float)
        if align_dx:
            pts = pts.copy()
            pts[:, 0] += align_dx
        ham = is_ham.get(nm, False)
        r = radius.get(nm, 0.005)

        if color_mode == "activation" and nm in dyn:
            a = _series_at(dyn[nm], p, "act")
            col, op = act_color(a), 0.45 + 0.5 * a
            rr = r * (0.7 + 0.9 * a)            # 活性で太く
        elif color_mode == "force" and nm in dyn:
            fr = _series_at(dyn[nm], p, "force")
            col, op = act_color(min(fr, 1.0)), 0.45 + 0.5 * min(fr, 1.0)
            rr = r * (0.7 + 0.9 * min(fr, 1.0))
        elif ham:
            col, op, rr = strain_color(strain_at(strain, nm, p)), \
                muscle_opacity_ham, r
        else:
            col, op, rr = NONHAM_COLOR, muscle_opacity_nonham, r * 0.8

        tube = muscle_tube(pts, rr)
        if tube is not None:
            pl.add_mesh(tube, color=col, opacity=op, smooth_shading=True,
                        specular=0.25)

    if show_grf:
        gf = entry.get("grf_force", None)
        # 接地足: GRF の鉛直成分が立っている側を calcn 高さで判定 (右優先)
        foot = None
        for fb in ("calcn_r", "calcn_l"):
            if fb in transforms:
                foot = transforms[fb][:3, 3]
                if transforms[fb][1, 3] < 0.12:    # 低い=接地
                    break
        arrow = _grf_arrow(gf[fi] if gf is not None else None, foot, 0.0)
        if arrow is not None:
            pl.add_mesh(arrow, color=GRF_COLOR, opacity=0.9, smooth_shading=True)
    return transforms["pelvis"][0, 3]


# ═══════════════════════════════════════════════════════════════════════════
# フレーム描画
# ═══════════════════════════════════════════════════════════════════════════

def render_sidebyside_frame(conds, fi, body_meshes, window_size,
                            color_mode="strain", show_grf=True):
    n = len(conds)
    pv.global_theme.background = "white"
    pl = pv.Plotter(off_screen=True, shape=(1, n), window_size=list(window_size),
                    border=False)
    for i, cond in enumerate(conds):
        pl.subplot(0, i)
        cx = _draw_one(pl, cond, fi, body_meshes, color_mode=color_mode,
                       show_grf=show_grf)
        frame_sagittal(pl, zoom=1.18)
        add_ground(pl, cx)
        add_lights(pl, cx)
        pl.add_text(f"{cond['label']}\n(mean tilt {cond['mean_tilt']:.1f} deg)",
                    position="upper_left", font_size=11, color="black")
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


def render_overlay_frame(conds, fi, body_meshes, window_size,
                         color_mode="strain", show_grf=True):
    pv.global_theme.background = "white"
    pl = pv.Plotter(off_screen=True, window_size=list(window_size), border=False)
    base_cx = None
    for cond in conds:
        cx0 = cond["cache"]["bodies"]["pelvis"][fi][0, 3]
        if base_cx is None:
            base_cx = cx0
        _draw_one(pl, cond, fi, body_meshes, bone_opacity=0.32,
                  muscle_opacity_nonham=0.3, muscle_opacity_ham=0.96,
                  align_dx=base_cx - cx0, color_mode=color_mode, show_grf=False)
    add_ground(pl, base_cx)
    frame_sagittal(pl, zoom=1.18)
    add_lights(pl, base_cx)
    handles = "  |  ".join(f"{c['label']} ({c['mean_tilt']:.1f}deg)" for c in conds)
    pl.add_text("Overlay (pelvis-aligned): " + handles, position="upper_left",
                font_size=11, color="black")
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


# ═══════════════════════════════════════════════════════════════════════════
# 出力生成
# ═══════════════════════════════════════════════════════════════════════════

def _frame_seq(F, n_frames, cycles):
    """[0,F) を n_frames 個に再標本化したインデックス列を cycles 回ループ。"""
    base = (np.linspace(0.0, 1.0, n_frames, endpoint=False) * F).astype(int) % F
    return np.tile(base, cycles)


def write_mp4(frame_fn, conds, body_meshes, out_path, n_frames, cycles, fps,
              window_size, color_mode="strain", show_grf=True):
    import imageio
    F = len(conds[0]["cache"]["phases"])
    seq = _frame_seq(F, n_frames, cycles)
    print(f"  {out_path.name}: {len(seq)} フレーム生成中 ...")
    writer = imageio.get_writer(str(out_path), fps=fps, codec="libx264",
                                quality=8, output_params=["-pix_fmt", "yuv420p"])
    try:
        for k, fi in enumerate(seq):
            writer.append_data(frame_fn(conds, int(fi), body_meshes, window_size,
                                        color_mode=color_mode, show_grf=show_grf))
            if (k + 1) % 15 == 0 or k == len(seq) - 1:
                print(f"    {k + 1}/{len(seq)}")
    finally:
        writer.close()
    mb = out_path.stat().st_size / (1024 * 1024)
    print(f"  [OK] {out_path.name}  ({mb:.1f} MB)")


def peak_stretch_index(conds):
    """最前傾条件のハム最大 lMtilde に対応するキャッシュ frame index。"""
    cond = min(conds, key=lambda c: c["mean_tilt"])
    phases = cond["cache"]["phases"]
    best_idx, best_v = int(len(phases) * 0.8) % len(phases), -np.inf
    for nm in ("bifemlh_r", "semimem_r", "semiten_r"):
        v = [strain_at(cond["strain"], nm, p) for p in phases]
        j = int(np.nanargmax(v))
        if v[j] > best_v:
            best_v, best_idx = v[j], j
    return best_idx


def peak_stance_index(conds):
    """GRF 最大 (接地ピーク) のキャッシュ frame index。GRF 無ければ中央。"""
    cond = conds[0]
    F = cond["cache"].get("grf_force", None)
    if F is None:
        return len(cond["cache"]["phases"]) // 4
    return int(np.argmax(np.linalg.norm(np.asarray(F), axis=1)))


def hero_index(conds, color_mode):
    """色モードに応じた hero フレーム: strain=最大伸張 / 他=接地ピーク(GRF可視)。"""
    return (peak_stretch_index(conds) if color_mode == "strain"
            else peak_stance_index(conds))


def write_hero_still(conds, body_meshes, out_path, window_size,
                    color_mode="strain", show_grf=True):
    fi = hero_index(conds, color_mode)
    img = render_sidebyside_frame(conds, fi, body_meshes, window_size,
                                  color_mode=color_mode, show_grf=show_grf)
    fig, ax = plt.subplots(figsize=(window_size[0] / 130, window_size[1] / 130))
    ax.imshow(img)
    ax.axis("off")
    p = float(conds[0]["cache"]["phases"][fi])
    if color_mode == "strain":
        ax.set_title(f"ピーク伸張位相 ({p * 100:.0f}%) のハムストリングひずみ比較 "
                 f"(wrapping込み筋経路)", fontsize=14, fontweight="bold")
        sm = ScalarMappable(norm=Normalize(LM_VMIN, LM_VMAX), cmap=STRAIN_CMAP)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.01)
        cbar.set_label("ハム正規化筋線維長 lMtilde (高=伸張・肉離れリスク大)",
                       fontsize=10)
    else:
        kindjp = "筋活性化 (act)" if color_mode == "activation" else "筋力比 (Fce/Fiso)"
        ax.set_title(f"ピーク伸張位相 ({p * 100:.0f}%) の全身{kindjp} + GRF",
                     fontsize=14, fontweight="bold")
        sm = ScalarMappable(norm=Normalize(0, 1), cmap=ACT_CMAP)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.01)
        cbar.set_label(f"{kindjp} (高=強く働いている)", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {out_path.name}")


# ═══════════════════════════════════════════════════════════════════════════
# 条件読込 + main
# ═══════════════════════════════════════════════════════════════════════════

def load_conditions(results_dir, cache):
    conds = []
    for off, ident in CONDITION_SPECS:
        if ident not in cache:
            print(f"  [WARN] cache に {ident} なし。スキップ")
            continue
        data = sorted(results_dir.glob(f"pred_sprinting_data_*{ident}*.mat"))
        if not data:
            print(f"  [WARN] {ident} の .mat なし。スキップ")
            continue
        entry = cache[ident]
        strain = load_hamstring_strain(data[-1])
        label = f"{off:+d}deg" if off != 0 else "0deg(nominal)"
        conds.append({
            "offset": off, "label": label, "mean_tilt": entry["mean_tilt"],
            "cache": entry, "strain": strain,
        })
        print(f"  [OK] {ident:18s} mean tilt {entry['mean_tilt']:6.2f} deg, "
              f"{len(entry['phases'])} frames")
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
        description="骨盤前後傾オフセットのリッチ筋骨格可視化 (wrapping込み筋経路)")
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--cycles", type=int, default=2)
    ap.add_argument("--width", type=int, default=1680)
    ap.add_argument("--height", type=int, default=950)
    ap.add_argument("--output_dir", type=str, default=None)
    ap.add_argument("--skip_video", action="store_true")
    ap.add_argument("--only", choices=["both", "side", "overlay"], default="both")
    ap.add_argument("--color", choices=["strain", "activation", "force"],
                    default="strain",
                    help="筋の着色: strain=ハムひずみ / activation=全身活性 / force=全身力")
    ap.add_argument("--no_grf", action="store_true", help="GRF ベクトルを描かない")
    args = ap.parse_args()

    setup_japanese_font()

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    results_dir = project_root / "Results"
    out_dir = (Path(args.output_dir) if args.output_dir
               else results_dir / "PelvicShift_Study")
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_path = out_dir / CACHE_NAME

    print("=" * 70)
    print("  骨盤前後傾オフセット × リッチ筋骨格可視化 (wrapping込み筋経路)")
    print("=" * 70)

    if not cache_path.exists():
        print(f"ERROR: 筋経路キャッシュが見つかりません: {cache_path}")
        print("  先に opensim 対応 env で compute_osim_muscle_paths.py を実行してください:")
        print("  & '<opencap env>\\python.exe' analysis/compute_osim_muscle_paths.py --frames 60")
        return 1
    with open(cache_path, "rb") as f:
        cache = pickle.load(f)
    print(f"  cache: {cache_path.name}  ({len(cache)} 条件)")

    geom_dir = find_geometry_dir()
    print(f"  Geometry: {geom_dir}")
    body_meshes = load_body_meshes(geom_dir)
    print(f"  body メッシュ数: {len(body_meshes)}")

    print("\n--- 条件読み込み ---")
    conds = load_conditions(results_dir, cache)
    if len(conds) < 2:
        print("ERROR: 比較できる条件が不足しています。")
        return 1

    win = (args.width, args.height)
    cm = args.color
    grf = not args.no_grf
    # strain モードは従来ファイル名、activation/force はサフィックス付き
    suf = "" if cm == "strain" else f"_{cm}"
    print(f"\n--- 出力生成 (color={cm}, GRF={'on' if grf else 'off'}) ---")
    if args.only == "both":
        write_hero_still(conds, body_meshes,
                         out_dir / f"pelvic_shift_musculoskeletal{suf}_hero.png",
                         win, color_mode=cm, show_grf=grf)
    if not args.skip_video:
        if args.only in ("both", "side"):
            write_mp4(render_sidebyside_frame, conds, body_meshes,
                      out_dir / f"pelvic_shift_musculoskeletal{suf}_sidebyside.mp4",
                      args.frames, args.cycles, args.fps, win,
                      color_mode=cm, show_grf=grf)
        if args.only in ("both", "overlay"):
            write_mp4(render_overlay_frame, conds, body_meshes,
                      out_dir / f"pelvic_shift_musculoskeletal{suf}_overlay.mp4",
                      args.frames, args.cycles, args.fps,
                      (int(win[0] * 0.65), win[1]), color_mode=cm, show_grf=grf)

    print(f"\n{'=' * 70}\n  完了! 出力先: {out_dir}\n{'=' * 70}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
