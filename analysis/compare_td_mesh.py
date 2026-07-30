"""Mesh-independence check: overlay the v3 (TDPT) dose-response at N=50 vs N=100.

Reads the two summary CSVs produced by plot_pelvic_td_figs.py:
  pelvic_td_summary.csv        (N=50)
  pelvic_td_summary_N100.csv   (N=100)
and overlays peak normalised fibre length (peakLM) and top speed vs the
touchdown anterior-tilt angle, with N=50 solid and N=100 dashed. If the curves
coincide, the conclusions are mesh-independent.

Run (base conda python): python analysis/compare_td_mesh.py
"""
from __future__ import annotations

import csv
import os

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.join(HERE, "..", "Results", "PelvicTD_Study")

HAM = {"semimem": ("半膜様筋 semimem", "#1f77b4", "o"),
       "semiten": ("半腱様筋 semiten", "#d62728", "s"),
       "bifemlh": ("二頭筋長頭 bifemlh", "#e8a200", "^"),
       "bifemsh": ("二頭筋短頭 bifemsh(対照)", "#7e3f9e", "D")}


def setup_jp_font():
    cand = ["Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP"]
    avail = {f.name for f in font_manager.fontManager.ttflist}
    pick = next((c for c in cand if c in avail), None)
    if pick:
        matplotlib.rcParams["font.family"] = pick
    matplotlib.rcParams["axes.unicode_minus"] = False


def load_csv(path):
    with open(path, encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    rows.sort(key=lambda r: float(r["anterior"]))
    return rows


def col(rows, name):
    return np.array([float(r[name]) for r in rows], dtype=float)


def slope(rows, name):
    x = col(rows, "anterior")
    y = col(rows, name)
    return np.polyfit(x, y, 1)[0]


def main():
    setup_jp_font()
    n50 = load_csv(os.path.join(STUDY, "pelvic_td_summary.csv"))
    n100 = load_csv(os.path.join(STUDY, "pelvic_td_summary_N100.csv"))

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.4))

    # --- panel A: peakLM dose-response overlay ---
    ax = axes[0]
    for mk, (lab, cl, mc) in HAM.items():
        ax.plot(col(n50, "anterior"), col(n50, f"{mk}_peakLM"),
                marker=mc, color=cl, lw=1.8, ls="-", ms=6, label=f"{lab} (N=50)")
        ax.plot(col(n100, "anterior"), col(n100, f"{mk}_peakLM"),
                marker=mc, color=cl, lw=1.5, ls="--", mfc="none", ms=7,
                label=f"{lab} (N=100)")
    ax.set_xlabel("接地時の骨盤前傾角（度、右ほど強い前傾）")
    ax.set_ylabel("peak 正規化筋線維長 lMtilde（左右平均）", fontsize=9)
    ax.set_title("ハムの伸び：N=50（実線）vs N=100（破線）", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=6.5, ncol=2)

    # --- panel B: speed overlay ---
    ax = axes[1]
    ax.plot(col(n50, "anterior"), col(n50, "speed"), "-o", color="#2ca02c",
            lw=1.8, ms=6, label="N=50")
    ax.plot(col(n100, "anterior"), col(n100, "speed"), "--s", color="#2ca02c",
            lw=1.5, ms=7, mfc="none", label="N=100")
    sp = np.concatenate([col(n50, "speed"), col(n100, "speed")])
    ax.set_ylim(sp.min() - 0.6, sp.max() + 0.6)
    ax.set_xlabel("接地時の骨盤前傾角（度、右ほど強い前傾）")
    ax.set_ylabel("達成トップ速度（m/s）")
    ax.set_title("速度：N=50 vs N=100（どちらもほぼ一定）", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9)

    fig.suptitle("v3(TDPT) メッシュ非依存性：用量反応は N=50 と N=100 で一致",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = os.path.join(STUDY, "td_fig4_mesh_compare.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print("wrote", out)

    # --- slope comparison table ---
    print("\nslope per deg anterior tilt   N=50      N=100     |diff|")
    for pk in ("peakLM", "peakLMT", "peakFpe"):
        print(f"[{pk}]")
        for mk, (lab, _, _) in HAM.items():
            s50 = slope(n50, f"{mk}_{pk}")
            s100 = slope(n100, f"{mk}_{pk}")
            print(f"   {lab:22s} {s50:+8.5f} {s100:+8.5f}  {abs(s50 - s100):.5f}")

    # --- speed range ---
    print(f"\nspeed range  N=50  [{col(n50,'speed').min():.3f}, {col(n50,'speed').max():.3f}] m/s"
          f"   N=100 [{col(n100,'speed').min():.3f}, {col(n100,'speed').max():.3f}] m/s")


if __name__ == "__main__":
    main()
