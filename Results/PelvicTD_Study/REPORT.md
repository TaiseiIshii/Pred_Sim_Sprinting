# Touchdown Pelvic Tilt and Hamstring Strain-Injury Risk in Maximal Sprinting

### A single-intervention predictive-simulation causal study (v3 / TDPT)

**Date:** 2026-06-24 · **Status:** N = 50 dose-response complete (8 conditions);
N = 100 mesh-independence **confirmed** (8 conditions, all `Solve_Succeeded`).

> 日本語のやさしい解説は [かんたんガイド.md](かんたんガイド.md) を参照してください。本ファイルは
> 論文化に向けた**厳密な手法・結果・限界**の記述です（英語）。

---

## 1. Summary

We used muscle-driven predictive simulation of maximal-speed sprinting to test, **causally**,
whether the **pelvic tilt at foot touchdown** modulates **hamstring strain-injury risk**. We
imposed a *single* equality constraint on the touchdown pelvic-tilt angle and re-optimised the
entire sprint for maximal speed, leaving every other coordinate, the muscle excitations, the
ground-reaction forces, and the movement timing free. This mirrors exactly the minimal-
intervention touchdown-distance designs (HTD/IKTD) of the source study, but applied to the
pelvis.

**Findings.** Across an 8-point dose-response spanning touchdown pelvic tilt from −1.5°
(near-neutral) to −15.5° (strong anterior tilt):

1. **Anterior touchdown tilt monotonically increases biarticular-hamstring stretch** (semimembranosus,
   semitendinosus, biceps femoris long head) across three independent proxies — peak normalised
   fibre length, peak musculotendon length, and peak passive force.
2. **The single-joint control (biceps femoris short head, which does not cross the hip) is flat**
   (slope ≈ 0), confirming the effect is specific to the hip-spanning biarticular hamstrings.
3. **Top sprint speed is essentially unchanged** (11.72–11.78 m/s, ≈0.6% variation) over the whole
   range. Anterior tilt is therefore **not a speed trade-off but a pure injury-risk factor**.
4. **There is no dynamic feasibility limit in the tested range.** An apparent anterior limit
   (≈ −9.9°, with "infeasibility" and "speed collapse") seen under the default settings was traced
   to a **modelling artefact — the pelvis-tilt coordinate bound** — and disappeared once that bound
   was relaxed (Section 5).

---

## 2. Source study and prior internal versions

- **Source method (Haralabidis, Eaton, Delp, Hicks, *Med Sci Sports Exerc* 2025; PMC12893165).**
  Two minimal touchdown interventions, each a *single scalar equality at the touchdown node* with
  full re-optimisation:
  - **HTD** (horizontal touchdown distance): `toe_x − COM_x`, nominal **0.328890590509637 m**,
    offsets ±2/4/6 cm.
  - **IKTD** (inter-knee touchdown distance): `kneeR_x − kneeL_x`, nominal **0.040824168566493 m**,
    offsets ±2/4/6 cm.
  - Reported optimal top speed ≈ **11.85 m/s**.
- **v1 (internal):** a wide allowable *band* on pelvic tilt — the optimiser collapsed to a single
  angle; abandoned.
- **v2 (PelvisShift, internal):** the *entire* pelvic-tilt waveform was held to a shifted band, and
  the hip/lumbar *initial* values were counter-adjusted to preserve touchdown. This produced a
  dose-response but (a) constrained the pelvis at all nodes and (b) touched coordinates other than
  the pelvis, weakening the "manipulate only the pelvis" claim.
- **v3 (PelvisTD / TDPT, this report):** matches the source method's *minimal single-equality*
  philosophy. Only the touchdown pelvic tilt is constrained; the rest of the motion is established
  naturally by re-optimisation. This is the cleanest single-intervention causal design.

---

## 3. Methods

### 3.1 Model and framework

A three-dimensional, full-body musculoskeletal model (Hamner–Delp sprinting lineage) with **37
generalised coordinates** and **92 lower-limb/trunk musculotendon units** (Hill-type, with
compliant tendons and an implicit activation/contraction formulation); the arms are driven by ideal
torque actuators. Foot–ground interaction uses a smooth contact model. The multibody dynamics and
contact are evaluated through a compiled CasADi external function. The motion is a **single
ground-contact half-stride with left–right symmetry**, so a full stride is reconstructed by
mirroring; the half-stride begins at right-foot **touchdown** (the initial node, `k = 0`).

### 3.2 Optimal control problem

- **Transcription:** direct collocation, **N = 50 mesh intervals**, **Radau** collocation of
  **degree d = 3**.
- **Objective** (maximise average speed with light effort regularisation):

  $$ J \;=\; \underbrace{\sum_i w_i\, \Phi_i}_{\text{effort / regularisation } (J_1)} \;-\; w_{12}\,\frac{\Delta x_{\text{pelvis}}}{t_f} $$

  with the speed weight `w12 = 10`. The **kinematic-tracking weights are zero**
  (`w1 = w2 = w3 = w4 = 0`): the Nominal and all TDPT conditions are **pure speed-maximising
  predictions**, not tracking simulations. The non-zero regularisers are accelerations (0.05),
  muscle activations (0.1), d(activation) (0.01), d(tendon force) (0.01), reserve actuators (0.01),
  and arm controls (0.1).
- **Constraints:** implicit skeletal (multibody) and muscle contraction dynamics at every
  collocation point; activation dynamics; an initial **multibody-pose matching window** of **±15°
  per coordinate** to the experimental touchdown pose (pelvis translations excepted; `pelvis_tx`
  pinned to 0); a vertical-GRF threshold (20–40 N) at touchdown; and half-stride symmetry/periodicity.
- **Solver:** IPOPT (MUMPS linear solver), limited-memory Hessian, adaptive barrier, convergence
  tolerance **1e-5**. TDPT conditions keep this **strict** tolerance (no acceptable-level
  relaxation); only a CPU-time safety net (90 min/condition) is added. Each condition is **warm-started
  (primal + dual)** from the matching-N Nominal solution.

### 3.3 The touchdown pelvic-tilt (TDPT) intervention

The Nominal touchdown pelvic tilt is extracted **programmatically** from the matching-N Nominal
solution (not hard-coded): **−7.46° at N = 50** (−7.99° at N = 100). In this model's convention
**negative pelvic tilt = anterior**, positive = posterior.

For each condition we add exactly **one equality** at the touchdown node:

$$ q_{\text{pelvis\_tilt}}(k{=}0) \;=\; q^{\text{Nom}}_{\text{pelvis\_tilt}}(k{=}0) \;+\; \Delta $$

where Δ is the imposed offset (e.g. −6° = more anterior, +6° = more posterior). **Nothing else is
touched:** pelvic tilt at all non-touchdown nodes, hip flexion, lumbar, every other joint, all
muscle excitations, the GRFs, and the movement duration re-optimise freely to maximise speed. This
is the same constraint *type* as HTD/IKTD, applied to the pelvis.

### 3.4 Conditions

Offsets Δ ∈ {−8, −6, −4, −2, 0, +2, +4, +6}° give target touchdown tilts of −15.46° … −1.46° in 2°
steps. Naming: `_PelvisTD_m6` → Δ = −6° (anterior), `_PelvisTD_p6` → Δ = +6° (posterior),
`_PelvisTD_p0` → Δ = 0° (reproduces the Nominal touchdown).

### 3.5 Hamstring strain-injury-risk proxies (multi-metric)

For each hamstring we compute, per side, the peak over the stride, then report the **bilateral mean**
of the two per-side peaks:

| Proxy | Definition | Interpretation |
| --- | --- | --- |
| `peakLM` | max normalised fibre length `lMtilde` | fibre stretch (primary) |
| `peakLMT` | max musculotendon length `lMTk_lr` (m) | whole-MTU stretch (injury site) |
| `peakFpe` | max normalised passive force `Fpetilde` | connective-tissue load |
| `peakEccLoad` | max( `max(0,vMtilde)·FMvtilde` ) | active force while lengthening |
| `peakComp` | max( `lMtilde·max(0,vMtilde)·Fce/Fiso` ) | composite strain×ecc×force |
| `eccWork` | Σ( `Fce·max(0,vMtilde)` )·dt | eccentric impulse |
| `tPeakPct` | % of stride at peak `lMtilde` | timing (expect late swing) |

The four hamstrings analysed (with `muscleValues` rows L/R, 1-based): semimembranosus (7/53),
semitendinosus (8/54), biceps femoris long head (9/55), and **biceps femoris short head (10/56)** —
the latter is the **negative control**, since it does **not** cross the hip and so should be
insensitive to pelvic tilt.

---

## 4. Results

### 4.1 Manipulation fidelity and natural adaptation

Every condition solved to the strict tolerance (`Solve_Succeeded`) and realised its target touchdown
tilt exactly. The only coordinate adaptation needed at touchdown is a **natural increase in hip
flexion** as the pelvis is tilted more anteriorly (26.4° at −1.46° → 41.8° at −15.46°); no other
coordinate is counter-adjusted, and no manual compensation is applied. This increased hip flexion
is precisely the mechanism that stretches the hip-spanning hamstrings.

### 4.2 Dose-response (N = 50)

| Touchdown tilt | anterior (°) | status | hip flex (°) | speed (m/s) | semimem | semiten | bifemlh | **bifemsh (control)** |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| −15.46° | 15.5 | Solved | 41.8 | 11.72 | 1.039 | 1.155 | 1.077 | 0.941 |
| −13.46° | 13.5 | Solved | 39.6 | 11.74 | 1.021 | 1.144 | 1.063 | 0.941 |
| −11.46° | 11.5 | Solved | 37.4 | 11.76 | 1.004 | 1.134 | 1.047 | 0.942 |
| −9.46° | 9.5 | Solved | 35.0 | 11.77 | 0.977 | 1.118 | 1.025 | 0.941 |
| **−7.46° (Nom)** | 7.5 | Solved | 32.9 | 11.78 | 0.960 | 1.108 | 1.010 | 0.942 |
| −5.46° | 5.5 | Solved | 30.7 | 11.77 | 0.943 | 1.098 | 0.995 | 0.942 |
| −3.46° | 3.5 | Solved | 28.6 | 11.76 | 0.928 | 1.090 | 0.982 | 0.942 |
| −1.46° | 1.5 | Solved | 26.4 | 11.74 | 0.916 | 1.082 | 0.971 | 0.942 |

*Muscle columns are peak `lMtilde` (bilateral mean). Full proxy set in `pelvic_td_summary.csv`.*

**Dose-response slopes** (per degree of anterior touchdown tilt; least-squares over all 8 points):

| Proxy | semimem | semiten | bifemlh | bifemsh (control) |
| --- | ---: | ---: | ---: | ---: |
| `peakLM` (fibre) | +0.0091 | +0.0053 | +0.0079 | **−0.0001** |
| `peakLMT` (MTU) | +0.0009 | +0.0011 | +0.0010 | **≈0** |
| `peakFpe` (passive) | +0.0010 | +0.0015 | +0.0012 | **≈0** |

The three biarticular hamstrings rise monotonically across all three robust proxies, while the
single-joint control is flat — a textbook specific dose-response (`td_fig1_dose_hamstring.png`,
`td_fig3_multiproxy.png`). The eccentric-load proxy (`peakEccLoad`) shows the same biarticular trend
but is noisier (its control is not perfectly flat) and is treated as supportive only.

### 4.3 Speed and feasibility

Top speed varies by ≈0.6% across the entire range, with a shallow maximum at the Nominal tilt
(`td_fig2_speed_feasibility.png`). There is **no infeasibility and no speed collapse** anywhere in
−1.46° … −15.46°. Anterior touchdown tilt thus increases hamstring strain **without a measurable
speed penalty**.

### 4.4 Mesh independence (N = 50 vs N = 100)

All eight conditions were re-solved at **N = 100** (twice the mesh) under the identical bound-
relaxed configuration, each warm-started from the N = 100 Nominal; **all eight reached strict
convergence** (`Solve_Succeeded`, tol 1e-5). The dose-response is mesh-independent
(`td_fig4_mesh_compare.png`):

| Slope (per ° anterior) | semimem | semiten | bifemlh | bifemsh (control) |
| --- | ---: | ---: | ---: | ---: |
| `peakLM`  N = 50  | +0.0091 | +0.0053 | +0.0079 | −0.0001 |
| `peakLM`  N = 100 | +0.0095 | +0.0054 | +0.0081 | −0.0001 |
| `peakLMT` N = 50  | +0.00089 | +0.00114 | +0.00096 | ≈0 |
| `peakLMT` N = 100 | +0.00090 | +0.00114 | +0.00097 | ≈0 |

The `peakLM` slopes agree to within |Δ| ≤ 0.0003 and the `peakLMT` slopes are essentially identical
(|Δ| ≤ 0.00001); the single-joint control stays flat at both meshes; and top speed stays flat at
both (N = 50: 11.72–11.78 m/s; N = 100: 11.75–11.80 m/s, marginally higher with the finer mesh as
expected). Monotonicity, specificity (biarticular vs single-joint), and the no-speed-penalty
finding all reproduce. (Per-condition N = 100 runtimes 44–101 min on a non-throttled, high-
performance machine; the heavier N = 100 NLP needed a larger CPU budget than N = 50.)

### 4.5 Ground reaction forces are essentially invariant to touchdown tilt

Stance-leg (right-foot) GRF (`optimumOutput.GRFs.R`) was analysed across all eight conditions.
**Peak vertical GRF is effectively constant** — 5.71–5.75 BW at N = 50 (5.80–5.84 BW at N = 100),
i.e. **±0.7%** — and the vertical/propulsive impulses and contact time (~74–76 ms) barely change.
The only systematic effect is a small increase in **peak braking force** with anterior tilt
(≈ +4–5% from neutral to −15.5°; slope +0.003 BW/° at N = 50, +0.011 at N = 100), with a slightly
lower vertical loading rate. Both meshes agree. **Interpretation:** the elevated hamstring strain
under anterior tilt is a *muscle-/kinematic-level* effect (increased hip flexion → biarticular
stretch), **not** an increase in whole-body ground loading — the ground does not push harder;
anterior tilt merely exposes the hamstrings to a more lengthened state (with a minor braking cost).
See `analyze_grf_td.py` and `td_fig5_grf_doseresponse.png`.

---

## 5. The apparent anterior limit was a coordinate-bound artefact (transparency)

Under the **default** settings the two strongest anterior conditions (Δ = −4°, −6°) failed to solve,
plateaued at ≈ −9.9° touchdown tilt, and showed reduced speed (≈9.2–9.6 m/s). We initially
interpreted this as a *biomechanical* limit. A three-step investigation showed it was not:

1. **Hypothesis — the ±15° initial-pose matching window.** Relaxing the pelvis-tilt entry of that
   window to ±25° **did not** help: still plateaued at −9.9°, still infeasible. **Window refuted.**
2. **Trajectory inspection.** Both feasible (Δ = −2°) and still-infeasible conditions — *and the
   Nominal itself* — flat-lined the pelvic tilt at exactly **−9.92°** for part of swing. This is not
   a constraint but the **pelvis-tilt coordinate (box) bound**, which `createScaledBounds` had set
   from the symmetrified experimental range (≈ ±9.9°). The Nominal silently rode this bound for
   ~19 of 200 nodes; the most anterior standard conditions for ~42 nodes.
3. **Definitive test — relax the coordinate bound too.** Widening **both** the matching window and
   the pelvis-tilt coordinate bound to ±25° (the `_PelvisTDwide_*` variants) made Δ = −4°/−6°/−8°
   **all solve** to their exact targets (−11.46°/−13.46°/−15.46°), at full speed (≈11.72–11.76 m/s),
   with hamstring stretch continuing to rise monotonically.

**Conclusion.** The "strong anterior tilt is infeasible / speed collapses / ≈ −10° is the limit"
finding was **entirely** an artefact of the pelvis-tilt coordinate bound, not biomechanics. We
therefore report the full dose-response using **bound-free** results everywhere: the bound-relaxed
runs for the five most-anterior points (−7.46° … −15.46°, which would otherwise touch the bound) and
the standard runs for the three posterior points (−5.46° … −1.46°, which never approach the bound,
verified minima −7.96°/−6.09°/−4.16°). No reported point is constrained by its coordinate bound.

*(Aside: an overnight run of Δ = −6° once took ≈17.4 h. This was an environment artefact — the
machine throttled the CPU in a power-saving/sleep state (~197 s per function evaluation vs ~0.6–1.1 s
in every daytime run). The identical condition re-run in daytime finished in 18.5 min. The scientific
result is unaffected.)*

---

## 6. v3 (TDPT) vs v2 (PelvisShift) vs source (HTD/IKTD)

| Aspect | Source HTD/IKTD | v2 PelvisShift | **v3 PelvisTD (this work)** |
| --- | --- | --- | --- |
| What is constrained | one touchdown scalar | whole pelvic-tilt waveform | **one touchdown scalar (pelvic tilt)** |
| Other coordinates | free (re-optimised) | hip/lumbar initial values adjusted | **untouched (re-optimised)** |
| Constraint form | single equality at `k=0` | per-node band | **single equality at `k=0`** |
| Tolerance | strict | relaxed/early-stop | **strict (1e-5), time-bounded** |
| Causal cleanliness | high | moderate | **high (minimal intervention)** |

v3 reproduces the source study's minimal-intervention rigour while targeting the pelvis, giving the
transparency and causal clarity required for publication.

---

## 7. Limitations

- **Single subject, left–right symmetric, no fatigue/no neural-control model.** Strain is inferred
  from a deterministic musculoskeletal model and is model-dependent.
- **No anterior limit was reached within the tested range (to −15.5°).** Whether a true dynamic
  limit exists at still-stronger anterior tilt is untested.
- **Strain proxies, not a tissue-damage model.** We report fibre/MTU stretch and passive force; the
  eccentric-load proxy is noisier and used only as support.
- **Mesh.** Results are reported at N = 50 and **confirmed mesh-independent at N = 100** (all eight
  conditions `Solve_Succeeded`; dose-response slopes and flat speed reproduce, §4.4). Both meshes use
  the bound-relaxed configuration.

---

## 8. Reproducibility

- **Driver / sweep:** `MainFunctions/run_pelvic_td_sweep.m(conditions, N)`; batch entry
  `run_pelvic_td.bat` (modes `pilot|full|validate|remaining|analyze|wide|widefill|n100`). `wide` =
  bound-relaxed {m4,m6,m8}; `widefill` = bound-relaxed {m2,p0}; `n100` = all 8 wide conditions at
  N = 100. `main_pred_sim_sprinting(sim, N)` takes an optional mesh override (default 50; N ≥ 100
  uses a 6 h CPU budget).
- **Core implementation:** `MainFunctions/main_pred_sim_sprinting.m`
  — TDPT equality at the `k==0` block (`if contains(file_ext,'PelvisTD')`);
  — `_PelvisTDwide_*` relaxes both the matching window (`k==0`) and the pelvis-tilt coordinate bound
    (`createScaledBounds`);
  — objective/weights and solver settings as in Section 3.2.
- **Analysis:** `analysis/plot_pelvic_td_figs.py [N]` (dose-response, multi-proxy, speed; filters
  results by `options.N`; default N = 50, pass `100` for the N = 100 figures with an `_N100` suffix);
  `analysis/compare_td_mesh.py` (N = 50 vs N = 100 overlay); `analysis/analyze_grf_td.py`
  (ground-reaction-force dose-response); `analysis/probe_pelvic_td.py`
  (per-condition probe); `analysis/compute_osim_muscle_paths_td.py` (OpenSim env: builds the
  wrapping muscle-path cache from the `.mat` joint trajectories) + `analysis/visualize_pelvic_td_musculoskeletal.py`
  (pyvista: posed OpenSim bone meshes + wrapping muscle paths with hamstring-strain colouring;
  side-by-side + overlay videos + hero still).
- **Outputs (this folder):** `pelvic_td_summary.csv` (+ `_N100`), `td_fig1_dose_hamstring.png`,
  `td_fig2_speed_feasibility.png`, `td_fig3_multiproxy.png` (+ `_N100` variants),
  `td_fig4_mesh_compare.png`, `td_fig5_grf_doseresponse.png`, `grf_td_summary.csv` (+ `_N100`),
  `pelvic_td_musculoskeletal_{sidebyside,overlay}.mp4`,
  `pelvic_td_musculoskeletal_hero.png`, `かんたんガイド.md`, `PLAN.md`.

---

*Source study:* Haralabidis N, Eaton C, Delp SL, Hicks JL. *Med Sci Sports Exerc* 2025 (PMC12893165).
