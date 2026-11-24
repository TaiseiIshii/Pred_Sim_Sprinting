"""
audit_boundary.py -- INDEPENDENT Phase-5 check of the adaptive (C) MTU dose using the
model's OWN saved MTU length (muscleValues.lMTk_lr), with PROPER normalized-phase (0-100%)
correspondence between the nominal and the re-optimized m8 step (they have different step
durations, so absolute-time nearest-neighbour -- as used in boundary_condition_motion.py --
mismatches phase near the end of the step).

Left hamstrings (rows 6,7,8,9 = semimem_l, semiten_l, bifemlh_l, bifemsh_l) because the LEFT
limb is the one approaching touchdown at tE (terminal swing). Reports, per muscle:
  * terminal-swing peak MTU of nominal vs m8, and their difference (mm)
  * the same computed with ABSOLUTE-TIME correspondence, to quantify the phase-mismatch bug
Writes Results/Independent_Audit_20260819/boundary_phase_corrected.csv.
This is OpenSim-free (uses the saved MTU); the A/B geometric counterfactuals still need OpenSim.
"""
from __future__ import annotations
import csv
import os
import numpy as np
from scipy.io import loadmat

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, ".."))
NOM = "pred_sprinting_data_10-April-2026__16-29-40___Nominal.mat"
M8 = "pred_sprinting_data_24-June-2026__23-17-49___PelvisTDwide_m8.mat"
HAM_L = {"semimem_l": 6, "semiten_l": 7, "bifemlh_l": 8, "bifemsh_l": 9}
BIARTIC = ["semimem_l", "semiten_l", "bifemlh_l"]
TS_FRAC = 0.25   # terminal swing = last 25% of the step


def _g(o, *n):
    for k in n:
        o = getattr(o, k) if hasattr(o, k) else o[k]
    return o


def load(fn):
    m = loadmat(os.path.join(RESULTS, fn), struct_as_record=False, squeeze_me=True)
    o = m["optimumOutput"]
    t = np.asarray(_g(o, "timeNodes"), float).ravel()
    lMT = np.asarray(_g(o, "muscleValues", "lMTk_lr"), float)   # (92,ncol) metres
    td = float(np.degrees(np.asarray(_g(o, "optVars_nsc", "q"), float)[0, 0]))
    return dict(t=t, lMT=lMT, td=td, phase=(t - t[0]) / (t[-1] - t[0]))


def main():
    nom = load(NOM)
    m8 = load(M8)
    delta = m8["td"] - nom["td"]
    print(f"nominal TD={nom['td']:.3f}  m8 TD={m8['td']:.3f}  delta={delta:+.3f} deg")
    print(f"nominal step dur={ (nom['t'][-1]-nom['t'][0])*1000:.2f}ms  "
          f"m8 step dur={(m8['t'][-1]-m8['t'][0])*1000:.2f}ms  "
          f"(diff {((m8['t'][-1]-m8['t'][0])-(nom['t'][-1]-nom['t'][0]))*1000:+.2f}ms)")

    ph = np.linspace(0.0, 1.0, 501)          # common normalized-phase grid
    ts = ph >= (1.0 - TS_FRAC)               # terminal-swing window

    rows = []
    print(f"\n{'muscle':10s} {'peakMTU_nom':>11s} {'peakMTU_m8':>10s} "
          f"{'dPeak_phaseNorm':>15s} {'dPeak_absTime':>13s} {'peak@phase%':>11s}")
    for nm, r in HAM_L.items():
        mtu_nom = np.interp(ph, nom["phase"], nom["lMT"][r]) * 1000.0   # mm on common phase
        mtu_m8 = np.interp(ph, m8["phase"], m8["lMT"][r]) * 1000.0
        # terminal-swing peak of each, phase-normalized
        pk_nom = mtu_nom[ts].max()
        pk_m8 = mtu_m8[ts].max()
        d_ts_peak = pk_m8 - pk_nom
        # difference at the phase where the m8 MTU peaks (terminal swing)
        ip = np.argmax(mtu_m8 * ts)
        d_at_peak = mtu_m8[ip] - mtu_nom[ip]
        peak_phase = 100.0 * ph[ip]
        # ABSOLUTE-TIME correspondence (the flagged bug): for each m8 node, nearest nominal
        # node by |t|, then dMTU; take terminal-swing peak on the m8 step timeline
        mtu_m8_nodes = m8["lMT"][r] * 1000.0
        d_abs = np.array([mtu_m8_nodes[j] -
                          nom["lMT"][r][int(np.argmin(np.abs(nom["t"] - m8["t"][j])))] * 1000.0
                          for j in range(m8["t"].size)])
        m8_ts_nodes = (m8["phase"] >= (1.0 - TS_FRAC))
        d_abs_ts_peak = d_abs[m8_ts_nodes].max()
        print(f"{nm:10s} {pk_nom:11.2f} {pk_m8:10.2f} {d_ts_peak:15.3f} "
              f"{d_abs_ts_peak:13.3f} {peak_phase:11.1f}")
        rows.append(dict(muscle=nm, is_biarticular=nm in BIARTIC,
                         delta_pelvis_deg=round(delta, 3),
                         peakMTU_nominal_mm=round(pk_nom, 3), peakMTU_m8_mm=round(pk_m8, 3),
                         dPeakMTU_phaseNorm_mm=round(d_ts_peak, 3),
                         dMTU_at_m8peak_phaseNorm_mm=round(d_at_peak, 3),
                         dPeakMTU_absTime_mm=round(d_abs_ts_peak, 3),
                         peak_phase_pct=round(peak_phase, 2)))

    out = os.path.join(HERE, "boundary_phase_corrected.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nExpected (phase-normalized adaptive peak diff): semimem 7.666, semiten 9.727, bifemlh 8.435 mm")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
