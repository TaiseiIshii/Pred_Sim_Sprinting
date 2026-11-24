# Pelvic Tilt & Hamstring Strain Injury Risk — Research Plan

## Research question
How does varying the anterior–posterior pelvic tilt angle (`pelvis_tilt`) affect
hamstring muscle strain injury risk during maximal predictive-simulation sprinting?

## Hypothesis
Greater **anterior** pelvic tilt lengthens the biarticular hamstrings at their
proximal (ischial) origin, increasing peak normalized fiber length (`lMtilde`),
peak eccentric lengthening velocity (`vMtilde`), and peak passive fiber force
(`Fpetilde`) during the late-swing / early-stance phase. We therefore predict a
**monotonic increase in hamstring strain-injury risk metrics with increasing
anterior pelvic tilt**, with the long-head biarticular muscles (semimembranosus,
semitendinosus, biceps femoris long head) most affected and the short head
(biceps femoris short head, monoarticular) least affected.

## Model / framework
- OpenSim full-body Hamner musculoskeletal model with contact, solved as a
  CasADi + IPOPT direct-collocation optimal-control problem in MATLAB R2017b.
- Cost function **maximizes average sprint speed** (`wJ(12)=10` on speed) with
  small regularization on accelerations, activations and their derivatives.
- Half-stride periodic formulation; `pelvis_tilt` is coordinate index 1.
- Baseline (`_Nominal`, verified from existing converged result):
  - average speed **11.835 m/s**, half-stride time 0.209 s, `Solve_Succeeded`.
  - self-selected `pelvis_tilt`: mean **−7.46°**, range [−9.92°, −3.28°]
    (≈6.6° peak-to-peak). In this model **negative = anterior** tilt
    (sprinters run anteriorly tilted, consistent with the data).

## Manipulation (reversible, condition-switched)
Activated only when `simulation_type` contains `PelvisTilt`; all other
conditions (`_Nominal`, `_HTD_*`, `_IKTD_*`) are byte-for-byte unchanged.

Inside `createScaledBounds`, after the existing pelvis/trunk symmetrification,
the `pelvis_tilt` **position** bounds are replaced by a shifted window
`[center − 4°, center + 4°]` centred on the imposed target. `createGuess` seeds
the `pelvis_tilt` initial guess at the window centre. The half-window (4°)
comfortably contains the ~6.6° natural oscillation while pinning the mean near
the target. Velocity/acceleration bounds and every other coordinate are left at
their baseline (symmetrified) values.

Naming: `_PelvisTilt_m13` → centre −13°, `_PelvisTilt_p00` → 0°
(m = minus/anterior, p = plus/posterior).

## Conditions (mesh strategy)
N=50 sweep first (cold start, ~10–15 min each):

| simulation_type    | imposed mean tilt | window        | description        |
|--------------------|-------------------|---------------|--------------------|
| `_PelvisTilt_p00`  |   0°              | [−4°, +4°]    | neutral            |
| `_PelvisTilt_m04`  |  −4°              | [−8°, 0°]     | mild anterior      |
| `_PelvisTilt_m07`  |  −7°              | [−11°, −3°]   | near nominal       |
| `_PelvisTilt_m10`  | −10°              | [−14°, −6°]   | more anterior      |
| `_PelvisTilt_m13`  | −13°              | [−17°, −9°]   | strong anterior    |

Baseline `_Nominal` (already converged, mean −7.46°) is used as an external
reference. After the N=50 sweep, the baseline-like (`m07`) and highest-risk
condition are refined at N=100 if time permits.

## Hamstring muscles & indices (verified)
`muscleValues` arrays are 92×nodes, ordered **left side rows 1–46, right side
rows 47–92**; within a side the order follows `muscleNames`. Hamstrings:
- Left:  semimem **7**, semiten **8**, bifemlh **9**, bifemsh **10**
- Right: semimem **53**, semiten **54**, bifemlh **55**, bifemsh **56**

## Strain-injury metrics (per hamstring, per condition)
From `optimumOutput.muscleValues` over the half stride:
1. **Peak `lMtilde`** — peak normalized fiber length (primary strain proxy; >1.2–1.5 = high strain).
2. **Peak eccentric loading** — peak of `max(0, vMtilde) .* FMvtilde` (active force during lengthening).
3. **Composite risk index** — peak of `lMtilde .* max(0, vMtilde) .* Fcetilde`.
4. **Peak `Fpetilde`** — peak normalized passive fiber force.
5. **Time-of-peak** of `lMtilde` as % of half-stride.
6. **L/R asymmetry** — |L − R| / mean for peak `lMtilde`.

Sanity checks: peak vertical GRF ~1–3× BW; `lMtilde` physiologically plausible
(≲1.5); `ave_speed` realistic (~10–12 m/s); solver `return_status`.

## Workflow / progress log
- [x] Verified MATLAB R2017b + CasADi + DLLs available (headless `-wait -r`).
- [x] Read main script bounds/symmetrification, wJ, saveOptimumFiles, calcObjFuncTerms; confirmed indices.
- [x] Probed `_Nominal` result → confirmed structures, ordering, baseline numbers.
- [x] Implemented reversible `simulation_type`-keyed pelvis_tilt override + guess seeding + optional arg + checkSimulationType passthrough.
- [x] Created sweep runner `MainFunctions/run_pelvic_tilt_sweep.m`.
- [x] Validate one N=50 condition (`_PelvisTilt_m10`): convergence + tilt shift + hamstring metrics present.
- [ ] Run full N=50 sweep (remaining `_p00`, `_m04`, `_m07`, `_m13` in progress after runner path fix).
- [x] Cross-condition analysis script + figures prepared (`analysis/analyze_pelvic_tilt.m`), pending remaining results.
- [ ] Refine at N=100 if feasible.
- [ ] Write REPORT.md.

## Notes / trial-and-error record
(Appended as the study proceeds.)

- Baseline _Nominal reference used for warm-start metrics is N=100 (11.835 m/s).
  N=50 cold nominals also exist & converged (e.g. 04-Feb-2026, 11.777 m/s).
- COLD start for a forced pelvis-tilt window does NOT converge: from the raw
  experimental guess, IPOPT primal infeasibility sticks at ~5e3 with exploding
  dual infeasibility and tiny steps (seen to iter ~110). Flatten-vs-shift of the
  guess did not help — the experimental guess is simply too far from a feasible
  point in the constrained subspace.
- FIX: warm-start each _PelvisTilt_* condition from the converged N=50 Nominal
  (dynamically consistent) and shift its pelvis_tilt to the target centre.
  Result: iter-0 inf_pr ~1.7e3 and steadily decreasing (1690->540 in ~23 iters)
  with healthy step sizes -> converges. Warm-start source auto-selected to match
  Options.N (avoids dimension mismatch with the N=100 nominal).
- OPERATIONAL: `cmd /c matlab -wait` grandchildren survive terminal kills ->
  orphaned MATLABs accumulate and steal CPU. Always `Stop-Process matlab` to
  clean up. Diary buffers heavily in -nodesktop (flushes in large chunks).
- KEY FIX (convergence): primal-only warm-start still plateaued (inf_pr ~500,
  inf_du exploding ~1e6) for any window width (4 or 6 deg) -> the DUAL variables
  were the problem. Passing the Nominal's saved multipliers lam_x_opt/lam_g_opt
  as IPOPT lam_x0/lam_g0 (with warm_start_init_point=yes, mu_strategy=monotone,
  mu_init=1e-4, small warm_start bound/mult pushes) gives healthy MONOTONE
  convergence: inf_du starts ~1.3e3 (not 1e6) and both infeasibilities decrease
  together (inf_pr 1270->267 over ~66 iters, accelerating). This is THE fix.
- Final config: half-window 6 deg, dual warm-start, ptStudy max_iter=3000 with
  acceptable_tol=1e-3 as a safety net. Baseline runs untouched.
- Validation success: `_PelvisTilt_m10` converged at N=50 from the N=50 Nominal
  dual warm-start in 720 IPOPT iterations / 31.2 min, `Solve_Succeeded`, final
  unscaled constraint violation 2.9e-5 and average speed 11.775 m/s. Saved file:
  `Results/pred_sprinting_data_05-June-2026__11-00-52___PelvisTilt_m10.mat`.
- Runner fix: calling `run_pelvic_tilt_sweep` directly bypassed the launcher path
  setup and caused `control_extrapolation` path errors. The runner now adds all
  required project folders itself, so direct headless calls are safe.