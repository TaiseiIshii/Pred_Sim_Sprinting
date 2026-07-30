function run_ham_pareto_sweep(conditions, N)
% RUN_HAM_PARETO_SWEEP  Sweep runner for the injury-minimising optimal-technique
% study (Research Questions 3 & 4: prescriptive speed<->safety trade-off and
% individualised technique-vs-training comparison).
%
% Each condition adds a smooth biarticular-hamstring fascicle-OVERSTRETCH
% penalty (wJ(13)) to the SAME maximal-sprinting objective and re-optimises,
% tracing the Pareto frontier between top speed and peak fascicle strain:
%
%   _HamPareto_[Nom|Sh|Wk]_wXXXX  -> wJ(13) = XXXX/1000
%       Nom = nominal athlete; Sh = short fascicle (lMo x0.80);
%       Wk = weak (Fmax x0.80). wXXXX = 0000 => penalty off (self-consistency).
%
% The kinematic task, bounds and constraints are byte-for-byte identical to
% Nominal (only the objective and, for Sh/Wk, the hamstring parameters change),
% so the NLP dimensions match and every condition warm-starts (primal+dual).
% CONTINUATION: run weights in INCREASING order so each point warm-starts from
% the previous (smaller-weight) same-athlete solution; the first point of a
% family warm-starts from that athlete's unpenalised base (Nominal / the RQ2
% HamFascicle_m20 / HamStrength_m20 solution). This ordering is the caller's
% responsibility -- keep each family's list monotonic in weight.
%
% Optional 2nd arg N sets the mesh size (default 50). N=100 requires a matching
% N=100 base (Nominal / RQ2) to already exist for the warm start.
%
% Usage:
%   run_ham_pareto_sweep                                       % nominal pilot
%   run_ham_pareto_sweep({'_HamPareto_Nom_w0000','_HamPareto_Nom_w0200'})
%   run_ham_pareto_sweep({'_HamPareto_Sh_w0000','_HamPareto_Sh_w0800'})
%
% Convergence status is NOT inferred here; it is read from optimumOutput.stats
% by the analysis (analysis/analyze_ham_pareto.py). This runner only sequences
% runs, logs timing, and continues past any error.

if nargin < 1 || isempty(conditions)
    % Default = nominal-athlete pilot (de-risk the penalty term first): the
    % w0000 self-consistency control MUST reproduce the N=50 Nominal, then two
    % non-zero weights confirm the penalty lowers peak fascicle strain.
    conditions = {'_HamPareto_Nom_w0000', '_HamPareto_Nom_w0200', '_HamPareto_Nom_w0800'};
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

logDir   = fullfile(projRoot,'Results','HamPareto_Study');
if ~exist(logDir,'dir'); mkdir(logDir); end
logFile  = fullfile(logDir,'sweep_log.txt');

fid = fopen(logFile,'a');
fprintf(fid,'\n===== Ham-Pareto sweep started %s (N=%d) =====\n', datestr(now), N);
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
    fprintf(fid,'%s | %-24s | %-9s | %6.1f min | %s\n', ...
        datestr(now), cond, status, elapsedMin, errMsg);
    fclose(fid);
    fprintf('### %s %s in %.1f min\n', cond, status, elapsedMin);
end

fprintf('\n=== Ham-Pareto sweep finished. Log: %s ===\n', logFile);
end
