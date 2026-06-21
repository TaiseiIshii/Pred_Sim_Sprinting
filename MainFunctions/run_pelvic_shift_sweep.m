function run_pelvic_shift_sweep(conditions)
% RUN_PELVIC_SHIFT_SWEEP  Continuation sweep for the pelvic-tilt CAUSAL study v2.
%
% Method B: each condition rigidly offsets the whole pelvis_tilt waveform by a
% constant (experimental reference + offset, pinned per node within a tight
% band). Because only bounds change, every condition is dimension-compatible
% with the Nominal solution and dual-warm-starts from the closest converged run.
%
% Usage:
%   run_pelvic_shift_sweep                      % default continuation order
%   run_pelvic_shift_sweep({'_PelvisShift_p00'})% single condition
%
% The default order goes outward from 0 so each step warm-starts from the
% nearest already-converged solution:
%   p00 -> m02 -> m04 -> m06   (more anterior)
%   p00 -> p02 -> p04 -> p06   (less anterior / toward posterior)
%
% Convergence status is NOT inferred here; it is read from optimumOutput.stats
% by the analysis script. This runner only sequences runs, logs timing, and
% continues past any run that errors.

if nargin < 1 || isempty(conditions)
    conditions = {'_PelvisShift_p00', ...
                  '_PelvisShift_m02', '_PelvisShift_m04', '_PelvisShift_m06', ...
                  '_PelvisShift_p02', '_PelvisShift_p04', '_PelvisShift_p06'};
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

logDir   = fullfile(projRoot,'Results','PelvicShift_Study');
if ~exist(logDir,'dir'); mkdir(logDir); end
logFile  = fullfile(logDir,'sweep_log.txt');

fid = fopen(logFile,'a');
fprintf(fid,'\n===== Pelvic SHIFT sweep started %s =====\n', datestr(now));
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
    fprintf(fid,'%s | %-22s | %-9s | %6.1f min | %s\n', ...
        datestr(now), cond, status, elapsedMin, errMsg);
    fclose(fid);
    fprintf('### %s %s in %.1f min\n', cond, status, elapsedMin);
end

fprintf('\n=== Pelvic SHIFT sweep finished. Log: %s ===\n', logFile);
end
