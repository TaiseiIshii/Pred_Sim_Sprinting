# FINAL STUDY PLAN — thesis + conference freeze

**Scope:** finalize pelvic-posture / hamstring-load / speed–load-Pareto results to a state usable
in an MSc thesis and a conference presentation. This plan integrates the original Phases 0–6 with
the added Phases A–F (muscle-tension confirmation, quantitative literature comparison,
optimization-on/off interpretation, tension-based objectives, matched-speed objective comparison,
per-muscle conclusions).

- Repo: `TaiseiIshii/Pred_Sim_Sprinting`
- HEAD at plan time: `bb0433af9e6b22c7403f7d9bef4d654a656a460e` (`main`, clean tree)
- Prior results generated under: `3da75fc` (same commit *message* as `bb0433a`; `bb0433a` only adds
  a MATLAB R2017b encoding fix to `main_pred_sim_sprinting.m` that is **not** on the simulation
  numerical path — so `3da75fc` outputs are numerically valid; see Phase 1.1 for provenance rules).
- Plan date: 2026-08-15

> **Central proposition (evaluated, not "proved").** When pelvic posture is manipulated under
> near-matched sprint performance, how do boundary-condition and whole-body-coordination changes
> alter hamstring **mechanical-load surrogates** in a muscle-driven predictive simulation, and can we
> find candidate motions that lower those surrogates with minimal performance loss?
> The evaluated quantity is **injury-related mechanical-load surrogates**, not injury probability.

---

## 0. Environment & state (verified Phase 0)

| Item | Finding |
|---|---|
| Branch / HEAD / origin | `main` = `origin/main` = `bb0433af…`, working tree clean (0 dirty/untracked) |
| Old commit in docs | `3da75fc` (manifest, VALIDATION_FINAL_REPORT) — pre-encoding-fix, same message |
| Source MATs (local) | **present**: 78 files, 384 MB, ~4.9 MB each (fresh clone does **not** have them) |
| HamPareto meshes | **all N=50** (Nom w0000…w3200; Sh/Wk subsets). Nominal N=100 exists (= w0 baseline) |
| TDPT 8-condition | strict set present at **N=50 and N=100** (`eight_condition_metrics_N50/N100.csv`) |
| Python | 3.13.9 (base conda): numpy 2.3.5, scipy 1.16.3, pandas 2.3.3, matplotlib 3.10.7 |
| MATLAB | R2017b `C:\Program Files\MATLAB\R2017b\bin\matlab.exe` (network license, slow start, ASCII-only `.m`) |
| OpenSim | conda `opencap` (OSim 4.4), `opensim42` |
| Metrics engine | `analysis/validation/ham_load_metrics.py` v1.0.0 (pure fns + MAT loaders) |
| Tests | `analysis/validation/test_ham_load_metrics.py` — 8 checks, all currently integration |
| Running jobs | none |

**Compute reality.** N=100 multi-start Pareto (Phase 2) and new tension-based objectives (Phases
D/E) are new MATLAB optimizations (each ≈0.5–1.5 h at N=100, plus MATLAB's >10 min cold start).
The full matrix is a multi-day effort. This plan therefore separates **doc/analysis tasks
executable now on existing data** from **new-compute tasks** that are built, launched with
checkpointing, and documented with a resume prompt.

---

## Legend
Status ∈ {TODO, WIP, DONE, BLOCKED, DEFERRED}. Each task: hypothesis · inputs · command · expected
output · pass criteria · est. time · deps · status · actual result · claim impact.

---

## Phase 1 — Reproducibility completion

### 1.1 Commit & provenance correction
- **Hypothesis:** results are traceable to the exact simulation/analysis/doc commits + data hashes.
- **Inputs:** `manifest.csv`, `VALIDATION_FINAL_REPORT.md`, `VALIDATION_MASTER_PLAN.md`,
  `CLAIM_EVIDENCE_MATRIX.md`, figure metadata.
- **Command:** edit docs; add `simulation_commit / analysis_commit / documentation_commit /
  source_sha256 / output_sha256 / generated_at` columns/fields.
- **Expected output:** provenance block distinguishing the three commits; note `3da75fc≡bb0433a`
  on the sim path.
- **Pass criteria:** no doc claims a result was produced by code it was not; every CSV/figure maps
  to a commit + input hash.
- **Est. time:** 30–40 min. **Deps:** none. **Status:** DONE.
- **Actual result:** `PROVENANCE.md` created (three-commit model + equivalence proof: `git diff
  3da75fc..bb0433a` touches only `main_pred_sim_sprinting.m` L1350 `±`→`+/-`, off the numerical
  path). `manifest.csv` gains `simulation_commit,analysis_commit,documentation_commit` columns.
- **Claim impact:** enables reproducibility PASS; keeps honest that outputs predate `bb0433a`.

### 1.2 Test separation (unit vs integration)
- **Hypothesis:** the audit-fix logic is testable from a fresh clone without the private MATs.
- **Inputs:** `ham_load_metrics.py` pure fns (`_trap`, `stride_metrics`, `_stride_window`,
  `reference_stride`, `gait_events`), objective aggregation.
- **Command:** add `test_unit_metrics.py` (synthetic fixtures) + make integration test skip cleanly.
- **Expected output:** unit tests pass offline; integration tests SKIP (exit 0) with a data-needed
  message when no MAT.
- **Pass criteria:** fresh clone → unit PASS, integration SKIP (no crash).
- **Est. time:** 60 min. **Deps:** none. **Status:** DONE.
- **Actual result:** see Phase 1 progress below.
- **Claim impact:** underpins the "18/18" honesty rule (record env + data version + datetime).

### 1.3 Fresh-clone verification
- **Hypothesis:** a clean checkout runs unit tests, resolves doc links, reads CSVs/figures.
- **Command:** clone to temp; run unit tests; check integration skip; verify README commands.
- **Pass criteria:** unit PASS, integration SKIP, no broken links in shipped docs.
- **Est. time:** 30 min. **Deps:** 1.2. **Status:** DONE (see Phase 1 progress).

### 1.4 Data-availability preparation
- **Command:** create `DATA_AVAILABILITY.md` (required MATs, size, SHA256, condition, releasable?,
  regeneration command, Zenodo/Release/lab-storage candidates, DOI slot).
- **Pass criteria:** third party can trace every output CSV to a hashed MAT even if MATs stay private.
- **Est. time:** 30 min. **Deps:** 1.1. **Status:** DONE.

---

## Phase 2 — Pareto primary-candidate final numerical verification (NEW COMPUTE)

- **Hypothesis:** `w=0.1` is a strict, near-matched-speed, non-dominated load-reduction candidate
  that reproduces at N=100 across ≥3 initializations and forward/backward continuation.
- **Inputs:** `main_pred_sim_sprinting.m` ham-penalty path (wJ(13)); N=50 solutions as warm starts.
- **Command:** `MainFunctions/run_ham_pareto_N100.m` (new) with per-condition checkpointing;
  weights {0, 0.05, 0.10, 0.20}; inits {mesh-matched nominal, N50-interpolated, prev-weight
  continuation fwd, next-weight continuation bwd}.
- **Expected output:** `Results/HamPareto_N100/…mat` + `pareto_nominal_N100.csv` with achieved
  speed, Δspeed, achieved TD tilt, objective, load-penalty term, biarticular TS peak lMtilde,
  active/passive/tendon force, lengthening velocity, negative work, solver status, residual, iters,
  init method, mesh N, runtime.
- **Pass criteria for conference-primary `w=0.1`:** strict `Solve_Succeeded`; |Δspeed|≤0.5%;
  surrogate ≤−3%; non-dominated; |load-reduction N50−N100|≤2 pp; |Δspeed N50−N100|≤0.5 pp; ≥2/3
  inits reach same solution basin; inter-solution speed & load spread ≲1% (or explained).
- **If failed:** do not discard — downgrade to *exploratory / mesh-sensitive / init-sensitive* and
  pick the most reproducible Pareto point.
- **Est. time:** ~12–24 h wall (12–24 solves). **Deps:** MATLAB. **Status:** WIP (infra + launch).
- **Actual result:** _to fill from runs; resume prompt in `docs/RESUME_PROMPT.md`._
- **Claim impact:** gates "Pareto candidate = Supported/Conditional/Rejected".

### 2.5 ε-constraint confirmation
- **Hypothesis:** minimizing biarticular load s.t. speed ≥ 99.5% baseline yields a solution similar
  to weighted-sum `w=0.1`.
- **Status:** DEFERRED behind weighted-sum multi-start (formulation plan documented in Phase E).

---

## Phase 3 — Candidate-motion mechanism & translation (existing data + N100 when ready)
- Compare `w=0` vs final candidate on kinematics (TD/terminal-swing/stride-mean pelvic tilt, pelvic
  angular velocity, trunk lean, hip/knee flexion & velocity, foot-vs-COM, step length/frequency,
  contact/swing time) and kinetics (GRF, impulse, hip/knee moment, activation, active/passive/tendon
  force, lengthening velocity, negative work; terminal-swing vs early-stance).
- **Mechanism chain:** load penalty → pelvis/hip/knee/trunk coordination → fiber length & velocity →
  active/passive force → negative work; confirm reduction is **not** merely a speed drop.
- **Field translation:** express as coach-observable kinematic hypotheses (TD pelvic-angle Δ, hip-flex
  Δ, knee-ext Δ, trunk Δ, contact-position Δ, contact-time Δ). Forbidden: "safe running form",
  "injury-preventing form", "proven coaching method". Allowed: *experimental intervention candidate*,
  *coach-observable kinematic hypothesis*, *candidate motion reducing mechanical-load surrogates*.
- **Status:** WIP (N=50 mechanism DONE via existing motion/force analyses; refresh with N=100 candidate).

---

## Phase 4 — Claim ↔ document reconciliation
- Audit `README.md`, `VALIDATION_FINAL_REPORT.md`, `VALIDATION_MASTER_PLAN.md`,
  `CLAIM_EVIDENCE_MATRIX.md`, `LITERATURE_COMPARISON.md`, `Conference_Poster_Plan.md`,
  `Epidemiological_Concordance_Report.md`, hamstring integrated reports, abstracts/poster sources.
- Required rewrites (examples): "injury-prevention Pareto"→"hamstring mechanical-load-surrogate
  Pareto"; "found safe technique"→"generated load-reduction candidate under performance constraint";
  "short-fascicle → training path superior"→exploratory (morphology×pelvis confound);
  "reproduces the epidemiological causal mechanism"→"epidemiological association and the model's
  mechanical-response direction are consistent"; "BFlh work max → reproduces most-injured muscle"→
  "part of the per-muscle load ranking is qualitatively consistent with the injury distribution";
  "Hill optimal-fiber-length matches ultrasound clinical threshold"→different constructs;
  "0.5% noise floor"→pre-declared numerical performance-matching tolerance; "speed-neutral"→
  "near-matched-speed" unless a strict no-difference is shown.
- **Status:** WIP.

## Phase 5 — Morphology scope decision
- Main paper contributions = (1) grid/unit-correct fiber-load evaluation, (2) boundary-condition-aware
  pelvis↔load decomposition, (3) near-matched-speed Pareto candidate. Morphology×pelvis full factorial
  must **not** delay these → move morphology to an exploratory thesis chapter / future work; do not
  make individualized intervention a primary conclusion. Optional factorial only if compute allows.
- **Status:** DECIDED (exploratory).

---

## Phase 6 — Thesis & conference deliverables
- **6.1** `docs/PAPER_RESULTS_FREEZE.md` — commit, data, primary/excluded conditions, key numbers,
  solver status, mesh, inits, supported/conditional/unverified claims, figure & CSV mapping.
- **6.2** `docs/THESIS_OUTLINE_JP.md` — 11-chapter outline with per-chapter figure/table/claim/CSV/code.
- **6.3** abstracts — JP ~600 chars, JP ~1000 chars, EN ~250 words (only final-verified numbers).
- **6.4** Figures 1–5 (formulation; 8-condition per-muscle length/tension/work; boundary-condition
  decomposition; N=100 multi-start Pareto; baseline vs candidate) — each with units, mesh, #conditions,
  solver criterion, achieved speed, surrogate label, caveats.
- **6.5** title (EN/JP) fixed.
- **Status:** WIP; freeze held until Phase A completes (added completion condition).

---

## Phase A — Freeze 8-condition muscle-tension results for the paper (existing N50/N100 data)
- Per muscle {semimem, semiten, bifemlh, bifemsh}: peak normalized fiber length, peak active/passive/
  tendon force, peak active eccentric power, negative active & total fiber work, peak lengthening
  velocity, terminal-swing & early-stance values, timing of peaks.
- Outputs: long-format CSV (pelvic-tilt × muscle × metric); slope/R²/monotonicity; N50–N100 relative
  diff; strict solver status; achieved speed; achieved TD tilt; TS vs ES; **per-muscle verdict table**
  ∈ {robust increase, robust decrease, approximately invariant, non-monotonic, mesh-sensitive,
  inconclusive}. Separate active/passive/tendon/work (no lumping). Flag passive & negative-work
  N50–N100 differences (direction primary, magnitude conditional if large).
- Figures A1 (angle × active/passive/tendon force), A2 (TS vs ES per-muscle), A3 (length/tension/negwork
  dose-response), A4 (N50/N100 mesh sensitivity).
- **Status:** WIP (data present; build `analysis/validation/phaseA_muscle_tension.py`).
- **Blocks the freeze** until complete (added completion condition).

## Phase B — Quantitative comparison with prior literature
- Primary sources: Schache 2012, Chumanov 2007, Thelen 2005, Mendiguchia 2024, Timmins 2016,
  Opar 2022, Kalkhoven 2023, Haralabidis et al., Lin & Pandy 2022. Extract study type, N, speed,
  treadmill/overground, phase, MTU/fiber/regional distinction, force def, work def, normalization,
  per-muscle ranking, peak timing, numeric ranges, agreement/disagreement, boundary/model reasons.
- Do **not** cite numbers not seen in full text; list to-acquire papers (name, DOI, needed table/figure,
  which claim needs it, priority). Never equate different constructs (optimal-fiber-length vs ultrasound
  fascicle; whole-MTU vs regional; tendon vs active fiber force; normalized length vs engineering strain;
  load surrogate vs injury probability).
- Output: `docs/LITERATURE_QUANTITATIVE_COMPARISON.md`. **Status:** WIP.

## Phase C — Finalize optimization-on/off interpretation
- Distinguish (1) tree-rigid kinematic counterfactual, (2) femur-fixed kinematic counterfactual,
  (3) adaptive dynamically-optimized solution. For each: same speed? same phase timing? dynamically
  feasible? muscle-force equilibrium? GRF/contact constraints? what is fixed / changed / claimable /
  not claimable. Do not treat tree-rigid/femur-fixed as equal-status optimal running motions. If
  possible, report inverse-dynamics / force-equilibrium residual for frozen-coordination conditions.
  Framing: "compared a re-optimized solution in the same speed band with boundary-condition-specific
  kinematic counterfactuals." **Status:** WIP (`docs/OPT_ON_OFF_INTERPRETATION.md`).

## Phase D — Implement & compare tension-including objectives (NEW COMPUTE)
- D0 baseline (no penalty); D1 fiber-length threshold (existing); D2 active-eccentric (active force ×
  positive fiber velocity / active negative work); D3 passive-force (terminal-swing peak/integral,
  compare smooth-max & phase-integral for mesh sensitivity); D4 tendon-force (report; note it is not
  hamstring-strain risk per se); D5 composite (nondimensionalized by nominal; weight sets: equal /
  length-dominant / active-eccentric-dominant / passive-dominant). Explore each at N=50 first, then
  confirm baseline + length + active-eccentric + composite primary candidates at N=100 multi-start.
- **Status:** DESIGN (implement penalty variants in `main_pred_sim_sprinting.m` guarded like wJ(13)).

## Phase E — Matched-speed (ε-constraint) objective comparison (NEW COMPUTE)
- Each objective compared at speed ≥ 99.5% of mesh-matched baseline; report achieved speed, speed loss,
  pelvis angle, hip/knee/trunk changes, all surrogates, solver status, residual, mesh, init, runtime.
  Test: does lowering length also lower tension/work? do objectives trade off? one motion improve all?
  any metric improved at another's expense? speed-drop-only explanation excluded? **Status:** DESIGN.

## Phase F — Per-muscle paper conclusions
- One numbered, numeric statement per muscle covering fiber-length / active / passive / tendon /
  negative-work response, TS vs ES, mesh robustness, literature agreement, interpretation limits.
  No lumping ("injury risk up"); use the model/speed/optimization-scoped template. **Status:** WIP
  (depends on Phase A). **Blocks freeze.**

---

## Added completion gates (freeze held until ALL true)
Strict 8-condition per-muscle tension organized; active/passive/tendon separated; TS vs ES separated;
N50/N100 diffs reported; literature comparison definition-consistent; no unseen numbers; opt-off
dynamical limits stated; non-length objectives actually optimized; tension/work candidates confirmed at
N=100; matched-speed objective comparison done; surrogate trade-offs reported; improve-one/worsen-another
checked; no "injury probability / prevention proven" language; `PAPER_RESULTS_FREEZE.md` reflects final;
`THESIS_OUTLINE_JP.md` + abstracts updated.

## Execution order (P0 first, then highest-priority implementable)
1. P1 (provenance, tests, fresh-clone, DATA_AVAILABILITY) — now.
2. Phase A (8-condition per-muscle, existing data) — now; unblocks freeze.
3. P4/P5 claim audit + morphology scoping — now.
4. Phase B / Phase C docs — now.
5. Phase 2 / D / E infra + launch + resume prompt — new compute, checkpointed.
6. P6 freeze + thesis + abstracts + Figures — after A and Pareto status known.
