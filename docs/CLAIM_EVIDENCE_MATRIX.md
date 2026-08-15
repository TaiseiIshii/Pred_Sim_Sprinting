# CLAIM–EVIDENCE MATRIX

Maps every paper-relevant statement to its concrete evidence (script, output file, numbers,
solver status, mesh robustness) and reframes the **forbidden** claims into defensible ones.
All numeric evidence is from **strict (`Solve_Succeeded`)** conditions unless noted.
Commit `3da75fc`; engine `ham_load_metrics.py` v1.0.0.

Legend: **PASS** = supported by strict, mesh-robust evidence · **CONDITIONAL** = supported
with a stated caveat · **BLOCKED** = needs new simulations/data.

## A. Supported claims (usable in the thesis/paper)

| # | Claim | Evidence | Status |
|---|-------|----------|--------|
| A1 | In this model, at matched sprint speed (11.75–11.80 m/s, spread ≤0.51%), more anterior **touchdown pelvic tilt** is associated with greater biarticular-hamstring peak normalized fiber length. | [eight_condition_metrics_N100.csv](../Results/Validation_Master/eight_condition_metrics_N100.csv); slopes semimem −0.0068, semiten −0.0037, bifemlh −0.0054 /deg, R²=0.95–0.96; [fig_e1](../Results/Validation_Master/fig_e1_dose_peakLMtilde.png) | **PASS** (N=50 & N=100) |
| A2 | The effect is **specific to hip-crossing muscles**: the mono-articular `bifemsh` shows no dose-response (slope +0.0003/deg, span 0.003). | same CSV; [fig_e1](../Results/Validation_Master/fig_e1_dose_peakLMtilde.png) | **PASS** |
| A3 | The biarticular hamstrings reach peak fiber length in **terminal swing** (87–91% of the reconstructed stride) and are **lengthening while active** at peak force (`leng_at_peak_Fce=True`). | [ham_load_metrics.py](../analysis/validation/ham_load_metrics.py); `_phase_diagnostic.py`; sanity output | **PASS** |
| A4 | The apparent "**zero direct effect** of pelvic tilt" is an **artefact of the tree-rigid boundary condition**; under a femur-fixed counterfactual, anterior tilt lengthens the biarticular MTU ≈1 mm/deg while `bifemsh` is unchanged. | [boundary_condition_static.csv](../Results/Validation_Master/boundary_condition_static.csv); world-transform errors: tree-rigid femur rot −25→0°, femur-fixed 0.000°; Δ semimem +21.6, semiten +26.9, bifemlh +24.7 mm/25°; [fig_b1](../Results/Validation_Master/fig_b1_boundary_static.png) | **PASS** |
| A4b | In the **full sprint motion** (−8° touchdown offset), the geometric femur-fixed counterfactual explains **~85–90%** of the adaptive terminal-swing biarticular MTU lengthening; neither "0" (tree-rigid) nor "100% re-optimization" holds. Terminal-swing ΔMTU: tree-rigid 0 mm, femur-fixed +7.1/+8.7/+8.1 mm, adaptive +8.2/+10.3/+9.1 mm (semimem/semiten/bifemlh); `bifemsh` +0.0/+0.0/+0.9 mm. | [boundary_condition_motion.csv](../Results/Validation_Master/boundary_condition_motion.csv); per-frame femur rot err A=−8.00°, B=[−0.06,0]°, C=[−5.81,+1.63]°; [fig_b2](../Results/Validation_Master/fig_b2_boundary_motion.png) | **PASS** |
| A5 | The optimizer realizes the touchdown-tilt manipulation primarily through **increased hip flexion** (peak hip-flexion slope ≈ −1.07 deg per deg tilt), i.e., a femur-fixed-like coordination. | [fair_opt_comparison_N100.csv](../Results/Validation_Master/fair_opt_comparison_N100.csv); [fig_s1](../Results/Validation_Master/fig_s1_fair_comparison.png) | **PASS** |
| A6 | A biarticular-overstretch penalty yields **candidate motions that reduce the load surrogate at near-matched performance** (w=0.1: surrogate −4.1%, speed −0.24% within the 0.5% noise floor); the knee point is w=0.2 (−7.0% surrogate, −0.61% speed). | [pareto_nominal.csv](../Results/Validation_Master/pareto_nominal.csv); [fig_p1](../Results/Validation_Master/fig_p1_pareto.png) | **PASS** |
| A7 | Peak `lMtilde`, MTU length, active force, and tendon force are **mesh-robust** (N=50 vs N=100 |Δ| median ≤1.0%, max ≤4.1%). | [mesh_robustness.csv](../Results/Validation_Master/mesh_robustness.csv); [fig_p2](../Results/Validation_Master/fig_p2_mesh_robustness.png) | **PASS** |
| A8 | Negative fiber work is a genuine energy in **joules** (≈15–37 J/muscle/stride) computed on the true non-uniform `timeNodes`; the legacy `Σ Fce·vMtilde·dt` is not in joules and distorts between-muscle comparison. | [test_ham_load_metrics.py](../analysis/validation/test_ham_load_metrics.py) (18/18 pass); `_check_velocity_sign.py` | **PASS** |
| A9 | The anterior-tilt → higher-load direction is consistent across **fiber length, active force, passive force, and negative work**, and the condition ranking is **robust to the aggregation scheme** (min Spearman ρ=0.976). | [objective_surrogates.csv](../Results/Validation_Master/objective_surrogates.csv); [objective_aggregation.csv](../Results/Validation_Master/objective_aggregation.csv); [fig_o1](../Results/Validation_Master/fig_o1_objective.png) | **PASS** |
| A10 | Shorter hamstring fascicles raise the biarticular normalized peak fiber length (slope −0.0139/%, e.g. −30% → lMtilde 1.69), whereas strength scaling leaves fiber length nearly unchanged (+0.0009/%) but scales speed/work — length and strength effects are largely orthogonal. | [morphology_fascicle.csv](../Results/Validation_Master/morphology_fascicle.csv); [morphology_strength.csv](../Results/Validation_Master/morphology_strength.csv); [fig_m1](../Results/Validation_Master/fig_m1_morphology.png) | **PASS** (main effects, nominal pelvis) |
| A11 | Pathway pelvis tilt → hip flexion → terminal-swing fiber stretch → negative work is supported (r=−0.999, +0.98, +0.90). | [determinants_correlations.csv](../Results/Validation_Master/determinants_correlations.csv) | **PASS** (descriptive, N=8) |

## B. Conditional claims (state the caveat)

| # | Claim | Caveat & evidence | Status |
|---|-------|-------------------|--------|
| B1 | Anterior touchdown tilt increases biarticular **negative fiber work** and **peak passive force**. | Direction consistent, but these two metrics are **mesh-sensitive** (N50–N100 |Δ| up to 34% and 20%); report N=100 values and the sensitivity. [mesh_robustness.csv](../Results/Validation_Master/mesh_robustness.csv) | **CONDITIONAL** |
| B2 | Short-fascicle / weak-strength "digital athletes" trade performance for load differently. | Only 3 penalty points each; their **achieved pelvic tilt also shifts** (Sh reaches +9–10° posterior), confounding morphology with posture. [pareto_morphology.csv](../Results/Validation_Master/pareto_morphology.csv) | **CONDITIONAL** |
| B3 | Femur-fixed geometric lengthening (~1 mm/deg) approximates the constrained-posture literature (Mendiguchia 2024). | **Do not equate** OpenSim whole-MTU length with regional tissue elongation. [LITERATURE_COMPARISON.md](LITERATURE_COMPARISON.md) | **CONDITIONAL** |
| B4 | Anterior tilt increases the hamstring load surrogate. | Holds for length/force/work but **fiber lengthening velocity is ~invariant** (R²=0.11); name the surrogate. [objective_surrogates.csv](../Results/Validation_Master/objective_surrogates.csv) | **CONDITIONAL** |
| B5 | Hip flexion (not pelvic tilt per se) drives the terminal-swing stretch. | Tilt and hip flexion are **near-collinear** (r=−0.999) in the TDPT set — independent effects are not separable from this data; use the Step-4 geometric decomposition. [determinants_correlations.csv](../Results/Validation_Master/determinants_correlations.csv) | **CONDITIONAL** |

## C. Forbidden claims → defensible reframing

| Forbidden statement | Why it fails | Defensible replacement |
|---------------------|--------------|------------------------|
| "Anterior pelvic tilt causes hamstring strain injury." | Surrogates ≠ injury probability; no epidemiology here. | "Under these boundary/optimization conditions, anterior touchdown tilt increased hamstring mechanical-load surrogates." |
| "Long fibers therefore get injured." | No damage model. | "Altered fascicle length changed the load surrogates of the hypothetical digital athlete." |
| "The pelvis direct effect is zero." | True only under tree-rigid; femur-fixed gives ~1 mm/deg (A4). | "The direct geometric effect is boundary-condition dependent: ~0 (tree-rigid) vs ~1 mm/deg (femur-fixed)." |
| "100% of the load change is from re-optimization." | Depends on the counterfactual choice. | "Under tree-rigid decomposition the change is coordination-mediated; a femur-fixed counterfactual attributes part to geometry." |
| "The short-fascicle model is a high-risk athlete." | Morphology ≠ risk category. | "A hypothetical morphology phenotype with shorter fascicles." |
| "We found a safe running technique." | No safety/injury outcome. | "A candidate motion that reduces the load surrogate at near-matched performance, to be tested experimentally." |
| "We demonstrated injury prevention." | Out of scope. | "We generated mechanistic hypotheses and intervention candidates for experimental validation." |

## D. Requires new work (BLOCKED on compute / data)

| # | Item | Why blocked |
|---|------|-------------|
| D1 | Full **morphology × pelvis** factorial (short/weak athletes × controlled touchdown-tilt sweep). | Only standard morphology has a strict 8-point tilt sweep; short/weak have penalty sweeps only → **new MATLAB solves** (R2017b, network license) needed. |
| D2 | Mesh **N=200** confirmation of the passive-force / negative-work magnitudes. | New solves. |
| D3 | Full-motion tree-rigid vs femur-fixed vs adaptive at **every phase** with parameter perturbations (lMo, Fmax, tendon slack, contact). | New solves / model rebuilds. |
| D4 | Exact quantitative literature reconciliation (Schache, Chumanov, Thelen numbers). | Full-text PDFs blocked this session; see [LITERATURE_COMPARISON.md](LITERATURE_COMPARISON.md) "to acquire". |
| D5 | PelvicShift / PelvicTilt sweeps as strict evidence. | Only 1/8 and 1/2 strict respectively → re-solve with dual warm-start. |
