# Phase C — optimization-on/off interpretation (what each comparison can claim)

Three "conditions" appear in the pelvis↔hamstring-load decomposition. They are **not** three
equally-valid running motions. Two are **geometric kinematic counterfactuals**; only one is a
**dynamically-optimized solution**. This document fixes the interpretation so the thesis never
treats a frozen-coordination counterfactual as an "optimization-off optimal running motion".

Data: `boundary_condition_static.csv` (geometric), `boundary_condition_motion.csv` (per-frame),
`fair_opt_comparison_N50/N100.csv` (adaptive). Analysis_commit `bb0433a`.

## C.1 Definitions
- **(1) tree-rigid kinematic counterfactual** — impose a pelvis-tilt change with **all joint angles
  held**; the femur (a child of the pelvis in the kinematic tree) **co-rotates** with the pelvis.
  MTU length is recomputed **geometrically only**.
- **(2) femur-fixed kinematic counterfactual** — impose the pelvis-tilt change but **hold the femur
  fixed in the world** by adding compensatory hip flexion; recompute MTU length **geometrically only**.
- **(3) adaptive dynamically-optimized solution** — the full predictive simulation re-solved
  (CasADi/IPOPT) at matched speed: satisfies the implicit multibody dynamics, muscle force–length–
  velocity equilibrium, activation dynamics, periodicity, and foot–ground contact constraints.

## C.2 Attribute matrix

| Attribute | (1) tree-rigid | (2) femur-fixed | (3) adaptive |
|---|---|---|---|
| Same top speed? | n/a (no dynamics) | n/a (no dynamics) | **yes** (matched 11.72–11.80 m/s) |
| Same phase timing? | frozen posture (single frame / imposed) | frozen posture | **solved** (own timing, ≤0.51% speed spread) |
| Dynamically feasible? | **no** (geometry only) | **no** (geometry only) | **yes** |
| Muscle force equilibrium enforced? | **no** | **no** | **yes** |
| GRF / contact constraints enforced? | **no** | **no** | **yes** |
| What is fixed | all joint angles | femur world orientation (via hip flexion) | nothing beyond task/bounds |
| What is changed | pelvis tilt only | pelvis tilt + compensatory hip flexion | pelvis touchdown tilt (re-optimized whole body) |
| Femur world-rotation error | grows to **−25°** at 25° tilt (femur co-rotates) | **0°** (held) | in-between, per-frame [−5.81, +1.63]° at −8° |
| Biarticular ΔMTU over 25° tilt | **0 mm** (semimem/semiten/bifemlh) | **+21.6 / +26.9 / +24.7 mm**; BFsh 0 | terminal-swing +8–10 mm at −8° |

## C.3 What each comparison MAY and MAY NOT claim
- **(1) tree-rigid** — MAY claim: "with the whole leg held, pelvis tilt alone changes hamstring MTU
  length by ~0, because the femur co-rotates with the pelvis" (a geometric identity; it explains why
  a naive 'direct effect = 0' statement is an **artefact of the boundary condition**). MAY NOT claim:
  that this is a runnable motion, or that pelvis tilt has "no effect".
- **(2) femur-fixed** — MAY claim: "if the femur is held in the world (i.e., the tilt is realized by
  added hip flexion), the biarticular MTU lengthens ~1 mm/deg while the mono-articular BFsh does not"
  (a geometric decomposition isolating the hip-crossing pathway). MAY NOT claim: dynamic feasibility,
  force equilibrium, or that this is the optimal technique.
- **(3) adaptive** — MAY claim: the dynamically-feasible, matched-speed effect. The optimizer realizes
  anterior touchdown tilt **mainly by adding hip flexion** (peak hip-flexion slope ≈ −1.07 deg/deg),
  i.e. a **femur-fixed-like** coordination; the femur-fixed geometry explains **~85–90%** of the
  adaptive terminal-swing biarticular lengthening, with a small additional coordination term. This is
  the only condition from which a mechanism or intervention hypothesis may be drawn.

## C.4 Required framing (do not write)
- ❌ "fair optimization-on vs optimization-off motion comparison"
- ❌ "a runnable motion that needs no re-optimization"
- ❌ "direct causal effect", "X% is due to re-optimization" (as if the frozen conditions were dynamic)

Use instead: **"we compared a re-optimized solution in the same speed band against
boundary-condition-specific kinematic counterfactuals (tree-rigid, femur-fixed) that isolate the
geometric femur-co-rotation vs added-hip-flexion pathways."**

## C.5 Dynamic-inconsistency of the frozen conditions (defined; optional to compute)
The frozen counterfactuals carry **no** dynamics solution, so no GRF/equilibrium is asserted for
them. To *quantify* their dynamic inconsistency (an optional strengthening), impose each frozen
kinematic trajectory (q, q̇, q̈) into the inverse-dynamics external function
(`ExternalFunctions/Spr_Imp_GRFs_ownCont_V21.dll`) and report the **residual generalized-force /
GRF imbalance** relative to the adaptive solution. Procedure (MATLAB, ~1 short run, no re-optimize):
1. Load the adaptive solution; build the frozen-coordination q(t) (tree-rigid: pelvis+offset, others
   fixed; femur-fixed: add the hip-flexion compensation).
2. Finite-difference q̇, q̈ on the saved non-uniform `timeNodes`.
3. Evaluate the ID function → residual root torques + contact GRF; report ‖residual‖ vs adaptive.
This is documented as future work; it is **not** required for the primary claims, which rest on the
geometric decomposition (C.2/C.3) plus the adaptive solution's own convergence.
