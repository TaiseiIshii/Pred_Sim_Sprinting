function run_pelvic_tilt_sweep(conditions)
% RUN_PELVIC_TILT_SWEEP  Run the predictive sprinting simulation across a set
% of imposed mean pelvic-tilt conditions for the hamstring strain study.
%
% Usage:
%   run_pelvic_tilt_sweep                       % runs the default N=50 sweep
%   run_pelvic_tilt_sweep({'_PelvisTilt_m10'})  % runs a single condition
%
% Each condition is a simulation_type string understood by
% main_pred_sim_sprinting (see the Pelvic Tilt study block near the top of
% that file). Results (.mat/.mot/.sto) are written to the Results folder by
% saveOptimumFiles with the condition name embedded in the filename.
%
% Convergence is NOT inferred here; it is read from optimumOutput.stats in the
% analysis script (analyze_pelvic_tilt.m). This runner only sequences the runs,
% logs timing, and continues past any run that errors.

if nargin < 1 || isempty(conditions)
    % Default sweep: imposed mean pelvis_tilt from neutral (0 deg) to strongly
    % anterior (-13 deg). Nominal self-selected mean is approx -7.5 deg.
    conditions = {'_PelvisTilt_p00', ...   % 0 deg  (neutral)
                  '_PelvisTilt_m04', ...   % -4 deg (mild anterior)
                  '_PelvisTilt_m07', ...   % -7 deg (near nominal)
                  '_PelvisTilt_m10', ...   % -10 deg (more anterior)
                  '_PelvisTilt_m13'};      % -13 deg (strong anterior)
end

mainDir  = fileparts(mfilename('fullpath'));        % MainFunctions
projRoot = fileparts(mainDir);

% Fresh headless MATLAB sessions may call this runner directly, bypassing
% run_pelvic_tilt_launcher. Ensure helpers such as control_extrapolation are
% available before entering main_pred_sim_sprinting.
addpath(projRoot);
addpath(fullfile(projRoot,'MainFunctions'));
addpath(fullfile(projRoot,'ExternalFunctions'));
addpath(fullfile(projRoot,'MuscleModel'));
addpath(fullfile(projRoot,'Polynomials'));
addpath(fullfile(projRoot,'CollocationScheme'));
addpath(fullfile(projRoot,'UtilityFunctions'));
addpath(fullfile(projRoot,'OpenSimModel'));

logDir   = fullfile(projRoot,'Results','PelvicTilt_Study');
if ~exist(logDir,'dir'); mkdir(logDir); end
logFile  = fullfile(logDir,'sweep_log.txt');

fid = fopen(logFile,'a');
fprintf(fid,'\n===== Pelvic tilt sweep started %s =====\n', datestr(now));
fprintf(fid,'Conditions: %s\n', strjoin(conditions,', '));
fclose(fid);

for c = 1:numel(conditions)
    cond = conditions{c};
    t0 = tic;
    fprintf('\n############################################################\n');
    fprintf('### [%d/%d] Running condition %s\n', c, numel(conditions), cond);
    fprintf('############################################################\n');
    status = 'COMPLETED';
    errMsg = '';
    try
        cd(mainDir);                     % main() changes cwd internally
        main_pred_sim_sprinting(cond);
    catch ME
        status = 'ERRORED';
        errMsg = ME.message;
        fprintf('### ERROR in %s: %s\n', cond, ME.message);
        for k = 1:numel(ME.stack)
            fprintf('###   %s : line %d\n', ME.stack(k).name, ME.stack(k).line);
        end
    end
    elapsedMin = toc(t0)/60;
    fid = fopen(logFile,'a');
    fprintf(fid,'%s | %-20s | %-9s | %6.1f min | %s\n', ...
        datestr(now), cond, status, elapsedMin, errMsg);
    fclose(fid);
    fprintf('### %s %s in %.1f min\n', cond, status, elapsedMin);
end

fprintf('\n=== Pelvic tilt sweep finished. Log: %s ===\n', logFile);
end
