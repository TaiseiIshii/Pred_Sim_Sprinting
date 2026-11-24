# CLAIM CALIBRATION — forbidden → defensible (governing reference)

This is the **authoritative language policy** for the thesis, abstracts, poster, and all reports.
Every deliverable must use the right-hand column. The evaluated quantity is an **injury-related
mechanical-load surrogate**, never injury probability. Companion: [CLAIM_EVIDENCE_MATRIX.md](CLAIM_EVIDENCE_MATRIX.md).

## 1. Mandatory rewrites (from the task) + where they occur

| # | Forbidden / over-claim | Required framing | Files touched |
|---|---|---|---|
| C1 | "injury-prevention Pareto design" / 「肉離れ予防のパレート設計」 | "Pareto design of hamstring **mechanical-load surrogates**" / 「ハムストリング**力学的負荷代理指標**の速度–負荷パレート」 | Conference_Poster_Plan, README, integrated reports |
| C2 | "found a safe running technique" / 「安全な走法を発見」 | "generated a **load-reduction candidate motion** under a performance constraint" | Poster, Pareto/integrated reports |
| C3 | "short-fascicle athletes are better served by the training path" / 「短筋束ではトレーニング経路が有利」 | **exploratory hypothesis** — morphology×pelvis is confounded (not a primary conclusion) | Poster H2, Epidemiological, morphology sections |
| C4 | "reproduces the epidemiological **causal mechanism**" / 「疫学の因果機序を再現」 | "the epidemiological **association** and the model's **mechanical-response direction** are **consistent**" | Epidemiological_Concordance_Report |
| C5 | "BFlh work is largest → reproduces the most-injured muscle" | "**part** of the per-muscle load **ranking** is **qualitatively consistent** with the injury distribution" | Epidemiological, integrated |
| C6 | "Hill optimal fiber length **matches** the ultrasound fascicle-length clinical threshold" | **different constructs**; not treated as a direct **quantitative** match (range-straddling only, with the caveat) | Epidemiological §4.1, LITERATURE_* |
| C7 | "0.5% noise floor" | "**pre-declared numerical performance-matching tolerance** (0.5%)" | CLAIM_EVIDENCE_MATRIX A6, pareto scripts, Pareto reports |
| C8 | "speed-neutral" | "**near-matched-speed**" (only use *speed-neutral* if a strict no-difference is demonstrated) | VALIDATION_FINAL_REPORT §9, Pareto reports |
| C9 | "free lunch" (poster body) | "**low-cost / near-zero-speed-cost region**" (lay talk only) | Poster, explainer |
| C10 | "proven coaching method / safe form that prevents injury" | "**experimental intervention candidate** / **coach-observable kinematic hypothesis**" | Poster, integrated |

## 2. Construct-distinction rules (never equate)
Do **not** compare, as if identical:
- OpenSim **optimal fiber length** (Hill parameter `lMo`) vs **ultrasound resting fascicle length**.
- **whole-MTU length** vs **regional tissue elongation** (Mendiguchia 2024).
- **tendon force** vs **active fiber force**.
- **normalized fiber length** (`lMtilde`) vs **engineering strain** (ΔL/L0).
- **mechanical-load surrogate** vs **injury probability**.

## 3. Muscle-specific rule (no lumping)
Never write "all hamstrings' tension increased." Report **active / passive / tendon force and
negative work separately**, per muscle, per phase (terminal-swing vs early-stance). Template
(Phase F): *"More anterior touchdown pelvic tilt was associated, in this model / speed / optimization,
with [increase/decrease] of [muscle]'s [specific surrogate] in [phase]; [note the mesh-conditional or
invariant channels]."* See `phaseA_verdicts.csv`.

## 4. Approved vocabulary
- **injury-related mechanical-load surrogate** (normalized fiber length, active/passive/tendon force,
  fiber lengthening velocity, negative fiber work; terminal-swing / early-stance peaks & integrals).
- **near-matched-speed**, **pre-declared performance-matching tolerance**.
- **candidate motion reducing mechanical-load surrogates**, **experimental intervention candidate**,
  **coach-observable kinematic hypothesis**.
- **boundary-condition counterfactual** (tree-rigid / femur-fixed) vs **adaptive re-optimized solution**.
- **consistent-in-direction** (not "reproduces the cause of").

## 5. Standing caveats to attach to every headline number
mesh (N=50/100) · solver status (`Solve_Succeeded`) · achieved speed (not requested) · achieved
pelvis angle (not requested) · "surrogate, not injury" · for passive force & negative work: "direction
robust, **magnitude mesh-conditional**".

## 6. Audit status of each document
| File | Status | Action |
|---|---|---|
| VALIDATION_FINAL_REPORT.md | mostly calibrated | fixed commit; change "speed-neutral"→"near-matched" (C8) |
| CLAIM_EVIDENCE_MATRIX.md | calibrated | fixed "0.5% noise floor"→tolerance (C7) in A6 |
| Conference_Poster_Plan.md | **over-claim** | title/axis C1; H2 C3; banner added |
| Epidemiological_Concordance_Report.md | **over-claim** | C4/C5/C6; banner + title/summary softened |
| README.md | check | scan for C1/C2 |
| LITERATURE_COMPARISON.md | conditional | C6 construct rules; superseded by LITERATURE_QUANTITATIVE_COMPARISON.md |
| Hamstring_*_Report.md (integrated/pareto) | partial | C1/C2/C8/C9 on next edit pass |
