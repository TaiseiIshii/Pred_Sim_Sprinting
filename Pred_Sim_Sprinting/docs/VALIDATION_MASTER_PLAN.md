# VALIDATION MASTER PLAN

Predictive-simulation study of pelvic posture, whole-body coordination, and muscle
morphology as determinants of hamstring **mechanical-load surrogates** at matched
sprint performance.

- **Repo**: `TaiseiIshii/Pred_Sim_Sprinting`
- **Framework**: Haralabidis et al., single symmetric sprint step, direct collocation
  (CasADi/IPOPT), OpenSim musculoskeletal model. Published optimal top speed 11.85 m/s.
- **Created**: 2026-08-15 · Branch `main` · **analysis_commit `bb0433a`** (clean tree). The
  `manifest.csv` `commit` column = `repo_head_at_runtime 3da75fc` (HEAD at the analysis run); the
  analysis scripts were committed at `bb0433a`. See [PROVENANCE.md](PROVENANCE.md).
- **Scope note**: We validate **injury-related mechanical-load surrogates**, NOT injury
  probability. Language rules in §Claims.

> **STATUS (final):** P0 all PASS; Steps 4, 5, 7, 8, 9 PASS; Step 6 CONDITIONAL (lit full-text
> blocked); Step 10 PASS (main effects) with the morphology×pelvis factorial incomplete (BLOCKED
> cells); Step 11 PASS with mesh caveat. See [VALIDATION_FINAL_REPORT.md](VALIDATION_FINAL_REPORT.md)
> and [CLAIM_EVIDENCE_MATRIX.md](CLAIM_EVIDENCE_MATRIX.md). New MATLAB solves = BLOCKED (in-session).

Load surrogates (per hamstring, per phase): normalized fiber length `lMtilde`, fiber
lengthening velocity, active fiber force `Fce`, passive fiber force `Fpe`, tendon/MTU
force `FT`, negative (eccentric) fiber work; and the peak / integral / time-of-occurrence
of each in **terminal swing** and **early stance**.

---

## Step 0 audit findings (evidence-backed)

| # | Audit hypothesis | Verdict | Evidence |
|---|------------------|---------|----------|
| 0a | Working tree may hold uncommitted user work | **Clean** | `git status` empty; HEAD=origin/main=`3da75fc` |
| 1 | TDPT N=50 has 8 strict-converged conditions | **CONFIRMED** | [pelvic_td_summary.csv](../Results/PelvicTD_Study/pelvic_td_summary.csv): m8..p6, all `Solve_Succeeded`, feasible, speed 11.71–11.78 |
| 2 | Tracked N=100 CSV has only 5 conditions | **CONFIRMED** | [pelvic_td_summary_N100.csv](../Results/PelvicTD_Study/pelvic_td_summary_N100.csv): only m8,m6,m4,m2,p0 (p2,p4,p6 absent) |
| 3 | opt-OFF is tree-rigid (pelvis-only, hip/knee rel. fixed) | **CONFIRMED (Step 4)** | [analyze_opt_on_off_pelvis.py](../analysis/analyze_opt_on_off_pelvis.py) docstring asserts "direct effect = 0"; Step-4 audit shows this is a tree-rigid artefact (femur-fixed = ~1 mm/deg) |
| 4 | Python analysis uses linspace/constant dt not saved Radau `timeNodes` | **CONFIRMED** | [injury_metrics.py](../analysis/injury_metrics.py#L149) `t=np.linspace`; [plot_pelvic_td_figs.py](../analysis/plot_pelvic_td_figs.py#L131) scalar `dt`, `tPeakPct=100*ix/(ncol-1)`. Real `timeNodes` non-uniform dt=[0.32,1.02] ms, starts 0.056 s |
| 5 | eccWork = Fce×normalized vel, not physical J | **CONFIRMED** | `eccWork=sum(Fce*vMtilde)*dt`; legacy vs physical differ up to 2.6× between muscles. `Fce`,`Fpass`,`FT` ARE Newtons |
| 6 | Some regressions include non-strict solver status | **To enforce** | manifest will carry `return_status`; primary analysis strict-only |
| 7 | morphology×pelvis full factorial incomplete | **Likely** | saved morphology = HamFascicle/HamStrength/HamPareto Sh/Wk; confirm coverage in Step 10 |

Extra verified facts: fiber velocity sign convention `vMtilde>0 = lengthening` (100%
sign agreement with d`lM`/dt); **physical fiber velocity = `vMtilde*vMax` [m/s]** exactly;
`Fiso` field is the normalized active force–length multiplier (0–1), not Fmax.

Environment: base Python (numpy/scipy/pandas), OpenSim 4.4 (`opencap` env). **New MATLAB
optimizations are not feasible in-session** (R2017b, network license, hours/solve) →
tasks needing new solves are marked `blocked(compute)` and use existing multi-mesh /
multi-condition saved results for robustness instead.

---

## Task table

Status ∈ pending / running / passed / conditional / failed / blocked.

### P0 — required for the paper's primary claims

#### P0.1 Corrected load-metric engine + tests
- **Hypothesis**: metrics change materially when computed on the true non-uniform
  `timeNodes` with physical units vs the legacy uniform-dt / normalized-velocity code.
- **Inputs**: saved `*.mat` `optimumOutput.muscleValues` (lM, lMtilde, lMTk_lr, Fce,
  Fpass, Fpetilde, FT, vMtilde, vMax), `timeNodes`, `GRFs.R`, `stats`.
- **Change**: new `analysis/validation/ham_load_metrics.py` (single source of truth) +
  `analysis/validation/test_ham_load_metrics.py`.
- **Command**: `python analysis/validation/test_ham_load_metrics.py`
- **Expected**: all tests pass; velocity sign test, unit test (J magnitude 1–60 J/muscle),
  timeNodes-vs-linspace divergence demonstrated, integral parameterization check.
- **Pass**: tests green; documented legacy-vs-corrected delta.
- **Deps**: none. **Est**: build now. **Status**: pending.

#### P0.2 Results manifest
- **Hypothesis**: every analyzed condition is traceable & convergence-labeled.
- **Change**: `analysis/validation/build_manifest.py` → `Results/Validation_Master/manifest.csv`.
- **Columns**: commit, source_file, source_sha256, experiment, condition, morphology,
  objective, mesh_N, solver_status, feasible, requested_pelvis_offset_deg,
  achieved_pelvis_angle_deg, achieved_speed_mps, speed_error_pct, constraint_residual,
  time_grid_type, analysis_script, analysis_version, generated_at.
- **Command**: `python analysis/validation/build_manifest.py`
- **Pass**: manifest lists all study `.mat`; strict/acceptable/failed separated; no mixing.
- **Deps**: P0.1 loader. **Status**: pending.

#### P0.3 Eight-condition muscle tension/stretch re-analysis (TDPT N=50)
- **Hypothesis**: across achieved pelvic tilt (matched speed), biarticular-ham load
  surrogates vary monotonically; bifemsh (mono-articular control) is ~flat.
- **Inputs**: 8 strict N=50 conditions (m8..p6). **Muscles**: semimem, semiten, bifemlh, bifemsh.
- **Metrics**: peak lMtilde, peak MTU length, peak fiber lengthening velocity, peak Fce,
  peak Fpe, peak FT, negative fiber work (J), co-timing of active force & lengthening,
  phase % of each peak, terminal-swing & early-stance aggregates.
- **Command**: `python analysis/validation/analyze_eight_conditions.py`
- **Expected**: `Results/Validation_Master/eight_condition_metrics.csv` (+ figures) with
  units & normalization columns; solver-status table.
- **Pass**: machine-readable CSV; figures; terminal-swing/early-stance split; tests reused.
- **Deps**: P0.1, P0.2. **Status**: pending.

#### P0.4 Metric definitions doc
- **Change**: `docs/METRIC_DEFINITIONS.md` (formula, unit, normalization denominator,
  time grid, phase-window definition, sign convention) for every surrogate.
- **Pass**: every CSV column defined. **Deps**: P0.1/3. **Status**: pending.

### P1 — robustness & novelty

#### P1.1 Boundary-condition validity (Step 4)
- **Hypothesis**: tree-rigid gives ~zero MTU range; femur-fixed produces monotonic
  biarticular change; bifemsh is a non-crossing control; adaptive re-optimization differs.
- **Static audit** (OpenSim exact MTU length, no re-sim): hip 30°, knee 20° (sign-checked),
  anterior tilt 0..25°, muscles SM/ST/BFlh/BFsh → **feasible now** (`opencap`).
- **Full-motion A/B/C** at every phase → A/B analytic + C from saved opt-ON;
  new C solves = `blocked(compute)` (use saved opt-ON as adaptive reference).
- **Command**: `python analysis/validation/boundary_condition_audit.py` (opencap env)
- **Pass**: world-transform errors reported; MTU ranges per condition. **Status**: pending.

#### P1.2 Fair opt-ON/OFF comparison (Step 5)
- **Hypothesis**: differences attributed to pelvis must survive speed-matching on the
  **achieved** pelvis angle axis.
- **Change**: extend/verify `analyze_opt_on_off_pelvis.py`; add speed-matched subset rule
  (documented pre-hoc tolerance), achieved-angle x-axis, solver-status filter.
- **Command**: `python analysis/validation/fair_opt_comparison.py`
- **Pass**: comparison table with achieved speed/tilt/stride/contact/residual/status.
  **Status**: pending.

#### P1.3 Literature comparison (Step 6)
- **Change**: `docs/LITERATURE_COMPARISON.md` table (subject, method, speed, phase, MTU/
  fiber/regional, force def, normalization, result, agreement, mismatch, boundary explan.,
  gap filled). Web-fetch primary sources; inaccessible → list as "to acquire".
- **Status**: pending.

#### P1.4 Determinant / mediation analysis (Step 7)
- **Hypothesis**: pelvis→achieved-motion→hip/knee/trunk coord→fiber len/vel→force→neg work.
- **Change**: `analysis/validation/determinants.py` (correlation vs time-diff vs condition-
  diff vs interaction; N=conditions honesty; no over-fitting).
- **Status**: pending.

### P2 — individualization & extensions

- **P2.1 Objective-function evaluation (Step 8)**: per-surrogate objective scaling/weights,
  aggregation methods (mean/max/threshold/phase/smoothmax) from saved HamPareto sweep. pending.
- **P2.2 Speed–load Pareto (Step 9)**: frontier from saved HamPareto (Nom/Sh/Wk), knee point,
  non-dominated set, "free-lunch" pre-definitions. pending.
- **P2.3 Morphology dependence (Step 10)**: standard/short-fascicle/weak × posterior/base/
  anterior × penalty; report completed vs missing cells; new cells `blocked(compute)`. pending.
- **P2.4 Numerical robustness (Step 11)**: mesh N=50 vs 100 (saved), solver success rate,
  objective variance; N=200 & parameter-perturbation solves `blocked(compute)`. pending.

---

## Deliverables checklist
- [x] docs/VALIDATION_MASTER_PLAN.md (this)
- [x] docs/VALIDATION_FINAL_REPORT.md
- [x] docs/METRIC_DEFINITIONS.md
- [x] docs/LITERATURE_COMPARISON.md
- [x] docs/CLAIM_EVIDENCE_MATRIX.md
- [x] Results/Validation_Master/manifest.csv
- [x] Results/Validation_Master/*.csv (re-analysis)
- [x] Primary figures (fig_e1..e4, fig_b1, fig_s1, fig_p1, fig_p2)
- [x] Re-run commands (in each doc)
- [x] Tests (analysis/validation/test_ham_load_metrics.py, 18/18)
- [x] Unresolved-issues list (final report §6)
- [x] Thesis result structure + 3 conference contributions + next interventions (final report §7-9)

## Claims language (enforced)
Forbidden: "anterior tilt causes hamstring strain", "long fibers therefore injure",
"pelvis direct effect is zero", "100% of load change is re-optimization", "short-fascicle
model is a high-risk athlete", "found a safe running technique", "demonstrated injury
prevention". Use: "under specified boundary/optimization conditions, the load surrogate
changed", "candidate motion reducing surrogate at matched performance", "hypothetical
digital athlete with altered morphology", "mechanistic hypothesis to be experimentally tested".
