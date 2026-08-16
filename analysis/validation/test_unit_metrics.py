"""
test_unit_metrics.py -- Phase 1.2 UNIT tests (no external .mat required).

Guards the Step-0 audit-fix logic with small synthetic fixtures so a *fresh clone* can verify the
maths offline. Complements test_ham_load_metrics.py (INTEGRATION, needs the private .mat data).

Covered (task Phase 1.2 list):
  1. non-uniform time integration (_trap)          5. phase-window calculation (_stride_window)
  2. fiber-velocity sign convention                6. reference-limb stride reconstruction
  3. physical velocity conversion (vMtilde*vMax)   7. aggregation methods (fit / spearman / smooth-max)
  4. negative fiber-work units (Joules)            8. solver-status filtering (strict select)

Run (base conda python), exits non-zero on failure, no pytest dependency:
  & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" analysis/validation/test_unit_metrics.py
"""
from __future__ import annotations

import datetime as _dt
import os
import platform
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ham_load_metrics as H          # noqa: E402  (pure import, no file access)
import objective_evaluation as OE     # noqa: E402  (pure import, no file access)

FAILS = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  -> ' + detail) if detail else ''}")
    if not cond:
        FAILS.append(name)


# --- synthetic non-uniform (Radau-like) grid over a step [t0, tE] --------------
def nonuniform_grid(n=40, t0=0.056, T=0.21):
    u = np.sort(np.random.RandomState(0).rand(n))          # non-uniform in [0,1]
    u = (u - u.min()) / (u.max() - u.min())
    return t0 + T * u


def test_trap():
    # 1a. exactness for a linear integrand on ANY grid (trapezoid is exact for lines).
    x = np.array([0.0, 0.01, 0.5, 0.97, 1.0])              # highly non-uniform
    y = 3.0 * x + 2.0
    exact = 1.5 * 1.0 ** 2 + 2.0 * 1.0                     # ∫0^1 (3x+2) = 3.5
    check("_trap exact on linear / non-uniform grid", abs(H._trap(y, x) - exact) < 1e-12,
          f"got {H._trap(y, x):.12f} exp {exact}")
    # 1b. a naive uniform-dt assumption (dt=x[1]-x[0]) would be badly wrong -> proves grid-awareness.
    dt0 = x[1] - x[0]
    naive = float(np.sum(0.5 * (y[1:] + y[:-1])) * dt0)
    check("_trap != naive-uniform-dt (grid-aware)", abs(naive - exact) > 0.5,
          f"naive {naive:.3f} vs exact {exact}")
    # 1c. constant integrand -> (b-a) regardless of node spacing.
    x2 = nonuniform_grid()
    check("_trap const == span", abs(H._trap(np.full_like(x2, 2.0), x2) - 2.0 * (x2[-1] - x2[0])) < 1e-12)


def _stride_dict(t, lMtilde, lM, lMT, Fce, Fpass, FT, vM, Fpetilde):
    return {"t": t, "T": float((t[-1] - t[0]) / 2.0), "lMtilde": lMtilde, "lM": lM, "lMT": lMT,
            "Fce": Fce, "Fpass": Fpass, "FT": FT, "vM": vM, "Fpetilde": Fpetilde}


def test_velocity_sign_and_work_units():
    # Build a stride where fibre velocity is +0.5 m/s (lengthening) for the FIRST half and
    # -0.5 m/s (shortening) for the second half, active force constant 200 N.
    t = np.linspace(0.0, 0.20, 101)                        # (uniform ok here; _trap handles both)
    half = t.size // 2
    vM = np.where(np.arange(t.size) < half, 0.5, -0.5)
    fce = np.full(t.size, 200.0)
    ones = np.ones(t.size)
    s = _stride_dict(t, lMtilde=1.0 + 0.05 * np.sin(t), lM=0.10 * ones, lMT=0.30 * ones,
                     Fce=fce, Fpass=50.0 * ones, FT=1000.0 * ones, vM=vM, Fpetilde=0.2 * ones)
    m = H.stride_metrics(s)
    # 2. only the lengthening (vM>0) portion contributes to negative (eccentric) work.
    dt_leng = t[half - 1] - t[0]                           # duration of vM>0 span
    expected_J = 200.0 * 0.5 * dt_leng                     # power(W)*time(s) = 200N*0.5m/s*t
    check("neg_fiber_work counts only vM>0 (lengthening)", abs(m["neg_fiber_work_J"] - expected_J) < 0.2,
          f"got {m['neg_fiber_work_J']:.3f} J exp {expected_J:.3f} J")
    # 4. units: active eccentric power peak = F*v = 200*0.5 = 100 W (a genuine Watt, not F*vMtilde).
    check("peak_act_ecc_power == F*v [W]", abs(m["peak_act_ecc_power_W"] - 100.0) < 1e-6,
          f"{m['peak_act_ecc_power_W']:.3f} W")
    check("peak_leng_vel is physical m/s (=0.5)", abs(m["peak_leng_vel_mps"] - 0.5) < 1e-9)


def test_physical_velocity_conversion():
    # 3. reference_stride must set vM = vMtilde * vMax on the true grid (both R & L rows).
    ncol = 20
    d = {"t": nonuniform_grid(ncol), "totalTime": 0.21}
    z = np.zeros((92, ncol))
    for f in ("lMtilde", "lM", "lMT", "Fce", "Fpass", "FT", "Fpetilde"):
        d[f] = z.copy()
    vMtilde = np.zeros((92, ncol)); vMax = np.zeros((92, ncol))
    rR, rL = H.HAM_R["bifemlh"], H.HAM_L["bifemlh"]
    vMtilde[rR] = 0.3; vMtilde[rL] = 0.3
    vMax[rR] = 8.0; vMax[rL] = 8.0
    d["vMtilde"] = vMtilde; d["vMax"] = vMax
    s = H.reference_stride(d, "bifemlh")
    check("reference_stride vM == vMtilde*vMax", np.allclose(s["vM"], 0.3 * 8.0),
          f"got {np.unique(np.round(s['vM'],6))} exp {0.3*8.0}")


def test_reference_stride_reconstruction():
    # 6. stride = concat(right step, left step); length doubles; time runs [0,T]∪[T,2T]; seam
    #    continuous when the left step's first sample equals the right step's last (mirror symmetry).
    ncol = 15
    t = nonuniform_grid(ncol)
    d = {"t": t, "totalTime": float(t[-1] - t[0])}
    z = np.zeros((92, ncol))
    for f in ("lM", "lMT", "Fce", "Fpass", "FT", "Fpetilde", "vMtilde", "vMax"):
        d[f] = z.copy()
    d["vMax"][:] = 1.0
    lMt = np.zeros((92, ncol))
    rR, rL = H.HAM_R["semimem"], H.HAM_L["semimem"]
    ramp = np.linspace(1.0, 1.1, ncol)
    lMt[rR] = ramp                       # right step ramps 1.0 -> 1.1
    lMt[rL] = ramp[::-1]                 # left step ramps 1.1 -> 1.0  (so seam R[-1]==L[0]==1.1)
    d["lMtilde"] = lMt
    s = H.reference_stride(d, "semimem")
    check("stride length == 2*ncol", s["lMtilde"].size == 2 * ncol, f"{s['lMtilde'].size}")
    check("stride time spans [0, 2T]", abs(s["t"][-1] - 2.0 * (t[-1] - t[0])) < 1e-9)
    seam = abs(s["lMtilde"][ncol - 1] - s["lMtilde"][ncol])
    check("seam continuous under mirror symmetry", seam < 1e-9, f"|Δ|={seam:.2e}")


def test_phase_windows():
    # 5. _stride_window returns the peak WITHIN a boolean mask only.
    ncol = 30
    t = np.linspace(0.0, 0.4, ncol)
    s = {"t": t, "lMtilde": np.ones(ncol), "Fce": np.full(ncol, 100.0),
         "Fpass": np.full(ncol, 20.0), "FT": np.full(ncol, 500.0), "vM": np.zeros(ncol)}
    s["lMtilde"][-3] = 1.4               # spike in the terminal-swing (late) window only
    es_mask = t <= 0.10                  # early-stance window (first 25%)
    ts_mask = t >= 0.30                  # terminal-swing window (last 25%)
    es = H._stride_window(s, es_mask)
    ts = H._stride_window(s, ts_mask)
    check("TS window captures late spike", abs(ts["peak_lMtilde"] - 1.4) < 1e-9, f"{ts['peak_lMtilde']}")
    check("ES window excludes late spike", abs(es["peak_lMtilde"] - 1.0) < 1e-9, f"{es['peak_lMtilde']}")
    check("empty mask -> nan (no false peak)", np.isnan(H._stride_window(s, None)["peak_lMtilde"]))


def test_aggregation_methods():
    # 7. reusable pure fns: linear fit (slope/R^2) and Spearman rank agreement.
    x = np.array([-8.0, -4.0, 0.0, 4.0, 8.0])
    s, r2 = OE.fit(x, 2.0 * x + 1.0)
    check("fit slope exact", abs(s - 2.0) < 1e-9, f"slope={s:.6f}")
    check("fit R2==1 on a line", abs(r2 - 1.0) < 1e-9, f"R2={r2:.6f}")
    check("spearman monotonic == +1", abs(OE.spearman(x, np.exp(x)) - 1.0) < 1e-9)
    check("spearman anti-monotonic == -1", abs(OE.spearman(x, -x) + 1.0) < 1e-9)
    # smooth-max (log-sum-exp) is an upper bound on the true max and >= the mean.
    v = np.array([1.02, 1.10, 0.98])
    beta = 20.0
    lse = (1.0 / beta) * np.log(np.exp(beta * v).sum())
    check("smooth_max >= max", lse >= v.max() - 1e-9, f"lse={lse:.4f} max={v.max():.4f}")
    check("threshold_exceedance = sum(clip(v-1,0))",
          abs(np.clip(v - 1.0, 0, None).sum() - (0.02 + 0.10)) < 1e-9)


def test_solver_status_filtering():
    # 8. select() keeps ONLY strict rows, dedups by requested offset (lowest residual), sorts.
    rows = [
        {"experiment": "PelvicTD", "strict": "True", "mesh_N": "100", "requested_pelvis_offset_deg": "-4",
         "constraint_residual": "5e-8", "achieved_td_tilt_deg": "-11.9", "source_file": "A.mat"},
        {"experiment": "PelvicTD", "strict": "True", "mesh_N": "100", "requested_pelvis_offset_deg": "-4",
         "constraint_residual": "9e-8", "achieved_td_tilt_deg": "-11.9", "source_file": "B.mat"},   # dup, worse
        {"experiment": "PelvicTD", "strict": "False", "mesh_N": "100", "requested_pelvis_offset_deg": "-2",
         "constraint_residual": "1e-3", "achieved_td_tilt_deg": "-9.9", "source_file": "C.mat"},    # non-strict
        {"experiment": "PelvicTD", "strict": "True", "mesh_N": "100", "requested_pelvis_offset_deg": "0",
         "constraint_residual": "2e-8", "achieved_td_tilt_deg": "-7.9", "source_file": "D.mat"},
        {"experiment": "PelvicShift", "strict": "True", "mesh_N": "100", "requested_pelvis_offset_deg": "0",
         "constraint_residual": "1e-8", "achieved_td_tilt_deg": "-7.4", "source_file": "E.mat"},     # wrong experiment
    ]
    sel = OE.select(rows, mesh_N=100)
    files = [r["source_file"] for r in sel]
    check("select drops non-strict + other experiments", "C.mat" not in files and "E.mat" not in files,
          f"{files}")
    check("select dedups offset by lowest residual (A over B)", "A.mat" in files and "B.mat" not in files)
    check("select sorted by requested offset", files == ["A.mat", "D.mat"], f"{files}")


def main():
    print("UNIT tests (synthetic fixtures, no .mat) -- ham_load_metrics / objective_evaluation")
    for fn in (test_trap, test_velocity_sign_and_work_units, test_physical_velocity_conversion,
               test_reference_stride_reconstruction, test_phase_windows, test_aggregation_methods,
               test_solver_status_filtering):
        fn()
    print(f"\nRUN RECORD: python {platform.python_version()} on {platform.platform()} | "
          f"numpy {np.__version__} | engine v{H.__version__} | "
          f"{_dt.datetime.now().isoformat(timespec='seconds')}")
    print("ALL PASSED" if not FAILS else "FAILURES: " + ", ".join(FAILS))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
