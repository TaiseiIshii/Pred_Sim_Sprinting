"""
compute_osim_muscle_paths.py
OpenSim 4.x Python API を使い、各骨盤傾斜条件の **解剖学的に正しい（wrapping 込み）
筋経路** と **各 body の ground 変換** を全フレームで計算してキャッシュに保存する。

これにより、レンダラ側（pyvista / conda base 環境）は wrapping 済みの taut な
筋ポリラインをそのまま描けるようになり、従来の「2点直線近似」で起きていた
筋肉の不自然な垂れ下がり（緩み）を解消する。

実行環境: **opensim を import できる env**（このマシンでは conda `opencap` env =
OpenSim 4.4, py3.9）。pyvista は不要。

  & 'C:\\Users\\...\\envs\\opencap\\python.exe' compute_osim_muscle_paths.py \
        --frames 60

出力: Results/PelvicShift_Study/_muscle_cache.pkl
  { ident: { 'offset', 'mean_tilt', 'phases'(F,), 'bodies'{name:(F,4,4)},
             'muscles'{name: [ (Ni,3) ]*F }, 'is_ham'{name:bool},
             'radius'{name:float} } }

Date: 2026-06-21
"""

import argparse
import pickle
from pathlib import Path

import numpy as np
import opensim as osim
from scipy.io import loadmat

# ---------------------------------------------------------------------------
# muscleValues / GRF の行探索ヘルパ
# ---------------------------------------------------------------------------


def _attr(o, *names):
    for n in names:
        try:
            o = getattr(o, n)
        except AttributeError:
            o = o[n]
    return o


def load_muscle_dynamics(mat_path, muscle_order):
    """.mat から 筋活性化(act) と 正規化筋力(Fce/Fiso) を位相[0,1]で返す。

    muscleValues は 92 行 (OpenSim の Muscle 順)。OpenSim の getMuscles() 順と
    同一と仮定し、名前で index を引く。
    戻り値: {muscle_name: (phases(K,), act(K,), forceRatio(K,))}
    """
    m = loadmat(str(mat_path), struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    act = np.asarray(_attr(o, "optVars_nsc", "act"), dtype=float)   # (92, Ka)
    Fce = np.asarray(_attr(o, "muscleValues", "Fce"), dtype=float)  # (92, Kf)
    Fiso = np.asarray(_attr(o, "muscleValues", "Fiso"), dtype=float)
    out = {}
    for idx, nm in enumerate(muscle_order):
        if idx >= act.shape[0]:
            break
        a = act[idx]
        ph_a = np.linspace(0.0, 1.0, a.shape[0])
        fr = Fce[idx] / np.maximum(Fiso[idx], 1.0)
        ph_f = np.linspace(0.0, 1.0, fr.shape[0])
        out[nm] = (ph_a, np.clip(a, 0.0, 1.0), ph_f, np.clip(fr, 0.0, 1.5))
    return out


def load_grf(grf_mot, frames):
    """_GRF.mot の total ground_force_v(xyz) と _p(xyz) を frames 個に補間。
    戻り値: force(F,3), point(F,3) (ground 座標, 単位 N / m)。treadmill 視点に
    合わせ点の x/z は後でレンダラ側で骨盤に揃えるため、ここでは raw を返す。
    """
    if grf_mot is None or not Path(grf_mot).exists():
        return None, None
    lines = Path(grf_mot).read_text(errors="replace").splitlines()
    hi = next(i for i, l in enumerate(lines) if l.strip().lower() == "endheader")
    hdr = lines[hi + 1].split("\t")
    hdr = [h.strip() for h in hdr if h.strip()]
    rows = []
    for l in lines[hi + 2:]:
        s = l.split()
        if len(s) == len(hdr):
            rows.append([float(v) for v in s])
    arr = np.array(rows, dtype=float)

    def col(name):
        return arr[:, hdr.index(name)]

    t = col("time")
    ph_src = (t - t[0]) / (t[-1] - t[0])
    ph_tgt = np.linspace(0.0, 1.0, frames, endpoint=False)
    F = np.stack([np.interp(ph_tgt, ph_src, col("ground_force_vx")),
                  np.interp(ph_tgt, ph_src, col("ground_force_vy")),
                  np.interp(ph_tgt, ph_src, col("ground_force_vz"))], axis=1)
    P = np.stack([np.interp(ph_tgt, ph_src, col("ground_force_px")),
                  np.interp(ph_tgt, ph_src, col("ground_force_py")),
                  np.interp(ph_tgt, ph_src, col("ground_force_pz"))], axis=1)
    return F.astype(np.float32), P.astype(np.float32)


# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------

CONDITION_SPECS = [
    (0,  "HamPareto_Nom_w0000"),
    (8,  "HamPareto_Nom_w0800"),
    (32, "HamPareto_Nom_w3200"),
]

# レンダラが骨メッシュを置く body (BODY_GEOMETRY と一致)
RENDER_BODIES = [
    "pelvis", "femur_r", "femur_l", "tibia_r", "tibia_l",
    "talus_r", "talus_l", "calcn_r", "calcn_l", "toes_r", "toes_l",
    "torso", "humerus_r", "humerus_l", "ulna_r", "ulna_l",
    "radius_r", "radius_l", "hand_r", "hand_l",
]

# 描画する主要下肢筋 (基底名; _r/_l を付けて探索)
# スペースの都合で None にすると モデル全筋(92) を描画する。
CURATED_BASES = None  # None = 全筋を描画 (下記 _LOWER_LIMB_BASES はハム判定用の参考)

HAM_BASES = ("semimem", "semiten", "bifemlh", "bifemsh")

TRANS_COORDS = {"pelvis_tx", "pelvis_ty", "pelvis_tz"}


def base_name(name):
    return name[:-2] if name.endswith(("_r", "_l")) else name


# ---------------------------------------------------------------------------
# .mot 読み込み + 位相補間
# ---------------------------------------------------------------------------

def read_mot(path):
    lines = Path(path).read_text(errors="replace").splitlines()
    hi = next(i for i, l in enumerate(lines)
              if l.strip().startswith("time") or l.strip().startswith("/jointset"))
    headers = [h.strip() for h in lines[hi].split("\t") if h.strip()]
    rows = []
    for l in lines[hi + 1:]:
        s = l.split()
        if len(s) == len(headers):
            rows.append([float(v) for v in s])
    return headers, np.array(rows, dtype=float)


def simplify(col):
    parts = col.strip("/").split("/")
    return parts[-2] if len(parts) >= 3 else col


def phase_interp(headers, data, frames):
    """時刻を [0,1] 位相に正規化し、frames 個に補間した {coord: values} を返す。"""
    names = [simplify(h) for h in headers]
    t = data[:, 0]
    order = np.argsort(t, kind="stable")
    t = t[order]
    keep = np.concatenate(([True], np.diff(t) > 1e-12))
    t = t[keep]
    ph_src = (t - t[0]) / (t[-1] - t[0])
    ph_tgt = np.linspace(0.0, 1.0, frames, endpoint=False)
    cols = {}
    for i, nm in enumerate(names):
        if nm == "time":
            continue
        vals = data[order, i][keep]
        cols[nm] = np.interp(ph_tgt, ph_src, vals)
    mean_tilt = float(np.mean(cols.get("pelvis_tilt", np.array([np.nan]))))
    return ph_tgt, cols, mean_tilt


# ---------------------------------------------------------------------------
# 1フレームの計算
# ---------------------------------------------------------------------------

def set_pose(model, state, cs, cols, fi):
    for i in range(cs.getSize()):
        c = cs.get(i)
        nm = c.getName()
        if nm not in cols:
            continue
        v = float(cols[nm][fi])
        if nm in TRANS_COORDS:
            # treadmill: 前後左右を 0 に固定（鉛直 ty は保持）
            if nm in ("pelvis_tx", "pelvis_tz"):
                v = 0.0
            c.setValue(state, v, False)
        else:
            c.setValue(state, float(np.deg2rad(v)), False)
    model.assemble(state)
    model.realizePosition(state)


def body_transform(model, state, name):
    b = model.getBodySet().get(name)
    T = b.getTransformInGround(state)
    R = T.R()
    p = T.p()
    M = np.eye(4, dtype=np.float32)
    for r in range(3):
        for c in range(3):
            M[r, c] = R.get(r, c)
        M[r, 3] = p.get(r)
    return M


def muscle_path_ground(state, muscle):
    gp = muscle.getGeometryPath()
    path = gp.getCurrentPath(state)
    pts = np.empty((path.getSize(), 3), dtype=np.float32)
    for j in range(path.getSize()):
        v = path.get(j).getLocationInGround(state)
        pts[j, 0] = v.get(0)
        pts[j, 1] = v.get(1)
        pts[j, 2] = v.get(2)
    return pts


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--osim", type=str, default=None)
    ap.add_argument("--results_dir", type=str, default=None)
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    root = here.parent
    osim_path = Path(args.osim) if args.osim else (
        root / "OpenSimModel" / "Scaled_FullBody_HamnerModel_Muscle_withContact.osim")
    results_dir = Path(args.results_dir) if args.results_dir else (root / "Results")
    out = Path(args.out) if args.out else (
        results_dir / "HamPareto_Study" / "_muscle_cache.pkl")
    out.parent.mkdir(parents=True, exist_ok=True)

    print("OpenSim", osim.GetVersion())
    model = osim.Model(str(osim_path))
    state = model.initSystem()
    cs = model.getCoordinateSet()

    # 描画対象の筋を確定。CURATED_BASES=None なら全筋を描画。
    wanted = None
    if CURATED_BASES is not None:
        wanted = set()
        for b in CURATED_BASES:
            wanted.add(b + "_r")
            wanted.add(b + "_l")
    muscles = {}
    muscle_order = []          # muscleValues 行と対応する OpenSim getMuscles() 順
    radius = {}
    is_ham = {}
    mset = model.getMuscles()
    for i in range(mset.getSize()):
        m = mset.get(i)
        nm = m.getName()
        muscle_order.append(nm)
        if wanted is not None and nm not in wanted:
            continue
        muscles[nm] = m
        f = float(m.getMaxIsometricForce())
        # 半径を最大等尺性力で軽くスケール (太い筋は太く)。ハムは強調。
        r = 0.0030 + 0.0040 * np.sqrt(max(f, 1.0) / 1500.0)
        if base_name(nm) in HAM_BASES:
            r = max(r, 0.009)
        radius[nm] = float(min(r, 0.013))
        is_ham[nm] = base_name(nm) in HAM_BASES
    print(f"描画筋数: {len(muscles)} / 全{len(muscle_order)} "
          f"(うちハム {sum(is_ham.values())})")

    cache = {}
    for off, ident in CONDITION_SPECS:
        coords = sorted(results_dir.glob(f"pred_sprinting_coords_*{ident}*.mot"))
        if not coords:
            print(f"  [WARN] {ident} の coords なし。スキップ")
            continue
        headers, data = read_mot(coords[-1])
        phases, cols, mean_tilt = phase_interp(headers, data, args.frames)
        F = args.frames
        bodies = {b: np.zeros((F, 4, 4), dtype=np.float32) for b in RENDER_BODIES}
        mus = {nm: [None] * F for nm in muscles}
        for fi in range(F):
            set_pose(model, state, cs, cols, fi)
            for b in RENDER_BODIES:
                bodies[b][fi] = body_transform(model, state, b)
            for nm, m in muscles.items():
                mus[nm][fi] = muscle_path_ground(state, m)

        # 筋活性化・力比 (.mat) と GRF ベクトル (_GRF.mot)
        data_mat = sorted(results_dir.glob(f"pred_sprinting_data_*{ident}*.mat"))
        dyn = (load_muscle_dynamics(data_mat[-1], muscle_order)
               if data_mat else {})
        grf_mot = sorted(results_dir.glob(f"pred_sprinting_*{ident}_GRF.mot"))
        grfF, grfP = (load_grf(grf_mot[-1], F) if grf_mot else (None, None))

        cache[ident] = {
            "offset": off, "mean_tilt": mean_tilt, "phases": phases,
            "bodies": bodies, "muscles": mus, "is_ham": is_ham, "radius": radius,
            "dyn": dyn, "grf_force": grfF, "grf_point": grfP,
        }
        ng = "GRF" if grfF is not None else "no-GRF"
        print(f"  [OK] {ident}: mean tilt {mean_tilt:.2f} deg, {F} frames, "
              f"dyn={len(dyn)} {ng}")

    with open(out, "wb") as f:
        pickle.dump(cache, f, protocol=4)
    mb = out.stat().st_size / (1024 * 1024)
    print(f"[OK] cache -> {out}  ({mb:.1f} MB)")


if __name__ == "__main__":
    main()
