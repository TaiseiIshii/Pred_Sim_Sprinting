"""
visualize_pelvic_td_motion.py
v3 (TDPT) 接地骨盤前傾スタディの「動作データ」可視化。

最適化結果 (.mat の optVars_nsc.q = 37自由度の関節角軌道) を、リポジトリの
フォワードキネマティクス・エンジン (visualize_motion_comparison.KINEMATIC_CHAIN)
で実際にポーズさせ、矢状面スティックフィギュアとして描く。さらに各脚の
「もも裏（ハムストリング）」帯を、最適化が出した正規化筋線維長 lMtilde で
緑→赤に着色し、「前傾を強める → ハムが伸びる（肉離れリスク↑）」を動画で示す。

代表3条件（接地骨盤角）を比較:
  強い前傾 −15.5° / 基準 −7.5° / 中立寄り −1.5°

出力 (Results/PelvicTD_Study/):
  pelvic_td_motion_sidebyside.mp4  横並び（各条件: 骨格＋ハムひずみ着色＋角度注記）
  pelvic_td_motion_overlay.mp4     重ね合わせ（骨盤を揃え姿勢差を直接比較）
  pelvic_td_motion_hero.png        最大伸張位相のスチル（ひずみカラーバー付き）

.mot は使わず .mat の q を直接ポーズするため、TDPT 条件で追加の前処理は不要。
実行（conda base python 推奨: imageio-ffmpeg が必要）:
  python analysis/visualize_pelvic_td_motion.py
  python analysis/visualize_pelvic_td_motion.py --fps 20 --frames 72 --cycles 2 --mesh 50
"""
from __future__ import annotations

import argparse
import glob
import os

import numpy as np
from scipy.io import loadmat

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import imageio.v2 as imageio

from visualize_motion_comparison import (
    KINEMATIC_CHAIN,
    STICK_SEGMENTS,
    compute_body_positions,
    HEAD_OFFSET_FROM_TORSO,
)

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "Results")
STUDY = os.path.join(RESULTS, "PelvicTD_Study")

# q row order == flattened KINEMATIC_CHAIN coordinate order (37 DOF).
COORD_INFO = [(c[0], c[2]) for body in KINEMATIC_CHAIN for c in body[3]]

# representative conditions: (tag, prefix, short JP label)
CONDITION_SPECS = [
    ("m8", "PelvisTDwide", "強い前傾"),
    ("p0", "PelvisTDwide", "基準（中間）"),
    ("p6", "PelvisTD", "中立寄り"),
]

# hamstring lMtilde rows (1-based): biarticular = semimem/semiten/bifemlh
HAM_BI = {"R": [53, 54, 55], "L": [7, 8, 9]}

# strain colour scale (fixed so colours are comparable across conditions)
LM_VMIN, LM_VMAX = 0.90, 1.16
STRAIN_CMAP = plt.get_cmap("RdYlGn_r")
BODY_COLOR = (0.34, 0.36, 0.42)
COND_CMAP = plt.get_cmap("coolwarm")     # overlay: anterior=blue .. posterior=red

XLIM = (-0.95, 0.95)
YLIM = (-0.12, 1.95)


def setup_jp_font():
    for cand in ("Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP"):
        if cand in {f.name for f in font_manager.fontManager.ttflist}:
            matplotlib.rcParams["font.family"] = cand
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


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


def latest_n(tag, prefix, target_n):
    fs = sorted(glob.glob(os.path.join(
        RESULTS, f"pred_sprinting_data_*{prefix}_{tag}.mat")),
        key=os.path.getmtime, reverse=True)
    for p in fs:
        if _mat_N(p) == target_n:
            return p
    return fs[0] if fs else None


def load_condition(tag, prefix, label, target_n):
    path = latest_n(tag, prefix, target_n)
    if not path:
        return None
    m = loadmat(path, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    q = np.asarray(_get(o, "optVars_nsc", "q"), dtype=float)     # 37 x nq
    lM = np.asarray(_get(o, "muscleValues", "lMtilde"), dtype=float)  # 92 x nl
    td_tilt = float(np.degrees(q[0, 0]))
    td_hip = float(np.degrees(q[6, 0]))
    try:
        speed = float(np.asarray(_get(o, "ave_speed")).ravel()[0])
    except Exception:
        speed = float("nan")
    qph = np.linspace(0.0, 1.0, q.shape[1])
    lph = np.linspace(0.0, 1.0, lM.shape[1])
    ham = {s: np.mean(lM[[r - 1 for r in rows], :], axis=0)
           for s, rows in HAM_BI.items()}
    cond = {"tag": tag, "label": label, "td_tilt": td_tilt, "td_hip": td_hip,
            "speed": speed, "q": q, "qph": qph, "ham": ham, "lph": lph,
            "path": os.path.basename(path)}
    # precompute the right-toe swing trace once (static over the animation)
    cond["trace"] = np.array([compute_body_positions(q_dict_at(cond, p))[0]["toes_r"]
                              for p in np.linspace(0, 1, 60)])
    return cond


def q_dict_at(cond, p, align=True):
    q, qph = cond["q"], cond["qph"]
    vals = np.array([np.interp(p, qph, q[i, :]) for i in range(q.shape[0])])
    qd = {}
    for i, (name, mode) in enumerate(COORD_INFO):
        qd[name] = float(np.degrees(vals[i])) if mode == "rot" else float(vals[i])
    if align:
        qd["pelvis_tx"] = 0.0
        qd["pelvis_tz"] = 0.0
    return qd


def strain_at(cond, side, p):
    return float(np.interp(p, cond["lph"], cond["ham"][side]))


def strain_color(lm):
    t = float(np.clip((lm - LM_VMIN) / (LM_VMAX - LM_VMIN), 0.0, 1.0))
    return STRAIN_CMAP(t)


def _proj(pos):
    return (pos[0], pos[1])


def _ham_band(ax, p_hip, p_knee, color, lw=8.0, alpha=0.95):
    """Draw a thick strain-coloured band along the posterior thigh."""
    a, b = np.array(_proj(p_hip)), np.array(_proj(p_knee))
    v = b - a
    n = np.linalg.norm(v)
    if n < 1e-6:
        return
    perp = np.array([-v[1], v[0]]) / n
    if perp[0] > 0:               # push to posterior side (-x = behind runner)
        perp = -perp
    off = perp * 0.045
    a2, b2 = a + off, b + off
    ax.plot([a2[0], b2[0]], [a2[1], b2[1]], color=color, lw=lw, alpha=alpha,
            solid_capstyle="round", zorder=5)


def draw_skeleton(ax, positions, color=BODY_COLOR, lw=2.6, alpha=1.0):
    for sa, sb in STICK_SEGMENTS:
        if sa in positions and sb in positions:
            pa, pb = _proj(positions[sa]), _proj(positions[sb])
            ax.plot([pa[0], pb[0]], [pa[1], pb[1]], color=color, lw=lw,
                    alpha=alpha, solid_capstyle="round", zorder=3)
    if "head" in positions and "torso" in positions:
        ph, pt = _proj(positions["head"]), _proj(positions["torso"])
        ax.plot([pt[0], ph[0]], [pt[1], ph[1]], color=color, lw=lw, alpha=alpha,
                zorder=3)
        ax.plot(ph[0], ph[1], "o", color=color, ms=11, alpha=alpha, zorder=4)
    for nm, pos in positions.items():
        if nm not in ("ground", "head"):
            pp = _proj(pos)
            ax.plot(pp[0], pp[1], "o", color=color, ms=4.5, alpha=alpha, zorder=4)


def add_height_ruler(ax, labels=True):
    for y in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6):
        g = (y == 0.0)
        ax.axhline(y, color=(0.25, 0.25, 0.25) if g else (0.83, 0.83, 0.85),
                   lw=2.4 if g else 0.8, alpha=0.9 if g else 0.5, zorder=0)
    if labels:
        for y in (0.5, 1.0, 1.5):
            ax.text(XLIM[0] + 0.02, y + 0.01, f"{y:.1f}m", fontsize=7,
                    color="0.45", va="bottom")


def foot_trace(ax, cond, color):
    ps = cond["trace"]
    ax.plot(ps[:, 0], ps[:, 1], color=color, lw=1.4, alpha=0.5, zorder=1)


def _panel(ax, cond, p, *, show_ruler=True, show_trace=True):
    ax.clear()
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_aspect("equal")
    ax.axis("off")
    if show_ruler:
        add_height_ruler(ax, labels=show_ruler)
    if show_trace:
        foot_trace(ax, cond, (1.0, 0.55, 0.10))
    pos = compute_body_positions(q_dict_at(cond, p))[0]
    draw_skeleton(ax, pos)
    for side, hipb, kneeb in (("R", "femur_r", "tibia_r"),
                              ("L", "femur_l", "tibia_l")):
        _ham_band(ax, pos[hipb], pos[kneeb], strain_color(strain_at(cond, side, p)),
                  lw=9.0 if side == "R" else 6.0,
                  alpha=0.97 if side == "R" else 0.6)
    ax.set_title(f"{cond['label']}\n接地骨盤角 {cond['td_tilt']:+.1f}°  "
                 f"速度 {cond['speed']:.1f} m/s", fontsize=10.5)


def _fig_to_rgb(fig):
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()


def render_sidebyside(conds, out, fps, frames, cycles):
    fig, axes = plt.subplots(1, len(conds), figsize=(4.4 * len(conds), 6.2))
    plt.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.06, wspace=0.04)
    phs = np.linspace(0, 1, frames, endpoint=False)
    with imageio.get_writer(out, fps=fps, codec="libx264", quality=8,
                            macro_block_size=8) as w:
        for _ in range(cycles):
            for p in phs:
                for ax, c in zip(axes, conds):
                    _panel(ax, c, p)
                fig.suptitle(f"v3(TDPT) 接地骨盤前傾の比較  —  ストライド位相 {p*100:4.0f}%"
                             "（もも裏: 緑=余裕 / 赤=伸張・肉離れリスク大）",
                             fontsize=12, fontweight="bold")
                w.append_data(_fig_to_rgb(fig))
    plt.close(fig)
    print("wrote", out)


def render_overlay(conds, out, fps, frames, cycles):
    fig, ax = plt.subplots(figsize=(7.2, 6.6))
    plt.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.06)
    phs = np.linspace(0, 1, frames, endpoint=False)
    n = len(conds)
    cols = [COND_CMAP(i / max(1, n - 1)) for i in range(n)]
    with imageio.get_writer(out, fps=fps, codec="libx264", quality=8,
                            macro_block_size=8) as w:
        for _ in range(cycles):
            for p in phs:
                ax.clear()
                ax.set_xlim(*XLIM)
                ax.set_ylim(*YLIM)
                ax.set_aspect("equal")
                ax.axis("off")
                add_height_ruler(ax)
                for c, col in zip(conds, cols):
                    pos = compute_body_positions(q_dict_at(c, p))[0]
                    draw_skeleton(ax, pos, color=col, lw=2.4, alpha=0.85)
                handles = [plt.Line2D([0], [0], color=col, lw=3,
                           label=f"{c['label']} {c['td_tilt']:+.1f}°")
                           for c, col in zip(conds, cols)]
                ax.legend(handles=handles, loc="upper right", fontsize=9,
                          framealpha=0.9)
                ax.set_title(f"骨盤を揃えた姿勢の重ね合わせ  —  位相 {p*100:4.0f}%\n"
                             "（前傾ほど体幹が前に倒れ、接地で股関節がより曲がる）",
                             fontsize=11, fontweight="bold")
                w.append_data(_fig_to_rgb(fig))
    plt.close(fig)
    print("wrote", out)


def render_hero(conds, out):
    # peak-strain phase of the most-anterior condition (right hamstring)
    c0 = conds[0]
    p_star = float(c0["lph"][int(np.argmax(c0["ham"]["R"]))])
    fig, axes = plt.subplots(1, len(conds), figsize=(4.4 * len(conds), 6.4))
    plt.subplots_adjust(left=0.01, right=0.88, top=0.88, bottom=0.06, wspace=0.04)
    for ax, c in zip(axes, conds):
        _panel(ax, c, p_star)
        pos = compute_body_positions(q_dict_at(c, p_star))[0]
        ax.annotate(f"股関節屈曲\n{c['td_hip']:.0f}°（接地時）",
                    xy=_proj(pos["femur_r"]), xytext=(0.30, 1.62),
                    fontsize=9, color="#202020", ha="left",
                    arrowprops=dict(arrowstyle="->", color="0.4", lw=1.2))
    sm = ScalarMappable(norm=Normalize(LM_VMIN, LM_VMAX), cmap=STRAIN_CMAP)
    sm.set_array([])
    cax = fig.add_axes([0.90, 0.16, 0.022, 0.62])
    cb = fig.colorbar(sm, cax=cax)
    cb.set_label("もも裏 正規化筋線維長 lMtilde（赤＝伸張＝肉離れリスク大）",
                 fontsize=9)
    fig.suptitle(f"最大伸張付近の姿勢（ストライド位相 {p_star*100:.0f}%）"
                 "  —  前傾を強めるほど もも裏が赤い＝伸びている",
                 fontsize=12.5, fontweight="bold")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--frames", type=int, default=72)
    ap.add_argument("--cycles", type=int, default=2)
    ap.add_argument("--mesh", type=int, default=50, help="mesh N to visualise")
    ap.add_argument("--only", choices=["side", "overlay", "hero"], default=None)
    args = ap.parse_args()

    setup_jp_font()
    conds = []
    for tag, prefix, label in CONDITION_SPECS:
        c = load_condition(tag, prefix, label, args.mesh)
        if c is None:
            print(f"  [skip] {prefix}_{tag} (N={args.mesh}) not found")
            continue
        print(f"  [OK] {label:8s} TD={c['td_tilt']:+6.1f}deg hip={c['td_hip']:4.0f} "
              f"v={c['speed']:.2f}  {c['path']}")
        conds.append(c)
    if len(conds) < 2:
        raise SystemExit("need >=2 conditions to compare")

    if args.only in (None, "hero"):
        render_hero(conds, os.path.join(STUDY, "pelvic_td_motion_hero.png"))
    if args.only in (None, "side"):
        render_sidebyside(conds, os.path.join(STUDY, "pelvic_td_motion_sidebyside.mp4"),
                          args.fps, args.frames, args.cycles)
    if args.only in (None, "overlay"):
        render_overlay(conds, os.path.join(STUDY, "pelvic_td_motion_overlay.mp4"),
                       args.fps, args.frames, args.cycles)


if __name__ == "__main__":
    main()
