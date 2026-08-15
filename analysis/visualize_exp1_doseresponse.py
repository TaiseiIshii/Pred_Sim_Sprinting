"""
visualize_exp1_doseresponse.py
Figure 2 (pelvic tilt -> hip flexion) and Figure 3 (pelvic tilt -> hamstring
peak fascicle length) for Experiment 1, from the P0 CSV. Speed-matched
conditions are drawn solid; the two infeasible anterior runs (speed collapsed
to ~10.5 m/s) are drawn as open markers and EXCLUDED from the regression, so the
dose-response is read only where speed is controlled.
"""
import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "..", "Results", "PelvicShift_Study")
CSV = os.path.join(OUTDIR, "pelvic_force_eccentric.csv")
HAM = ["semimem", "semiten", "bifemlh", "bifemsh"]
COL = {"semimem": "#d62728", "semiten": "#2ca02c", "bifemlh": "#1f77b4",
       "bifemsh": "#9467bd"}


def load():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    for r in rows:
        for k, v in list(r.items()):
            if k not in ("cond", "status", "speedMatched") and not k.endswith("lengAtPeakLM") \
                    and not k.endswith("peakInStance"):
                try:
                    r[k] = float(v)
                except (ValueError, TypeError):
                    pass
        r["matched"] = str(r["speedMatched"]).startswith("True")
    rows.sort(key=lambda r: r["ptMean"])
    return rows


def _fit(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    s, b = np.polyfit(x, y, 1)
    yh = s * x + b
    r2 = 1 - np.sum((y - yh) ** 2) / np.sum((y - y.mean()) ** 2)
    return s, b, r2


def fig2(rows):
    sub = [r for r in rows if r["matched"]]
    fig, ax = plt.subplots(figsize=(6.4, 5))
    for key, lab, c in (("hipR_TD", "hip flexion @ touchdown", "#1f77b4"),
                        ("hipR_peak", "hip flexion peak", "#d62728")):
        xs = [r["ptMean"] for r in sub]
        ys = [r[key] for r in sub]
        ax.plot(xs, ys, "o", color=c, label=lab)
        s, b, r2 = _fit(xs, ys)
        xx = np.linspace(min(xs), max(xs), 50)
        ax.plot(xx, s * xx + b, "-", color=c, lw=1.5,
                label=f"  slope {s:.2f}°/°, R²={r2:.2f}")
        # infeasible (open)
        for r in rows:
            if not r["matched"]:
                ax.plot(r["ptMean"], r[key], "o", mfc="none", mec=c, ms=8)
    ax.set_xlabel("realised mean pelvis tilt (deg)   (more negative = more anterior)")
    ax.set_ylabel("hip flexion angle (deg)")
    ax.set_title("Figure 2  Imposed pelvic tilt drives hip flexion\n"
                 "(open markers = infeasible, speed-collapsed, excluded)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.invert_xaxis()
    fig.tight_layout()
    p = os.path.join(OUTDIR, "fig2_tilt_vs_hip.png")
    fig.savefig(p, dpi=150)
    print("wrote", os.path.relpath(p, HERE))


def fig3(rows):
    sub = [r for r in rows if r["matched"]]
    fig, ax = plt.subplots(figsize=(6.8, 5))
    for m in HAM:
        xs = [r["ptMean"] for r in sub]
        ys = [r[f"{m}_peakLM"] for r in sub]
        c = COL[m]
        s, b, r2 = _fit(xs, ys)
        lab = f"{m}  ({s:+.4f}/°, R²={r2:.2f})"
        ax.plot(xs, ys, "o", color=c, label=lab)
        xx = np.linspace(min(xs), max(xs), 50)
        ax.plot(xx, s * xx + b, "-", color=c, lw=1.3)
        for r in rows:
            if not r["matched"]:
                ax.plot(r["ptMean"], r[f"{m}_peakLM"], "o", mfc="none", mec=c, ms=7)
    ax.axhline(1.0, color="0.6", ls=":", lw=1, label="optimal fibre length")
    ax.set_xlabel("realised mean pelvis tilt (deg)   (more negative = more anterior)")
    ax.set_ylabel("peak normalised fascicle length $\\tilde l_M$")
    ax.set_title("Figure 3  Anterior pelvic tilt lengthens the biarticular hamstrings\n"
                 "(monoarticular bifemsh is flat; open markers = infeasible)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="best")
    ax.invert_xaxis()
    fig.tight_layout()
    p = os.path.join(OUTDIR, "fig3_tilt_vs_fascicle.png")
    fig.savefig(p, dpi=150)
    print("wrote", os.path.relpath(p, HERE))


def main():
    rows = load()
    fig2(rows)
    fig3(rows)


if __name__ == "__main__":
    main()
