@echo off
set OMP_NUM_THREADS=8
del /q "c:\Users\T11648sTb\Documents\VSCODE\Pred_Sim_Sprinting\matlab_N100_sim.log" 2>nul
echo Starting MATLAB N=100 simulation with OMP_NUM_THREADS=%OMP_NUM_THREADS%
matlab -nosplash -nodesktop -logfile "c:\Users\T11648sTb\Documents\VSCODE\Pred_Sim_Sprinting\matlab_N100_sim.log" -r "run('c:\Users\T11648sTb\Documents\VSCODE\Pred_Sim_Sprinting\run_N100.m')"
