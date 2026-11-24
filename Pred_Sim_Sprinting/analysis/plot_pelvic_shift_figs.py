"""Regenerate the PelvicShift study figures (fig1-fig4) with proper Japanese fonts.

The original figures were produced by ``analyze_pelvic_shift.m``. On this machine
MATLAB renders the Japanese titles as mojibake (garbled glyphs), so this script
reproduces the same four figures from ``pelvic_shift_summary.csv`` using matplotlib
with a Japanese-capable font. Output PNGs overwrite the originals in the study folder.

Run (base conda env with matplotlib + numpy):
    python analysis/plot_pelvic_shift_figs.py
"""
from __future__ import annotations

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY_DIR = os.path.join(HERE, "..", "Results", "PelvicShift_Study")
CSV_PATH = os.path.join(STUDY_DIR, "pelvic_shift_summary.csv")

HAM_KEYS = ["semimem", "semiten", "bifemlh", "bifemsh"]
HAM_LABELS = {
    "semimem": "半膜様筋 (semimem)",
    "semiten": "半腱様筋 (semiten)",
    "bifemlh": "大腿二頭筋長頭 (bifemlh)",
    "bifemsh": "大腿二頭筋短頭・単関節 (bifemsh)",
}
MARKERS = ["o", "s", "^", "D"]
COLORS = ["#1f77b4", "#d62728", "#e8a200", "#7e3f9e"]


def setup_japanese_font() -> str:
    """Pick the first available Japanese font and configure matplotlib."""
    candidates = [
        "Yu Gothic", "Meiryo", "MS Gothic", "MS PGothic",
        "Noto Sans CJK JP", "Noto Sans JP", "Yu Mincho", "Hiragino Sans",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((c for c in candidates if c in available), None)
    if chosen is None:
        # Try common Windows font files directly.
        for path in (r"C:\Windows\Fonts\YuGothM.ttc", r"C:\Windows\Fonts\meiryo.ttc",
                     r"C:\Windows\Fonts\msgothic.ttc"):
            if os.path.exists(path):
                font_manager.fontManager.addfont(path)
                chosen = font_manager.FontProperties(fname=path).get_name()
                break
    if chosen:
        matplotlib.rcParams["font.family"] = chosen
    matplotlib.rcParams["axes.unicode_minus"] = False
    matplotlib.rcParams["figure.dpi"] = 150
    matplotlib.rcParams["savefig.dpi"] = 150
    return chosen or "(default)"


def load_rows() -> list[dict]:
    with open(CSV_PATH, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    # Deduplicate by offset (Nominal(0) and +0 deg are the same condition).
    seen: dict[float, dict] = {}
    for r in rows:
        off = float(r["offset"])
        if off not in seen:
            seen[off] = r
    out = [seen[o] for o in sorted(seen)]
    return out


def col(rows: list[dict], name: str) -> np.ndarray:
    return np.array([float(r[name]) for r in rows], dtype=float)


def bilateral(rows: list[dict], ham: str, metric: str) -> np.ndarray:
    left = col(rows, f"{ham}_L_{metric}")
    right = col(rows, f"{ham}_R_{metric}")
    return (left + right) / 2.0


def fig1_manipulation(rows, offs, out):
    fig, ax = plt.subplots(figsize=(6.2, 4.8))
    real = col(rows, "ptMean")
    i0 = int(np.argmin(np.abs(offs)))
    ref0 = real[i0] - offs[i0]
    ax.plot(offs, real, "-o", color="#1f77b4", lw=1.8, mfc="#1f77b4", label="実現値")
    ax.plot(offs, ref0 + offs, "k--", lw=1.3, label="基準 + オフセット（理想直線）")
    ax.set_xlabel("指示オフセット（度）")
    ax.set_ylabel("実現した平均 骨盤傾斜 pelvis_tilt（度）")
    ax.set_title("操作の成立：狙った傾きに正確にずらせている")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def fig2_dose_lm(rows, offs, out):
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    for ham, mk, cl in zip(HAM_KEYS, MARKERS, COLORS):
        y = bilateral(rows, ham, "peakLM")
        ax.plot(offs, y, marker=mk, color=cl, lw=1.6, mfc=cl, label=HAM_LABELS[ham])
    ax.axhline(1.2, color="k", ls=":", lw=1.0)
    ax.text(offs.min(), 1.205, "伸張のめやす (1.2)", fontsize=9)
    ax.set_xlabel("指示オフセット（度、マイナス＝前傾を強める）")
    ax.set_ylabel("peak 正規化筋線維長 lMtilde（左右平均）")
    ax.set_title("ハムストリングの伸び（peak 筋線維長）の用量反応")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def fig3_passive_ecc(rows, offs, out):
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.8))
    for ham, mk, cl in zip(HAM_KEYS, MARKERS, COLORS):
        axes[0].plot(offs, bilateral(rows, ham, "peakFpe"), marker=mk, color=cl,
                     lw=1.6, mfc=cl, label=HAM_LABELS[ham])
    axes[0].set_xlabel("指示オフセット（度、マイナス＝前傾）")
    axes[0].set_ylabel("peak 受動張力 Fpetilde（左右平均）")
    axes[0].set_title("受動張力（伸ばされたゴムの突っ張り）")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc="best", fontsize=9)
    for ham, mk, cl in zip(HAM_KEYS, MARKERS, COLORS):
        axes[1].plot(offs, bilateral(rows, ham, "eccWork"), marker=mk, color=cl,
                     lw=1.6, mfc=cl, label=HAM_LABELS[ham])
    axes[1].set_xlabel("指示オフセット（度、マイナス＝前傾）")
    axes[1].set_ylabel("伸張性負荷（エキセントリック）")
    axes[1].set_title("伸張性負荷（参考：強前傾では誤差大）")
    axes[1].grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def fig4_mechanism_cost(rows, offs, out):
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.8))
    # Left: touchdown hip flexion (left axis) + bifemlh MTU length (right axis)
    ax = axes[0]
    ln1 = ax.plot(offs, col(rows, "hipR_TD"), "-o", color="#1f77b4", lw=1.8,
                  label="接地時の股関節屈曲（度）")
    ax.set_xlabel("指示オフセット（度、マイナス＝前傾）")
    ax.set_ylabel("接地時の股関節屈曲（度）", color="#1f77b4")
    ax.tick_params(axis="y", labelcolor="#1f77b4")
    axr = ax.twinx()
    bifem_mtu = bilateral(rows, "bifemlh", "peakLMT")
    ln2 = axr.plot(offs, bifem_mtu, "-s", color="#d62728", lw=1.8,
                   label="大腿二頭筋長頭 MTU長（m）")
    axr.set_ylabel("ハムMTU長（m）", color="#d62728")
    axr.tick_params(axis="y", labelcolor="#d62728")
    ax.set_title("メカニズム：接地股関節屈曲 → ハムMTU長")
    ax.grid(True, alpha=0.3)
    lns = ln1 + ln2
    ax.legend(lns, [l.get_label() for l in lns], loc="best", fontsize=9)
    # Right: speed (left axis) + effort (right axis)
    ax = axes[1]
    ln1 = ax.plot(offs, col(rows, "speed"), "-o", color="#2ca02c", lw=1.8,
                  label="達成速度（m/s）")
    ax.set_xlabel("指示オフセット（度、マイナス＝前傾）")
    ax.set_ylabel("達成速度（m/s）", color="#2ca02c")
    ax.tick_params(axis="y", labelcolor="#2ca02c")
    axr = ax.twinx()
    ln2 = axr.plot(offs, col(rows, "effort"), "-s", color="#9467bd", lw=1.8,
                   label="筋努力 Σact²（平均）")
    axr.set_ylabel("筋努力 Σact²", color="#9467bd")
    axr.tick_params(axis="y", labelcolor="#9467bd")
    ax.set_title("課題コスト：速度と筋努力")
    ax.grid(True, alpha=0.3)
    lns = ln1 + ln2
    ax.legend(lns, [l.get_label() for l in lns], loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def main():
    font = setup_japanese_font()
    print(f"日本語フォント: {font}")
    rows = load_rows()
    offs = col(rows, "offset")
    print(f"条件数: {len(rows)} (offsets={offs.tolist()})")
    out = lambda name: os.path.join(STUDY_DIR, name)
    fig1_manipulation(rows, offs, out("fig1_manipulation_check.png"))
    fig2_dose_lm(rows, offs, out("fig2_dose_peakLM.png"))
    fig3_passive_ecc(rows, offs, out("fig3_dose_passive_eccwork.png"))
    fig4_mechanism_cost(rows, offs, out("fig4_mechanism_cost.png"))
    print("4枚の図を再生成しました（日本語ラベル）。")


if __name__ == "__main__":
    main()
