# RESUME PROMPT — continuation state for the thesis-freeze task

Use this to resume if the session ends. Read `docs/FINAL_STUDY_PLAN.md` for the full plan and
`/memories/session/final_study_state.md` (session memory) for the working log.

## Repo state
- HEAD `bb0433af` (`main`). Working tree has **uncommitted** new/edited files (do NOT discard):
  new: `docs/{FINAL_STUDY_PLAN,PROVENANCE,DATA_AVAILABILITY,PHASE_A_MUSCLE_TENSION_REPORT,RESUME_PROMPT}.md`,
  `analysis/validation/{add_provenance,data_inventory,test_unit_metrics,phaseA_muscle_tension}.py`,
  `MainFunctions/run_ham_pareto_N100.m`; edited: `MainFunctions/main_pred_sim_sprinting.m`
  (additive optional 3rd arg `warmStartFile_in`), `analysis/validation/test_ham_load_metrics.py`
  (graceful skip), `docs/{VALIDATION_FINAL_REPORT,VALIDATION_MASTER_PLAN,CLAIM_EVIDENCE_MATRIX}.md`
  (provenance), plus new CSVs/figs in `Results/Validation_Master/`.
- No git commits/pushes were made (per task rules; awaiting human).

## RUNNING JOB (Phase 2): N=100 multi-start Pareto
- Launched: MATLAB R2017b background, `run_ham_pareto_N100`.
- Console log: `Results/HamPareto_N100/matlab_console.log`
- Checkpoint (authoritative): `Results/HamPareto_N100/checkpoint.csv` (one row per completed job)
- Output MATs: `Results/pred_sprinting_data_*HamPareto_Nom_w0*.mat` (mesh N=100)
- Jobs (7), each ~0.5–1.5 h at N=100 (+ ~10–15 min MATLAB cold start once):
  1. `w0000_F` self-consistency (from Nominal N100)  2. `w0050_F`  3. `w0100_F`  4. `w0200_F`
  (forward continuation);  5. `w0100_B` (from Nominal N100)  6. `w0200_B` (from Nominal N100)
  7. `w0100_C` (backward from w0200)  → gives w0.1 THREE independent inits (F/B/C) + w0.2 two.
- ETA: ~4–10 h wall. Completed jobs are checkpointed and never re-run.

### To check progress
```powershell
Get-Content "C:\Users\T11648sTb\Documents\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting\Results\HamPareto_N100\checkpoint.csv"
Get-Content "C:\Users\T11648sTb\Documents\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting\Results\HamPareto_N100\matlab_console.log" -Tail 40
Get-Process matlab -ErrorAction SilentlyContinue   # still running?
```
### To resume the sweep (safe, skips completed jobs)
```powershell
& "C:\Program Files\MATLAB\R2017b\bin\matlab.exe" -nosplash -nodesktop -minimize -wait `
  -logfile "...\Results\HamPareto_N100\matlab_console.log" `
  -r "cd('...\MainFunctions'); run_ham_pareto_N100; exit"
```
Do NOT kill a running MATLAB (a solve in progress will be lost; completed ones are safe).

## After the N=100 solves complete
1. Rebuild the manifest to include the new N=100 Pareto MATs, then re-hash:
   `python analysis/validation/build_manifest.py` (if it scans Results) **or** extend it; then
   `python analysis/validation/add_provenance.py`.
2. Re-run the Pareto analysis at N=100 and multi-start reproducibility:
   `python analysis/validation/pareto_and_robustness.py` (add an N=100 branch — see plan Phase 2).
3. Apply the Phase-2.4 pass/fail gates to `w=0.1` (strict; |Δspeed|≤0.5%; surrogate ≤−3%;
   non-dominated; |load N50−N100|≤2 pp; |Δspeed N50−N100|≤0.5 pp; ≥2/3 inits same basin).
   If it fails, downgrade to exploratory/mesh-sensitive/init-sensitive and pick the most
   reproducible Pareto point. Record in `PAPER_RESULTS_FREEZE.md`.

## NOT YET DONE (highest-priority remaining, no new compute needed for most)
- Phase 4/5: finish claim-language audit across README, Conference_Poster_Plan,
  Epidemiological_Concordance_Report, LITERATURE_COMPARISON, integrated reports.
- Phase B: `docs/LITERATURE_QUANTITATIVE_COMPARISON.md` (definition-level; to-acquire list).
- Phase C: `docs/OPT_ON_OFF_INTERPRETATION.md` (tree-rigid / femur-fixed / adaptive).
- Phase F: per-muscle numeric conclusions (from `phaseA_verdicts.csv`).
- Phase 6: `docs/PAPER_RESULTS_FREEZE.md`, `docs/THESIS_OUTLINE_JP.md`, abstracts (JP/EN),
  Figures 1–5 assembly.
- Phase D/E (NEW COMPUTE, lower priority): tension-based objectives + matched-speed comparison —
  design in plan; implement penalty variants guarded like wJ(13); run N=50 then N=100 primary.

## Freeze is HELD until: Phase A done (DONE), N=100 Pareto status known, claim audit done,
literature definition-consistency done, per-muscle conclusions done, freeze/outline/abstracts done.
