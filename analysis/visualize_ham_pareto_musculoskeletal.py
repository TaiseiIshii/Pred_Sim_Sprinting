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
    (0,  "HamPareto_Nom_w0000"),
    (8,  "HamPareto_Nom_w0800"),
    (32, "HamPareto_Nom_w3200"),
]

# ident -> ASCII panel label (VTK は日本語不可) と 最高速度(m/s)。w=傷害ペナルティ重み。
COND_LABEL = {
    "HamPareto_Nom_w0000": "w=0 (current)",
    "HamPareto_Nom_w0800": "w=0.8",
    "HamPareto_Nom_w3200": "w=3.2 (safest)",
}
COND_SPEED = {
    "HamPareto_Nom_w0000": 11.78,
    "HamPareto_Nom_w0800": 11.60,
    "HamPareto_Nom_w3200": 11.51,
}

# .mat muscleValues.lMtilde の行 (1-based) → ハム基底名
HAM_ROW_1BASED = {
    "semimem_l": 7,  "semiten_l": 8,  "bifemlh_l": 9,  "bifemsh_l": 10,
    "semimem_r": 53, "semiten_r": 54, "bifemlh_r": 55, "bifemsh_r": 56,
}

# ひずみ着色レンジ (固定 = 条件横断で比較可能)。低=緑, 高=赤。
# レンジを狭めて条件差(=数%のlMtilde差)が色で見えるようにする。
LM_VMIN, LM_VMAX = 0.92, 1.14
STRAIN_CMAP = plt.get_cmap("RdYlGn_r")

# 筋活性化 (0..1) のカラーマップ。低=青灰, 高=赤 (筋電図風)。
ACT_CMAP = plt.get_cmap("turbo")

BONE_COLOR = (0.92, 0.89, 0.82)
NONHAM_COLOR = (0.50, 0.11, 0.11)
# strain モードでは非ハム筋を薄いグレーに沈めてハムの色を際立たせる
NONHAM_STRAIN_COLOR = (0.78, 0.76, 0.72)
NONHAM_STRAIN_OPACITY = 0.16
HAM_EMPHASIS_SCALE = 1.9     # strain モードでハム筋を太く描いて見やすく
GRF_COLOR = (0.10, 0.45, 0.95)
GRF_SCALE = 0.00018          # N -> m (体重~750N で ~0.7m の矢)

# 足の軌跡トレース (右つま先 toes_r) — スイング高さの違いを可視化
FOOT_TRACE_BODY = "toes_r"
FOOT_TRACE_COLOR = (1.0, 0.50, 0.05)     # 当該条件: オレンジ
FOOT_GHOST_COLOR = (0.45, 0.47, 0.55)    # 基準(0deg)の影: 灰
FOOT_TRACE_RADIUS = 0.007

# 共有カメラ (3枚を同一スケール/接地位置で固定 → 足の高さを横断比較可能)
SHARED_FOCAL = (0.0, 0.92, 0.0)
SHARED_PARALLEL_SCALE = 1.08

# 右側の凡例ストリップ幅 (px)
LEGEND_W = 250
_LEGEND_CACHE = {}

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


def set_shared_camera(pl):
    """全パネル共通の固定平行投影カメラ。接地(y=0)とスケールを揃え、足の高さを
    パネル横断で直接比較できるようにする (treadmill で pelvis_x は 0 固定)。"""
    pl.enable_parallel_projection()
    cam = pl.camera
    cam.focal_point = SHARED_FOCAL
    cam.position = (SHARED_FOCAL[0], SHARED_FOCAL[1], SHARED_FOCAL[2] + 3.0)
    cam.up = (0.0, 1.0, 0.0)
    cam.parallel_scale = SHARED_PARALLEL_SCALE


def add_height_ruler(pl, with_labels=False):
    """固定高さの水平グリッド線 (高さ定規)。y=0 は接地線として濃く太く描く。
    with_labels=True (左端パネル) のとき高さラベルを付す。"""
    x0, x1 = -0.85, 0.85
    levels = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6]
    for y in levels:
        ground = (y == 0.0)
        line = pv.Line((x0, y, 0.0), (x1, y, 0.0))
        pl.add_mesh(line, color=(0.30, 0.30, 0.30) if ground else (0.80, 0.80, 0.82),
                    line_width=3 if ground else 1, opacity=0.95 if ground else 0.55)
    if with_labels:
        try:
            pts = np.array([[-0.48, y, 0.0] for y in (0.0, 0.5, 1.0, 1.5)])
            labels = ["0.0m", "0.5m", "1.0m", "1.5m"]
            pl.add_point_labels(pts, labels, font_size=12, text_color="black",
                                shape=None, show_points=False, always_visible=True)
        except Exception:
            pass


def foot_trace_pts(entry, body=FOOT_TRACE_BODY):
    """全フレームの足 body 位置 (F,3) を返す。スイング軌跡の描画用。"""
    if body not in entry["bodies"]:
        return None
    T = entry["bodies"][body]            # (F,4,4)
    return np.asarray(T[:, :3, 3], dtype=float)


def add_foot_trace(pl, pts, color, opacity, align_dx=0.0):
    """足の軌跡 (F,3) を細いチューブで描く。"""
    if pts is None or len(pts) < 3:
        return
    p = pts.copy()
    if align_dx:
        p[:, 0] += align_dx
    try:
        poly = pv.lines_from_points(p)
        tube = poly.tube(radius=FOOT_TRACE_RADIUS, n_sides=8, capping=False)
        pl.add_mesh(tube, color=color, opacity=opacity, smooth_shading=True)
    except Exception:
        pass


def build_legend_strip(mode, height, width=LEGEND_W):
    """右側に付ける固定カラーバー凡例 (matplotlib で1回だけ生成しキャッシュ)。"""
    key = (mode, height, width)
    if key in _LEGEND_CACHE:
        return _LEGEND_CACHE[key]
    fig = plt.figure(figsize=(width / 100.0, height / 100.0), dpi=100)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.16, 0.16, 0.26, 0.66])
    if mode == "strain":
        sm = ScalarMappable(norm=Normalize(LM_VMIN, LM_VMAX), cmap=STRAIN_CMAP)
        sm.set_array([])
        cb = fig.colorbar(sm, cax=ax)
        cb.set_label("ハム正規化筋線維長 lMtilde", fontsize=10)
        fig.text(0.10, 0.90, "もも裏の伸び具合", fontsize=12, fontweight="bold")
        fig.text(0.52, 0.74, "赤 = 伸びている\n（肉離れリスク大）", fontsize=10,
                 color="#a01010", va="top")
        fig.text(0.52, 0.34, "緑 = 余裕あり\n（低リスク）", fontsize=10,
                 color="#1a7a1a", va="top")
        fig.text(0.06, 0.085, "オレンジ線 = 右足の軌跡\n灰の線 = 基準(現状 w=0)の足軌跡\n"
                 "横線 = 高さ定規", fontsize=8.5, va="top")
    else:
        kindjp = "筋活性化 act" if mode == "activation" else "筋力比 Fce/Fiso"
        sm = ScalarMappable(norm=Normalize(0, 1), cmap=ACT_CMAP)
        sm.set_array([])
        cb = fig.colorbar(sm, cax=ax)
        cb.set_label(kindjp, fontsize=10)
        fig.text(0.10, 0.90, "筋の働き", fontsize=12, fontweight="bold")
        fig.text(0.52, 0.74, "赤 = フル稼働", fontsize=10, color="#a01010")
        fig.text(0.52, 0.30, "青 = 休み", fontsize=10, color="#10408a")
        fig.text(0.06, 0.085, "青矢印 = 地面反力(GRF)\n横線 = 高さ定規",
                 fontsize=8.5, va="top")
    fig.canvas.draw()
    arr = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
    plt.close(fig)
    if arr.shape[0] != height:           # 念のため高さを合わせる
        arr = arr[:height] if arr.shape[0] > height else np.pad(
            arr, ((0, height - arr.shape[0]), (0, 0), (0, 0)), constant_values=255)
    _LEGEND_CACHE[key] = arr
    return arr


def draw_phase_bar(img, p):
    """フレーム下端に位相進捗バーを描く (0=接地直後 .. 1=1周)。"""
    h, w = img.shape[:2]
    bh = max(7, h // 110)
    img[h - bh:h, :, :] = 232
    xw = int(w * float(np.clip(p, 0.0, 1.0)))
    img[h - bh:h, :xw, :] = (45, 45, 48)
    return img



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
            col = strain_color(strain_at(strain, nm, p))
            op = muscle_opacity_ham
            rr = r * (HAM_EMPHASIS_SCALE if color_mode == "strain" else 1.0)
        elif color_mode == "strain":
            col, op, rr = NONHAM_STRAIN_COLOR, NONHAM_STRAIN_OPACITY, r * 0.7
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
                            color_mode="strain", show_grf=True, with_legend=True):
    n = len(conds)
    legend_w = LEGEND_W if with_legend else 0
    panel_w = max(240, int(window_size[0]) - legend_w)
    H = int(window_size[1])
    pv.global_theme.background = "white"
    pl = pv.Plotter(off_screen=True, shape=(1, n), window_size=[panel_w, H],
                    border=False)
    nom_trace = next((c.get("foot_trace") for c in conds if c["offset"] == 0), None)
    for i, cond in enumerate(conds):
        pl.subplot(0, i)
        _draw_one(pl, cond, fi, body_meshes, color_mode=color_mode,
                  show_grf=show_grf)
        add_height_ruler(pl, with_labels=(i == 0))
        # 足の軌跡: 基準(0°)の影を全パネルに重ね、当該条件をオレンジで強調
        if nom_trace is not None and cond["offset"] != 0:
            add_foot_trace(pl, nom_trace, FOOT_GHOST_COLOR, 0.34)
        add_foot_trace(pl, cond.get("foot_trace"), FOOT_TRACE_COLOR, 0.65)
        add_lights(pl, 0.0)
        set_shared_camera(pl)
        # パネル見出し (VTK は日本語不可のため ASCII)
        spd = cond.get("speed")
        spd_s = f"speed {spd:.2f} m/s\n" if spd is not None else ""
        pk = cond.get("peak_strain")
        pk_s = f"peak ham lMtilde {pk:.2f}" if pk is not None else ""
        pl.add_text(f"{cond['label']}\n{spd_s}{pk_s}", position="upper_left", font_size=11,
                    color="black")
    img = np.asarray(pl.screenshot(return_img=True))[:, :, :3]
    pl.close()
    if with_legend:
        legend = build_legend_strip(color_mode, img.shape[0])
        legend = legend[:img.shape[0]]
        img = np.hstack([img, legend])
    img = draw_phase_bar(img, float(conds[0]["cache"]["phases"][fi]))
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
    handles = "  |  ".join(f"{c['label']}" for c in conds)
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


def write_gif(frame_fn, conds, body_meshes, out_path, n_frames, cycles, fps,
              window_size, color_mode="strain", show_grf=True, max_w=1000):
    """走行アニメーションを GIF で保存 (Markdown にインライン埋め込み可能)。
    各フレームを max_w に縮小し適応 256 色パレット化して軽量化する。"""
    from PIL import Image
    F = len(conds[0]["cache"]["phases"])
    seq = _frame_seq(F, n_frames, cycles)
    print(f"  {out_path.name}: {len(seq)} フレーム生成中 ...")
    pil = []
    for k, fi in enumerate(seq):
        img = np.asarray(frame_fn(conds, int(fi), body_meshes, window_size,
                                  color_mode=color_mode, show_grf=show_grf))[:, :, :3]
        im = Image.fromarray(img)
        w, h = im.size
        if w > max_w:
            im = im.resize((max_w, int(round(h * max_w / w))), Image.LANCZOS)
        pil.append(im.convert("P", palette=Image.ADAPTIVE, colors=256))
        if (k + 1) % 15 == 0 or k == len(seq) - 1:
            print(f"    {k + 1}/{len(seq)}")
    pil[0].save(str(out_path), save_all=True, append_images=pil[1:],
                duration=int(round(1000.0 / fps)), loop=0, optimize=True, disposal=2)
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
                                  color_mode=color_mode, show_grf=show_grf,
                                  with_legend=False)
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

def load_speeds(study_dir):
    """pelvic_shift_summary.csv から offset->speed を読む (無ければ空)。"""
    import csv as _csv
    path = Path(study_dir) / "pelvic_shift_summary.csv"
    out = {}
    if not path.exists():
        return out
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            for row in _csv.DictReader(fh):
                try:
                    out[int(round(float(row["offset"])))] = float(row["speed"])
                except (KeyError, ValueError):
                    pass
    except Exception:
        pass
    return out


def _peak_ham_strain(strain):
    """3つの二関節ハム(右)の位相横断 lMtilde 最大 = ピーク伸張。"""
    best = np.nan
    grid = np.linspace(0, 1, 60)
    for nm in ("semimem_r", "semiten_r", "bifemlh_r"):
        if nm in strain:
            v = max(strain_at(strain, nm, p) for p in grid)
            best = v if not np.isfinite(best) else max(best, v)
    return None if not np.isfinite(best) else float(best)


def load_conditions(results_dir, cache, study_dir=None):
    conds = []
    speeds = load_speeds(study_dir if study_dir is not None
                         else results_dir / "HamPareto_Study")
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
        label = COND_LABEL.get(ident, f"w={off/10:.1f}")
        conds.append({
            "offset": off, "label": label, "mean_tilt": entry["mean_tilt"],
            "cache": entry, "strain": strain,
            "foot_trace": foot_trace_pts(entry),
            "peak_strain": _peak_ham_strain(strain),
            "speed": COND_SPEED.get(ident),
        })
        print(f"  [OK] {ident:18s} mean tilt {entry['mean_tilt']:6.2f} deg, "
              f"{len(entry['phases'])} frames")
    return conds


def setup_japanese_font():
    import os
    try:
        import matplotlib.font_manager as fm
        for _f in [r"C:\Windows\Fonts\meiryo.ttc", r"C:\Windows\Fonts\YuGothM.ttc",
                   r"C:\Windows\Fonts\msgothic.ttc"]:
            if os.path.exists(_f):
                fm.fontManager.addfont(_f)
                plt.rcParams["font.family"] = fm.FontProperties(fname=_f).get_name()
                break
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
    ap.add_argument("--gif", action="store_true",
                    help="側面比較を GIF でも出力 (Markdown 埋め込み用・軽量)")
    args = ap.parse_args()

    setup_japanese_font()

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    results_dir = project_root / "Results"
    out_dir = (Path(args.output_dir) if args.output_dir
               else results_dir / "HamPareto_Study")
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_path = out_dir / CACHE_NAME

    print("=" * 70)
    print("  傷害最小化テクニック(ペナルティ重み) × リッチ筋骨格可視化 (wrapping込み筋経路)")
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
    conds = load_conditions(results_dir, cache, out_dir)
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
                         out_dir / f"ham_pareto_musculoskeletal{suf}_hero.png",
                         win, color_mode=cm, show_grf=grf)
    if not args.skip_video:
        if args.only in ("both", "side"):
            write_mp4(render_sidebyside_frame, conds, body_meshes,
                      out_dir / f"ham_pareto_musculoskeletal{suf}_sidebyside.mp4",
                      args.frames, args.cycles, args.fps, win,
                      color_mode=cm, show_grf=grf)
        if args.only in ("both", "overlay"):
            write_mp4(render_overlay_frame, conds, body_meshes,
                      out_dir / f"ham_pareto_musculoskeletal{suf}_overlay.mp4",
                      args.frames, args.cycles, args.fps,
                      (int(win[0] * 0.65), win[1]), color_mode=cm, show_grf=grf)

    if args.gif:
        write_gif(render_sidebyside_frame, conds, body_meshes,
                  out_dir / f"ham_pareto_musculoskeletal{suf}_sidebyside.gif",
                  args.frames, args.cycles, args.fps, win,
                  color_mode=cm, show_grf=grf)

    print(f"\n{'=' * 70}\n  完了! 出力先: {out_dir}\n{'=' * 70}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
