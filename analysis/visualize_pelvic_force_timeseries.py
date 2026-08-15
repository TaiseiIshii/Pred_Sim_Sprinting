"""
visualize_pelvic_force_timeseries.py
Figure 5: hamstring fibre length, fibre velocity, contractile force and
activation over the sprint step, for representative anterior / nominal /
posterior pelvic-tilt conditions (speed-matched). Visualises the terminal-swing
ECCENTRIC window (fibre lengthening while force is high) that STEP 5 quantified.

Uses saved data only (scipy). Left biarticular hamstrings (their terminal-swing
stretch peak falls inside this right-stance step ~65-85%).

  & '...\\miniconda3\\python.exe' analysis\\visualize_pelvic_force_timeseries.py
"""
import glob
import os
import re

import numpy as np
from scipy.io import loadmat
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "Results")
OUTDIR = os.path.join(RESULTS, "PelvicShift_Study")

# left biarticular hamstrings (0-based rows)
MUSC = [("semimem_l", 6), ("bifemlh_l", 8)]
# representative speed-matched conditions: token substring -> (label, colour)
CONDS = [
    ("PelvisShift_m02", "anterior (+2 deg ant., tilt -9.2)", "#d62728"),
    ("04-February-2026__12-27-31___Nominal", "Nominal (tilt -7.3)", "#333333"),
    ("PelvisShift_p06", "posterior (+6 deg post., tilt -1.5)", "#1f77b4"),
]


def _get(o, *names):
    for n in names:
        try:
            o = getattr(o, n)
        except AttributeError:
            o = o[n]
    return o


def load(token):
    f = sorted(glob.glob(os.path.join(RESULTS, f"pred_sprinting_data_*{token}*.mat")),
               key=os.path.getmtime)[-1]
    m = loadmat(f, struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    mv = _get(o, "muscleValues")
    tt = float(_get(o, "optVars_nsc", "totalTime"))
    lMt = np.asarray(_get(mv, "lMtilde"), float)
    lM = np.asarray(_get(mv, "lM"), float)
    Fce = np.asarray(_get(mv, "Fce"), float)
    ncol = lMt.shape[1]
    t = np.linspace(0, 100, ncol)                     # % of step
    act = np.asarray(_get(o, "optVars_nsc", "act"), float)
    if act.shape[1] != ncol:
        xa = np.linspace(0, 1, act.shape[1])
        xg = np.linspace(0, 1, ncol)
        act = np.vstack([np.interp(xg, xa, act[r]) for r in range(act.shape[0])])
    tsec = np.linspace(0, tt, ncol)
    return dict(t=t, lMt=lMt, lM=lM, Fce=Fce, act=act, tsec=tsec,
                speed=float(_get(o, "ave_speed")))


def main():
    data = [(lab, col, load(tok)) for tok, lab, col in CONDS]

    nrows = len(MUSC)
    fig, axes = plt.subplots(nrows, 4, figsize=(16, 3.4 * nrows), sharex=True)
    if nrows == 1:
        axes = axes[None, :]

    for i, (mname, row) in enumerate(MUSC):
        for lab, col, d in data:
            t = d["t"]
            lMt = d["lMt"][row]
            dlmdt = np.gradient(d["lM"][row], d["tsec"])      # m/s
            Fce = d["Fce"][row]
            act = d["act"][row]
            axes[i, 0].plot(t, lMt, color=col, lw=1.8, label=lab)
            axes[i, 1].plot(t, dlmdt, color=col, lw=1.8)
            axes[i, 2].plot(t, Fce, color=col, lw=1.8)
            axes[i, 3].plot(t, act, color=col, lw=1.8)
        axes[i, 0].axhline(1.0, color="0.7", ls=":", lw=1)
        axes[i, 1].axhline(0.0, color="0.7", ls=":", lw=1)
        # shade terminal-swing eccentric window (~65-85% of step)
        for j in range(4):
            axes[i, j].axvspan(65, 85, color="orange", alpha=0.08)
        axes[i, 0].set_ylabel(f"{mname}\n\nnorm. fibre len $\\tilde l_M$")
        axes[i, 1].set_ylabel("fibre vel dlM/dt (m/s)\n(+ = lengthening=ECC)")
        axes[i, 2].set_ylabel("contractile force Fce (N)")
        axes[i, 3].set_ylabel("activation")
    for j, ttl in enumerate(["fibre length", "fibre velocity", "contractile force",
                             "activation"]):
        axes[0, j].set_title(ttl)
        axes[-1, j].set_xlabel("% of step")
    axes[0, 0].legend(fontsize=8, loc="upper left")
    fig.suptitle("Figure 5  Hamstring fibre length / velocity / force / activation over the step "
                 "(orange = terminal-swing eccentric window)", fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTDIR, "fig5_force_timeseries.png")
    fig.savefig(out, dpi=150)
    print("wrote", os.path.relpath(out, HERE))
    for lab, col, d in data:
        print(f"  {lab:38s} speed={d['speed']:.3f} m/s")


if __name__ == "__main__":
    main()
