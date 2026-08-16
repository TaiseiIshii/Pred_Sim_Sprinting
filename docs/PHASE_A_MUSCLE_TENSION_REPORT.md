# Phase A — 8-condition per-muscle hamstring load (paper freeze)

Strict, speed-matched **touchdown-pelvic-tilt (TDPT)** 8-condition set, at **both** meshes
(N=50, N=100). Each hamstring is reported separately; **active / passive / tendon force and negative
work are never lumped**. Values are **mechanical-load surrogates**, not injury probability.

- Data: `eight_condition_metrics_N50.csv`, `eight_condition_metrics_N100.csv` (engine
  `ham_load_metrics.py` v1.0.0, analysis_commit `bb0433a`).
- Achieved touchdown tilt spans −15.99° (most anterior) … −1.99° (least anterior); speed
  11.72–11.80 m/s; all 8 conditions strict `Solve_Succeeded`.
- Analysis: [phaseA_muscle_tension.py](../analysis/validation/phaseA_muscle_tension.py) →
  `phaseA_long.csv`, `phaseA_doseresponse.csv`, `phaseA_mesh_sensitivity.csv`,
  `phaseA_verdicts.csv`, figures A1–A4.
- Verdict thresholds: robust monotonic |Spearman ρ|≥0.90 (N=100) with N=50 sign-consistent
  (|ρ|≥0.70); approximately invariant if relative span <3%; magnitude flagged **mesh-conditional**
  if mean |N100−N50|/N50 >10% (matched by requested offset).

## A.1 Per-muscle verdict table (primary full-stride surrogates, N=100 primary)

| muscle | peak fiber length | peak active force | peak passive force | peak tendon force | negative active work | peak lengthening vel |
|---|---|---|---|---|---|---|
| **semimem** | robust ↑ (mesh 1.5%) | robust ↑ (+6.6%) | robust ↑ **·mesh-cond 10.5%** | robust ↑ (+7.7%) | inconclusive **·mesh 21.7%** | inconclusive |
| **semiten** | robust ↑ (mesh 0.8%) | robust ↓ (−3.3%) | robust ↑ (mesh 6.3%) | ≈ invariant | robust ↑ (mesh 7.5%) | non-monotonic |
| **bifemlh** | robust ↑ (mesh 1.3%) | ≈ invariant | robust ↑ (mesh 9.3%) | ≈ invariant | inconclusive | non-monotonic |
| **bifemsh** (mono, control) | ≈ invariant (0.4%) | ≈ invariant | ≈ invariant | ≈ invariant | robust ↓ **·mesh-cond** | robust ↑ |

↑ = increases with **more anterior** touchdown tilt; ↓ = decreases. Full 73-row table:
`phaseA_verdicts.csv`. Terminal-swing / early-stance rows are in the same file.

## A.2 What is robust vs conditional (honest separation)

**Robust, mesh-insensitive (paper-primary):**
- **Peak normalized fiber length** rises monotonically with anterior touchdown tilt for **all three
  biarticular** hamstrings and is **mesh-robust** (|N100−N50| ≤1.5%): semimem 0.97→1.07 (+9.3%),
  semiten 1.13→1.18 (+4.6%), bifemlh 1.04→1.11 (+7.0%) from −2°→−16° touchdown tilt (N=100,
  R²=0.95–0.96). The mono-articular **bifemsh is flat** (span 0.4%) → the effect is **hip-crossing
  specific**. Peaks occur in **terminal swing** (88–91% of stride) and shift slightly earlier with
  anterior tilt.
- **semimem** additionally shows robust, mesh-insensitive increases in **active** (+6.6%) and
  **tendon** (+7.7%) force — it is the muscle whose *active-force* channel tracks the length change.

**Direction robust but magnitude mesh-conditional (report direction; treat magnitude as conditional):**
- **Passive fiber force** increases with anterior tilt for all three biarticular (ρ≤−0.98) but the
  span is large (36–66%) and the N50↔N100 magnitude differs 6–10.5% (semimem flagged conditional).
- **Terminal-swing negative (eccentric) active work** increases with anterior tilt for all three
  biarticular (ρ≤−0.95) with very large span (74–100%) but **strongly mesh-conditional** (semiten
  28.4%, bifemlh 33.4%). Report the **direction** as the result; the absolute joules are conditional.
- **Terminal-swing lengthening velocity** increases with anterior tilt (mesh-conditional for
  semiten/bifemlh, 15–21%).

**Not uniform across muscles (must be stated per-muscle):**
- **Active force**: semimem robust ↑, **semiten robust ↓ (−3.3%, small)**, bifemlh ≈ invariant.
- **Tendon force**: semimem robust ↑, semiten & bifemlh ≈ invariant.
- **Full-stride negative work**: semiten robust ↑, semimem & bifemlh inconclusive (mesh noise).
- **Full-stride peak lengthening velocity**: biarticular non-monotonic/inconclusive (small,
  R²≤0.61) — consistent with the earlier "velocity ≈ invariant" finding; only bifemsh (control)
  is monotonic in velocity (a stance-phase effect, not terminal-swing stretch).

## A.3 Terminal swing vs early stance
Biarticular peak fiber length, passive force, and negative work all concentrate in **terminal
swing**; early-stance `lMtilde` also rises with anterior tilt (ρ=−1.0, mesh <1%) but at lower
absolute stretch. `bifemsh` peaks in **early stance** (~2% stride) — a different, mono-articular
mechanism. See `fig_A2_TS_vs_ES.png`.

## A.4 Figures
- **Figure A1** `fig_A1_force_doseresponse.png` — pelvic tilt vs active / passive / tendon force.
- **Figure A2** `fig_A2_TS_vs_ES.png` — terminal-swing vs early-stance per-muscle load.
- **Figure A3** `fig_A3_length_tension_work.png` — fiber length, tension, negative-work dose-response.
- **Figure A4** `fig_A4_mesh_sensitivity.png` — N50 vs N100 mesh sensitivity (passive force &
  negative work exceed the 10% conditional line).

## A.5 One-line paper statement (safe language)
> Across a strict, speed-matched 8-condition set at N=50 and N=100, more anterior touchdown pelvic
> tilt was associated, **in this model and optimization**, with robustly higher **terminal-swing
> peak normalized fiber length** in all three biarticular hamstrings (mesh-robust; mono-articular
> `bifemsh` unchanged). Passive force and terminal-swing negative work increased in the **same
> direction** but with **mesh-conditional magnitude**; active and tendon force responses were
> **muscle-specific** (semimem increased; semiten active force slightly decreased; bifemlh ~flat);
> fiber lengthening velocity was approximately invariant/non-monotonic. These are mechanical-load
> surrogates, not injury outcomes.
