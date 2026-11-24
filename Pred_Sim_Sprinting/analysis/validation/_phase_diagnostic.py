"""Diagnostic: gait structure, L/R symmetry, seam continuity, per-leg peak timing.

Confirms the phase framework used in ham_load_metrics.py:
  * t0 = right touchdown (GRFs.R high at start), tE = left touchdown (step end),
  * L<->R mirror symmetry with half-stride offset,
  * a single reference-limb full stride = concat(R over [0,T], L over [0,T]).

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" \
       analysis/validation/_phase_diagnostic.py
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ham_load_metrics as H


def run(token="Nominal"):
    p = H.find_latest(token)
    d = H.load_optimum(p)
    t = d["t"]
    T = t[-1] - t[0]
    ev = H.gait_events(d)
    print(f"=== {d['name']} N={d['N']} ===")
    print(f"step T={T*1e3:.1f} ms  right contact={ev['contact_s']*1e3:.1f} ms "
          f"({100*ev['contact_s']/T:.0f}% of step)  toeoff@{100*(t[ev['to']]-t[0])/T:.0f}%")

    # per-leg peak-lMtilde timing (true-time % of step) for each hamstring
    print(f"{'muscle':9s} {'R_pkLMt':>8s} {'R_t%':>5s} | {'L_pkLMt':>8s} {'L_t%':>5s} "
          f"| {'LRpkΔ%':>6s}")
    for nm in H.HAM:
        for side, rows in (("R", H.HAM_R), ("L", H.HAM_L)):
            r = rows[nm]
            lMt = d["lMtilde"][r]
            ip = int(np.argmax(lMt))
            tp = 100 * (t[ip] - t[0]) / T
            if side == "R":
                Rpk, Rt = lMt.max(), tp
            else:
                Lpk, Lt = lMt.max(), tp
        print(f"{nm:9s} {Rpk:8.3f} {Rt:5.0f} | {Lpk:8.3f} {Lt:5.0f} "
              f"| {100*(Rpk-Lpk)/Rpk:6.2f}")

    # seam continuity: does R(end) ~ L(start) for pelvis-independent muscle states?
    # (mirror symmetry => right-limb state at tE equals left-limb state at t0)
    print("\nSeam check (reference-limb full stride = R[0,T] then L[0,T]):")
    for nm in H.HAM:
        rR, rL = H.HAM_R[nm], H.HAM_L[nm]
        lMtR = d["lMtilde"][rR]
        lMtL = d["lMtilde"][rL]
        seam = abs(lMtR[-1] - lMtL[0])
        # build reference full stride and find global peak timing over 2T
        full = np.concatenate([lMtR, lMtL])
        tfull = np.concatenate([t - t[0], (t - t[0]) + T])
        ip = int(np.argmax(full))
        print(f"  {nm:9s} seam|Δ lMtilde|={seam:.4f}  full-stride peak={full.max():.3f} "
              f"@{100*tfull[ip]/(2*T):.0f}% of stride "
              f"({'stance/early-swing' if tfull[ip] < T else 'late-swing/terminal'})")


if __name__ == "__main__":
    for tok in (sys.argv[1:] or ["Nominal", "PelvisTDwide_m8"]):
        run(tok)
        print()
