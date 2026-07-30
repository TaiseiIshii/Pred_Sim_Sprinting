"""
visualize_ham_pareto.py
=======================
Publication figures for the injury-minimising optimal-technique study (RQ3+RQ4).

Figure A  - Pareto frontier: top speed vs peak biarticular fascicle strain, one
            curve per athlete (nominal / short-fascicle / weak), annotated by the
            injury-penalty weight. The injury-risk band (lMtilde > 1.15) and the
            "free-lunch" points (>=2% strain cut for <0.5% speed loss) are marked.
Figure B  - RQ4 technique-vs-training: for an at-risk athlete, the TECHNIQUE path
            (this study's Pareto frontier) is overlaid on the TRAINING path (the
            RQ2 architecture dose-response) in the same speed<->strain plane.
Figure C  - Per-muscle peak strain vs penalty weight (nominal athlete): the
            penalty preferentially protects the biarticular hamstrings while the
            monoarticular bifemsh control barely moves.

Reads saved data only. Run analyze_ham_pareto.py first (or alongside).

Usage:
    python visualize_ham_pareto.py
"""
import os

import numpy as np

import analyze_ham_pareto as AP
from injury_metrics import BIARTIC, HAM, compute_injury_metrics

RISK = 1.15  # normalised fibre length flagged as injury-risk in the report gallery
COLOR = {"Nom": "navy", "Sh": "crimson", "Wk": "darkorange"}


def _mpl():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except Exception as e:  # noqa: BLE001
        print(f"[viz skipped] matplotlib unavailable: {e}")
        return None


def fig_frontier(by_ath, plt):
    from matplotlib.transforms import blended_transform_factory
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    # Gather all strain values to size the risk band / x-limits sensibly.
    allx = [r["peak_lMtilde"] for ath in AP.ATHLETES
            for r in AP.free_lunch(by_ath[ath]) if len(by_ath[ath]) >= 1]
    xmax = max(allx + [RISK]) + 0.05 if allx else 2.0
    xmin = min(allx) - 0.03 if allx else 0.85
    ax.axvspan(RISK, xmax, color="red", alpha=0.06, zorder=0)
    ax.axvline(RISK, ls="--", color="red", lw=1, alpha=0.6)
    trans = blended_transform_factory(ax.transData, ax.transAxes)
    ax.text(RISK + 0.008, 0.5, "injury-risk zone (lMtilde > 1.15)", color="red",
            fontsize=8, va="center", rotation=90, transform=trans, alpha=0.7)
    any_pts = False
    for ath in AP.ATHLETES:
        rows = AP.free_lunch(by_ath[ath])
        if len(rows) < 2:
            continue
        any_pts = True
        x = [r["peak_lMtilde"] for r in rows]
        y = [r["speed"] for r in rows]
        ax.plot(x, y, "o-", color=COLOR[ath], label=f"{AP.ATH_LABEL[ath]} (technique sweep)")
        for r in rows:
            ax.annotate(f"{r['weight']:.2f}", (r["peak_lMtilde"], r["speed"]),
                        textcoords="offset points", xytext=(4, 4), fontsize=7,
                        color=COLOR[ath])
            if r["free_lunch"]:
                ax.plot(r["peak_lMtilde"], r["speed"], "*", color="gold",
                        markersize=16, markeredgecolor="k", zorder=5)
    if not any_pts:
        print("[fig A skipped] need >=2 weights for at least one athlete")
        plt.close(fig)
        return
    ax.set_xlim(xmin, xmax)
    ax.set_xlabel("peak biarticular fascicle strain  (norm. fibre length)")
    ax.set_ylabel("top sprinting speed  (m/s)")
    ax.set_title("RQ3: speed\u2013safety Pareto frontier\n"
                 "(gold star = free-lunch: risk\u2193 at negligible speed cost)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    _save(fig, "pareto_frontier.png")


def fig_technique_vs_training(by_ath, plt):
    """RQ4: overlay technique (Pareto) and training (RQ2 architecture) paths."""
    try:
        import analyze_ham_architecture as AA
    except Exception as e:  # noqa: BLE001
        print(f"[fig B skipped] cannot import analyze_ham_architecture: {e}")
        return
    specs = [("Sh", "Fascicle", "fibre-length"), ("Wk", "Strength", "strength")]
    panels = []
    for ath, mode, label in specs:
        tech = AP.free_lunch(by_ath[ath])
        if len(tech) >= 2:
            panels.append((ath, mode, label, tech))
    if not panels:
        print("[fig B skipped] need an at-risk athlete Pareto sweep (short/weak)")
        return
    fig, axes = plt.subplots(1, len(panels), figsize=(6.6 * len(panels), 5.2),
                             squeeze=False)
    for ax, (ath, mode, label, tech) in zip(axes[0], panels):
        # TECHNIQUE path (this study): fixed architecture, sweep penalty weight.
        tx = [r["peak_lMtilde"] for r in tech]
        ty = [r["speed"] for r in tech]
        ax.plot(tx, ty, "o-", color=COLOR[ath],
                label="technique change (this study)")
        # TRAINING path (RQ2): unpenalised, vary architecture from this athlete
        # (factor 0.80) toward nominal (1.00) and beyond.
        try:
            arch = AA.collect(mode, target_N=50)
        except Exception as e:  # noqa: BLE001
            arch = []
            print(f"[fig B: {ath}] RQ2 collect failed: {e}")
        arch = [a for a in arch if a.get("factor", 0) >= 0.80]
        arch.sort(key=lambda a: a["factor"])
        if len(arch) >= 2:
            ax.plot([a["biartic_peak_lMtilde"] for a in arch],
                    [a["speed"] for a in arch], "s--", color="seagreen",
                    label=f"training: {label} adaptation (RQ2)")
            for a in arch:
                ax.annotate(f"x{a['factor']:.2f}",
                            (a["biartic_peak_lMtilde"], a["speed"]),
                            textcoords="offset points", xytext=(4, -8),
                            fontsize=7, color="seagreen")
        ax.axvspan(RISK, 2.0, color="red", alpha=0.06)
        ax.axvline(RISK, ls="--", color="red", lw=1, alpha=0.6)
        ax.set_xlabel("peak biarticular fascicle strain  (norm. fibre length)")
        ax.set_ylabel("top sprinting speed  (m/s)")
        ax.set_title(f"RQ4: {AP.ATH_LABEL[ath]} athlete\ntechnique vs training")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="best")
    fig.suptitle("RQ4: which lever lowers fascicle strain more efficiently?",
                 fontsize=12)
    fig.tight_layout()
    _save(fig, "technique_vs_training.png")


def fig_permuscle(by_ath, plt):
    """Per-muscle peak strain vs penalty weight for the nominal athlete."""
    rows = sorted(by_ath.get("Nom", []), key=lambda r: r["weight"])
    rows = [r for r in rows if r.get("_file")]
    if len(rows) < 2:
        print("[fig C skipped] need >=2 nominal weights")
        return
    weights, permusc = [], {m: [] for m in HAM}
    for r in rows:
        try:
            d = compute_injury_metrics(r["_file"])
        except Exception as e:  # noqa: BLE001
            print(f"[fig C skip] {r['cond']}: {e}")
            continue
        weights.append(r["weight"])
        for m in HAM:
            permusc[m].append(d[m + "_peak_lMtilde"])
    if len(weights) < 2:
        return
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    styles = {"semimem": "o-", "semiten": "s-", "bifemlh": "^-", "bifemsh": "x--"}
    for m in HAM:
        lbl = m + (" (biartic)" if m in BIARTIC else " (mono, control)")
        ax.plot(weights, permusc[m], styles[m], label=lbl,
                lw=2 if m in BIARTIC else 1.4,
                color="grey" if m == "bifemsh" else None)
    ax.axhline(RISK, ls="--", color="red", lw=1, alpha=0.6)
    ax.set_xlabel("injury-penalty weight  wJ(13)")
    ax.set_ylabel("peak fascicle strain  (norm. fibre length)")
    ax.set_title("RQ3: the penalty preferentially protects the biarticular hamstrings\n"
                 "(nominal athlete; monoarticular bifemsh barely moves)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    _save(fig, "permuscle_vs_weight.png")


def _save(fig, name):
    os.makedirs(AP.OUTDIR, exist_ok=True)
    out = os.path.join(AP.OUTDIR, name)
    fig.savefig(out, dpi=150)
    print(f"Figure saved: {out}")


def main():
    plt = _mpl()
    if plt is None:
        return
    by_ath = AP.collect(target_N=50)
    if not any(by_ath[a] for a in AP.ATHLETES):
        print("No Pareto results found. Run run_ham_pareto.bat pilot first.")
        return
    fig_frontier(by_ath, plt)
    fig_technique_vs_training(by_ath, plt)
    fig_permuscle(by_ath, plt)


if __name__ == "__main__":
    main()
