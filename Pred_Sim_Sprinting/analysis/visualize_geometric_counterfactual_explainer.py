"""Create a Japanese explainer figure for the geometric counterfactual audit.

The figure is generated only from existing validation CSVs:
  - Results/Validation_Master/boundary_condition_static.csv
  - Results/Validation_Master/boundary_condition_motion.csv
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parent.parent
VAL = ROOT / "Results" / "Validation_Master"
OUTDIR = VAL

BI = ["semimem_l", "semiten_l", "bifemlh_l"]
BF = "bifemsh_l"
LAB = {"semimem_l": "SM", "semiten_l": "ST", "bifemlh_l": "BFlh", "bifemsh_l": "BFsh"}
COL = {
    "semimem_l": "#1b7837",
    "semiten_l": "#762a83",
    "bifemlh_l": "#2166ac",
    "bifemsh_l": "#666666",
}


def setup_font():
    for p in [
        Path(r"C:\Windows\Fonts\NotoSansJP-VF.ttf"),
        Path(r"C:\Windows\Fonts\YuGothB.ttc"),
        Path(r"C:\Windows\Fonts\meiryo.ttc"),
    ]:
        if p.exists():
            font_manager.fontManager.addfont(str(p))
            prop = font_manager.FontProperties(fname=str(p))
            matplotlib.rcParams["font.family"] = prop.get_name()
            break
    matplotlib.rcParams["axes.unicode_minus"] = False
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["svg.fonttype"] = "none"


def load_motion():
    with open(VAL / "boundary_condition_motion.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    motion = {}
    for cond in ["A_tree_rigid", "B_femur_fixed", "C_adaptive"]:
        motion[cond] = {}
        for m in BI + [BF]:
            vals = [
                float(r["dMTU_from_nominal_mm"])
                for r in rows
                if r["boundary_condition"] == cond
                and r["muscle"] == m
                and float(r["phase_pct"]) >= 85
            ]
            motion[cond][m] = max(vals) if vals else float("nan")
    return motion


def text(ax, *args, **kwargs):
    return ax.text(*args, **kwargs)


def box(ax, xy, w, h, text_value="", fc="white", ec="#222", lw=1.5, radius=0.025,
        fontsize=11, color="black", weight="normal"):
    patch = FancyBboxPatch(
        xy,
        w,
        h,
        boxstyle=f"round,pad=0.012,rounding_size={radius}",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
    )
    ax.add_patch(patch)
    if text_value:
        text(
            ax,
            xy[0] + w / 2,
            xy[1] + h / 2,
            text_value,
            ha="center",
            va="center",
            fontsize=fontsize,
            color=color,
            fontweight=weight,
        )
    return patch


def skeleton(ax, cx, cy, scale, mode, *, variant="compact"):
    pelvis_angle = math.radians(-25)
    if mode == "tree":
        femur_angle = math.radians(-115)
        femur_color = "#d95f02"
        caption = "大腿も一緒に回る"
    elif mode == "fixed":
        femur_angle = math.radians(-90)
        femur_color = "#1b9e77"
        caption = "大腿は世界座標で固定"
    else:
        femur_angle = math.radians(-96)
        femur_color = "#2166ac"
        caption = "再最適化でほぼ固定寄り"

    pelvis_len = 0.17 * scale
    dx = math.cos(pelvis_angle) * pelvis_len / 2
    dy = math.sin(pelvis_angle) * pelvis_len / 2
    ax.plot([cx - dx, cx + dx], [cy - dy, cy + dy], color="#333333", lw=8,
            solid_capstyle="round", zorder=4)
    text(ax, cx, cy + 0.055 * scale, "骨盤", ha="center", va="center", fontsize=10)

    hipx, hipy = cx + dx, cy + dy
    ax.add_patch(Circle((hipx, hipy), 0.012 * scale, fc="white", ec="#222", lw=1.5, zorder=5))

    femur_len = (0.19 if variant == "legacy" else 0.115) * scale
    fx = hipx + math.cos(femur_angle) * femur_len
    fy = hipy + math.sin(femur_angle) * femur_len
    ax.plot([hipx, fx], [hipy, fy], color=femur_color, lw=7, solid_capstyle="round", zorder=3)
    text(ax, (hipx + fx) / 2 + 0.03 * scale, (hipy + fy) / 2, "大腿",
         ha="left", va="center", fontsize=9, color=femur_color)

    origin = (cx - dx * 0.45, cy - dy * 0.45 - 0.015 * scale)
    ax.plot([origin[0], fx], [origin[1], fy], color="#b2182b", lw=3.5, alpha=0.85, zorder=6)
    text(ax, (origin[0] + fx) / 2 - 0.04 * scale, (origin[1] + fy) / 2, "ハム",
         ha="right", va="center", fontsize=9, color="#b2182b")

    ax.add_patch(FancyArrowPatch(
        (cx - 0.105 * scale, cy + 0.11 * scale),
        (cx - 0.035 * scale, cy + 0.06 * scale),
        connectionstyle="arc3,rad=-0.5",
        arrowstyle="-|>",
        mutation_scale=14,
        color="#c44e52",
        lw=2,
    ))
    text(ax, cx - 0.13 * scale, cy + 0.12 * scale, "前傾", fontsize=9, color="#c44e52")
    text(ax, cx, cy - 0.23 * scale, caption, ha="center", va="center", fontsize=10)


def bar_group(ax, x0, y0, w, h, vals, title):
    text(ax, x0, y0 + h + 0.025, title, ha="left", va="bottom", fontsize=10, fontweight="bold")
    maxv = 11.0
    gap = h / 5.2
    for i, m in enumerate(BI + [BF]):
        y = y0 + h - (i + 1) * gap
        value = vals[m]
        text(ax, x0, y + 0.008, LAB[m], ha="left", va="center",
             fontsize=9, color=COL[m], fontweight="bold")
        ax.add_patch(Rectangle((x0 + 0.07, y), w - 0.15, 0.017, facecolor="#eeeeee",
                               edgecolor="none"))
        width = max(0, min(w - 0.15, (value / maxv) * (w - 0.15)))
        ax.add_patch(Rectangle((x0 + 0.07, y), width, 0.017, facecolor=COL[m],
                               edgecolor="none", alpha=0.85))
        text(ax, x0 + w, y + 0.008, f"{value:+.1f} mm", ha="right", va="center", fontsize=9)


def panel_title(ax, x, y, num, title, subtitle, fc):
    box(ax, (x, y), 0.285, 0.085, fc=fc, ec="#333", lw=1.2)
    text(ax, x + 0.018, y + 0.045, num, ha="left", va="center",
         fontsize=18, fontweight="bold", color="#333")
    text(ax, x + 0.072, y + 0.055, title, ha="left", va="center",
         fontsize=13, fontweight="bold")
    text(ax, x + 0.072, y + 0.026, subtitle, ha="left", va="center",
         fontsize=9.5, color="#333")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["compact", "legacy"], default="compact")
    args = ap.parse_args()

    setup_font()
    motion = load_motion()
    ratio_mean = np.mean([100 * motion["B_femur_fixed"][m] / motion["C_adaptive"][m] for m in BI])

    fig = plt.figure(figsize=(16, 9), dpi=180)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    text(ax, 0.5, 0.965, "骨盤前傾がハムストリングを伸ばす「幾何学的な理由」",
         ha="center", va="center", fontsize=24, fontweight="bold")
    text(ax, 0.5, 0.925,
         "tree-rigid と femur-fixed は走動作ではなく、adaptive 解を解釈するための幾何学的反実仮想",
         ha="center", va="center", fontsize=13, color="#444")

    xs = [0.045, 0.36, 0.675]
    fcs = ["#f3f3f3", "#e8f4ef", "#e8f0fb"]
    titles = [
        ("1", "tree-rigid", "骨盤と大腿が一体で回る"),
        ("2", "femur-fixed", "大腿を固定し股関節で補償"),
        ("3", "adaptive", "実際に再最適化された走動作"),
    ]
    for x, fc, item in zip(xs, fcs, titles):
        box(ax, (x, 0.515), 0.28, 0.365, fc="white", ec="#cccccc", lw=1.2)
        panel_title(ax, x + 0.012, 0.79, *item, fc)

    for x, mode in zip(xs, ["tree", "fixed", "adaptive"]):
        skeleton(ax, x + 0.145, 0.665, 1.0, mode, variant=args.variant)

    box(ax, (xs[0] + 0.035, 0.535), 0.21, 0.075, "終末遊脚 ΔMTU\n二関節ハム ≈ 0 mm",
        fc="#fff7f7", ec="#d9b0b0", fontsize=11, weight="bold", color="#8c2d04")
    box(ax, (xs[1] + 0.035, 0.535), 0.21, 0.075, "終末遊脚 ΔMTU\n+7〜9 mm",
        fc="#f2fff9", ec="#9ac9b0", fontsize=11, weight="bold", color="#006d2c")
    box(ax, (xs[2] + 0.035, 0.535), 0.21, 0.075, "終末遊脚 ΔMTU\n+8〜10 mm",
        fc="#f2f7ff", ec="#9bbce0", fontsize=11, weight="bold", color="#084594")

    for x0, x1 in [(0.325, 0.36), (0.64, 0.675)]:
        ax.add_patch(FancyArrowPatch((x0, 0.70), (x1, 0.70), arrowstyle="simple",
                                     mutation_scale=18, color="#777", alpha=0.55))

    box(ax, (0.045, 0.115), 0.45, 0.345, fc="#fbfbfb", ec="#cccccc", lw=1.2)
    text(ax, 0.065, 0.432, "終末遊脚期の筋腱長変化（代表 −8° 条件）",
         ha="left", va="center", fontsize=15, fontweight="bold")
    bar_group(ax, 0.065, 0.245, 0.19, 0.135, motion["A_tree_rigid"], "A tree-rigid")
    bar_group(ax, 0.285, 0.245, 0.19, 0.135, motion["B_femur_fixed"], "B femur-fixed")
    bar_group(ax, 0.065, 0.13, 0.19, 0.085, motion["C_adaptive"], "C adaptive")
    box(ax, (0.285, 0.13), 0.19, 0.085,
        f"femur-fixed は\nadaptive の約 {ratio_mean:.0f}% を再現",
        fc="#fff7e6", ec="#d79f2a", fontsize=12, weight="bold", color="#8a5a00")

    box(ax, (0.525, 0.115), 0.43, 0.345, fc="#fbfbfb", ec="#cccccc", lw=1.2)
    text(ax, 0.545, 0.432, "この図から言えること／言えないこと",
         ha="left", va="center", fontsize=15, fontweight="bold")

    chain_y = 0.355
    items = [
        ("骨盤前傾を\n課す", "#f6d6d6"),
        ("股関節屈曲で\n実現される", "#d6e6f5"),
        ("二関節ハムだけ\n伸びる", "#f6d6d6"),
        ("負荷代理指標が\n増える", "#fdf2c8"),
    ]
    for i, (label, fc) in enumerate(items):
        x = 0.545 + i * 0.096
        box(ax, (x, chain_y - 0.045), 0.078, 0.09, label,
            fc=fc, ec="#777", fontsize=9.5, weight="bold")
        if i < len(items) - 1:
            ax.add_patch(FancyArrowPatch((x + 0.08, chain_y), (x + 0.095, chain_y),
                                         arrowstyle="-|>", mutation_scale=12, color="#555", lw=1.5))

    if args.variant == "legacy":
        text(ax, 0.55, 0.265, "✓ 安全な主張", fontsize=12, fontweight="bold", color="#006d2c")
        text(ax, 0.565, 0.23,
             "・骨盤前傾は、股関節をまたぐ幾何学的経路を通じて二関節ハムを伸ばす", fontsize=10.5)
        text(ax, 0.565, 0.20,
             "・BFsh（単関節）はほぼ変わらず、股関節横断性に特異的", fontsize=10.5)
        text(ax, 0.55, 0.16, "✕ 言い過ぎ", fontsize=12, fontweight="bold", color="#b2182b")
        text(ax, 0.565, 0.13,
             "・tree-rigid / femur-fixed が「走れる動作」だとは言わない", fontsize=10.5)
        text(ax, 0.565, 0.10,
             "・受傷確率を直接証明したとは言わない（負荷代理指標）", fontsize=10.5)
    else:
        text(ax, 0.55, 0.275, "✓ 安全な主張", fontsize=12, fontweight="bold", color="#006d2c")
        text(ax, 0.565, 0.24,
             "・骨盤前傾は、股関節をまたぐ幾何学的経路を通じて二関節ハムを伸ばす", fontsize=10.5)
        text(ax, 0.565, 0.212,
             "・BFsh（単関節）はほぼ変わらず、股関節横断性に特異的", fontsize=10.5)
        text(ax, 0.55, 0.172, "避ける主張", fontsize=12, fontweight="bold", color="#b2182b")
        text(ax, 0.565, 0.142,
             "・tree-rigid / femur-fixed が「走れる動作」だとは言わない", fontsize=10.5)
        text(ax, 0.565, 0.114,
             "・受傷確率を直接証明したとは言わない（負荷代理指標）", fontsize=10.5)

    text(ax, 0.5, 0.045,
         "Data: boundary_condition_static.csv / boundary_condition_motion.csv, OpenSim MTU length; "
         "dynamic feasibility is asserted only for adaptive re-optimized solutions.",
         ha="center", va="center", fontsize=9.5, color="#555")

    stem = ("fig_b3_geometric_counterfactual_explainer_JP_legacy"
            if args.variant == "legacy"
            else "fig_b3_geometric_counterfactual_explainer_JP")
    for ext in ["png", "svg", "pdf"]:
        path = OUTDIR / f"{stem}.{ext}"
        fig.savefig(path, dpi=300 if ext == "png" else None, bbox_inches="tight", facecolor="white")
        print(path)


if __name__ == "__main__":
    main()
