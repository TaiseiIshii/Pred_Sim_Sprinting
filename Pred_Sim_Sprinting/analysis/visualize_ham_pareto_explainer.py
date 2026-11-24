"""
visualize_ham_pareto_explainer.py
=================================
"専門外の人向け" の高度な可視化（日本語ラベル・注釈つきインフォグラフィック）。
既存の analyze_ham_pareto / analyze_ham_architecture の実測データから、物語で
理解できる図を生成する。数値はすべて strict 収束したシミュレーション結果由来。

生成物 (Results/HamPareto_Study/):
  explainer_frontier_jp.png  -- 「安全ダイヤルを少し回すと、速さはほぼそのまま
        でケガのリスクだけ下がる」= フリーランチ領域と収穫逓減を注釈で明示。
  explainer_decision_jp.png  -- 「あなたはどのタイプ? 最適な直し方」= 技術 vs
        トレーニングを速度-安全平面の矢印で対比し、平易な結論ボックスを添える。

Usage:  python visualize_ham_pareto_explainer.py
"""
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch

import analyze_ham_pareto as AP

# --- 日本語フォント設定（Windows 標準フォントを順に試す） --------------------- #
_JP_CANDIDATES = [
    r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\YuGothM.ttc",
    r"C:\Windows\Fonts\YuGothR.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
    r"C:\Windows\Fonts\BIZ-UDGothicR.ttc",
]
for _f in _JP_CANDIDATES:
    if os.path.exists(_f):
        try:
            fm.fontManager.addfont(_f)
            plt.rcParams["font.family"] = fm.FontProperties(fname=_f).get_name()
            break
        except Exception:  # noqa: BLE001
            continue
plt.rcParams["axes.unicode_minus"] = False  # マイナス記号の豆腐化を防ぐ

RISK = 1.15
GOLD, GREEN, RED, NAVY, ORANGE = "#E8A317", "#2E8B57", "#C0392B", "#1F3A93", "#E67E22"


def _box(ax, x, y, text, fc, ec, fontsize=10, ha="left", va="top", alpha=0.95):
    ax.text(x, y, text, transform=ax.transAxes, fontsize=fontsize, ha=ha, va=va,
            bbox=dict(boxstyle="round,pad=0.5", fc=fc, ec=ec, lw=1.5, alpha=alpha),
            zorder=10)


# --------------------------------------------------------------------------- #
#  図1: 標準的な選手の「速さ vs 安全」地図（フリーランチ）
# --------------------------------------------------------------------------- #
def fig_frontier_explainer(by_ath):
    rows = AP.free_lunch(by_ath["Nom"])
    if len(rows) < 3:
        print("[図1 skip] 標準アスリートの掃引データが足りません")
        return
    x = np.array([r["peak_lMtilde"] for r in rows])
    y = np.array([r["speed"] for r in rows])
    fl = [r for r in rows if r["free_lunch"]]

    fig, ax = plt.subplots(figsize=(10.5, 6.6))
    # フリーランチ帯（上部・ほぼ水平）と収穫逓減帯（下部・急降下）を背景で示す
    yb = y.min() - 0.05
    x_fl = min(r["peak_lMtilde"] for r in fl) if fl else x[len(x) // 2]
    ax.axhspan(y.max() - 0.05, y.max() + 0.02, xmin=0, xmax=1, color=GREEN, alpha=0.05)
    ax.fill_betweenx([yb, y.max() + 0.02], x_fl, x.max() + 0.02,
                     color=GREEN, alpha=0.08, zorder=0)
    ax.fill_betweenx([yb, y.max() + 0.02], x.min() - 0.02, x_fl,
                     color=RED, alpha=0.06, zorder=0)

    ax.plot(x, y, "-", color=NAVY, lw=2.5, zorder=3)
    ax.plot(x, y, "o", color=NAVY, ms=8, zorder=4)
    for r in fl:
        ax.plot(r["peak_lMtilde"], r["speed"], "*", color=GOLD, ms=26,
                mec="k", mew=1.2, zorder=6)

    # 現状（ペナルティなし）
    ax.annotate("現状の全力疾走\n（何も足さない）",
                xy=(x[0], y[0]), xytext=(x[0] - 0.005, y[0] - 0.18),
                fontsize=10, ha="right", va="top", color=NAVY,
                arrowprops=dict(arrowstyle="->", color=NAVY, lw=1.5))
    # フリーランチ注釈
    if fl:
        best = max(fl, key=lambda r: r["dstrain_pct"])
        ax.annotate(
            f"◎ ほぼ無料ゾーン\n速さ −{best['dspeed_pct']:.2f}% だけで\n"
            f"ケガの危険サイン −{best['dstrain_pct']:.1f}%",
            xy=(best["peak_lMtilde"], best["speed"]),
            xytext=(x_fl - 0.045, y.max() - 0.02),
            fontsize=10.5, ha="left", va="center", color=GREEN, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", fc="#EAF7EF", ec=GREEN, lw=1.8),
            arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.8))
    # 収穫逓減注釈
    ax.annotate("▲ ここから先は\n速さが大きく落ちる\n（安全の“買い過ぎ”）",
                xy=(x[-1], y[-1]), xytext=(x[-1] + 0.008, y[-1] + 0.10),
                fontsize=10.5, ha="left", va="bottom", color=RED,
                bbox=dict(boxstyle="round,pad=0.5", fc="#FDEDEC", ec=RED, lw=1.6),
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.6))

    ax.set_xlabel("ケガの危険サイン →（ハムストリング筋束の“伸ばされ過ぎ”度）", fontsize=12)
    ax.set_ylabel("最高速度（m/s）→", fontsize=12)
    ax.set_title("「安全ダイヤル」を少し回すと、速さはほぼそのままでケガのリスクだけ下がる\n"
                 "― 標準的なスプリンターの“速さ vs 安全”地図 ―", fontsize=13.5,
                 fontweight="bold")
    ax.invert_xaxis()  # 左ほど安全になるように（現状=右上、安全化=左へ）
    ax.grid(alpha=0.25)
    _box(ax, 0.015, 0.16,
         "読み方：右上が「現状」。左へ動く＝安全、下へ動く＝遅い。\n"
         "上部（緑）は“横に大きく・縦はわずか”＝ほぼ無料で安全。\n"
         "下部（赤）は“縦に大きく落ちる”＝速さの代償が大きい。",
         fc="#FBFCF5", ec="#999999", fontsize=9.5, va="bottom")
    fig.tight_layout()
    _save(fig, "explainer_frontier_jp.png")


# --------------------------------------------------------------------------- #
#  図2: 選手タイプ別・最適な直し方（技術 vs トレーニング）
# --------------------------------------------------------------------------- #
def fig_decision_explainer(by_ath):
    try:
        import analyze_ham_architecture as AA
    except Exception as e:  # noqa: BLE001
        print(f"[図2 skip] analyze_ham_architecture 読み込み失敗: {e}")
        return
    sh = AP.free_lunch(by_ath["Sh"])
    wk = AP.free_lunch(by_ath["Wk"])
    if len(sh) < 2 or len(wk) < 2:
        print("[図2 skip] アスリート別データが足りません")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14.5, 6.8))

    def panel(ax, tech, mode, title, concl, concl_color):
        from matplotlib.transforms import blended_transform_factory
        # 技術パス（本研究のパレート境界）
        tx = [r["peak_lMtilde"] for r in tech]
        ty = [r["speed"] for r in tech]
        # トレーニングパス（RQ2 の筋形態用量反応、factor>=0.80）
        arch = [a for a in AA.collect(mode, target_N=50) if a.get("factor", 0) >= 0.80]
        arch.sort(key=lambda a: a["factor"])
        ax_min = min(tx + [a["biartic_peak_lMtilde"] for a in arch]) - 0.03
        ax_max = max(tx + [a["biartic_peak_lMtilde"] for a in arch]) + 0.05
        # 危険域（lMtilde>1.15）は“表示範囲に入るときだけ”描く（弱い選手は安全域なので出ない）
        if RISK <= ax_max:
            ax.axvspan(RISK, ax_max, color=RED, alpha=0.07)
            ax.axvline(RISK, ls="--", color=RED, lw=1.2, alpha=0.7)
            trans = blended_transform_factory(ax.transData, ax.transAxes)
            ax.text(RISK - 0.004, 0.06, "←危険域（伸ばされ過ぎ）", color=RED, fontsize=9,
                    ha="right", va="bottom", transform=trans, alpha=0.85)
        # 技術（赤系の矢印つき折れ線）
        ax.annotate("", xy=(tx[-1], ty[-1]), xytext=(tx[0], ty[0]),
                    arrowprops=dict(arrowstyle="-|>", color=RED, lw=2.4,
                                    connectionstyle="arc3,rad=-0.05"))
        ax.plot(tx, ty, "o", color=RED, ms=7, zorder=5)
        ax.text(tx[-1], ty[-1], " 技術（走り方を変える）", color=RED, fontsize=10,
                va="center", ha="left", fontweight="bold")
        # トレーニング（緑系の矢印つき折れ線）
        if len(arch) >= 2:
            ex = [a["biartic_peak_lMtilde"] for a in arch]
            ey = [a["speed"] for a in arch]
            ax.annotate("", xy=(ex[-1], ey[-1]), xytext=(ex[0], ey[0]),
                        arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=2.4))
            ax.plot(ex, ey, "s", color=GREEN, ms=7, zorder=5)
            ax.text(ex[-1], ey[-1], " トレーニング（筋を鍛える）", color=GREEN,
                    fontsize=10, va="center", ha="left", fontweight="bold")
        # 現状（出発点）
        ax.plot(tx[0], ty[0], "P", color="k", ms=13, zorder=6)
        ax.annotate("現状", xy=(tx[0], ty[0]), xytext=(tx[0], ty[0] + 0.12),
                    ha="center", fontsize=10, fontweight="bold")
        ax.set_xlim(ax_max, ax_min)  # 左ほど安全
        ax.set_xlabel("ケガの危険サイン →（筋束の伸ばされ過ぎ）", fontsize=11)
        ax.set_ylabel("最高速度（m/s）→", fontsize=11)
        ax.set_title(title, fontsize=12.5, fontweight="bold")
        ax.grid(alpha=0.25)
        _box(ax, 0.03, 0.16, concl, fc=concl_color, ec="#555555", fontsize=10.5,
             va="bottom")

    panel(axes[0], sh, "Fascicle",
          "① 筋束が“短い”選手（もともと高リスク）",
          "結論：原因が“筋束の短さ（形）”なら、走り方より\n"
          "【筋を鍛えて筋束を伸ばす】方が有利。\n"
          "→ 速さを保ったまま危険域から抜けられる。\n"
          "（走り方だけで安全にすると速度が急落）",
          "#EAF7EF")
    panel(axes[1], wk, "Strength",
          "② 筋力が“弱い”選手（もともと過伸張ではない）",
          "結論：強化＝“速さ”、技術＝“安全”の別々のつまみ。\n"
          "ひずみは元々安全域なので、強化は主に速さ用。\n"
          "→ 目的に合わせて使い分ける。",
          "#FEF9E7")

    fig.suptitle("あなたはどのタイプ？ ― 選手ごとに“最適な直し方”は違う（技術 vs トレーニング）",
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    _save(fig, "explainer_decision_jp.png")


def _save(fig, name):
    os.makedirs(AP.OUTDIR, exist_ok=True)
    out = os.path.join(AP.OUTDIR, name)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"図を保存: {out}")


def main():
    by_ath = AP.collect(target_N=50)
    if not any(by_ath[a] for a in AP.ATHLETES):
        print("Paretoデータが見つかりません。先に run_ham_pareto.bat を実行してください。")
        return
    fig_frontier_explainer(by_ath)
    fig_decision_explainer(by_ath)


if __name__ == "__main__":
    main()
