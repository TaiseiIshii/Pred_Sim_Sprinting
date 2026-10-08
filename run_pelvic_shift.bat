@echo off
REM ============================================================
REM Pelvic SHIFT causal study v2 - headless runner (Windows / R2017b)
REM Robust against PowerShell line-corruption: cmd reads from disk.
REM Usage:
REM   run_pelvic_shift.bat remaining  - m02,m04,m06,p02,p04,p06 (p00 done)
REM   run_pelvic_shift.bat full       - p00..p06 (all 7)
REM   run_pelvic_shift.bat validate   - single condition m02
REM ============================================================
setlocal
set MODE=%1
if "%MODE%"=="" set MODE=remaining

set MAINDIR=%~dp0Pred_Sim_Sprinting\MainFunctions
set LOGDIR=%~dp0Pred_Sim_Sprinting\Results\PelvicShift_Study
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

cd /d "%MAINDIR%"

if "%MODE%"=="validate" (
  set CONDS={'_PelvisShift_m02'}
) else if "%MODE%"=="full" (
  set CONDS={'_PelvisShift_p00','_PelvisShift_m02','_PelvisShift_m04','_PelvisShift_m06','_PelvisShift_p02','_PelvisShift_p04','_PelvisShift_p06'}
) else if "%MODE%"=="missing" (
  set CONDS={'_PelvisShift_m04','_PelvisShift_m06','_PelvisShift_p02','_PelvisShift_p04','_PelvisShift_p06'}
) else (
  set CONDS={'_PelvisShift_m02','_PelvisShift_m04','_PelvisShift_m06','_PelvisShift_p02','_PelvisShift_p04','_PelvisShift_p06'}
)

matlab -nosplash -nodesktop -wait -r "diary(fullfile('%LOGDIR%','run_%MODE%.log')); diary on; try; run_pelvic_shift_sweep(%CONDS%); catch e; disp(getReport(e)); end; diary off; exit"
endlocal
