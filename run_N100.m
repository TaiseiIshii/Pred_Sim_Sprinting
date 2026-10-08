% Run N=100 simulation script
try
    cd('c:\Users\T11648sTb\Documents\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting\MainFunctions');
    fprintf('=== Starting N=100 simulation ===\n');
    fprintf('OMP_NUM_THREADS: %s\n', getenv('OMP_NUM_THREADS'));
    fprintf('%s\n', datestr(now));
    tic;
    main_pred_sim_sprinting_N100();
    elapsed = toc;
    fprintf('=== Simulation completed in %.1f minutes ===\n', elapsed/60);
    fprintf('%s\n', datestr(now));
catch ME
    fprintf('ERROR: %s\n', ME.message);
    for i=1:length(ME.stack)
        fprintf('%s : line %d\n', ME.stack(i).file, ME.stack(i).line);
    end
end
exit;
