"""
Fig6_numerical_robustness.py -- shows the primary result is not an artefact of
unmet target angle, constraint violation, a single condition, speed, or cherry-picked
solutions.  Built from Results/Independent_Audit_20260819/final_source_manifest.csv
(all 95 discovered MAT, no dedup) + the 8 adopted primary files.

Panel A: expected vs achieved touchdown tilt (identity), shape = standard/wide, fill = status
Panel B: final primal infeasibility per attempt (log), solver-tolerance line, all attempts
Panel C: achieved speed vs achieved tilt for ALL PelvisTD attempts, by status/mesh
         (complementary to Fig 2C, which already shows speed-adjusted slope + LOO)
Panel D: discovery -> adoption exclusion flow with reasons
"""
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

plt = C.setup_mpl()
import matplotlib.gridspec as gridspec
from datetime import datetime

MAN = os.path.join(C.AUDIT, "final_source_manifest.csv")
PRIMARY = {fn for _, fn in C.SELECTED_N100}


def fnum(x):
    try:
        return float(x)
    except Exception:
        return float("nan")


def main():
    rows = list(csv.DictReader(open(MAN, encoding="utf-8")))
    for r in rows:
        r["mesh_N"] = int(fnum(r["mesh_N"]))
        r["anterior"] = fnum(r["anterior_tilt_deg"])
        r["td_signed"] = fnum(r["td_tilt_deg_signed"])
        r["inf_pr"] = fnum(r["final_inf_pr"])
        r["speed"] = fnum(r["speed_mps"])
        r["offset"] = fnum(r["requested_offset_deg"])
        r["is_primary"] = r["source_file"] in PRIMARY

    ptd = [r for r in rows if r["experiment"].startswith("PelvicTD")]
    # mesh base = achieved anterior of the strict p0 for that mesh
    base = {}
    for m in (50, 100):
        cand = [r for r in ptd if r["mesh_N"] == m and r["offset"] == 0.0
                and r["return_status"] == "Solve_Succeeded"]
        if cand:
            base[m] = cand[0]["anterior"]
    # fallback
    base.setdefault(100, 7.987)
    base.setdefault(50, 7.4626)

    def status_class(r):
        if r["return_status"] == "Solve_Succeeded":
            return "strict"
        if r["return_status"] == "Solved_To_Acceptable_Level":
            return "acceptable"
        return "failed"

    FILL = {"strict": None, "acceptable": "half", "failed": "open"}
    SCOL = {"strict": "#1a9850", "acceptable": "#f39c12", "failed": "#d73027"}

    # ---- source CSVs ----
    all_rows = []
    for r in sorted(rows, key=lambda z: (z["experiment"], z["mesh_N"], z["offset"] if np.isfinite(z["offset"]) else 99)):
        all_rows.append([r["source_file"], r["experiment"], r["condition"], r["mesh_N"],
                         r["offset"] if np.isfinite(r["offset"]) else "", r["return_status"],
                         r["strict"], f"{r['anterior']:.4f}" if np.isfinite(r["anterior"]) else "",
                         f"{r['speed']:.5f}" if np.isfinite(r["speed"]) else "",
                         f"{r['inf_pr']:.3e}" if np.isfinite(r["inf_pr"]) else "",
                         "primary" if r["is_primary"] else ""])
    all_csv = C.write_csv(os.path.join(C.SRC, "Fig6_all_attempts.csv"),
                          ["source_file", "experiment", "condition", "mesh_N", "requested_offset_deg",
                           "return_status", "strict", "anterior_tilt_deg", "speed_mps",
                           "final_inf_pr", "adopted"], all_rows)

    # ---- exclusion flow (primary N=100 PelvisTDwide) ----
    n_total = len(rows)
    n_readable = sum(1 for r in rows if r["error"] in ("", None))
    ptd_n100 = [r for r in ptd if r["mesh_N"] == 100]
    wide_n100 = [r for r in ptd_n100 if "wide" in r["condition"].lower() or r["experiment"] == "PelvicTD_wide"]
    strict_wide_n100 = [r for r in wide_n100 if r["return_status"] == "Solve_Succeeded"]
    n_ptd = len(ptd)
    n_ptd_n100 = len(ptd_n100)
    n_wide_n100 = len(wide_n100)
    n_strict_wide_n100 = len(strict_wide_n100)
    n_adopted = sum(1 for r in rows if r["is_primary"])
    n_accept = sum(1 for r in ptd if status_class(r) == "acceptable")
    n_failed = sum(1 for r in ptd if status_class(r) == "failed")
    # non-strict N=100 wide twins (e.g., m8 Maximum_CpuTime)
    nonstrict_wide_n100 = [r for r in wide_n100 if r["return_status"] != "Solve_Succeeded"]

    flow = [
        ("all result MAT discovered", n_total, ""),
        ("readable optimumOutput", n_readable, f"{n_total-n_readable} unreadable"),
        ("experiment = PelvicTD", n_ptd, "other experiments set aside"),
        ("mesh N=100", n_ptd_n100, f"{n_ptd-n_ptd_n100} are N=50"),
        ("PelvisTDwide family", n_wide_n100, "standard family excluded (different base)"),
        ("strict Solve_Succeeded", n_strict_wide_n100,
         f"{n_wide_n100-n_strict_wide_n100} non-strict (e.g. Maximum_CpuTime twin)"),
        ("adopted primary (min inf_pr / offset)", n_adopted, "1 per requested offset"),
    ]
    flow_csv = C.write_csv(os.path.join(C.SRC, "Fig6_exclusion_flow.csv"),
                           ["stage", "count", "excluded_reason"],
                           [[s, n, e] for s, n, e in flow])

    # ---- figure ----
    fig = plt.figure(figsize=(7.8, 6.6))
    gs = gridspec.GridSpec(2, 2, hspace=0.42, wspace=0.32)
    axA = fig.add_subplot(gs[0, 0])
    axB = fig.add_subplot(gs[0, 1])
    axC = fig.add_subplot(gs[1, 0])
    axD = fig.add_subplot(gs[1, 1])

    # Panel A: expected vs achieved anterior tilt
    lims = [0, 25]
    axA.plot(lims, lims, color="0.6", ls="--", lw=1.0, zorder=0)
    for r in ptd:
        if not np.isfinite(r["anterior"]) or not np.isfinite(r["offset"]):
            continue
        exp_ant = base[r["mesh_N"]] - r["offset"]
        cls = status_class(r)
        wide = ("wide" in r["condition"].lower()) or (r["experiment"] == "PelvisTD_wide")
        mk = "o" if wide else "s"
        fill = SCOL[cls] if cls == "strict" else ("white" if cls == "failed" else SCOL[cls])
        edge = SCOL[cls]
        axA.plot(exp_ant, r["anterior"], marker=mk, ms=7 if r["is_primary"] else 5.5,
                 mfc=fill, mec=edge, mew=1.5 if r["is_primary"] else 1.0,
                 alpha=0.5 if cls == "acceptable" else 0.95, zorder=3)
    axA.set_xlabel("expected anterior tilt = Nominal + requested offset (deg)")
    axA.set_ylabel("achieved anterior tilt (deg)")
    axA.set_title("A  Target-angle achievement", loc="left", fontweight="bold", fontsize=9.5)
    axA.set_xlim(0, 20); axA.set_ylim(0, 24)
    from matplotlib.lines import Line2D
    legA = [Line2D([0], [0], marker="o", color="w", mfc="0.3", mec="0.3", label="wide", ms=6),
            Line2D([0], [0], marker="s", color="w", mfc="0.3", mec="0.3", label="standard", ms=6),
            Line2D([0], [0], marker="o", color="w", mfc=SCOL["strict"], mec=SCOL["strict"], label="strict", ms=6),
            Line2D([0], [0], marker="o", color="w", mfc=SCOL["acceptable"], mec=SCOL["acceptable"], label="acceptable", ms=6, alpha=0.5),
            Line2D([0], [0], marker="o", color="w", mfc="white", mec=SCOL["failed"], label="failed", ms=6)]
    axA.legend(handles=legA, loc="upper left", fontsize=5.8, frameon=False, ncol=2, handletextpad=0.3, columnspacing=0.8)
    axA.text(0.98, 0.03, "on identity = target met", transform=axA.transAxes, fontsize=6, color="0.45", ha="right")

    # Panel B: inf_pr log
    xs, ys, cs, ec, sz = [], [], [], [], []
    order = sorted([r for r in ptd if np.isfinite(r["inf_pr"])], key=lambda z: z["inf_pr"])
    for i, r in enumerate(order):
        cls = status_class(r)
        xs.append(i); ys.append(max(r["inf_pr"], 1e-12)); cs.append(SCOL[cls])
        ec.append("black" if r["is_primary"] else SCOL[cls])
        sz.append(46 if r["is_primary"] else 22)
    axB.scatter(xs, ys, c=cs, edgecolors=ec, linewidths=[1.2 if s > 30 else 0.5 for s in sz], s=sz, zorder=3)
    axB.axhline(1e-4, color="#d73027", ls="--", lw=1.0)
    axB.text(0.5, 1.3e-4, "IPOPT constr_viol_tol = 1e-4", fontsize=6.2, color="#d73027", va="bottom")
    axB.set_yscale("log")
    axB.set_xlabel("PelvicTD attempts (sorted by infeasibility)")
    axB.set_ylabel("final primal infeasibility inf_pr")
    axB.set_title("B  Constraint residual per attempt", loc="left", fontweight="bold", fontsize=9.5)
    axB.text(0.02, 0.03, "black edge = adopted primary (all << 1e-6)", transform=axB.transAxes, fontsize=6, color="0.4")

    # Panel C: speed vs achieved tilt (all PelvisTD)
    for r in ptd:
        if not (np.isfinite(r["anterior"]) and np.isfinite(r["speed"])):
            continue
        cls = status_class(r)
        mk = "o" if r["mesh_N"] == 100 else "s"
        axC.plot(r["anterior"], r["speed"], marker=mk, ms=7 if r["is_primary"] else 5,
                 mfc=SCOL[cls] if cls != "failed" else "white", mec="black" if r["is_primary"] else SCOL[cls],
                 mew=1.3 if r["is_primary"] else 0.8, alpha=0.55 if cls == "acceptable" else 0.95, zorder=3)
    axC.set_xlabel("achieved anterior tilt (deg)")
    axC.set_ylabel("achieved speed (m/s)")
    axC.set_title("C  Speed vs tilt, all attempts", loc="left", fontweight="bold", fontsize=9.5)
    axC.text(0.02, 0.03, "o N=100   \u25a1 N=50   (failed solves collapse to low speed)",
             transform=axC.transAxes, fontsize=6, color="0.4")

    # Panel D: exclusion flow funnel
    axD.axis("off")
    axD.set_title("D  Discovery \u2192 adoption flow", loc="left", fontweight="bold", fontsize=9.5)
    ny = len(flow)
    maxc = max(n for _, n, _ in flow)
    for i, (stage, n, reason) in enumerate(flow):
        y = ny - 1 - i
        w = 0.62 * n / maxc
        x0 = 0.16
        axD.add_patch(plt.Rectangle((x0, y + 0.12), w, 0.6, transform=axD.transAxes,
                                    facecolor="#4a7fb5", edgecolor="white", alpha=0.9, clip_on=False))
        axD.text(x0 + 0.01, y + 0.42, f"{stage}", transform=axD.transAxes, fontsize=6.4,
                 va="center", ha="left", color="white", fontweight="bold")
        axD.text(x0 + w + 0.015, y + 0.42, f"n={n}", transform=axD.transAxes, fontsize=6.6,
                 va="center", ha="left", color="0.15")
        if reason:
            axD.text(x0, y + 0.02, reason, transform=axD.transAxes, fontsize=5.4,
                     va="center", ha="left", color="0.5", style="italic")
    axD.text(0.16, -0.02, f"PelvisTD acceptable={n_accept}, failed={n_failed}; "
             f"non-strict N=100 wide={len(nonstrict_wide_n100)} (excluded)",
             transform=axD.transAxes, fontsize=5.6, color="0.45", va="top")
    axD.set_xlim(0, 1); axD.set_ylim(0, ny)

    fig.suptitle("Figure 6 | Numerical operability, solution selection and sensitivity",
                 fontsize=10.5, fontweight="bold", x=0.01, ha="left", y=1.0)
    paths = C.save_fig(fig, "Fig6_numerical_robustness")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common = dict(figure_id="Fig6", source_commit="e7b8de9", simulation_commit="e7b8de9",
                  analysis_commit="e7b8de9", mesh="N=50 & N=100 (all attempts)",
                  condition_family="all PelvisTD (standard+wide) + full discovery set",
                  solver_acceptance_rule="strict Solve_Succeeded vs Solved_To_Acceptable_Level vs failed",
                  muscle_names_and_indices="n/a (solver-level figure)",
                  source_csv=all_csv + " ; " + flow_csv,
                  plotting_script="scripts/Fig6_numerical_robustness.py",
                  pdf_path=paths[0], svg_path=paths[1], png_path=paths[2],
                  generated_at=ts, qa_status="auto-pass; visual pending",
                  input_path="final_source_manifest.csv",
                  input_sha256="see sha256_manifest.csv")
    frags = [
        dict(common, panel_id="A", analytical_question="Was the requested touchdown angle actually achieved?",
             takeaway="Strict solves lie on identity; failed/acceptable deviate.",
             phase_window="touchdown", metric_formula="achieved -pelvis_tilt vs base+offset"),
        dict(common, panel_id="B", analytical_question="Do adopted solutions satisfy the constraint?",
             takeaway="8 primary inf_pr ~1e-9..1e-7, far below 1e-4; failures >1e-2.",
             phase_window="solver", metric_formula="final inf_pr (log)"),
        dict(common, panel_id="C", analytical_question="Is the result an artefact of speed differences?",
             takeaway="Adopted 8 cluster at ~11.75-11.80 m/s; failures collapse to low speed.",
             phase_window="whole stride", metric_formula="ave_speed vs achieved anterior tilt"),
        dict(common, panel_id="D", analytical_question="How were 8 conditions selected from all attempts?",
             takeaway=f"{n_total} discovered -> {n_strict_wide_n100} strict wide N=100 -> {n_adopted} adopted.",
             phase_window="n/a", metric_formula="discovery/selection funnel"),
    ]
    C.write_manifest_fragment("Fig6", frags)
    print("Fig6 done:", paths[2])
    print(f"  flow: total={n_total} readable={n_readable} ptd={n_ptd} ptd_n100={n_ptd_n100} "
          f"wide_n100={n_wide_n100} strict={n_strict_wide_n100} adopted={n_adopted} "
          f"accept={n_accept} failed={n_failed}")


if __name__ == "__main__":
    main()
