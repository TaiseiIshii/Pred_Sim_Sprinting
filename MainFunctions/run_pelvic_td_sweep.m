function run_pelvic_td_sweep(conditions, N)
% RUN_PELVIC_TD_SWEEP  Sweep runner for the pelvic-tilt CAUSAL study v3 (TDPT).
%
% Optional 2nd arg N sets the mesh size (default 50). N=100 runs the mesh-
% convergence sweep; the matching N=100 Nominal must already exist (it is the
% warm-start and the touchdown-tilt reference).
%
% Method TDPT ("Touchdown Pelvic Tilt"): each condition adds a SINGLE equality
% constraint at the touchdown (initial) node pinning pelvis_tilt to the Nominal
% touchdown tilt PLUS a constant offset, and touches NOTHING else. pelvis_tilt
% is free at every other node; hip flexion, lumbar and the whole sprint
% re-optimise NATURALLY to maximise speed. This mirrors the original HTD/IKTD
% method exactly (one scalar touchdown equality), so it is the cleanest single-
% intervention causal design. No initial-guess compensation, no per-node pin,
% strict IPOPT settings (same as Nominal/HTD/IKTD), warm-started (primal) from
% the converged N=50 Nominal.
%
% Usage:
%   run_pelvic_td_sweep                          % full sweep (p0,m2..m6,p2..p6)
%   run_pelvic_td_sweep({'_PelvisTD_m6','_PelvisTD_p6'})  % pilot (extremes)
%   run_pelvic_td_sweep({'_PelvisTD_p0'})        % single condition
%
% Every condition warm-starts from the SAME Nominal solution (not from each
% other), so order is irrelevant for convergence. Convergence status is NOT
% inferred here; it is read from optimumOutput.stats by the analysis script.
% This runner only sequences runs, logs timing, and continues past any error.

if nargin < 1 || isempty(conditions)
    conditions = {'_PelvisTD_p0', ...
                  '_PelvisTD_m2', '_PelvisTD_m4', '_PelvisTD_m6', ...
                  '_PelvisTD_p2', '_PelvisTD_p4', '_PelvisTD_p6'};
end
if nargin < 2 || isempty(N)
    N = 50;                 % default mesh; [] passed to main -> main keeps 50
end

mainDir  = fileparts(mfilename('fullpath'));        % MainFunctions
projRoot = fileparts(mainDir);

% Fresh headless MATLAB sessions may call this runner directly. Add the
% required top-level folders to the path (recursive genpath is slow at start).
addpath(projRoot);
addpath(fullfile(projRoot,'MainFunctions'));
addpath(fullfile(projRoot,'ExternalFunctions'));
addpath(fullfile(projRoot,'MuscleModel'));
addpath(fullfile(projRoot,'Polynomials'));
addpath(fullfile(projRoot,'CollocationScheme'));
addpath(fullfile(projRoot,'UtilityFunctions'));
addpath(fullfile(projRoot,'OpenSimModel'));

logDir   = fullfile(projRoot,'Results','PelvicTD_Study');
if ~exist(logDir,'dir'); mkdir(logDir); end
logFile  = fullfile(logDir,'sweep_log.txt');

fid = fopen(logFile,'a');
fprintf(fid,'\n===== Pelvic TD (TDPT) sweep started %s (N=%d) =====\n', datestr(now), N);
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
        main_pred_sim_sprinting(cond, N);
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

fprintf('\n=== Pelvic TD sweep finished. Log: %s ===\n', logFile);
end
