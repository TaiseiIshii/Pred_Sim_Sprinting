function run_ham_arch_sweep(conditions, N)
% RUN_HAM_ARCH_SWEEP  Sweep runner for the hamstring muscle-architecture study
% (Research Question 2: epidemiology<->biomechanics bridge / individualisation).
%
% Each condition scales ONLY the hamstring muscle-tendon parameters, creating
% "virtual athletes" that span the principal MODIFIABLE epidemiological HSI
% risk factors, then re-optimises the SAME maximal-sprinting task:
%
%   _HamFascicle_[mp]NN  -> hamstring optimal FIBRE length x (1 -/+ NN/100)
%                           (short fascicles = Timmins 2016 top risk factor)
%   _HamStrength_[mp]NN  -> hamstring maximal isometric FORCE x (1 -/+ NN/100)
%                           (weakness = classic HSI risk factor)
%
% m = minus (shorter / weaker = HIGHER modelled risk), p = plus. The kinematic
% task, bounds and constraints are byte-for-byte identical to Nominal, so the
% NLP dimensions match and every condition warm-starts (primal+dual) from the
% SAME strict Nominal solution. Speed and fascicle-strain differences are then
% attributable purely to the manipulated muscle architecture.
%
% Optional 2nd arg N sets the mesh size (default 50). N=100 runs the mesh-
% convergence sweep; the matching N=100 Nominal must already exist (warm-start).
%
% Usage:
%   run_ham_arch_sweep                                   % fascicle family (default)
%   run_ham_arch_sweep({'_HamFascicle_m20','_HamFascicle_p20'})   % pilot extremes
%   run_ham_arch_sweep({'_HamStrength_m30'})             % single strength condition
%
% Convergence status is NOT inferred here; it is read from optimumOutput.stats
% by the analysis (analysis/injury_metrics.py). This runner only sequences
% runs, logs timing, and continues past any error.

if nargin < 1 || isempty(conditions)
    % Default = primary RQ2 fascicle-length family (incl. p00 self-consistency
    % control, which re-solves Nominal with the architecture machinery active
    % at factor 1.0 and should reproduce the Nominal result).
    conditions = {'_HamFascicle_m30', '_HamFascicle_m20', '_HamFascicle_m10', ...
                  '_HamFascicle_p00', '_HamFascicle_p10', '_HamFascicle_p20'};
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

logDir   = fullfile(projRoot,'Results','HamArch_Study');
if ~exist(logDir,'dir'); mkdir(logDir); end
logFile  = fullfile(logDir,'sweep_log.txt');

fid = fopen(logFile,'a');
fprintf(fid,'\n===== Hamstring-architecture sweep started %s (N=%d) =====\n', datestr(now), N);
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
    fprintf(fid,'%s | %-22s | %-9s | %6.1f min | %s\n', ...
        datestr(now), cond, status, elapsedMin, errMsg);
    fclose(fid);
    fprintf('### %s %s in %.1f min\n', cond, status, elapsedMin);
end

fprintf('\n=== Hamstring-architecture sweep finished. Log: %s ===\n', logFile);
end
