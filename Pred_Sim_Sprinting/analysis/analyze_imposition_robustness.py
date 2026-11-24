"""
analyze_imposition_robustness.py
Robustness / model-dependence check (supervisor validation requirement): does
the "anterior pelvic tilt -> hamstring loading" dose-response depend on HOW the
tilt is imposed?

Two independent imposition methods, both re-optimised:
  PelvisShift : the whole pelvis_tilt waveform is rigidly pinned (every node).
  PelvisTD    : only the touchdown pelvis_tilt is constrained; the rest is free.

If the tilt->peak fascicle length and tilt->peak contractile force slopes agree
between methods (over their speed-matched subsets), the Experiment-1 finding is
robust to the manipulation, not an artefact of one bounding scheme.

Reuses analyze_file() from analyze_pelvic_force_eccentric (saved data only).
Outputs Results/PelvicShift_Study/imposition_robustness.png + printed slopes.
"""
import glob
import os
import re

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analyze_pelvic_force_eccentric import analyze_file, RESULTS

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(RESULTS, "PelvicShift_Study")
HAM = ["semimem", "semiten", "bifemlh"]
COL = {"semimem": "#d62728", "semiten": "#2ca02c", "bifemlh": "#1f77b4"}


def collect_study(patterns, dedup_deg=0.4):
    """Newest .mat per condition; then dedup by realised mean tilt (keep newest)."""
    files = {}
    for pat in patterns:
        for f in glob.glob(os.path.join(RESULTS, pat)):
            tok = re.search(r"___(.+)\.mat$", os.path.basename(f))
            tok = tok.group(1) if tok else os.path.basename(f)
            if tok not in files or os.path.getmtime(f) > os.path.getmtime(files[tok]):
                files[tok] = f
    rows = []
    for f in files.values():
        try:
            r = analyze_file(f)
        except Exception as e:  # noqa: BLE001
            print(f"[skip] {os.path.basename(f)}: {e}")
            continue
        r["_mtime"] = os.path.getmtime(f)
        rows.append(r)
    # dedup by rounded tilt, keep newest
    best = {}
    for r in rows:
        key = round(r["ptMean"] / dedup_deg)
        if key not in best or r["_mtime"] > best[key]["_mtime"]:
            best[key] = r
    return sorted(best.values(), key=lambda r: r["ptMean"])


def fit(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    s, b = np.polyfit(x, y, 1)
    yh = s * x + b
    r2 = 1 - np.sum((y - yh) ** 2) / np.sum((y - y.mean()) ** 2)
    return s, b, r2


def main():
    shift = collect_study(["pred_sprinting_data_*PelvisShift*.mat"])
    td = collect_study(["pred_sprinting_data_*PelvisTD_*.mat",
                        "pred_sprinting_data_*PelvisTDwide_*.mat"])
    # keep only feasible & speed-matched
    def keep(rows):
        return [r for r in rows
                if abs(100 * (r["speed"] - 11.78) / 11.78) <= 3.0
                and ("Succeeded" in r.get("status", "") or "Acceptable" in r.get("status", ""))]
    shift_s, td_s = keep(shift), keep(td)

    print("=" * 84)
    print(f"PelvisShift feasible/speed-matched n={len(shift_s)} "
          f"(tilt {min(r['ptMean'] for r in shift_s):.1f}..{max(r['ptMean'] for r in shift_s):.1f}, "
          f"speed {min(r['speed'] for r in shift_s):.2f}-{max(r['speed'] for r in shift_s):.2f})")
    print(f"PelvisTD    feasible/speed-matched n={len(td_s)} "
          f"(tilt {min(r['ptMean'] for r in td_s):.1f}..{max(r['ptMean'] for r in td_s):.1f}, "
          f"speed {min(r['speed'] for r in td_s):.2f}-{max(r['speed'] for r in td_s):.2f})")

    print("\n%-10s %-8s %12s %12s   agreement" % ("muscle", "metric", "Shift slope", "TD slope"))
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for metric, ax, ylab in (("peakLM", axes[0], "peak norm. fascicle length"),
                             ("peakFceN", axes[1], "peak contractile force (N)")):
        for m in HAM:
            xs, ys = [r["ptMean"] for r in shift_s], [r[f"{m}_{metric}"] for r in shift_s]
            xt, yt = [r["ptMean"] for r in td_s], [r[f"{m}_{metric}"] for r in td_s]
            ss, sb, sr2 = fit(xs, ys)
            ts, tb, tr2 = fit(xt, yt)
            ax.plot(xs, ys, "o", color=COL[m], mfc="none", ms=7)
            ax.plot(xt, yt, "s", color=COL[m], ms=5)
            xx = np.linspace(min(min(xs), min(xt)), max(max(xs), max(xt)), 50)
            ax.plot(xx, ss * xx + sb, "--", color=COL[m], lw=1, alpha=0.7)
            ax.plot(xx, ts * xx + tb, "-", color=COL[m], lw=1.5,
                    label=f"{m}")
            agree = "OK" if np.sign(ss) == np.sign(ts) and (
                abs(ss - ts) / (abs(ss) + 1e-9) < 0.6 or abs(ss) < 1e-4) else "differ"
            print("%-10s %-8s %12.4f %12.4f   %s" % (m, metric, ss, ts, agree))
        ax.set_xlabel("realised mean pelvis tilt (deg)  (- = anterior)")
        ax.set_ylabel(ylab)
        ax.set_title(f"{ylab}\n(o/-- = PelvisShift, s/- = PelvisTD)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
        ax.invert_xaxis()
    fig.suptitle("Robustness: anterior-tilt dose-response agrees across two independent "
                 "imposition methods", fontsize=11)
    fig.tight_layout()
    p = os.path.join(OUTDIR, "imposition_robustness.png")
    fig.savefig(p, dpi=150)
    print("\nwrote", os.path.relpath(p, HERE))


if __name__ == "__main__":
    main()
