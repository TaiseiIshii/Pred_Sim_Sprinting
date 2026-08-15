# VALIDATION FINAL REPORT

**Reproducible analysis of pelvic posture, whole-body coordination, and muscle morphology as
determinants of hamstring mechanical-load surrogates at matched sprint performance.**

- Repo `TaiseiIshii/Pred_Sim_Sprinting` · commit `3da75fc` (clean tree) · date 2026-08-15
- Engine: [analysis/validation/ham_load_metrics.py](../analysis/validation/ham_load_metrics.py) v1.0.0 (18/18 tests pass)
- Companion docs: [VALIDATION_MASTER_PLAN.md](VALIDATION_MASTER_PLAN.md) · [METRIC_DEFINITIONS.md](METRIC_DEFINITIONS.md) · [LITERATURE_COMPARISON.md](LITERATURE_COMPARISON.md) · [CLAIM_EVIDENCE_MATRIX.md](CLAIM_EVIDENCE_MATRIX.md)
- All results: `Results/Validation_Master/` (existing study outputs were **not** overwritten)

> Scope: we validate **injury-related mechanical-load surrogates**, not injury probability.
> Claim language follows [CLAIM_EVIDENCE_MATRIX.md](CLAIM_EVIDENCE_MATRIX.md) §C.

---

## 1. Executive summary

1. **Two audit bugs were confirmed and fixed.** Legacy analyses computed metrics on a uniform
   `np.linspace`/scalar-dt grid and multiplied force by the **dimensionless** normalized
   velocity ("eccWork"). The saved `timeNodes` are **non-uniform Radau** (dt 0.32–1.02 ms,
   3.16×) and `Fce/Fpass/FT` are in **Newtons**. The corrected engine differentiates and
   integrates on the true grid and reports physical units; negative fiber work is now a
   genuine **joule** quantity. Fiber-velocity sign was verified (`vMtilde>0 = lengthening`).
2. **Primary result (mesh-robust, speed-matched).** Across a strict, speed-matched 8-condition
   touchdown-pelvic-tilt (TDPT) set (11.75–11.80 m/s, ≤0.51% spread) at **both** N=50 and
   N=100, more anterior touchdown tilt raises biarticular peak `lMtilde` (slopes −0.0037…
   −0.0068/deg, R²≈0.95), peaking in **terminal swing** (87–91% of stride). The mono-articular
   `bifemsh` control is flat → the effect is hip-crossing-specific.
3. **Construct-validity correction.** The "pelvic-tilt direct effect = 0" statement is a
   **tree-rigid artefact**: with the hip angle held, the femur rotates with the pelvis
   (world-transform error −25→0°) so MTU cannot change. A **femur-fixed** counterfactual gives
   ~1 mm/deg biarticular lengthening (0 for `bifemsh`). The optimizer's own solution is
   femur-fixed-like: it tilts the pelvis mainly by **adding hip flexion** (≈−1.07 deg/deg).
4. **Convergence honesty.** A provenance manifest labels every condition with its exact IPOPT
   status. The **PelvicShift** study is only 1/8 strict (two conditions infeasible with speed
   collapse to ~10.5 m/s); the **PelvicTilt** study 1/2. Quantitative claims use strict TDPT.
5. **Robustness caveat.** Peak `lMtilde`, MTU, active and tendon force are mesh-robust (≤4%);
   **peak passive force and negative work are mesh-sensitive** (up to 20% and 34%) — report
   N=100 with the caveat.

---

## 2. Step 0 audit (evidence)

See [VALIDATION_MASTER_PLAN.md](VALIDATION_MASTER_PLAN.md) §Step-0 for the full table. Key
re-verified facts (not assumed): non-uniform `timeNodes`; `muscleValues` on that grid;
`Fce/Fpass/FT` in N; `Fpetilde/Fiso/vMtilde` normalized; `vMtilde>0`=lengthening; physical
fiber velocity `= vMtilde·vMax` (exact); solver status saved as `stats.return_status`.
Audit scripts: [_probe_matfields.py](../analysis/validation/_probe_matfields.py),
[_check_velocity_sign.py](../analysis/validation/_check_velocity_sign.py),
[_phase_diagnostic.py](../analysis/validation/_phase_diagnostic.py).

## 3. Methods corrected (Steps 3, metric engine)

- Time base: reconstructed **reference-limb full stride** = concat(right step, left step);
  seam continuous to |Δ|=0.000 (enforced L↔R mirror symmetry). Terminal-swing peaks appear on
  one continuous limb without bilateral-timing averaging.
- Phase windows: early stance = first 50% of contact; terminal swing = last 25% of swing.
- All formulas, units, normalizations, sign conventions: [METRIC_DEFINITIONS.md](METRIC_DEFINITIONS.md).

## 4. Results by step

### Step 3 — eight-condition muscle analysis (PASS)
[eight_condition_metrics_N50.csv / _N100.csv], [eight_condition_status.csv], figures
`fig_e1…e4`. Biarticular dose-response monotonic and mesh-consistent; `bifemsh` flat;
`leng_at_peak_Fce=True`; speed spread ≤0.51%.

### Step 4 — boundary-condition validity (PASS)
[boundary_condition_static.csv], [fig_b1]. tree-rigid ΔMTU=0 (world-transform proves the
femur co-rotates with the pelvis); femur-fixed +21.6/+26.9/+24.7 mm over 25° for semimem/
semiten/bifemlh, 0 for `bifemsh`; femur & tibia world-rotation error 0.000°. **Adaptive**
(full re-optimized motion) is referenced from Step 3/5. Caveat: whole-MTU ≠ regional tissue
elongation (Mendiguchia 2024).

**Full-motion decomposition** ([boundary_condition_motion.csv], [fig_b2]): for the −8° touchdown
condition, per-frame femur world-rotation error is exactly −8.00° (tree-rigid), [−0.06, 0]°
(femur-fixed), and [−5.81, +1.63]° (adaptive). Terminal-swing biarticular ΔMTU: tree-rigid
0 mm, femur-fixed +7–9 mm, adaptive +8–10 mm → the femur-fixed geometry explains **~85–90%**
of the adaptive lengthening, with a small additional coordination term; `bifemsh` ≈ 0 in all.
This quantitatively refutes both "direct effect = 0" and "100% from re-optimization".

### Step 5 — fair opt-ON/OFF comparison (PASS)
[fair_opt_comparison_N50/100.csv], [fig_s1]. Achieved-tilt x-axis; speed within ±1% (declared
pre-hoc). Manipulation mediated by hip flexion (≈−1.07 deg/deg). The legacy
`analyze_opt_on_off_pelvis.py` opt-OFF is tree-rigid **and** built on non-strict PelvicShift
data → superseded here.

### Step 6 — literature comparison (CONDITIONAL)
[LITERATURE_COMPARISON.md]. Qualitative agreement with Chumanov 2007 / Thelen 2005 (terminal-
swing eccentric peak), Schache 2012 (negative work), Kalkhoven 2023 (fiber vs MTU). Exact
numbers require full-text PDFs (automated retrieval blocked; "to acquire" list provided).

### Step 7 — determinants / mediation (PASS, descriptive)
[determinants.csv], [determinants_correlations.csv]. Pathway (Pearson r, N=8 conditions):
pelvis tilt → hip flexion **r=−0.999** → terminal-swing peak `lMtilde` **r=+0.98** → negative
work **r=+0.90**. Trunk lean (r=+0.89) and pelvic angular velocity (r=−0.94) are covariates
coupled to tilt; peak knee flexion (bounded 118.5°) and swing duration are **non-determinants**.
**Caveat:** tilt and hip flexion are near-collinear (r=−0.999), so their independent effects
cannot be separated from the TDPT set — the Step-4 boundary-condition audit supplies that
geometric decomposition. N = 8 **simulation conditions** (not subjects); descriptive only.

### Step 8 — objective-function evaluation (PASS)
[objective_surrogates.csv], [objective_aggregation.csv], [fig_o1]. All force/length/work
surrogates increase with anterior tilt (R² 0.70–0.96), **except fiber lengthening velocity**
(R²=0.11, ~invariant) — claims must name the surrogate. Across five aggregation schemes
(mean / max / threshold-exceedance / phase-max / smooth-max) the condition ranking is
**robust** (min Spearman ρ = 0.976); a composite is only formed with explicit per-term scales.

### Step 9 — speed–load Pareto (PASS, corrected surrogate)
[pareto_nominal.csv], [pareto_morphology.csv], [fig_p1]. 7 non-dominated points; knee at
w=0.2; one **speed-neutral load-reduction** candidate at w=0.1 under pre-declared thresholds
(surrogate ≤−3%, |Δspeed|≤0.5%). No causal/"safe technique" language.

### Step 10 — morphology dependence (PASS main effects; factorial partially BLOCKED)
[morphology_fascicle.csv], [morphology_strength.csv], [morphology_coverage.csv], [fig_m1].
**Fascicle length** (nominal pelvis): shorter fascicles raise biarticular peak `lMtilde`
strongly (slope −0.0139/%, −30% → lMtilde 1.69, an extreme descending-limb regime).
**Strength**: peak `lMtilde` nearly flat (slope +0.0009/%) but speed and negative work scale
with strength — strength and fiber-length effects are largely **orthogonal**. Morphology ×
objective (HamPareto): the short-fascicle athlete's frontier is far steeper (speed collapses
to 8.4 m/s), but **posture co-shifts** confound it. Coverage: standard morphology complete
(tilt + fascicle + strength sweeps); short/weak morphologies lack a controlled tilt sweep →
**morphology × pelvis factorial incomplete** (§6 BLOCKED). Phenotypes are hypothetical, not
risk categories.

### Step 11 — numerical robustness (PASS with caveat)
[mesh_robustness.csv], [solver_success.csv], [fig_p2]. N=50 vs N=100: peak `lMtilde`/MTU/
active/tendon force robust (≤4%); passive force and negative work sensitive (≤20%, ≤34%).
N=200 and parameter-perturbation runs are BLOCKED (compute).

## 5. Reproduce everything

```powershell
$py = "C:\Users\T11648sTb\AppData\Local\miniconda3\python.exe"
$osim = "C:\Users\T11648sTb\AppData\Local\miniconda3\envs\opencap\python.exe"
cd <repo>\Pred_Sim_Sprinting
& $py analysis\validation\test_ham_load_metrics.py        # tests (18/18)
& $py analysis\validation\build_manifest.py               # manifest
& $py analysis\validation\analyze_eight_conditions.py     # Step 3
& $osim analysis\validation\boundary_condition_audit.py   # Step 4 (OpenSim)
& $py analysis\validation\fair_opt_comparison.py          # Step 5
& $osim analysis\validation\boundary_condition_motion.py  # Step 4 full-motion (OpenSim)
& $py analysis\validation\determinants.py                 # Step 7
& $py analysis\validation\objective_evaluation.py         # Step 8
& $py analysis\validation\pareto_and_robustness.py        # Steps 9 & 11
& $py analysis\validation\morphology_analysis.py          # Step 10
```

## 6. Unresolved issues / BLOCKED (need new simulations or full-text)
1. Morphology × pelvis factorial (short/weak × controlled tilt) — new MATLAB solves.
2. Mesh N=200 confirmation of passive-force / negative-work magnitudes — new solves.
3. Parameter perturbations (lMo, Fmax, tendon slack, contact) — new solves.
4. Strict re-solve of PelvicShift / PelvicTilt sweeps (dual warm-start) — new solves.
5. Exact literature numbers (Schache/Chumanov/Thelen/Mendiguchia/Timmins) — acquire PDFs.
6. Full swing-leg (contralateral) hip/knee/trunk mediation decomposition — analysis extension.

(New MATLAB optimizations are infeasible in-session: R2017b, network license, hours/solve.)

## 7. Thesis result structure (proposed)
1. Framework & face validity (nominal 11.83 m/s; terminal-swing eccentric hamstring loading).
2. **Corrected load-surrogate methodology** (timeNodes, physical units, fiber vs MTU) — a
   methodological contribution in itself.
3. Touchdown-pelvic-tilt dose-response at matched performance (Step 3) with mono-articular
   control (specificity).
4. Boundary-condition decomposition (tree-rigid / femur-fixed / adaptive) — resolves the
   "direct effect" ambiguity (Step 4–5).
5. Speed–load trade-off and candidate motions (Step 9).
6. Hypothetical morphology phenotypes (Step 10, partial) + robustness (Step 11).
7. Limitations, convergence honesty, and experimental hypotheses.

## 8. Conference contributions (three)
1. **Methodological:** unit- and grid-correct fiber-level hamstring load surrogates for
   collocation-based predictive sprint simulations (fixes a common `linspace`/normalized-
   velocity pitfall; open, tested code).
2. **Mechanistic:** the pelvic-tilt "direct effect" on hamstring load is boundary-condition
   dependent, and the optimal solution realizes anterior tilt through hip flexion, lengthening
   the biarticular hamstrings specifically (mono-articular control) at matched top speed.
3. **Applied trade-off:** a reproducible speed–load Pareto with a pre-declared "speed-neutral
   load-reduction" candidate and explicit convergence/mesh-robustness accounting.

## 9. Next experimental intervention candidates (hypotheses to test)
- Manipulate **touchdown hip flexion / pelvic tilt** in athletes and measure hamstring MTU/
  fascicle behavior (ultrasound + motion capture) in terminal swing.
- Compare fascicle-length phenotypes (Timmins-style) for terminal-swing fiber excursion at
  matched speed.
- Test whether coaching toward reduced anterior touchdown tilt lowers terminal-swing biarticular
  fiber stretch without a top-speed penalty (the w=0.1 candidate analogue).
