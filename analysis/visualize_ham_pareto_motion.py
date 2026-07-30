"""
visualize_ham_pareto_motion.py
=============================
実際に生成された“走りフォーム”（関節キネマティクス）の比較を可視化する。
OpenSim モデルのフォワードキネマティクス（visualize_motion_comparison.py の
運動連鎖）で、保存済み座標 .mot からスティックフィギュアを描き、

  ・現状の走り（ペナルティなし）   vs   最も安全な走り（強いペナルティ）

を重ね描き（骨盤で整列）して、走り方が“実際にどう変わるか”を示す。数値・姿勢は
すべて strict 収束したシミュレーション結果由来。

生成物 (Results/HamPareto_Study/):
  motion_compare_nominal_jp.png / motion_compare_short_jp.png
      6 局面のスナップショット重ね描き＋股関節・膝の角度波形。
  motion_pareto_run_nominal.gif
      走行アニメーション（現状=灰 vs 安全=色、骨盤で整列して重ね描き）。

Usage:  python visualize_ham_pareto_motion.py
"""
import glob
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.animation import FuncAnimation, PillowWriter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from visualize_motion_comparison import (  # noqa: E402
    compute_body_positions, read_mot, mot_to_q_series, draw_stick_figure_2d)

RESULTS = os.path.join(os.path.dirname(__file__), "..", "Results")
OUTDIR = os.path.join(RESULTS, "HamPareto_Study")
GRAY, NAVY, RED = "#8A8A8A", "#1F3A93", "#C0392B"

# --- 日本語フォント ---------------------------------------------------------- #
for _f in [r"C:\Windows\Fonts\meiryo.ttc", r"C:\Windows\Fonts\YuGothM.ttc",
           r"C:\Windows\Fonts\msgothic.ttc"]:
    if os.path.exists(_f):
        fm.fontManager.addfont(_f)
        plt.rcParams["font.family"] = fm.FontProperties(fname=_f).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False


def _newest_coords(token):
    fs = glob.glob(os.path.join(RESULTS, f"pred_sprinting_coords_*{token}.mot"))
    return max(fs, key=os.path.getmtime) if fs else None


def _series(token):
    f = _newest_coords(token)
    if f is None:
        return None
    return mot_to_q_series(read_mot(f))


def _peak_angles(series):
    """遊脚脚（右）の股関節屈曲・膝角度のピーク（度）を返す。"""
    hip = np.array([q.get("hip_flexion_r", 0.0) for _, q in series])
    knee = np.array([q.get("knee_angle_r", 0.0) for _, q in series])
    return hip, knee


def snapshot_figure(base_tok, safe_tok, safe_color, title, subtitle,
                    base_label, safe_label, out_name, k=6):
    sb, ss = _series(base_tok), _series(safe_tok)
    if sb is None or ss is None:
        print(f"[skip] {out_name}: 座標 .mot が見つかりません ({base_tok} / {safe_tok})")
        return None
    fig = plt.figure(figsize=(14, 7.4))
    gs = fig.add_gridspec(2, 3, height_ratios=[2.5, 1.0], hspace=0.32, wspace=0.24)
    axm = fig.add_subplot(gs[0, :])

    DX = 1.32
    ymin, ymax = 1e9, -1e9
    for i, frac in enumerate(np.linspace(0, 1, k)):
        ib = int(round(frac * (len(sb) - 1)))
        isf = int(round(frac * (len(ss) - 1)))
        pb = compute_body_positions(sb[ib][1])[0]
        ps = compute_body_positions(ss[isf][1])[0]
        zb = i * DX - pb["pelvis"][0]
        zs = i * DX - ps["pelvis"][0]
        draw_stick_figure_2d(axm, pb, GRAY, alpha=0.55, lw=2.2, view="sagittal",
                             z_offset=zb, label=(base_label if i == 0 else None))
        draw_stick_figure_2d(axm, ps, safe_color, alpha=0.95, lw=2.7, view="sagittal",
                             z_offset=zs, label=(safe_label if i == 0 else None))
        for p in (pb, ps):
            ys = [p[b][1] for b in p if b not in ("ground",)]
            ymin, ymax = min(ymin, min(ys)), max(ymax, max(ys))
        axm.text(i * DX, -0.05, f"{int(round(frac * 100))}%", ha="center", va="top",
                 fontsize=10.5, fontweight="bold", transform=axm.get_xaxis_transform())
    axm.set_aspect("equal")
    axm.set_ylim(ymin - 0.05, ymax + 0.12)
    axm.set_xlim(-0.55, (k - 1) * DX + 0.55)
    axm.axis("off")
    axm.text(0.5, 1.06, title, transform=axm.transAxes, ha="center", va="bottom",
             fontsize=14, fontweight="bold")
    axm.text(0.5, 1.005, subtitle, transform=axm.transAxes, ha="center", va="bottom",
             fontsize=10.5, color="#444444")
    axm.text(0.5, -0.13, "← 1歩（接地〜次の接地）の局面 →", transform=axm.transAxes,
             ha="center", va="top", fontsize=10.5)
    axm.legend(loc="upper left", fontsize=10, framealpha=0.9)

    # 角度波形（股関節屈曲・膝角度）
    hb, kb = _peak_angles(sb)
    hs, ks = _peak_angles(ss)
    xb = np.linspace(0, 100, len(hb))
    xs = np.linspace(0, 100, len(hs))
    axh = fig.add_subplot(gs[1, 0])
    axh.plot(xb, hb, color=GRAY, lw=2.2, label=base_label)
    axh.plot(xs, hs, color=safe_color, lw=2.2, label=safe_label)
    axh.set_title("股関節の屈曲角（度）", fontsize=10.5)
    axh.set_xlabel("1歩の進行 (%)", fontsize=9)
    axh.grid(alpha=0.3)
    axk = fig.add_subplot(gs[1, 1])
    axk.plot(xb, kb, color=GRAY, lw=2.2)
    axk.plot(xs, ks, color=safe_color, lw=2.2)
    axk.set_title("膝の角度（度）", fontsize=10.5)
    axk.set_xlabel("1歩の進行 (%)", fontsize=9)
    axk.grid(alpha=0.3)

    # 差分の要約ボックス
    dhip = np.max(np.abs(hs)) - np.max(np.abs(hb))
    dknee = np.max(np.abs(ks)) - np.max(np.abs(kb))
    axt = fig.add_subplot(gs[1, 2])
    axt.axis("off")
    axt.text(0.02, 0.95,
             "実データが示す“安全な走り”の中身\n"
             f"・股関節 屈曲ピーク: {np.max(np.abs(hb)):.0f}° → {np.max(np.abs(hs)):.0f}°"
             f"（{dhip:+.0f}°）\n"
             f"・膝 角度ピーク: {np.max(np.abs(kb)):.0f}° → {np.max(np.abs(ks)):.0f}°"
             f"（{dknee:+.0f}°）\n"
             "→ 遊脚脚の“振り出し過ぎ”を抑え、\n"
             "  ハムストリングの伸ばされ過ぎを回避。",
             transform=axt.transAxes, fontsize=10, va="top",
             bbox=dict(boxstyle="round,pad=0.5", fc="#F4F8FF", ec=safe_color, lw=1.5))

    fig.tight_layout()
    out = os.path.join(OUTDIR, out_name)
    os.makedirs(OUTDIR, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"図を保存: {out}")
    print(f"  {base_tok}: hipPk={np.max(np.abs(hb)):.1f} kneePk={np.max(np.abs(kb)):.1f} "
          f"| {safe_tok}: hipPk={np.max(np.abs(hs)):.1f} kneePk={np.max(np.abs(ks)):.1f}")
    return out


def run_animation(base_tok, safe_tok, safe_color, base_label, safe_label,
                  title, out_name, frames=48):
    sb, ss = _series(base_tok), _series(safe_tok)
    if sb is None or ss is None:
        print(f"[skip anim] {out_name}")
        return
    fig, ax = plt.subplots(figsize=(6.4, 6.4))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=12, fontweight="bold")

    def frame(fi):
        ax.clear()
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=12, fontweight="bold")
        frac = fi / (frames - 1)
        ib = int(round(frac * (len(sb) - 1)))
        isf = int(round(frac * (len(ss) - 1)))
        pb = compute_body_positions(sb[ib][1])[0]
        ps = compute_body_positions(ss[isf][1])[0]
        draw_stick_figure_2d(ax, pb, GRAY, alpha=0.5, lw=2.4, view="sagittal",
                             z_offset=-pb["pelvis"][0], label=base_label)
        draw_stick_figure_2d(ax, ps, safe_color, alpha=0.95, lw=3.0, view="sagittal",
                             z_offset=-ps["pelvis"][0], label=safe_label)
        ax.set_xlim(-0.9, 0.9)
        ax.set_ylim(-0.05, 2.0)
        ax.legend(loc="upper left", fontsize=10, framealpha=0.9)
        ax.text(0.5, -0.02, f"1歩の進行: {int(round(frac*100))}%", transform=ax.transAxes,
                ha="center", va="top", fontsize=10)
        return []

    anim = FuncAnimation(fig, frame, frames=frames, interval=70)
    out = os.path.join(OUTDIR, out_name)
    os.makedirs(OUTDIR, exist_ok=True)
    anim.save(out, writer=PillowWriter(fps=15))
    plt.close(fig)
    print(f"アニメーションを保存: {out}")


def main():
    snapshot_figure(
        "HamPareto_Nom_w0000", "HamPareto_Nom_w3200", NAVY,
        "実際に生成された走りフォームの比較（標準的な選手）",
        "現状の全力疾走 vs 最も安全な走り ― 同じ選手・走り方だけが違う",
        "現状（11.78 m/s）", "最も安全な走り（11.51 m/s）",
        "motion_compare_nominal_jp.png")
    snapshot_figure(
        "HamFascicle_m20", "HamPareto_Sh_w3200", RED,
        "実際に生成された走りフォームの比較（筋束が短い高リスク選手）",
        "現状 vs 走り方だけで最大限安全化 ― 速度の代償が大きい",
        "現状（11.68 m/s）", "安全化した走り（8.37 m/s）",
        "motion_compare_short_jp.png")
    run_animation(
        "HamPareto_Nom_w0000", "HamPareto_Nom_w3200", NAVY,
        "現状（11.78 m/s）", "最も安全な走り（11.51 m/s）",
        "走りフォームの比較（骨盤で整列）", "motion_pareto_run_nominal.gif")


if __name__ == "__main__":
    main()
