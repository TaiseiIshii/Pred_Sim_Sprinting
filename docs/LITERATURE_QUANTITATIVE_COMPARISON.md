# LITERATURE QUANTITATIVE COMPARISON (Phase B)

Structured, definition-level comparison of this study's surrogates against the primary literature.
Builds on the qualitative [LITERATURE_COMPARISON.md](LITERATURE_COMPARISON.md). **Rule (task):** no
number is asserted as verified unless confirmed in the source full text; automated retrieval was
blocked this session, so numeric cells needing the PDF are marked **[FT]** (full-text required) and
listed in §4. No purchase/registration was performed.

This study (verified, own computation): international-caliber male sprinter model, symmetric step,
direct collocation; nominal top speed 11.83 m/s (N=100); biarticular hamstring peak normalized fiber
length in **terminal swing (88–91% stride)**, `leng_at_peak_Fce=True`; per-stride active negative
fiber work ≈15–37 J/muscle; peak tendon force ≈3.1–3.3 kN (semimem); mono-articular `bifemsh` flat
(specificity control). Per-muscle ranking of biarticular fiber-length response to anterior tilt:
semimem > bifemlh > semiten (see `phaseA_doseresponse.csv`).

## 1. Construct-distinction rules (never compare as the same quantity)
| A | B | Why not equal |
|---|---|---|
| OpenSim optimal fiber length `lMo` | ultrasound resting fascicle length | model parameter vs imaging measurement; different definitions |
| whole-MTU length (this study) | regional tissue elongation (Mendiguchia) | line-of-action MTU vs local strain field |
| tendon force `FT` | active fiber force `Fce` | series-elastic vs contractile element |
| normalized fiber length `lMtilde` | engineering strain ΔL/L0 | ratio to `lMo` vs unstressed-length strain |
| mechanical-load surrogate | injury probability | biomechanics vs epidemiology |

## 2. Per-study extraction (definition-level; numbers marked [FT] need the PDF)
| Study | DOI | Type | N | Speed | TM/OG | Phase | fiber/MTU/regional | Force def | Work def | Normalization | Per-muscle ranking | Peak timing | Direction agreement w/ us | Disagreement / boundary reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Schache 2012 | 10.1249/MSS.0b013e31823fe0e2 | Exp + MTU model | [FT] | ~max | OG | late swing→stance | **MTU** | MTU force | MTU negative work | body mass | BFlh largest MTU stretch [FT] | late swing | **Yes** (terminal-swing eccentric; BFlh prominence) | their force=MTU; we split `Fce`/`FT`. Exact J/N [FT] |
| Chumanov 2007 | 10.1016/j.jbiomech.2007.05.026 | Tracking sim | [FT] | 80–100% | TM | swing | **MTU** | musculotendon | negative work | – | – | late swing | **Yes** (hip flexion+knee ext drive stretch; ↑ with speed) | MTU not fiber; swing-only |
| Thelen 2005 | 10.1249/01.mss.0000150078.79120.c8 | Forward sim | [FT] | sprint | TM | terminal swing | **MTU** | musculotendon | – | % upright | BFlh peak MTU strain [FT] | terminal swing | **Yes** (timing, eccentric-before-contact) | our fiber `lMtilde` 1.05–1.18 ≠ their MTU strain |
| Kalkhoven 2023 | 10.1007/s40279-023-01906-0 | Review | – | – | – | – | **fiber vs MTU** | – | active eccentric emphasis | – | – | – | **Yes** (motivates fiber-level metric) | conceptual; we operationalize `Fce·v_M` in J |
| Mendiguchia 2024 | [FT] | Exp/imaging | [FT] | – | – | constrained posture | **regional** | – | – | – | proximal BFlh [FT] | – | **Qual.** (anterior tilt ↑ proximal elongation ~ our femur-fixed) | whole-MTU ≠ regional; do not equate |
| Timmins 2016 | 10.1136/bjsports-2015-095362 | Prospective cohort | 152 [FT] | – | – | – | fascicle length (US) | eccentric strength | – | – | BFlh | – | Contextual (short fascicle risk) | risk HR & 10.56 cm threshold [FT]; `lMo`≠US fascicle |
| Opar 2022 | 10.1249/MSS.0000000000002744 [FT] | Cohort/meta | [FT] | – | – | – | eccentric strength | NordBord force | – | – | – | – | Contextual (strength risk) | epidemiological, not mechanical |
| Haralabidis 2024 | 10.1249/MSS.0000000000003797 | **Predictive sim (base)** | 1 | 11.85 m/s | – | whole step | musculoskeletal | – | – | – | – | – | **Baseline** (our 11.83 reproduces) | we add load surrogates + pelvis manipulation |
| Lin & Pandy 2022 | 10.1016/j.jbiomech.2022.111203 [FT] | Predictive sim | 1 | sprint | – | swing/stance | MTU properties | – | – | – | – | – | Consistent (MT props shape performance) | different objective |

TM=treadmill, OG=overground. `N`, exact speeds, and numeric ranges left [FT] unless printed above.

## 3. What we may state now (verified) vs after full text
- **Now (own data + established qualitative direction):** terminal-swing eccentric loading of the
  biarticular hamstrings; hip flexion as the mediator; BFlh prominence in the fiber-length ranking;
  fiber vs MTU distinction (Kalkhoven's argument). These situate — they do **not** validate — our
  independently computed numbers.
- **Only after full text:** any *numeric* agreement (e.g., "our X J vs Schache's Y J", Thelen's MTU
  strain %, Timmins' HR / 10.56 cm threshold, Mendiguchia's % regional elongation). Until then these
  are **not** quoted.

## 4. To-acquire (prioritized) — full text needed
| Priority | Paper | DOI | Needed table/figure/number | Which of our claims it supports |
|---|---|---|---|---|
| **High** | Schache 2012 | 10.1249/MSS.0b013e31823fe0e2 | peak MTU force/length & negative work per hamstring (Tables) | numeric bracket for our terminal-swing negative-work & tendon-force order |
| **High** | Kalkhoven 2023 | 10.1007/s40279-023-01906-0 | fiber-vs-MTU decoupling statements / any quoted ranges | justifies fiber-level surrogate choice |
| **High** | Mendiguchia 2024 | (find DOI) | regional elongation vs pelvic tilt magnitudes & method | frames femur-fixed counterfactual (2C) |
| Med | Chumanov 2007 | 10.1016/j.jbiomech.2007.05.026 | speed-effect magnitudes on stretch/negative work (Figs) | direction & speed-scaling context |
| Med | Thelen 2005 | 10.1249/01.mss.0000150078.79120.c8 | BFlh peak MTU strain value | terminal-swing timing/eccentric context |
| Med | Timmins 2016 | 10.1136/bjsports-2015-095362 | fascicle-length threshold & HR (Table 2) | morphology chapter context (NOT `lMo` equivalence) |
| Low | Opar 2022 | 10.1249/MSS.0000000000002744 | eccentric-strength risk estimates | strength-vs-length orthogonality context |
| Low | Lin & Pandy 2022 | 10.1016/j.jbiomech.2022.111203 | MT-property sensitivity | morphology/performance coupling |

Copilot must not purchase, register, or sign contracts to obtain these; the human author retrieves
them and fills the [FT] cells, after which the thesis may quote the numeric comparisons.
