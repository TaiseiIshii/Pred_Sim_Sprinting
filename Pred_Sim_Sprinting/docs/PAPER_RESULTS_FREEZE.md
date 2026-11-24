# PAPER RESULTS FREEZE

Single source of truth for the thesis/conference numbers. Every figure/abstract must cite this file.
**Freeze status: FROZEN** — the N=100 Pareto multi-start is confirmed (§5, Supported). Remaining
optional refinements (Phase D composite/passive, Phase E ε-constraint) are exploratory and do not gate
the primary claims.

## 0. Provenance
- simulation_commit `59877aa` (penalty + baseline framework; numerically identical through `bb0433a`;
  combined `_athSh` only used in an exploratory row) · analysis_commit `bb0433a` · documentation_commit
  `bb0433a`+uncommitted-2026-08-15. See [PROVENANCE.md](PROVENANCE.md), `manifest_provenance.csv`,
  `output_hashes.csv`.
- Engine `ham_load_metrics.py` v1.0.0; tests 22/22 unit (offline) + 18/18 integration (Nominal N=100,
  sha256 `c75590b5…`, 2026-08-15). Data map: [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md).
- Language policy: [CLAIM_CALIBRATION.md](CLAIM_CALIBRATION.md). All numbers are **mechanical-load
  surrogates**, not injury outcomes.

## 1. Primary vs excluded conditions
- **Primary (strict `Solve_Succeeded`, speed-matched):** touchdown-pelvic-tilt (TDPT) 8-condition set
  `PelvisTD/PelvisTDwide` at **N=50 and N=100** (offsets −8…+6; achieved TD tilt −15.99…−1.99°; speed
  11.72–11.80 m/s, ≤0.51% spread); Nominal (N=50, N=100); HamPareto_Nom weight sweep (N=50; N=100 in §5).
- **Excluded from primary (kept for transparency):** PelvisShift 7/8 non-strict (2 infeasible, speed
  collapse ~10.5 m/s); PelvisTilt 1/2; PelvisTD_{m4,m6} infeasible (speed ~9.2). Morphology &
  combined-athlete = **exploratory chapter only** (not primary).

## 2. Frozen primary findings

### 2A. Touchdown pelvic tilt → biarticular hamstring fiber length (PRIMARY, mesh-robust)
More anterior touchdown pelvic tilt is associated with **robustly higher terminal-swing peak
normalized fiber length** in all three biarticular hamstrings, at **both** N=50 and N=100:
| muscle | slope (/deg) | R²(N100) | −2°→−16° change | mesh |Δ|N50-N100 | verdict |
|---|---|---|---|---|---|
| semimem | −0.0068 | 0.96 | 0.97→1.07 (+9.3%) | 1.5% | robust increase |
| semiten | −0.0037 | 0.96 | 1.13→1.18 (+4.6%) | 0.8% | robust increase |
| bifemlh | −0.0054 | 0.95 | 1.04→1.11 (+7.0%) | 1.3% | robust increase |
| **bifemsh (control)** | +0.0003 | — | 0.945→0.942 (span 0.4%) | 0.1% | **approximately invariant** |
Peaks occur in **terminal swing** (88–91% of stride), `leng_at_peak_Fce=True`. CSV:
`eight_condition_metrics_N50/N100.csv`, `phaseA_verdicts.csv`. Figure 2 / A1–A3.

### 2B. Per-muscle force & work channels (muscle-specific; some mesh-conditional)
- **Passive force**: direction robust ↑ (all biarticular) but **magnitude mesh-conditional** (6–10.5%).
- **Active force**: semimem ↑ (+6.6%), **semiten ↓ (−3.3%)**, bifemlh ≈ flat. **Tendon force**:
  semimem ↑ (+7.7%), others ≈ flat.
- **Terminal-swing negative active work**: direction robust ↑ (all biarticular) but **strongly
  mesh-conditional** (8.6–33.4%) → report direction, magnitude conditional.
- **Fiber lengthening velocity**: approximately invariant / non-monotonic (biarticular). Full per-muscle
  statements: [PER_MUSCLE_CONCLUSIONS.md](PER_MUSCLE_CONCLUSIONS.md). Figure A2/A4.

### 2C. Boundary-condition decomposition (PRIMARY)
The "pelvic-tilt direct effect = 0" is a **tree-rigid artefact** (femur co-rotates with pelvis,
world-rotation error →−25° over 25°, ΔMTU=0). A **femur-fixed** counterfactual gives biarticular
lengthening +21.6/+26.9/+24.7 mm over 25° (BFsh 0). In the full adaptive motion (−8° touchdown), the
femur-fixed geometry explains **~85–90%** of the adaptive terminal-swing biarticular MTU lengthening;
the optimizer realizes tilt mainly via **added hip flexion** (peak slope ≈ −1.07 deg/deg). Only the
**adaptive** solution is dynamically feasible — see [OPT_ON_OFF_INTERPRETATION.md](OPT_ON_OFF_INTERPRETATION.md).
CSV: `boundary_condition_static.csv`, `boundary_condition_motion.csv`, `fair_opt_comparison_N100.csv`.
Figure 3.

### 2D. Speed–load Pareto (N=50 FROZEN; N=100 PENDING §5)
Nominal weight sweep (N=50, all strict `Solve_Succeeded`), surrogate = biarticular terminal-swing
peak `lMtilde`:
| w | Δspeed % | Δsurrogate % | Δneg-work % | note |
|---|---|---|---|---|
| 0.05 | −0.09 | −2.51 | −1.44 | |
| **0.10** | **−0.24** | **−4.14** | −5.64 | near-matched-speed candidate (≤0.5% tol, ≥3% surrogate) |
| 0.20 | −0.61 | −6.96 | −13.18 | knee point |
7 non-dominated points. CSV `pareto_nominal.csv` (N=50), `pareto_N100.csv` (N=100). Figure 4.
**N=100 multi-start CONFIRMED (§5): w=0.1 −0.34% speed, −5.19% surrogate, 3/3 inits agree, all
Phase-2.4 gates pass → Supported.**

### 2E. Mesh robustness (PRIMARY caveat)
Peak `lMtilde`, MTU length, active & tendon force: mesh-robust (|N50−N100| median ≤1%, max ≤4.1%).
**Peak passive force and negative work: mesh-sensitive** (up to ~20% and ~34%). CSV `mesh_robustness.csv`,
`phaseA_mesh_sensitivity.csv`. Figure A4.

## 3. Exploratory (thesis exploratory chapter / future work; NOT primary)
- **Morphology main effects (nominal pelvis):** shorter hamstring fascicles raise biarticular peak
  `lMtilde` (slope −0.0139/%); strength scaling ≈ flat in length (+0.0009/%) but scales speed/work →
  length and strength effects largely orthogonal. `morphology_fascicle.csv`, `morphology_strength.csv`.
- **Morphology × pelvis / objective:** confounded; the short-fascicle "training path advantage" is an
  **exploratory hypothesis** (CLAIM_CALIBRATION C3), not a conclusion.
- **Tension-based objectives (Phase D, N=50 exploration):** four objectives were implemented and
  optimized. They **dissociate**: the active-eccentric objective cuts active negative work −20% at
  −0.03% speed with almost no fibre-length change, the length objective lowers overstretch + passive
  force (−55%), and the **equal-mix composite w=0.1 lowers ALL surrogates at once** (fibre length
  −4.5%, eccentric power −28.5%, negative work −27.4%, passive −27.6%) at −0.34% speed — the
  strongest all-round near-matched-speed candidate. At high ecc weight the ecc objective trades off
  (passive +14%). See [PHASE_D_E_FINDINGS.md](PHASE_D_E_FINDINGS.md). **N=50; N=100 confirmation of the
  composite/ecc candidates pending.**

## 4. Claim ledger
- **Supported (PASS, mesh-robust, strict):** 2A (biarticular fiber-length dose-response, hip-specific),
  2C (boundary-condition decomposition + hip-flexion mediation), 2E (mesh-robust set), semimem active/
  tendon increase, terminal-swing timing; **2D speed–load Pareto candidate w=0.1 (N=100 multi-start,
  3/3 inits, all Phase-2.4 gates — §5).**
- **Conditional:** 2B passive force & negative work (direction robust, magnitude mesh-conditional);
  literature quantitative match (definition-level only, Phase B);
  Phase D objective dissociation (active-eccentric vs length lever; N=50, N=100 pending).
- **Unverified / out of scope:** injury probability or prevention; individualized intervention;
  morphology×pelvis factorial; `lMo`↔ultrasound and `lMtilde`↔engineering-strain equivalence;
  dynamic feasibility of the frozen counterfactuals.

## 5. N=100 multi-start Pareto — **SUPPORTED** (2026-08-16)
Runner `run_ham_pareto_N100.m`; checkpoint `Results/HamPareto_N100/checkpoint.csv`; verification
`pareto_N100_verify.py` → `pareto_N100.csv`, `fig_4_pareto_N100.png`. All 7 solves strict
`Solve_Succeeded`. Surrogate = biarticular terminal-swing peak `lMtilde`.

| w | init | speed | Δspeed% | TD tilt | Δsurrogate% | iters |
|---|---|---|---|---|---|---|
| 0 | forward (Nominal N100) | 11.83460 | 0.00 | −7.99 | 0.00 | 153 |
| 0.05 | forward | 11.81750 | −0.145 | −6.00 | — | 682 |
| **0.10** | **forward** | **11.79510** | **−0.334** | **−4.32** | **−5.15** | 446 |
| **0.10** | **from-Nominal** | **11.79509** | **−0.334** | **−4.30** | **−5.14** | 553 |
| **0.10** | **backward (from w0.2)** | **11.79286** | **−0.353** | **−4.46** | **−5.28** | 532 |
| 0.20 | forward | 11.74548 | −0.755 | −1.71 | — | 915 |
| 0.20 | from-Nominal | 11.74307 | −0.775 | −1.65 | — | 702 |

**Phase-2.4 gate for w=0.1 (all PASS → Supported):** strict ✓; |Δspeed| −0.34% ≤ 0.5% ✓; surrogate
−5.19% ≤ −3% ✓; non-dominated (forward frontier {0,0.05,0.1,0.2} all non-dominated) ✓; |load N50−N100|
= 1.05 pp ≤ 2 pp ✓; |Δspeed N50−N100| = 0.10 pp ≤ 0.5 pp ✓; **3/3 inits agree** (speed spread 0.019%,
surrogate spread 0.14%) ✓. → **Pareto candidate w=0.1 = SUPPORTED.** Figure 4 = `fig_4_pareto_N100.png`.

## 6. Figure ↔ CSV ↔ claim map
| Fig | Content | CSV | Claim |
|---|---|---|---|
| 1 | formulation & counterfactual | — | scope |
| 2 | 8-cond per-muscle length/tension/work | `eight_condition_metrics_N100.csv` | 2A/2B |
| 3 | tree-rigid/femur-fixed/adaptive | `boundary_condition_*.csv` | 2C |
| 4 | N=100 multi-start Pareto | `pareto_nominal.csv` (+N100 pending) | 2D |
| 5 | baseline vs candidate motion | motion/force CSVs | 2D mechanism |
| A1–A4 | force dose-response / TS-vs-ES / length-tension-work / mesh | `phaseA_*.csv` | 2A/2B/2E |
