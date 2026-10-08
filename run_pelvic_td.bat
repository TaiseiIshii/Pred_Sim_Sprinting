@echo off
REM ============================================================
REM Pelvic-tilt causal study v3 = TDPT (Touchdown Pelvic Tilt)
REM Headless runner (Windows / MATLAB R2017b - NO -batch, use -r).
REM Robust against PowerShell line-corruption: cmd reads from disk.
REM Usage:
REM   run_pelvic_td.bat pilot     - m6,p6 (de-risk extremes first)
REM   run_pelvic_td.bat full      - p0,m2,m4,m6,p2,p4,p6 (all 7)
REM   run_pelvic_td.bat validate  - single condition m6
REM   run_pelvic_td.bat analyze   - run the v3 analysis (MATLAB metrics+CSV)
REM   run_pelvic_td.bat n100      - ALL 8 wide conditions at N=100 (mesh check)
REM ============================================================
setlocal
set MODE=%1
if "%MODE%"=="" set MODE=pilot
set NARG=

set MAINDIR=%~dp0Pred_Sim_Sprinting\MainFunctions
set ANADIR=%~dp0Pred_Sim_Sprinting\analysis
set LOGDIR=%~dp0Pred_Sim_Sprinting\Results\PelvicTD_Study
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

if "%MODE%"=="analyze" (
  cd /d "%ANADIR%"
  matlab -nosplash -nodesktop -wait -r "diary(fullfile('%LOGDIR%','analyze.log')); diary on; try; analyze_pelvic_td; catch e; disp(getReport(e)); end; diary off; exit"
  endlocal
  goto :eof
)

cd /d "%MAINDIR%"

if "%MODE%"=="validate" (
  set CONDS={'_PelvisTD_m6'}
) else if "%MODE%"=="pilot" (
  set CONDS={'_PelvisTD_m6','_PelvisTD_p6'}
) else if "%MODE%"=="full" (
  set CONDS={'_PelvisTD_p0','_PelvisTD_m2','_PelvisTD_m4','_PelvisTD_m6','_PelvisTD_p2','_PelvisTD_p4','_PelvisTD_p6'}
) else if "%MODE%"=="remaining" (
  set CONDS={'_PelvisTD_p0','_PelvisTD_m2','_PelvisTD_m4','_PelvisTD_p2','_PelvisTD_p4'}
) else if "%MODE%"=="wide" (
  set CONDS={'_PelvisTDwide_m4','_PelvisTDwide_m6','_PelvisTDwide_m8'}
) else if "%MODE%"=="widefill" (
  set CONDS={'_PelvisTDwide_m2','_PelvisTDwide_p0'}
) else if "%MODE%"=="n100" (
  set CONDS={'_PelvisTDwide_m8','_PelvisTDwide_m6','_PelvisTDwide_m4','_PelvisTDwide_m2','_PelvisTDwide_p0','_PelvisTDwide_p2','_PelvisTDwide_p4','_PelvisTDwide_p6'}
  set NARG=,100
) else (
  set CONDS={'_PelvisTD_m6','_PelvisTD_p6'}
)

matlab -nosplash -nodesktop -wait -r "diary(fullfile('%LOGDIR%','run_%MODE%.log')); diary on; try; run_pelvic_td_sweep(%CONDS%%NARG%); catch e; disp(getReport(e)); end; diary off; exit"
endlocal
