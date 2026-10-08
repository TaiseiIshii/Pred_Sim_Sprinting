@echo off
REM ============================================================
REM Injury-minimising optimal-technique study (Research Q3 + Q4)
REM Adds a smooth biarticular-hamstring fascicle-overstretch penalty
REM (wJ(13)) to the maximal-sprint objective and sweeps its weight to
REM trace the speed<->peak-fascicle-strain PARETO frontier, optionally
REM on an at-risk virtual athlete (short fascicle / weak).
REM Headless runner (Windows / MATLAB - use -r, robust to disk read).
REM Weights are run in INCREASING order for warm-start continuation.
REM Usage:
REM   run_ham_pareto.bat pilot     - nominal w0000,w0200,w0800 (de-risk first)
REM   run_ham_pareto.bat nominal   - full nominal frontier (8 weights)
REM   run_ham_pareto.bat short     - short-fascicle athlete (4 weights)
REM   run_ham_pareto.bat weak      - weak athlete (4 weights)
REM   run_ham_pareto.bat athletes  - short + weak (8 conds)
REM   run_ham_pareto.bat full      - nominal + short + weak (16 conds)
REM   run_ham_pareto.bat analyze   - Pareto frontier analysis (Python)
REM ============================================================
setlocal
set MODE=%1
if "%MODE%"=="" set MODE=pilot
set NARG=

set MAINDIR=%~dp0Pred_Sim_Sprinting\MainFunctions
set ANADIR=%~dp0Pred_Sim_Sprinting\analysis
set LOGDIR=%~dp0Pred_Sim_Sprinting\Results\HamPareto_Study
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

if "%MODE%"=="analyze" (
  cd /d "%ANADIR%"
  python analyze_ham_pareto.py
  endlocal
  goto :eof
)

cd /d "%MAINDIR%"

if "%MODE%"=="pilot" (
  set CONDS={'_HamPareto_Nom_w0000','_HamPareto_Nom_w0200','_HamPareto_Nom_w0800'}
) else if "%MODE%"=="nominal" (
  set CONDS={'_HamPareto_Nom_w0000','_HamPareto_Nom_w0050','_HamPareto_Nom_w0100','_HamPareto_Nom_w0200','_HamPareto_Nom_w0400','_HamPareto_Nom_w0800','_HamPareto_Nom_w1600','_HamPareto_Nom_w3200'}
) else if "%MODE%"=="short" (
  set CONDS={'_HamPareto_Sh_w0000','_HamPareto_Sh_w0200','_HamPareto_Sh_w0800','_HamPareto_Sh_w3200'}
) else if "%MODE%"=="weak" (
  set CONDS={'_HamPareto_Wk_w0000','_HamPareto_Wk_w0200','_HamPareto_Wk_w0800','_HamPareto_Wk_w3200'}
) else if "%MODE%"=="athletes" (
  set CONDS={'_HamPareto_Sh_w0000','_HamPareto_Sh_w0200','_HamPareto_Sh_w0800','_HamPareto_Sh_w3200','_HamPareto_Wk_w0000','_HamPareto_Wk_w0200','_HamPareto_Wk_w0800','_HamPareto_Wk_w3200'}
) else if "%MODE%"=="full" (
  set CONDS={'_HamPareto_Nom_w0000','_HamPareto_Nom_w0050','_HamPareto_Nom_w0100','_HamPareto_Nom_w0200','_HamPareto_Nom_w0400','_HamPareto_Nom_w0800','_HamPareto_Nom_w1600','_HamPareto_Nom_w3200','_HamPareto_Sh_w0000','_HamPareto_Sh_w0200','_HamPareto_Sh_w0800','_HamPareto_Sh_w3200','_HamPareto_Wk_w0000','_HamPareto_Wk_w0200','_HamPareto_Wk_w0800','_HamPareto_Wk_w3200'}
) else (
  set CONDS={'_HamPareto_Nom_w0000','_HamPareto_Nom_w0200','_HamPareto_Nom_w0800'}
)

matlab -nosplash -nodesktop -wait -r "diary(fullfile('%LOGDIR%','run_%MODE%.log')); diary on; try; run_ham_pareto_sweep(%CONDS%%NARG%); catch e; disp(getReport(e)); end; diary off; exit"
endlocal
