@echo off
REM ============================================================
REM Pelvic Tilt strain study - headless runner (Windows / R2017b)
REM Usage:
REM   run_pelvic_tilt.bat validate   - single condition machinery check
REM   run_pelvic_tilt.bat sweep      - full N=50 sweep (default)
REM ============================================================
setlocal
set MODE=%1
if "%MODE%"=="" set MODE=sweep

set MAINDIR=%~dp0Pred_Sim_Sprinting\MainFunctions
set LOGDIR=%~dp0Pred_Sim_Sprinting\Results\PelvicTilt_Study

cd /d "%MAINDIR%"
matlab -nosplash -nodesktop -wait -r "diary(fullfile('%LOGDIR%','run_%MODE%.log')); diary on; try; run_pelvic_tilt_launcher('%MODE%'); catch e; disp(getReport(e)); end; diary off; exit"
endlocal
