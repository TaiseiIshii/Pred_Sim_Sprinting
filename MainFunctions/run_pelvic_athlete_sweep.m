function run_pelvic_athlete_sweep(conditions)
% RUN_PELVIC_ATHLETE_SWEEP  Individual x pelvic-tilt CROSS experiment (RQ4 ext).
%
% Combines the PelvisShift pelvic-tilt manipulation with a virtual at-risk
% athlete (short fascicle / weak) via the additive _athSh / _athWk hook in
% main_pred_sim_sprinting. Tests whether the tilt->hamstring-loading response
% (and hence the optimal intervention) differs by muscle architecture.
%
% Naming:  _PelvisShift_mNN_athSh  (short fascicle, oMFL x0.80)
%          _PelvisShift_mNN_athWk  (weak,          Fmax x0.80)
%
% Usage:
%   run_pelvic_athlete_sweep                              % default pilot+sweep
%   run_pelvic_athlete_sweep({'_PelvisShift_m02_athSh'})  % single (pilot)
%
% Each condition warm-starts (dimension-compatible) from the nearest converged
% PelvisShift/Nominal solution. Runs are N=50, ~20-30 min each. Results land in
% Results/ exactly like the plain PelvisShift runs and are analysed by
% analysis/analyze_pelvic_force_eccentric.py (extend its glob to *_ath*).

if nargin < 1 || isempty(conditions)
    conditions = {'_PelvisShift_m02_athSh', ...                     % pilot (short, -2 deg)
                  '_PelvisShift_m04_athSh', '_PelvisShift_p04_athSh', ...
                  '_PelvisShift_m02_athWk', '_PelvisShift_m04_athWk', '_PelvisShift_p04_athWk'};
end

mainDir  = fileparts(mfilename('fullpath'));            % MainFunctions
projRoot = fileparts(mainDir);
addpath(projRoot);
addpath(fullfile(projRoot,'MainFunctions'));
addpath(fullfile(projRoot,'ExternalFunctions'));
addpath(fullfile(projRoot,'MuscleModel'));
addpath(fullfile(projRoot,'Polynomials'));
addpath(fullfile(projRoot,'CollocationScheme'));
addpath(fullfile(projRoot,'UtilityFunctions'));
addpath(fullfile(projRoot,'OpenSimModel'));

logDir = fullfile(projRoot,'Results','PelvicAthlete_Study');
if ~exist(logDir,'dir'); mkdir(logDir); end
logFile = fullfile(logDir,'sweep_log.txt');
fid = fopen(logFile,'a');
fprintf(fid,'\n===== Pelvic ATHLETE cross sweep started %s =====\n', datestr(now));
fprintf(fid,'Conditions: %s\n', strjoin(conditions,', '));
fclose(fid);

for c = 1:numel(conditions)
    cond = conditions{c};
    t0 = tic;
    fprintf('\n############################################################\n');
    fprintf('### [%d/%d] Running combined condition %s\n', c, numel(conditions), cond);
    fprintf('############################################################\n');
    status = 'COMPLETED'; errMsg = '';
    try
        cd(mainDir);
        main_pred_sim_sprinting(cond);
    catch ME
        status = 'ERRORED'; errMsg = ME.message;
        fprintf('### ERROR in %s: %s\n', cond, ME.message);
        for k = 1:numel(ME.stack)
            fprintf('###   %s : line %d\n', ME.stack(k).name, ME.stack(k).line);
        end
    end
    elapsedMin = toc(t0)/60;
    fid = fopen(logFile,'a');
    fprintf(fid,'%s | %-26s | %-9s | %6.1f min | %s\n', ...
        datestr(now), cond, status, elapsedMin, errMsg);
    fclose(fid);
    fprintf('### %s %s in %.1f min\n', cond, status, elapsedMin);
end
fprintf('\n=== Pelvic ATHLETE cross sweep finished. Log: %s ===\n', logFile);
end
