# METRIC DEFINITIONS

Authoritative definitions for every hamstring mechanical-load surrogate produced by the
validation pipeline. Source of truth: [analysis/validation/ham_load_metrics.py](../analysis/validation/ham_load_metrics.py)
(`__version__ = 1.0.0`). All surrogates are computed **from saved optimization output only**
(no re-simulation).

## Provenance of the raw quantities

`optimumOutput.muscleValues` stores, per muscle row (92 rows) and per time node:

| field | symbol | unit | notes (empirically verified) |
|-------|--------|------|------------------------------|
| `lM` | fiber length | m | physical fiber length |
| `lMtilde` | `lM/lMo` | – | normalized fiber length (lMo = optimal fiber length) |
| `lMTk_lr` | MTU length | m | muscle–tendon unit length |
| `Fce` | active fiber force | **N** | contractile-element force (median≈170, max≈7000 N) |
| `Fpass` | passive fiber force | **N** | passive element force (0–842 N) |
| `FT` | tendon force | **N** | tendon/MTU force |
| `Fpetilde` | passive force / Fmax | – | normalized passive force (0–~0.6) |
| `vMtilde` | `vM/vMax` | – | normalized fiber velocity; **`>0 = lengthening`** (verified) |
| `vMax` | max shortening velocity | m/s | per-muscle constant (semimem 1.042) |
| `Fiso` | active force–length multiplier | – | **NOT** Fmax (0–1) |

Time grid: `optimumOutput.timeNodes` — the saved **Radau collocation grid**, which is
**non-uniform** (dt ∈ [0.32, 1.02] ms at N=100, a 3.16× range) and starts at the step
touchdown (t₀ ≈ 0.056 s, not 0). `muscleValues` columns = `len(timeNodes)` = 3·N+1.
**All differentiation and integration uses this grid** — never `np.linspace`/scalar dt.

Physical fiber velocity is taken as the exact model quantity
$v_M = \tilde v_M \cdot v_\text{max}$ [m/s] (verified to equal $d\,l_M/dt$ on the real grid
to machine precision), avoiding finite-difference grid sensitivity. `vMtilde > 0` denotes
lengthening (eccentric), so eccentric = "active fiber force positive **and** fiber lengthening".

Hamstring rows (0-based): left semimem/semiten/bifemlh/bifemsh = 6/7/8/9; right = 52/53/54/55.
Biarticular (hip+knee) = semimem, semiten, bifemlh. `bifemsh` crosses only the knee and is
used as a **mono-articular control** for pelvis/hip-mediated effects.

## Reference-limb full stride (primary time base)

The simulation is one symmetric **step** (half stride) over `[t₀, t_E]`, with `t₀ = right
touchdown` and `t_E = left touchdown` (verified: right vertical GRF high at t₀). Because the
model enforces left↔right **mirror symmetry with a half-stride offset**, one full stride of
the reference (right) limb is reconstructed by concatenating the right-leg step `[0,T]` with
the left-leg step mapped to `[T,2T]`. The seam is continuous (|Δ lMtilde| < 1e-3, verified),
giving a single continuous limb signal spanning stance → mid-swing → **terminal swing** →
next touchdown. Primary per-muscle metrics are computed on this stride, so terminal-swing
peaks are represented without bilateral-timing-averaging artefacts. (Bilateral-mean *peak
magnitude* and per-leg peaks are retained as cross-checks: `<m>_R/L/bimean_peak_lMtilde`.)

## Phase windows

- **Early stance (ES)**: first `ES_FRAC = 50%` of ground contact (`[0, 0.5·contact]`), the
  stance loading window. Contact detected from right vertical GRF > 5% BW.
- **Terminal swing (TS)**: last `TS_SWING_FRAC = 25%` of the swing phase before touchdown
  (`[2T − 0.25·(2T − contact), 2T]`), the pre-touchdown eccentric window. Captures the
  observed biarticular peak at ~87–91% of stride.

BW = 72.17 kg × 9.80665 = 707.75 N.

## Surrogate metrics (per muscle, on the reconstructed stride)

| CSV column | definition | unit |
|------------|------------|------|
| `<m>_peak_lMtilde` | max normalized fiber length over the stride | – |
| `<m>_min_lMtilde` | min normalized fiber length | – |
| `<m>_peak_MTU_len_m` | max MTU length `lMTk_lr` | m |
| `<m>_MTU_excursion_m` | max − min MTU length | m |
| `<m>_peak_leng_vel_mps` | max of positive fiber velocity `max(v_M,0)` | m/s |
| `<m>_peak_leng_rate_hz` | `max(v_M,0)/lMo` peak (normalized lengthening rate) | 1/s |
| `<m>_peak_active_force_N` | max `Fce` | N |
| `<m>_peak_passive_force_N` | max `Fpass` | N |
| `<m>_peak_tendon_force_N` | max `FT` | N |
| `<m>_peak_Fpetilde` | max normalized passive force | – |
| `<m>_peak_act_ecc_power_W` | max active eccentric power `max(Fce·v_M, 0)` | W |
| `<m>_neg_fiber_work_J` | **∫ max(Fce·v_M, 0) dt** over the stride (trapezoid on timeNodes) | J |
| `<m>_neg_fiber_work_tot_J` | ∫ max((Fce+Fpass)·v_M, 0) dt | J |
| `<m>_lMo_m` | optimal fiber length = median(lM/lMtilde) | m |
| `<m>_tPeak_lMtilde_pct` | time of peak lMtilde as % of stride (0–100) | % stride |
| `<m>_tPeak_Fce_pct` | time of peak active force as % of stride | % stride |
| `<m>_leng_at_peak_Fce` | is the fiber lengthening (v_M>0) when Fce peaks? | bool |
| `<m>_cotiming_lMt_Fce_pct` | |t(peak lMtilde) − t(peak Fce)| as % of stride | % stride |

**Negative fiber work** is the energy absorbed by the (active) contractile element while it
is forcibly lengthened — a genuine mechanical energy in joules, because `Fce` [N] × `v_M`
[m/s] is watts and the integral is over real time [s]. This replaces the legacy `eccWork =
Σ(Fce·vMtilde)·dt`, which multiplies force by the **dimensionless** normalized velocity and
uses a uniform scalar dt, so it is neither in joules nor grid-consistent and distorts
between-muscle comparison (e.g. semiten legacy 5.6 vs physical 14.7 J).

## Phase-windowed metrics

`<m>_ES_<x>` and `<m>_TS_<x>` are the same peak/integral surrogates restricted to the early
stance / terminal swing windows: `peak_lMtilde`, `peak_active_force_N`,
`peak_passive_force_N`, `peak_tendon_force_N`, `peak_leng_vel_mps`, `neg_fiber_work_J`.

## Convergence & performance columns (manifest + condition tables)

| column | meaning |
|--------|---------|
| `solver_status` | exact IPOPT `return_status` (e.g. `Solve_Succeeded`) |
| `strict` | `solver_status == Solve_Succeeded` |
| `feasible` | IPOPT `success` flag |
| `constraint_residual` | final primal infeasibility `inf_pr` (when logged) |
| `achieved_td_tilt_deg` | pelvis_tilt at touchdown (deg; the manipulated variable) |
| `achieved_pelvis_angle_deg` | stride-mean pelvis_tilt (deg; emergent) |
| `achieved_speed_mps` | `ave_speed` |
| `speed_error_pct` | vs mesh-matched Nominal (performance-match check) |

Sign: `pelvis_tilt` is **negative for anterior** tilt (nominal ≈ −7.5°); "more anterior" =
more negative. Primary analyses use **strict** conditions only; `Solved_To_Acceptable_Level`
is reserved for sensitivity, and `Maximum_Iterations_Exceeded`/`Infeasible_Problem_Detected`
are excluded from quantitative claims.
