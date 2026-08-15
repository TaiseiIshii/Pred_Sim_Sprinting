# Pelvic Tilt → Hamstring Strain — Causal Study v3 (TDPT) — PLAN

**Repo:** Pred_Sim_Sprinting (fork of nicos1993/Pred_Sim_Sprinting; Haralabidis et al., *MSSE* 2025).
**Model:** 3D musculoskeletal sprinter, 37 generalized coordinates, single symmetric
half-stride at top speed, OpenSim + CasADi/IPOPT direct collocation (Radau degree 3),
N = 50 mesh intervals (N = 100 for mesh-independence checks). Objective **maximizes
average sprint speed** (`J = J1 − wJ(12)·Δx/finalTime`, `wJ(12)=10`) plus small
acceleration/activation/derivative regularizers.

## Research question
Does the **anterior–posterior pelvic tilt angle at touchdown** causally change
**hamstring muscle strain-injury risk** (peak normalized fiber length `lMtilde`,
peak passive force `Fpetilde`, eccentric loading) during maximal sprinting — and at
what dose (per degree)?

## Hypothesis
More **anterior** pelvic tilt at touchdown (more negative `pelvis_tilt` in this model)
increases hamstring musculotendon length and eccentric demand at/around touchdown,
raising peak `lMtilde` and passive force — i.e., higher strain-injury risk — while
more **posterior** tilt reduces it. Effects should be largest in the biarticular
hamstrings (semimembranosus, semitendinosus, biceps femoris long head) and the
swing/early-stance limb.

## Method — TDPT ("Touchdown Pelvic Tilt"), the v3 intervention
Mirror the original HTD/IKTD method EXACTLY, but on `pelvis_tilt`:
- Add **ONE scalar equality constraint at the touchdown (initial, k==0) node**:
  `Xk_nsc_ini(1) − (nominalTD_tilt + offsetRad) = 0`  (lbg=ubg=0),
  where index 1 = `pelvis_tilt` (`jointi.pelvis.tilt`), `Xk_nsc_ini` is the
  touchdown-node state (radians, non-scaled), `offsetRad = deg2rad(offset_deg)`.
- `nominalTD_tilt` is extracted **programmatically** from the matching-N converged
  Nominal solution (`optimumOutput.optVars_nsc.q(1,1)`), NOT hardcoded.

### Constrained vs Free (the whole point of v3)
- **CONSTRAINED (only this):** pelvis_tilt at the single touchdown node.
- **FREE / re-optimized:** pelvis_tilt at every OTHER node; hip flexion; lumbar/trunk;
  all other joints, muscle states, GRFs, and stride/step timing. No initial-guess
  compensation, no per-node pin. The body adapts NATURALLY to maximize speed subject
  only to the imposed touchdown tilt.
- **Warm-start:** primal initial guess = the converged Nominal solution, UNMODIFIED.
- **Solver:** SAME strict IPOPT as Nominal/HTD/IKTD (tol 1e-5, max_iter 50000,
  adaptive μ). No v2 hacks (no max_iter=700, no acceptable-level early stop).

This is the cleanest single-intervention causal design: one minimal manipulation +
full re-optimization isolates the pelvis-tilt → response pathway.

## Extracted reference (programmatic, logged)
- **N=50 nominalTD = −7.4626°** (from `pred_sprinting_data_04-February-2026__12-27-31___Nominal.mat`,
  Solve_Succeeded, speed 11.777 m/s).
- **N=100 nominalTD = −7.9870°** (from `pred_sprinting_data_10-April-2026__16-29-40___Nominal.mat`,
  Solve_Succeeded, speed 11.835 m/s).
- Note: negative `pelvis_tilt` = anterior tilt in this model.

## Conditions (offsets in deg; m = anterior, p = posterior)
| name | offset | N=50 target TD tilt | feasible vs ±15° band |
|------|-------:|--------------------:|:---------------------:|
| `_PelvisTD_m6` | −6 | −13.46° | yes |
| `_PelvisTD_m4` | −4 | −11.46° | yes |
| `_PelvisTD_m2` | −2 |  −9.46° | yes |
| `_PelvisTD_p0` |  0 |  −7.46° | yes (≈Nominal) |
| `_PelvisTD_p2` | +2 |  −5.46° | yes |
| `_PelvisTD_p4` | +4 |  −3.46° | yes |
| `_PelvisTD_p6` | +6 |  −1.46° | yes |

Targets are within the existing initial multibody-matching band (±deg2rad(15) about
the experimental initial pose), so all are feasible w.r.t. it.

## Mesh strategy
1. **Pilot first (de-risk):** run `_PelvisTD_m6` and `_PelvisTD_p6` at N=50. Verify
   the realized touchdown tilt = nominalTD ± 6° exactly; IPOPT status; and that other
   joints (touchdown hip flexion, lumbar) changed because they re-optimized.
2. If the pilot validates → **full N=50 sweep** (7 conditions).
3. **Re-run key conditions at N=100** (p0, m6, p6, and the most-affected) for
   mesh-independence.

## Metrics (emergent unless noted)
- **Manipulation check (imposed):** realized touchdown pelvis_tilt vs nominalTD+offset.
- **Performance:** achieved top speed, stride/half-stride time, step length, peak
  vertical GRF (+ propulsive impulse if extractable).
- **Kinematics:** emergent stride-mean pelvis_tilt, touchdown hip flexion (L/R).
- **Hamstring strain (per muscle, L & R + bilateral mean):** peak `lMtilde`, peak
  `Fpetilde` (passive force), peak eccentric loading `max(0,vMtilde)·FMvtilde`,
  composite `lMtilde·max(0,vMtilde)·(Fce/Fiso)`, eccentric impulse, time-of-peak
  (% stride), MTU length/excursion, L/R asymmetry. Muscles: semimembranosus (`semimem`),
  semitendinosus (`semiten`), biceps femoris long head (`bifemlh`), biceps femoris
  short head (`bifemsh`). Rows in 92-row `muscleValues`: L = 7,8,9,10; R = 53,54,55,56.
- **Dose-response:** linear regression of each metric vs offset → slope (per deg) + R².

## v3 vs v2 comparison
Compare the TDPT dose-response (hamstring strain, speed) to v2 (`PelvisShift`,
per-node pin + guess compensation). Assess whether removing the per-node pin and
guess compensation changes the conclusions, and comment on naturalness / causal
cleanliness.

## Outputs (do NOT overwrite v2)
`Results/PelvicTD_Study/`: per-condition `.mat` (in `Results/`), `pelvic_td_summary.csv`,
`pelvic_td_slopes.csv`, figures (Japanese labels via matplotlib + Yu Gothic), and
`REPORT.md`.

## Status log
- [done] Implemented gated v3 code (parse + warm-start/nominalTD + touchdown equality),
  checkSimulationType passthrough, runner, bat, probe.
- [done] Probe: extracted nominalTD (N50 −7.4626°, N100 −7.9870°); MATLAB headless OK.
- [next] Launch pilot m6, p6 at N=50; verify; then full sweep; then N=100; analyze; report.
