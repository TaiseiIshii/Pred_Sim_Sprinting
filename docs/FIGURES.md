# FIGURES — paper figure set (Phase 6.4)

Final central figures = 5 (+ supplementary A1–A4). Every figure carries: units · mesh (N) · #conditions
· solver criterion · achieved speed · "surrogate, not injury" · caveats. Source PNGs in
`Results/Validation_Master/`. Numbers: [PAPER_RESULTS_FREEZE.md](PAPER_RESULTS_FREEZE.md).

| Fig | File | Content | Source CSV | Mesh | Status |
|---|---|---|---|---|---|
| **1** | `fig_1_formulation.png` | Study formulation + counterfactual (adaptive vs tree-rigid/femur-fixed) | — | — | **ready** |
| **2** | `fig_e1_dose_peakLMtilde.png` (+`fig_A3`) | 8-condition per-muscle length/tension/work dose-response | `eight_condition_metrics_N50/N100.csv` | 50 & 100 | **ready** |
| **3** | `fig_b1_boundary_static.png` + `fig_b2_boundary_motion.png` | tree-rigid / femur-fixed / adaptive decomposition | `boundary_condition_static/motion.csv` | 50/100 | **ready** |
| **4** | `fig_4_pareto_N100.png` | N=100 multi-start speed–load Pareto (w=0.1 Supported, 3/3 inits) | `pareto_N100.csv` | 100 | **ready** |
| **5** | `fig_5_candidate_motion.png` | baseline vs candidate: kinematics + per-muscle length + surrogate change | w0/w0.1 N=100 MATs | 100 | **ready** |
| D1 | `fig_D1_objective_frontier.png` | active-eccentric vs fiber-length objective frontier | `phaseD_objective_frontier.csv` | 50 | ready (exploratory) |
| A1 | `fig_A1_force_doseresponse.png` | tilt vs active/passive/tendon force | `phaseA_long.csv` | 50 & 100 | ready |
| A2 | `fig_A2_TS_vs_ES.png` | terminal-swing vs early-stance per muscle | `phaseA_long.csv` | 100 | ready |
| A3 | `fig_A3_length_tension_work.png` | fiber length / tension / negative work dose-response | `phaseA_long.csv` | 50 & 100 | ready |
| A4 | `fig_A4_mesh_sensitivity.png` | N50 vs N100 mesh sensitivity (passive & neg work flagged) | `phaseA_mesh_sensitivity.csv` | 50 vs 100 | ready |

## Standard captions (fill achieved-speed range from the freeze)
- **Fig 1.** Study formulation. A performance objective plus a biarticular-hamstring overstretch
  penalty is re-optimized (CasADi/IPOPT) at matched speed to a *dynamically feasible adaptive*
  solution; two *geometric kinematic counterfactuals* (tree-rigid, femur-fixed) isolate the
  femur-co-rotation vs added-hip-flexion pathways. Only the adaptive branch is dynamically feasible.
- **Fig 2.** Strict 8-condition touchdown-pelvic-tilt set (speed 11.72–11.80 m/s, `Solve_Succeeded`,
  N=50 & N=100). More anterior touchdown tilt → higher terminal-swing peak normalized fiber length in
  the three biarticular hamstrings; mono-articular `bifemsh` flat. Mechanical-load surrogates.
- **Fig 3.** Boundary-condition decomposition. tree-rigid ΔMTU≈0 (femur co-rotates); femur-fixed
  +21.6/+26.9/+24.7 mm over 25° (BFsh 0); adaptive explained ~85–90% by femur-fixed geometry. Geometry
  for the counterfactuals; adaptive is the matched-speed dynamic solution.
- **Fig 4.** Speed–load Pareto (Nominal, **N=100**). Near-matched-speed candidate w=0.1 confirmed by
  3/3 multi-start inits (−0.34% speed, −5.2% surrogate; all Phase-2.4 gates). Surrogate, not injury.
- **Fig 5.** Baseline (w=0) vs near-matched-speed candidate (w=0.1), **N=100**: the candidate lowers
  terminal-swing peak hip flexion, biarticular peak fiber length, passive force and negative work at
  −0.35% speed. Mechanical-load surrogates, not injury.

## Regeneration
```
python analysis/validation/analyze_eight_conditions.py   # fig 2, e1..e4
python analysis/validation/boundary_condition_audit.py    # fig 3 (b1)
python analysis/validation/boundary_condition_motion.py   # fig 3 (b2)
python analysis/validation/pareto_and_robustness.py       # fig 4 (p1) [add N=100 branch]
python analysis/validation/phaseA_muscle_tension.py       # fig A1..A4
python analysis/validation/phase6_figures.py              # fig 1, fig 5
```
