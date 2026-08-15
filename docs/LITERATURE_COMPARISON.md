# LITERATURE COMPARISON

Comparison of this predictive-simulation study's hamstring mechanical-load surrogates
against the primary literature. **Access note:** automated full-text retrieval was blocked
by anti-bot / paywall challenges during this session (PubMed proof-of-work; bioRxiv redirect;
publisher paywalls). The qualitative findings below are well-established in these sources;
**exact numeric values marked "[verify PDF]" must be confirmed against the source PDF before
being quoted in the thesis.** A "to acquire" list is given at the end.

This study (reference numbers): international-caliber male sprinter model, single symmetric
step, direct collocation; nominal top speed **11.83 m/s** (N=100); biarticular hamstring peak
normalized fiber length at **87–91% of stride (terminal swing)**; peak fiber lengthening and
`leng_at_peak_Fce = True` (eccentric at peak active force); per-stride active negative fiber
work ≈ **15–37 J/muscle**; peak tendon force up to ≈ **3.1 kN (semimem)**; monoarticular
`bifemsh` shows no pelvic-tilt dose-response (specificity control).

## Comparison table

| Study | Type | Speed | Phase evaluated | Length/force basis | Force definition | Normalization | Key result | Agreement with this study | Mismatch / boundary-condition note |
|-------|------|-------|-----------------|--------------------|------------------|---------------|------------|---------------------------|------------------------------------|
| **Chumanov, Heiderscheit & Thelen 2007** (J Biomech) | Tracking simulation (EMG-driven/forward) | ~80–100% max | Swing (late) | MTU length & velocity | musculotendon | – | Biarticular hamstring MTU stretch peaks in **late swing**; peak stretch and negative work **increase with speed**; hip flexion + knee extension jointly drive stretch | **Yes** — our biarticular peak at 87–91% stride = terminal swing; hip flexion is the mediator (Step 5) | They isolate swing; our single step reconstructs full stride. MTU (not fiber) |
| **Thelen et al. 2005** (MSSE) | Forward dynamic sim | sprint | Terminal swing | MTU length | musculotendon | % of upright | BFlh peak MTU strain ~**[verify PDF]** in terminal swing; eccentric before contact | **Yes** (timing, eccentric) | Our fiber `lMtilde` peak ≈1.05–1.18; theirs is MTU strain — not identical metrics |
| **Schache et al. 2012** (MSSE, "Mechanics of the human hamstrings during sprinting") | Experimental + MTU model | ~max overground | Late swing & stance | MTU length, velocity, force, work | musculotendon force/work | body mass | BFlh largest peak MTU stretch & **high eccentric (negative) work** in late swing; forces scale with speed | **Yes** (qualitative: terminal-swing eccentric loading; force magnitude order) | Their force = MTU force; we separate `Fce` (fiber, N) vs `FT` (tendon, N). Exact J/N values [verify PDF] |
| **Kalkhoven et al. 2023** (Sports Med review) | Review / mechanistic | – | – | Fiber vs MTU decoupling | – | – | Peak **MTU length is a crude injury proxy**; damage driven by **active eccentric fiber** loading; tendon/aponeurosis decouples fiber from MTU | **Yes** — motivates our fiber-level metrics & fasc:MTU decoupling ratio | Conceptual agreement; we operationalize with `Fce·v_M` work |
| **Mendiguchia et al. 2024** | Experimental/imaging (constrained posture) | – | – | **Regional tissue elongation** with femur/shank fixed | – | – | Anterior pelvic tilt increases **proximal** hamstring regional elongation under fixed distal segments | **Qualitative** — our Step 4 **femur-fixed** static audit: anterior tilt lengthens biarticular MTU ≈1 mm/deg | **Do NOT equate**: OpenSim **whole-MTU length** ≠ their **regional tissue elongation**. Our tree-rigid vs femur-fixed contrast frames their constraint |
| **Timmins et al. 2016** (BJSM) | Prospective cohort | – | – | BFlh **fascicle length**, eccentric strength | – | – | Shorter BFlh fascicles & lower eccentric strength → **higher future HSI risk** | Contextual — motivates our morphology (fascicle-scaled) digital athlete | We alter fascicle/strength as **hypothetical phenotype**; we make **no injury-probability claim** |
| **Opar et al. 2015/2021** | Cohort / reliability | – | – | Eccentric strength (NordBord) | – | – | Eccentric strength & prior injury are leading HSI risk factors; between-session reliability characterized | Contextual — why load surrogates ≠ injury probability | Our surrogates are mechanical, not epidemiological |
| **Haralabidis et al. 2024** (bioRxiv 2024.10.08.617292 → MSSE) | **Predictive simulation** (this framework) | **11.85 m/s** optimal | Whole step | full musculoskeletal | – | – | Touchdown kinematic variables affect top sprinting speed | **Baseline** — our nominal 11.83 m/s reproduces it | We add hamstring load surrogates & pelvic-tilt manipulation |
| **Lin & Pandy 2022** (J Biomech) | Predictive simulation | sprint | Swing/stance | muscle–tendon properties | – | – | Muscle–tendon properties (incl. hamstrings) shape sprint performance | Consistent — our morphology sweep shows load/performance coupling | Different objective; we focus on load surrogates |

## Where this study fills a gap
1. **Fiber-level, physically-unit-correct load surrogates** (negative fiber work in **J** on
   the true non-uniform collocation grid), instead of MTU-length or dimensionless "eccWork"
   proxies (Kalkhoven's critique operationalized).
2. **Boundary-condition decomposition** (tree-rigid vs femur-fixed vs adaptive) that makes
   explicit why a "pelvic-tilt direct effect" can appear as 0 or as ~1 mm/deg depending on the
   counterfactual — connecting Mendiguchia's constrained-posture regional finding to a
   whole-body predictive simulation at **matched sprint performance**.
3. **Monoarticular `bifemsh` control** demonstrating hip-crossing specificity of the pelvic
   effect within a single consistent model.
4. **Morphology × pelvis** hypothetical-phenotype exploration under a performance constraint.

## To acquire (full text needed to verify exact quantitative values)
- Schache AG, et al. 2012, *Med Sci Sports Exerc* — hamstring length/velocity/force/work numbers.
- Chumanov ES, Heiderscheit BC, Thelen DG 2007, *J Biomech* 40:3555–3562 — speed effect magnitudes.
- Thelen DG, et al. 2005, *Med Sci Sports Exerc* — BFlh peak MTU strain value.
- Mendiguchia J, et al. 2024 — regional tissue elongation vs pelvic tilt (method & magnitudes).
- Timmins RG, et al. 2016, *Br J Sports Med* 50:1524–1535 — fascicle length / eccentric-strength risk HRs.
- Opar DA, et al. 2015 *MSSE* / 2021 reliability — eccentric strength risk & measurement reliability.
- Haralabidis N, et al. 2024, bioRxiv 2024.10.08.617292 (published *MSSE* doi:10.1249/MSS.0000000000003797).
- Lin Y-C, Pandy MG 2022, *J Biomech* — muscle–tendon properties & sprint performance.

**Rule applied**: no exact numeric result from an inaccessible source is asserted as verified;
qualitative directions above are established consensus in the cited works and are used only to
situate—not to validate—the simulation's own (independently computed) numbers.
