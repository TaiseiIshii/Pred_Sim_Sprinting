# Phase D/E — tension-based objectives: implementation recipe (ready to code)

MATLAB is currently running the Phase-2 N=100 Pareto sweep, so this recipe is written to be
implemented + tested in the next compute window. It is concrete (exact insertion point, variables,
guard pattern) so it can be coded quickly and safely. Follow the **gated, additive** pattern used by
`wJ(13)` so every existing condition stays byte-identical.

## Available CasADi expressions at collocation point j (verified, main L2384)
```
[Hilldiffkj, FTkj, Fcekj, Fpasskj, Fisokj, vMaxkj, ~, lMkj, lMtildekj] = ...
    f_forceEquilibrium_FtildeState_all_tendon_M(actkj_nsc{j}, FTtildekj_nsc{j}, ...);
```
- `Fcekj` = active contractile force (N) · `Fpasskj` = passive fiber force (N) · `FTkj` = tendon
  force (N) · `lMtildekj` = normalized fiber length · `FTtildekj_nsc{j}` = normalized tendon force.
- **Fiber velocity `vMtilde` is NOT returned** here → for the active-eccentric objective (D2) either
  (a) extend `loadMuscleModelFunctions` to also return `vMtildekj`, or (b) approximate lengthening by
  finite-difference of `lMtildekj` across consecutive collocation nodes. (a) is cleaner.
- Biarticular rows (L/R): `parHamBi = [7 8 9 53 54 55]` (semimem, semiten, bifemlh; bifemsh excluded).

## Insertion point
Same block as the existing penalty (main ~L2582), immediately after the `if wJ(13) ~= 0 … end`.
Use **new, independent weight indices** so each objective sweeps alone and is off by default:
`wJ(14)=passive`, `wJ(15)=tendon`, `wJ(16)=active-eccentric`, `wJ(17)=composite-mode weight`.
Set them from new `simulation_type` tokens near the `paretoStudy` parse (main ~L223), e.g.
`_HamPasv_wXXXX`, `_HamTdn_wXXXX`, `_HamEcc_wXXXX`, `_HamComp[EQ|LEN|ECC|PAS]_wXXXX`.

## Objective variants (all gated `if wJ(k)~=0`, integrated `*B(j+1)*…*h` like every running cost)
```matlab
% D3 passive-force objective (terminal-swing peak proxy via smooth one-sided hinge)
if wJ(14) ~= 0
    pasThr = pasThrN;                      % e.g. nominal biarticular peak Fpass (N); document
    pasOvr = Fpasskj(parHamBi) - pasThr;
    pasPos = 0.5*(pasOvr + sqrt(pasOvr.^2 + 1e-3^2));
    J = J + pScalePas.*wJ(14).*B(j+1)*(sum(pasPos.^2))*h;
end
% D4 tendon-force objective (report; NOT equated to strain risk)
if wJ(15) ~= 0
    J = J + pScaleTdn.*wJ(15).*B(j+1)*(sum(FTkj(parHamBi).^2))*h;   % or FTtildekj_nsc
end
% D2 active-eccentric objective (needs vMtildekj; smoothpos(vM)=lengthening only)
if wJ(16) ~= 0
    vMpos = 0.5*(vMtildekj(parHamBi) + sqrt(vMtildekj(parHamBi).^2 + 1e-3^2));
    ecc   = Fcekj(parHamBi) .* vMpos;      % active eccentric power (W); >0 only when lengthening
    J = J + pScaleEcc.*wJ(16).*B(j+1)*(sum(ecc))*h;   % integral = active negative work (J)
end
% D5 composite (nondimensionalize each term by its nominal value, documented weights)
if wJ(17) ~= 0
    lenT = sum((0.5*((lMtildekj(parHamBi)-1)+sqrt((lMtildekj(parHamBi)-1).^2+1e-3^2))).^2)/nomLen;
    pasT = sum(pasPos.^2)/nomPas;  eccT = sum(ecc)/nomEcc;
    J = J + wJ(17).*B(j+1)*(cLen*lenT + cPas*pasT + cEcc*eccT)*h;   % weight sets below
end
```
`pScale*`/`nom*` are fixed calibration constants (mirror `parScale=1e4`): choose so each raw
integrated term ≈ the length term's magnitude at the Nominal optimum, and **document them**.

## D5 composite weight sets (compare, do not pick one arbitrarily)
`equal` (cLen=cPas=cEcc=1) · `length-dominant` (cLen=2) · `active-eccentric-dominant` (cEcc=2) ·
`passive-dominant` (cPas=2). Encode as a suffix token, e.g. `_HamCompEQ_/_LEN_/_ECC_/_PAS_`.

## Search plan
1. **N=50 exploration** for D2/D3/D4/D5 (all weight sets), reuse `run_ham_pareto_N100.m` structure
   (new tokens; forward continuation from Nominal N=50 base which has duals).
2. **N=100 multi-start** ONLY for the paper candidates: baseline (D0), length (D1, done),
   active-eccentric (D2 primary), composite (D5 primary) — 3 inits each (forward / from-Nominal /
   backward), same checkpoint pattern.

## Phase E — matched-speed (ε-constraint) comparison
Instead of (or alongside) weighted-sum, minimize a load surrogate s.t. **speed ≥ 0.995 × mesh-matched
baseline**:
- Add ONE inequality `g_speed = ave_speed - 0.995*speed_base ≥ 0` to the constraint set (near the
  performance/periodicity constraints). This changes the NLP dimension by +1 → **skip the dual
  warm-start** for these runs (use primal-only, exactly like `tdStudy`; see main ~L1091/L1119 guards).
- Report per candidate: achieved speed, speed loss %, achieved pelvis/hip/knee/trunk, all surrogates,
  solver status, constraint residual, mesh, init, runtime.
- Tests to run on the outputs (Phase E questions): does lowering length also lower tension/work? do
  the objectives trade off? does one motion improve all? is any metric improved at another's expense?
  is the reduction explained by speed drop alone (compare at equalized speed)?

## Guardrails
- Keep every edit ASCII-only (R2017b). Gate on `wJ(k)~=0` so `w0000` is byte-identical to baseline.
- Validate `w0000` self-consistency FIRST for each new objective (must reproduce the baseline).
- Tendon-force objective (D4): report only; state it is not hamstring-strain risk per se.
- Do not run Phase D/E while the Phase-2 sweep is using MATLAB (one heavy job at a time).
