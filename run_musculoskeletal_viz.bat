@echo off
REM Robust launcher for the rich musculoskeletal visualization (immune to PowerShell ^U corruption)
set PY=C:\Users\T11648sTb\AppData\Local\miniconda3\python.exe
set SCRIPT=%~dp0Pred_Sim_Sprinting\analysis\visualize_pelvic_shift_musculoskeletal.py
set LOGDIR=%~dp0Pred_Sim_Sprinting\Results\PelvicShift_Study
"%PY%" "%SCRIPT%" %* > "%LOGDIR%\musculoskeletal_render.log" 2>&1
