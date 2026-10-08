@echo off
REM ============================================================
REM Hamstring muscle-architecture study (Research Question 2)
REM Epidemiology<->biomechanics bridge: scale ONLY hamstring
REM muscle-tendon parameters (fascicle length / strength) to make
REM "virtual athletes", then re-optimise the same maximal sprint.
REM Headless runner (Windows / MATLAB - use -r, robust to disk read).
REM Usage:
REM   run_ham_arch.bat pilot      - fascicle extremes m20,p20 (de-risk first)
REM   run_ham_arch.bat fascicle   - fibre-length family m30..p20 (6 conds)
REM   run_ham_arch.bat strength   - strength family m30..p20 (6 conds)
REM   run_ham_arch.bat full       - fascicle + strength families (12 conds)
REM   run_ham_arch.bat validate   - single condition _HamFascicle_m20
REM   run_ham_arch.bat analyze    - fascicle-level injury metrics (Python)
REM   run_ham_arch.bat n100       - fascicle family at N=100 (mesh check)
REM ============================================================
setlocal
set MODE=%1
if "%MODE%"=="" set MODE=pilot
set NARG=

set MAINDIR=%~dp0Pred_Sim_Sprinting\MainFunctions
set ANADIR=%~dp0Pred_Sim_Sprinting\analysis
set LOGDIR=%~dp0Pred_Sim_Sprinting\Results\HamArch_Study
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

if "%MODE%"=="analyze" (
  cd /d "%ANADIR%"
  python injury_metrics.py
  endlocal
  goto :eof
)

cd /d "%MAINDIR%"

if "%MODE%"=="validate" (
  set CONDS={'_HamFascicle_m20'}
) else if "%MODE%"=="pilot" (
  set CONDS={'_HamFascicle_m20','_HamFascicle_p20'}
) else if "%MODE%"=="fascicle" (
  set CONDS={'_HamFascicle_m30','_HamFascicle_m20','_HamFascicle_m10','_HamFascicle_p00','_HamFascicle_p10','_HamFascicle_p20'}
) else if "%MODE%"=="strength" (
  set CONDS={'_HamStrength_m30','_HamStrength_m20','_HamStrength_m10','_HamStrength_p00','_HamStrength_p10','_HamStrength_p20'}
) else if "%MODE%"=="full" (
  set CONDS={'_HamFascicle_m30','_HamFascicle_m20','_HamFascicle_m10','_HamFascicle_p00','_HamFascicle_p10','_HamFascicle_p20','_HamStrength_m30','_HamStrength_m20','_HamStrength_m10','_HamStrength_p00','_HamStrength_p10','_HamStrength_p20'}
) else if "%MODE%"=="n100" (
  set CONDS={'_HamFascicle_m30','_HamFascicle_m20','_HamFascicle_m10','_HamFascicle_p00','_HamFascicle_p10','_HamFascicle_p20'}
  set NARG=,100
) else (
  set CONDS={'_HamFascicle_m20','_HamFascicle_p20'}
)

matlab -nosplash -nodesktop -wait -r "diary(fullfile('%LOGDIR%','run_%MODE%.log')); diary on; try; run_ham_arch_sweep(%CONDS%%NARG%); catch e; disp(getReport(e)); end; diary off; exit"
endlocal
