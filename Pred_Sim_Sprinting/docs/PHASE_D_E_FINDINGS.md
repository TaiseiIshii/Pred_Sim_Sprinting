# Phase D/E — tension-based objective findings (N=50 exploration)

Implemented and ran a second, physiologically-distinct load objective and compared it to the
fiber-length objective at matched performance. Answers the Phase E trade-off questions.
**Mechanical-load surrogates, not injury.** Provisional penalty scales (exploration); primary
candidates to be confirmed at N=100 (see §4).

- Objectives (strict `Solve_Succeeded`, N=50, standard morphology):
  - **D1 fiber-length** `_HamPareto_Nom_w{0..0.8}` — penalizes biarticular peak `lMtilde`.
  - **D2 active-eccentric** `_HamEcc_w{0..8}` — penalizes `Fce·[vMtilde]+` (active force during
    fibre lengthening), integrated (= active eccentric loading). NEW (main `wJ(16)`).
  - **D3 passive-force** `_HamPasv_w{0.2,0.8}` — penalizes `smoothpos(Fpass−50)^2` (main `wJ(14)`;
    under-calibrated at the provisional scale, see §2.6).
  - **D5 composite (equal mix)** `_HamCompEQ_w{0.1,0.5,2}` — length + ecc + passive combined.
- Data: `phaseD_objective_frontier.csv`, `fig_D1_objective_frontier.png`. Engine
  `ham_load_metrics.py` v1.0.0. Implementation: [PHASE_D_E_OBJECTIVE_RECIPE.md](PHASE_D_E_OBJECTIVE_RECIPE.md).
- Self-consistency: `_HamEcc_w0000` reproduces baseline (speed 11.7734 vs 11.7774, 0.03%) → the
  Phase D optimizer edits are validated.

## 1. Speed–load frontier (biarticular mean, % vs the shared penalty-off baseline w=0)

| obj | w | Δspeed% | Δ peak lMtilde% | Δ act-ecc power% | Δ neg-work% | Δ passive% | near-matched? |
|---|---|---|---|---|---|---|---|
| length | 0.10 | −0.24 | −4.14 | −9.5 | −5.6 | −25.5 | **yes** |
| length | 0.80 | −1.52 | −11.8 | −34.8 | −22.1 | −55.4 | no |
| **ecc** | **0.10** | **−0.06** | −0.20 | **−16.5** | **−20.4** | −1.4 | **yes** |
| ecc | 2.00 | −1.12 | −0.00 | −95.9 | −90.9 | +4.9 | no |
| ecc | 8.00 | −1.91 | **+1.70** | −97.6 | −94.2 | **+13.8** | no |
| passive | 0.20 / 0.80 | −0.03 | +0.9 | ≈0 | ≈0 | **+6.8** | no (under-calibrated) |
| **composite** | **0.10** | **−0.34** | **−4.54** | **−28.5** | **−27.4** | **−27.6** | **yes** |
| composite | 0.50 | −1.86 | −10.9 | −77.1 | −75.3 | −53.7 | no |
| composite | 2.00 | −2.80 | −13.4 | −91.3 | −89.3 | −59.5 | no |

(Shared baseline = `HamPareto_Nom_w0000` N=50. The ecc/passive penalty-off runs land ~0.03% speed /
~0.9% lMtilde / ~6.7% passive from it — local-solution non-uniqueness of the sprint NLP, not a penalty
effect; the *penalty effects* below are read relative to that small offset.)

## 2. Key findings (the two objectives are NOT equivalent)
1. **Objective dissociation.** The fiber-length objective lowers peak `lMtilde` steeply (to −11.8%)
   and drags down everything downstream (**passive force −55%**). The active-eccentric objective
   collapses active eccentric power/work (to **−97% / −94%**) while **barely changing fiber length**
   (−0.8%…+0.8%). Fiber length and active-eccentric work are **largely decoupled levers**.
2. **Near-matched-speed candidates differ by target.** At ≈0 speed cost, the **ecc objective w=0.1**
   cuts active negative work **−20.0%** (and eccentric power −15.9%) for only **−0.03% speed** — a
   far larger eccentric-load reduction per unit speed than the length objective (−5.6% neg-work at
   −0.24% speed). If the target surrogate is **active eccentric loading**, D2 is the stronger
   near-matched-speed candidate; if it is **fiber overstretch / passive force**, D1 is.
3. **Trade-off / one-metric-improves-another-worsens (Phase E).** At high ecc weight (w=8.0) the ecc
   objective **worsens** passive force (**+6.7%**) and fiber length (**+0.8%**) while still cutting
   active eccentric work — i.e. it shifts load from the active-eccentric channel toward a stiffer,
   more-passive strategy. No single objective monotonically improves *all* surrogates.
4. **Not a speed artefact.** The ecc w=0.1 candidate reduces negative work −20% at −0.03% speed;
   the reduction is not explained by speed loss.
5. **Composite improves ALL surrogates at once (Phase E "one motion for all metrics?" = yes).** The
   equal-mix composite at w=0.1 reduces fibre length −4.5%, eccentric power −28.5%, negative work
   −27.4% **and** passive force −27.6% simultaneously, at −0.34% speed — a single near-matched-speed
   candidate that lowers every surrogate, which **no single objective achieves** (length leaves
   eccentric power only −9.5%; ecc leaves fibre length/passive ~0). It shifts touchdown tilt more
   posterior (−4.3°→−3.6° at w0.1). This is the strongest all-round candidate.
6. **Passive objective under-calibrated.** At the provisional scale (5e-1) the passive penalty barely
   moved the solution (speed −0.03%, passive +6.8% — within local-solution noise). Its scale must be
   raised ~10× before a passive-only frontier is meaningful (recorded for the next pass).

## 3. Interpretation (safe language)
> In this model, penalizing active-eccentric hamstring loading generates a near-matched-speed
> candidate motion that markedly lowers active negative fibre work with little change in peak fibre
> length, whereas penalizing fibre length lowers overstretch and passive force. The two are distinct
> mechanical levers; the appropriate objective depends on which load surrogate is targeted. These are
> experimental intervention hypotheses on mechanical-load surrogates, not demonstrated injury effects.

## 4. Remaining (needs a MATLAB slot)
- **N=100 multi-start confirmation** of the primary candidates: the **composite w=0.1** (best
  all-round) and **ecc w=0.1**, with from-Nominal/backward inits + the Phase-2.4 gates (the length
  w=0.1 is already N=100-Supported, see PAPER_RESULTS_FREEZE §5).
- **Re-calibrate the passive scale** (~10×) and re-run the passive frontier.
- **Tendon (D4)** `_HamTdn_` — report only.
- **Phase E ε-constraint** (speed ≥ 99.5% baseline) formulation (recipe §Phase E) for a formal
  matched-speed comparison; the near-matched-speed band here is the weighted-sum proxy.
- Refine the provisional penalty scales (pasv 5e-1, tdn 1e-6, ecc 1e-1) so weights span a comparable
  fraction of the speed term.
