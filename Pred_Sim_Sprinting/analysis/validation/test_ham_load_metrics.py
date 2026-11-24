"""
test_ham_load_metrics.py -- guards the Step-0 audit fixes in ham_load_metrics.py.

Run (base conda python):
  & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" \
      analysis/validation/test_ham_load_metrics.py

Exits non-zero on failure.  Pure asserts, no pytest dependency.
"""
from __future__ import annotations

import datetime as _dt
import os
import platform
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ham_load_metrics as H  # noqa: E402


FAILS = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {name}{('  -> ' + detail) if detail else ''}")
    if not cond:
        FAILS.append(name)


def main():
    p = H.find_latest("Nominal")
    if not p:
        # Graceful INTEGRATION skip: the private source .mat is not in a fresh clone.
        print("SKIP: integration test requires a Nominal result .mat (not shipped with the repo).")
        print("      Needed: Results/pred_sprinting_data_*Nominal.mat  (see docs/DATA_AVAILABILITY.md).")
        print("      Unit-level logic is covered offline by test_unit_metrics.py.")
        sys.exit(0)  # 0 = skipped, NOT a failure (fresh-clone friendly)
    d = H.load_optimum(p)
    t = d["t"]
    print(f"Nominal: {d['name']} N={d['N']} status={d['return_status']}")

    # 1. time grid is the saved non-uniform Radau grid (NOT linspace)
    dt = np.diff(t)
    nonuniform = (dt.max() / dt.min()) > 1.5
    check("timeNodes non-uniform (Radau, not linspace)", nonuniform,
          f"dt_min={dt.min()*1e3:.3f}ms dt_max={dt.max()*1e3:.3f}ms ratio={dt.max()/dt.min():.2f}")
    check("time grid starts at t0>0 (step touchdown)", t[0] > 0.01, f"t0={t[0]:.4f}s")
    check("timeNodes length == muscleValues cols", t.size == d["lMtilde"].shape[1])

    # 2. velocity sign convention: vMtilde>0 == lengthening (== sign of d lM/dt)
    for nm, row in H.HAM_L.items():
        vM_model = d["vMtilde"][row] * d["vMax"][row]
        dlmdt = np.gradient(d["lM"][row], t)
        agree = np.mean(np.sign(vM_model) == np.sign(dlmdt))
        check(f"vMtilde sign == d(lM)/dt sign [{nm}]", agree > 0.97, f"{agree*100:.1f}%")

    # 3. physical fibre velocity (vMtilde*vMax) matches finite-difference d lM/dt
    row = H.HAM_L["bifemlh"]
    vM_model = d["vMtilde"][row] * d["vMax"][row]
    dlmdt = np.gradient(d["lM"][row], t)
    # compare on interior (finite diff is exact-ish where signal is smooth)
    rel = np.abs(vM_model - dlmdt)
    scale = np.percentile(np.abs(dlmdt), 95) + 1e-9
    med_rel = np.median(rel) / scale
    check("physical vel vMtilde*vMax ~ d(lM)/dt", med_rel < 0.15,
          f"median|delta|/p95={med_rel:.3f}")

    # 4. forces are in NEWTONS (order of magnitude), Fpetilde is normalised
    check("Fce in Newtons (max>500)", d["Fce"].max() > 500, f"max={d['Fce'].max():.0f} N")
    check("Fpass in Newtons (max>50)", d["Fpass"].max() > 50, f"max={d['Fpass'].max():.0f} N")
    check("Fpetilde normalised (<=1.5)", d["Fpetilde"].max() <= 1.5, f"max={d['Fpetilde'].max():.3f}")

    # 5. negative fibre work is a plausible ENERGY in joules (per hamstring, per step)
    m = H.condition_metrics(p)
    for nm in H.BIARTIC:
        w = m[f"{nm}_neg_fiber_work_J"]
        check(f"neg_fiber_work plausible J [{nm}]", 1.0 <= w <= 80.0, f"{w:.2f} J")

    # 6. integral parameterisation: on a purely-lengthening span, ∫Fce·vM dt ≈ ∫Fce dlM
    #    (work is parameterisation-independent -> validates non-uniform trapezoid).
    row = H.HAM_L["semimem"]
    vM = d["vMtilde"][row] * d["vMax"][row]
    fce = d["Fce"][row]
    lm = d["lM"][row]
    leng = vM > 0
    # integrate over the largest contiguous lengthening run
    idx = np.where(leng)[0]
    if idx.size > 5:
        # split into contiguous runs, take the longest
        splits = np.split(idx, np.where(np.diff(idx) != 1)[0] + 1)
        run = max(splits, key=len)
        i0, i1 = run[0], run[-1]
        w_time = H._trap(fce[i0:i1 + 1] * vM[i0:i1 + 1], t[i0:i1 + 1])
        w_space = H._trap(fce[i0:i1 + 1], lm[i0:i1 + 1])   # ∫F dlM
        rel = abs(w_time - w_space) / (abs(w_space) + 1e-9)
        check("int Fce*vM dt == int Fce dlM (param-independent)", rel < 0.05,
              f"time={w_time:.2f} space={w_space:.2f} rel={rel:.3f}")

    # 7. legacy uniform-dt eccWork differs from physical (documents the bug impact)
    tt = d["totalTime"]
    t_lin = np.linspace(0, tt, t.size)
    dt_lin = t_lin[1] - t_lin[0]
    row = H.HAM_L["semiten"]
    vMt = d["vMtilde"][row]
    fce = d["Fce"][row]
    legacy = np.sum(fce * np.clip(vMt, 0, None)) * dt_lin          # Fce*vMtilde*dt (NOT J)
    vM = vMt * d["vMax"][row]
    phys = H._trap(np.clip(fce * vM, 0, None), t)                  # J
    diff = abs(phys - legacy) / (abs(phys) + 1e-9)
    check("legacy eccWork != physical J (bug demonstrated)", diff > 0.3,
          f"legacy={legacy:.1f} phys={phys:.2f}J reldiff={diff:.2f}")

    # 8. gait events sane
    ev = H.gait_events(d)
    check("touchdown node is ground contact", ev["td_is_contact"] is True)
    check("contact time plausible 40-120 ms", 0.040 <= ev["contact_s"] <= 0.120,
          f"{ev['contact_s']*1e3:.1f} ms")

    print(f"\nRUN RECORD: python {platform.python_version()} on {platform.platform()} | "
          f"numpy {np.__version__} | engine v{H.__version__}")
    print(f"  data: {d['name']}  N={d['N']}  status={d['return_status']}  "
          f"sha256={H.sha256(p)[:16]}...  at {_dt.datetime.now().isoformat(timespec='seconds')}")
    print(f"{'ALL PASSED' if not FAILS else 'FAILURES: ' + ', '.join(FAILS)}")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
