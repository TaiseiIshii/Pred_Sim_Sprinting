"""
visualize_pelvic_shift_musculoskeletal.py
骨盤前後傾オフセット条件の「リッチ」筋骨格可視化 (棒人間ではなく実OpenSim骨メッシュ+筋)

実OpenSim 4.x の Geometry (.vtp 骨メッシュ) をフォワードキネマティクスで配置し、
.osim から抽出した主要下肢筋の経路を 3D チューブで重ね描きする。ハムストリング
4筋 (semimembranosus, semitendinosus, biceps femoris long/short head) は、各条件の
最適化結果 (.mat) の正規化筋線維長 lMtilde で色付けし、「伸張 = 肉離れリスク」を
直接 3D で表現する。代表3条件 (-6° / 0° / +6°) を比較する:

  1) 横並びアニメーション (sidebyside MP4)   — 各条件を並置
  2) 重ね合わせアニメーション (overlay MP4)   — 骨盤を揃え骨を半透明、ハムを強調
  3) ピーク伸張スチル (hero PNG)              — 最大伸張位相 + ひずみカラーバー

既存の FK / メッシュ読込ヘルパ (visualize_form_comparison_v2.py) を再利用する。

Usage:
    python visualize_pelvic_shift_musculoskeletal.py
    python visualize_pelvic_shift_musculoskeletal.py --fps 25 --frames 70 --cycles 2

依存: pyvista, vtk, imageio (+imageio-ffmpeg), scipy, numpy, matplotlib
推奨実行: conda base python (pyvista/vtk/imageio_ffmpeg が入っている環境)

Date: 2026-06-21
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pyvista as pv
from scipy.io import loadmat

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

# 既存スクリプトから FK エンジン・ジオメトリ読込を再利用
from visualize_form_comparison_v2 import (
    BODY_GEOMETRY,
    compute_body_transforms,
    read_mot,
    simplify_column,
    find_geometry_dir,
    load_body_meshes,
    build_posed_model,
)

# ═══════════════════════════════════════════════════════════════════════════
# 設定
# ═══════════════════════════════════════════════════════════════════════════

# 代表3条件 (offset deg, ファイル名識別子)
CONDITION_SPECS = [
    (-6, "PelvisShift_m06"),
    (0,  "PelvisShift_p00"),
    (6,  "PelvisShift_p06"),
]

# ハムストリング4筋の基底名 (強調 + ひずみ着色)
HAM_BASES = ("semimem", "semiten", "bifemlh", "bifemsh")

# .mat muscleValues.lMtilde の行番号 (1-based) → ハム基底名
#   左 7,8,9,10 / 右 53,54,55,56  (semimem, semiten, bifemlh, bifemsh)
HAM_ROW_1BASED = {
    "semimem_l": 7,  "semiten_l": 8,  "bifemlh_l": 9,  "bifemsh_l": 10,
    "semimem_r": 53, "semiten_r": 54, "bifemlh_r": 55, "bifemsh_r": 56,
}

# 描画する主要下肢筋 (基底名; _r/_l を付けて探索, 無いものは自動スキップ)
CURATED_MUSCLE_BASES = (
    # 殿筋
    "glut_max1", "glut_max2", "glut_max3",
    "glut_med1", "glut_med2", "glut_med3",
    "glut_min1", "glut_min2", "glut_min3",
    # ハムストリング (強調)
    "semimem", "semiten", "bifemlh", "bifemsh",
    # 大腿四頭筋
    "rect_fem", "vas_med", "vas_int", "vas_lat",
    # 下腿三頭筋 + 前脛骨
    "med_gas", "lat_gas", "soleus", "tib_ant", "tib_post",
    # 股関節屈筋・内転筋・その他
    "psoas", "iliacus",
    "add_long", "add_brev", "add_mag1", "add_mag2", "add_mag3",
    "sar", "tfl", "grac",
    "per_long", "per_brev",
)

# ひずみ着色レンジ (固定 = 条件横断で比較可能)。低=緑, 高=赤。
LM_VMIN, LM_VMAX = 0.85, 1.18
STRAIN_CMAP = plt.get_cmap("RdYlGn_r")

# 外観
BONE_COLOR = (0.92, 0.89, 0.82)
NONHAM_COLOR = (0.55, 0.20, 0.20)
HAM_TUBE_RADIUS = 0.0085
NONHAM_TUBE_RADIUS = 0.0040

XVIEW = "side"  # サジタル


# ═══════════════════════════════════════════════════════════════════════════
# 1) 筋経路パーサ (.osim)
# ═══════════════════════════════════════════════════════════════════════════

def _local_tag(elem):
    """名前空間を除いたタグ名。"""
    return elem.tag.split("}")[-1]


def parse_muscle_paths(osim_path):
    """.osim から各筋の経路点 [(body_name, location_vec3), ...] を抽出する。

    PathPoint / ConditionalPathPoint (location を持つ) を採用。
    MovingPathPoint (location を関数で持つ) は近似のためスキップする。
    戻り値: {muscle_name: [(body, np.array([x,y,z])), ...]} (>=2 点のもののみ)
    """
    # OpenSim の .osim はタグ名に '::' を含む (例 HuntCrossleyForce::ContactParametersSet)
    # ため、厳密 XML としては不正トークンになる。'::' を '_' に置換して well-formed 化する
    # (筋関連タグ Thelen2003Muscle / PathPoint / socket_parent_frame / location には影響なし)。
    text = Path(osim_path).read_text(encoding="utf-8", errors="replace")
    text = text.replace("::", "_")
    root = ET.fromstring(text)

    muscle_tags = {"Thelen2003Muscle", "Millard2012EquilibriumMuscle",
                   "RigidTendonMuscle", "DeGrooteFregly2016Muscle"}
    point_tags = {"PathPoint", "ConditionalPathPoint"}

    muscle_paths = {}
    for elem in root.iter():
        if _local_tag(elem) not in muscle_tags:
            continue
        name = elem.get("name", "")
        if not name:
            continue
        # GeometryPath/PathPointSet/objects 配下の点を文書順に取得
        pts = []
        for pp in elem.iter():
            if _local_tag(pp) not in point_tags:
                continue
            frame_el = pp.find("socket_parent_frame")
            loc_el = pp.find("location")
            if frame_el is None or loc_el is None or not loc_el.text:
                continue  # MovingPathPoint など location 無しは近似スキップ
            body = frame_el.text.strip().split("/")[-1]
            try:
                loc = np.array([float(v) for v in loc_el.text.split()],
                               dtype=float)
            except ValueError:
                continue
            if loc.size == 3:
                pts.append((body, loc))
        if len(pts) >= 2:
            muscle_paths[name] = pts
    return muscle_paths


def base_name(muscle_name):
    """'bifemlh_r' -> 'bifemlh' (末尾 _r/_l を除去)。"""
    if muscle_name.endswith("_r") or muscle_name.endswith("_l"):
        return muscle_name[:-2]
    return muscle_name


def select_curated(muscle_paths):
    """描画対象を curated 集合に絞る。{name: pts, is_ham}。"""
    wanted = set()
    for base in CURATED_MUSCLE_BASES:
        wanted.add(base + "_r")
        wanted.add(base + "_l")
    out = {}
    for name, pts in muscle_paths.items():
        if name in wanted:
            out[name] = pts
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 2) ハムストリングひずみ loader (.mat)
# ═══════════════════════════════════════════════════════════════════════════

def _get(o, *names):
    for n in names:
        try:
            o = getattr(o, n)
        except AttributeError:
            o = o[n]
    return o


def load_hamstring_strain(mat_path):
    """.mat の muscleValues.lMtilde からハム4筋(L/R)の位相→lMtilde を作る。

    戻り値: {muscle_name: (phases_array, lMtilde_array)}  位相は [0,1]。
    """
    m = loadmat(str(mat_path), struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    lM = np.asarray(_get(o, "muscleValues", "lMtilde"), dtype=float)  # (92, ncol)
    ncol = lM.shape[1]
    phases = np.linspace(0.0, 1.0, ncol)
    strain = {}
    for mname, row1 in HAM_ROW_1BASED.items():
        strain[mname] = (phases, lM[row1 - 1, :].copy())
    return strain


def strain_at(strain, muscle_name, p):
    """位相 p における lMtilde を補間。無ければ NaN。"""
    if muscle_name not in strain:
        return np.nan
    ph, vals = strain[muscle_name]
    return float(np.interp(np.clip(p, 0.0, 1.0), ph, vals))


def strain_color(lm_val):
    """lMtilde 値 → RGB (0..1)。"""
    if not np.isfinite(lm_val):
        return (0.6, 0.6, 0.6)
    t = (lm_val - LM_VMIN) / (LM_VMAX - LM_VMIN)
    t = float(np.clip(t, 0.0, 1.0))
    r, g, b, _ = STRAIN_CMAP(t)
    return (r, g, b)


# ═══════════════════════════════════════════════════════════════════════════
# 3) 位相補間 (.mot)
# ═══════════════════════════════════════════════════════════════════════════

def build_phase_data(df):
    """`.mot` DataFrame からストライド位相 [0,1] 補間データを作る。"""
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


# ═══════════════════════════════════════════════════════════════════════════
# 4) 描画ヘルパ
# ═══════════════════════════════════════════════════════════════════════════

def world_polyline(path_pts, transforms):
    """筋経路点を world 座標 Nx3 に変換。body が無ければ None。"""
    out = []
    for body, loc in path_pts:
        if body not in transforms:
            return None
        T = transforms[body]
        w = T @ np.array([loc[0], loc[1], loc[2], 1.0])
        out.append(w[:3])
    pts = np.asarray(out, dtype=float)
    if len(pts) < 2:
        return None
    return pts


def polyline_tube(points, radius, n_interp=50):
    """world 折れ線 → チューブ mesh。"""
    try:
        n = max(n_interp, len(points))
        spline = pv.Spline(points, n)
        return spline.tube(radius=radius, n_sides=10)
    except Exception:
        try:
            poly = pv.lines_from_points(np.asarray(points, dtype=float))
            return poly.tube(radius=radius, n_sides=10)
        except Exception:
            return None


def add_ground(pl, cx):
    ground = pv.Plane(center=(cx, 0.0, 0.0), direction=(0, 1, 0),
                      i_size=4.0, j_size=2.4, i_resolution=8, j_resolution=8)
    pl.add_mesh(ground, color="#8B7355", opacity=0.18, style="wireframe",
                line_width=1)


def frame_sagittal(pl, zoom=1.0):
    """現在の actor(骨+筋)の bounds に合わせてサジタル視点で自動フレーミング。

    地面を追加する *前* に呼ぶこと(地面で bounds が広がるのを避ける)。
    """
    pl.view_vector((0.0, 0.0, 1.0), viewup=(0.0, 1.0, 0.0))
    pl.reset_camera()
    if zoom != 1.0:
        pl.camera.zoom(zoom)


def add_lights(pl, cx):
    pl.add_light(pv.Light(position=(cx + 2, 3, 3), intensity=0.65))
    pl.add_light(pv.Light(position=(cx - 2, 3, -3), intensity=0.35))


def _draw_one(pl, cond, p, body_meshes, muscles, *, bone_opacity=1.0,
              muscle_opacity_nonham=0.45, muscle_opacity_ham=0.97,
              align_dx=0.0):
    """1体ぶんの骨+筋を現在の (sub)plot に描く。pelvis world x を返す。"""
    q = q_at_phase(cond["phases"], cond["col_map"], p, treadmill=True)
    transforms = compute_body_transforms(q)
    if align_dx:
        for b in transforms:
            transforms[b] = transforms[b].copy()
            transforms[b][0, 3] += align_dx

    bones = build_posed_model(body_meshes, transforms)
    if bones.n_points > 0:
        pl.add_mesh(bones, color=BONE_COLOR, opacity=bone_opacity,
                    smooth_shading=True, specular=0.2)

    strain = cond["strain"]
    for mname, pts in muscles.items():
        poly = world_polyline(pts, transforms)
        if poly is None:
            continue
        if base_name(mname) in HAM_BASES:
            lm = strain_at(strain, mname, p)
            tube = polyline_tube(poly, HAM_TUBE_RADIUS)
            if tube is not None:
                pl.add_mesh(tube, color=strain_color(lm),
                            opacity=muscle_opacity_ham, smooth_shading=True,
                            specular=0.3)
        else:
            tube = polyline_tube(poly, NONHAM_TUBE_RADIUS)
            if tube is not None:
                pl.add_mesh(tube, color=NONHAM_COLOR,
                            opacity=muscle_opacity_nonham, smooth_shading=True)
    return transforms["pelvis"][0, 3]


# ═══════════════════════════════════════════════════════════════════════════
# 5) フレーム描画
# ═══════════════════════════════════════════════════════════════════════════

def render_sidebyside_frame(conds, p, body_meshes, muscles, window_size):
    n = len(conds)
    pv.global_theme.background = "white"
    pl = pv.Plotter(off_screen=True, shape=(1, n), window_size=list(window_size),
                    border=False)
    for i, cond in enumerate(conds):
        pl.subplot(0, i)
        cx = _draw_one(pl, cond, p, body_meshes, muscles)
        frame_sagittal(pl, zoom=1.18)   # 骨+筋を基準にフレーミング
        add_ground(pl, cx)              # 地面は後で(フレーミングに影響させない)
        add_lights(pl, cx)
        pl.add_text(f"{cond['label']}\n(mean tilt {cond['mean_tilt']:.1f} deg)",
                    position="upper_left", font_size=11, color="black")
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


def render_overlay_frame(conds, p, body_meshes, muscles, window_size):
    pv.global_theme.background = "white"
    pl = pv.Plotter(off_screen=True, window_size=list(window_size), border=False)
    # 骨盤 world x を条件0に揃える
    base_cx = None
    for cond in conds:
        q0 = q_at_phase(cond["phases"], cond["col_map"], p, treadmill=True)
        tf0 = compute_body_transforms(q0)
        cx0 = tf0["pelvis"][0, 3]
        if base_cx is None:
            base_cx = cx0
        dx = base_cx - cx0
        _draw_one(pl, cond, p, body_meshes, muscles,
                  bone_opacity=0.35, muscle_opacity_nonham=0.25,
                  muscle_opacity_ham=0.95, align_dx=dx)
    frame_sagittal(pl, zoom=1.18)
    add_ground(pl, base_cx)
    add_lights(pl, base_cx)
    handles = "  |  ".join(f"{c['label']} ({c['mean_tilt']:.1f}deg)" for c in conds)
    # VTK text は CJK フォントを持たないため ASCII で表記
    pl.add_text("Overlay (pelvis-aligned): " + handles, position="upper_left",
                font_size=11, color="black")
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


# ═══════════════════════════════════════════════════════════════════════════
# 6) 出力生成
# ═══════════════════════════════════════════════════════════════════════════

def _phase_seq(n_frames, cycles):
    one = np.linspace(0.0, 1.0, n_frames, endpoint=False)
    return np.tile(one, cycles)


def write_mp4(frame_fn, conds, body_meshes, muscles, out_path,
              n_frames, cycles, fps, window_size):
    import imageio
    seq = _phase_seq(n_frames, cycles)
    print(f"  {out_path.name}: {len(seq)} フレーム生成中 ...")
    writer = imageio.get_writer(str(out_path), fps=fps, codec="libx264",
                                quality=8, output_params=["-pix_fmt", "yuv420p"])
    try:
        for fi, p in enumerate(seq):
            img = frame_fn(conds, p, body_meshes, muscles, window_size)
            writer.append_data(img)
            if (fi + 1) % 15 == 0 or fi == len(seq) - 1:
                print(f"    {fi + 1}/{len(seq)}")
    finally:
        writer.close()
    mb = out_path.stat().st_size / (1024 * 1024)
    print(f"  [OK] {out_path.name}  ({mb:.1f} MB)")


def peak_stretch_phase(conds):
    """最も前傾した条件のハム最大 lMtilde 位相を返す。"""
    cond = min(conds, key=lambda c: c["mean_tilt"])  # 最小 = 最前傾
    best_p, best_v = 0.8, -np.inf
    for mname in ("bifemlh_r", "semimem_r", "semiten_r"):
        if mname not in cond["strain"]:
            continue
        ph, vals = cond["strain"][mname]
        j = int(np.argmax(vals))
        if vals[j] > best_v:
            best_v = vals[j]
            best_p = float(ph[j])
    return best_p


def write_hero_still(conds, body_meshes, muscles, out_path, window_size):
    p = peak_stretch_phase(conds)
    img = render_sidebyside_frame(conds, p, body_meshes, muscles, window_size)
    fig, ax = plt.subplots(figsize=(window_size[0] / 130, window_size[1] / 130))
    ax.imshow(img)
    ax.axis("off")
    ax.set_title(f"ピーク伸張位相 ({p * 100:.0f}%) のハムストリングひずみ比較",
                 fontsize=14, fontweight="bold")
    sm = ScalarMappable(norm=Normalize(LM_VMIN, LM_VMAX), cmap=STRAIN_CMAP)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.01)
    cbar.set_label("ハム正規化筋線維長 lMtilde (高=伸張・肉離れリスク大)",
                   fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {out_path.name}")


# ═══════════════════════════════════════════════════════════════════════════
# 7) 条件発見 + main
# ═══════════════════════════════════════════════════════════════════════════

def load_conditions(results_dir):
    conds = []
    for off, ident in CONDITION_SPECS:
        coords = sorted(results_dir.glob(f"pred_sprinting_coords_*{ident}*.mot"))
        data = sorted(results_dir.glob(f"pred_sprinting_data_*{ident}*.mat"))
        if not coords or not data:
            print(f"  [WARN] 条件 {ident} の coords/data が見つかりません。スキップ。")
            continue
        df = read_mot(coords[-1])
        phases, col_map, mean_tilt = build_phase_data(df)
        strain = load_hamstring_strain(data[-1])
        label = f"{off:+d}deg" if off != 0 else "0deg(nominal)"
        conds.append({
            "offset": off, "label": label, "mean_tilt": mean_tilt,
            "phases": phases, "col_map": col_map, "strain": strain,
            "coords": coords[-1], "data": data[-1],
        })
        print(f"  [OK] {ident:18s} mean tilt {mean_tilt:6.2f} deg  "
              f"({coords[-1].name})")
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
        description="骨盤前後傾オフセットのリッチ筋骨格可視化")
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--frames", type=int, default=70)
    ap.add_argument("--cycles", type=int, default=2)
    ap.add_argument("--width", type=int, default=1680)
    ap.add_argument("--height", type=int, default=950)
    ap.add_argument("--output_dir", type=str, default=None)
    ap.add_argument("--skip_video", action="store_true",
                    help="hero スチルのみ生成 (動画スキップ)")
    ap.add_argument("--only", choices=["both", "side", "overlay"], default="both",
                    help="生成する動画を選択 (再レンダラ用)")
    args = ap.parse_args()

    setup_japanese_font()

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    results_dir = project_root / "Results"
    out_dir = (Path(args.output_dir) if args.output_dir
               else results_dir / "PelvicShift_Study")
    out_dir.mkdir(parents=True, exist_ok=True)
    osim_path = (project_root / "OpenSimModel" /
                 "Scaled_FullBody_HamnerModel_Muscle_withContact.osim")

    print("=" * 70)
    print("  骨盤前後傾オフセット × リッチ筋骨格可視化 (骨メッシュ + 筋ひずみ)")
    print("=" * 70)

    # Geometry
    geom_dir = find_geometry_dir()
    print(f"  Geometry: {geom_dir}")
    body_meshes = load_body_meshes(geom_dir)
    print(f"  読み込んだ body メッシュ数: {len(body_meshes)}")

    # 筋経路
    print(f"  .osim: {osim_path.name}")
    all_muscles = parse_muscle_paths(osim_path)
    muscles = select_curated(all_muscles)
    n_ham = sum(1 for m in muscles if base_name(m) in HAM_BASES)
    print(f"  筋経路: 全 {len(all_muscles)} / 描画 {len(muscles)} "
          f"(うちハム {n_ham})")

    # 条件
    print("\n--- 条件読み込み ---")
    conds = load_conditions(results_dir)
    if len(conds) < 2:
        print("ERROR: 比較できる条件が不足しています。")
        return 1

    win = (args.width, args.height)
    print("\n--- 出力生成 ---")
    # hero still (最優先; 動画前に確認できる)
    if args.only == "both":
        write_hero_still(conds, body_meshes, muscles,
                         out_dir / "pelvic_shift_musculoskeletal_hero.png", win)

    if not args.skip_video:
        if args.only in ("both", "side"):
            write_mp4(render_sidebyside_frame, conds, body_meshes, muscles,
                      out_dir / "pelvic_shift_musculoskeletal_sidebyside.mp4",
                      args.frames, args.cycles, args.fps, win)
        if args.only in ("both", "overlay"):
            write_mp4(render_overlay_frame, conds, body_meshes, muscles,
                      out_dir / "pelvic_shift_musculoskeletal_overlay.mp4",
                      args.frames, args.cycles, args.fps,
                      (int(win[0] * 0.65), win[1]))

    print(f"\n{'=' * 70}\n  完了! 出力先: {out_dir}\n{'=' * 70}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
