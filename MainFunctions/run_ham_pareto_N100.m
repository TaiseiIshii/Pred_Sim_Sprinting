function run_ham_pareto_N100(resume)
% RUN_HAM_PARETO_N100  Phase-2 driver: N=100, multi-start speed-load Pareto for the
% NOMINAL athlete, with per-condition CHECKPOINTING (completed solves are never lost)
% and PROVENANCE logging (each solve records its exact initial-guess / continuation path).
%
% Weights {0, 0.05, 0.10, 0.20}. Initialisations (genuinely different guesses, NOT renamed
% duplicates):
%   (F) forward continuation : w0000<-NominalN100, w0050<-w0000, w0100<-w0050, w0200<-w0100
%   (B) from-Nominal          : w0100 and w0200 warm-started DIRECTLY from Nominal N100
%   (C) backward continuation : w0100 warm-started from the w0200 N100 solution
% The 3rd arg of main_pred_sim_sprinting (warmStartFile) forces (B)/(C); (F) uses the
% automatic newest-strict selection.
%
% CHECKPOINT: Results/HamPareto_N100/checkpoint.csv records every job (tag, cond, init,
% ws_file, out_file, solver_status, speed, td_tilt, iters, runtime_min, timestamp). On
% re-run, jobs whose tag already has a Solve_Succeeded row are SKIPPED. Pass resume=false
% to force re-run of all jobs.
%
% Usage:   run_ham_pareto_N100            % run/continue the checkpointed sweep
%          run_ham_pareto_N100(false)     % ignore checkpoint, run everything
%
% This driver only sequences solves, logs, and continues past errors. Convergence is read
% from optimumOutput.stats (never inferred here).

if nargin < 1 || isempty(resume); resume = true; end

mainDir  = fileparts(mfilename('fullpath'));
projRoot = fileparts(mainDir);
addpath(projRoot); addpath(mainDir);
addpath(fullfile(projRoot,'ExternalFunctions')); addpath(fullfile(projRoot,'MuscleModel'));
addpath(fullfile(projRoot,'Polynomials'));       addpath(fullfile(projRoot,'CollocationScheme'));
addpath(fullfile(projRoot,'UtilityFunctions'));  addpath(fullfile(projRoot,'OpenSimModel'));

% CasADi (provides external/collocation_points) MUST be on the path. setup_paths.m only does
% 'import casadi.*' assuming CasADi is already added (historically via a now-stale pathdef.m).
if isempty(which('casadiMEX'))
    casadiRoots = {'C:\casadi', fullfile(projRoot,'casadi'), fullfile(getenv('USERPROFILE'),'casadi')};
    for iR = 1:numel(casadiRoots)
        if exist(fullfile(casadiRoots{iR},'+casadi'),'dir'); addpath(casadiRoots{iR}); break; end
    end
end
if isempty(which('casadiMEX'))
    error('CasADi not found on the MATLAB path (looked in C:\\casadi etc). Add CasADi first.');
end
fprintf('[precheck] CasADi = %s\n', fileparts(which('casadiMEX')));

resultsDir = fullfile(projRoot,'Results');
outDir     = fullfile(resultsDir,'HamPareto_N100');
if ~exist(outDir,'dir'); mkdir(outDir); end
ckptFile = fullfile(outDir,'checkpoint.csv');
logFile  = fullfile(outDir,'run_N100.log');

% --- precheck: main accepts 3 args, and a strict N=100 Nominal base exists with duals ---
if nargin('main_pred_sim_sprinting') < 3
    error('main_pred_sim_sprinting must accept the 3rd (warmStartFile) arg; update main first.');
end
nomN100 = local_find_strict(resultsDir, '*Nominal.mat', 100, true);
if isempty(nomN100)
    error('No strict N=100 Nominal base with saved duals found. Run main_pred_sim_sprinting_N100 first.');
end
fprintf('[precheck] N=100 Nominal base = %s\n', nomN100);

% --- job list (tag, condition, init label, explicit warm-start file or '') ---------------
% ws='' -> automatic newest-strict continuation (forward pass). ws=NOMINAL/W0200 -> override.
J = { ...
  'w0000_F', '_HamPareto_Nom_w0000', 'forward_from_NominalN100',   ''; ...
  'w0050_F', '_HamPareto_Nom_w0050', 'forward_cont_from_w0000',    ''; ...
  'w0100_F', '_HamPareto_Nom_w0100', 'forward_cont_from_w0050',    ''; ...
  'w0200_F', '_HamPareto_Nom_w0200', 'forward_cont_from_w0100',    ''; ...
  'w0100_B', '_HamPareto_Nom_w0100', 'from_NominalN100',           nomN100; ...
  'w0200_B', '_HamPareto_Nom_w0200', 'from_NominalN100',           nomN100; ...
  'w0100_C', '_HamPareto_Nom_w0100', 'backward_cont_from_w0200',   'DEFER_W0200'; ...
};

if ~exist(ckptFile,'file')
    fid = fopen(ckptFile,'w');
    fprintf(fid,'tag,condition,init_method,ws_file,out_file,solver_status,speed_mps,td_tilt_deg,iters,runtime_min,timestamp\n');
    fclose(fid);
end
done = local_done_tags(ckptFile, resume);

fid = fopen(logFile,'a');
fprintf(fid,'\n===== N=100 Pareto multi-start started %s =====\n', datestr(now));
fclose(fid);

for j = 1:size(J,1)
    tag = J{j,1}; cond = J{j,2}; initm = J{j,3}; ws = J{j,4};
    if any(strcmp(done, tag))
        fprintf('### [%d/%d] SKIP %s (already Solve_Succeeded in checkpoint)\n', j, size(J,1), tag);
        continue;
    end
    if strcmp(ws,'DEFER_W0200')   % resolve backward-continuation base at runtime
        ws = local_find_strict(resultsDir, '*HamPareto_Nom_w0200.mat', 100, true);
        if isempty(ws)
            fprintf('### [%d/%d] SKIP %s (no strict w0200 N=100 yet for backward cont.)\n', j, size(J,1), tag);
            continue;
        end
    end
    fprintf('\n############################################################\n');
    fprintf('### [%d/%d] %s  cond=%s  init=%s\n', j, size(J,1), tag, cond, initm);
    if ~isempty(ws); fprintf('###        ws=%s\n', ws); end
    fprintf('############################################################\n');
    t0 = tic; status = 'ERRORED'; outFile = ''; spd = NaN; tdt = NaN; iters = -1; emsg = '';
    try
        cd(mainDir);
        if isempty(ws)
            main_pred_sim_sprinting(cond, 100);
        else
            main_pred_sim_sprinting(cond, 100, ws);
        end
        [outFile, status, spd, tdt, iters] = local_newest_result(resultsDir, cond);
    catch ME
        emsg = ME.message;
        fprintf('### ERROR %s: %s\n', tag, emsg);
    end
    rt = toc(t0)/60;
    fid = fopen(ckptFile,'a');
    fprintf(fid,'%s,%s,%s,%s,%s,%s,%.5f,%.4f,%d,%.2f,%s\n', tag, cond, initm, ...
        local_bn(ws), local_bn(outFile), status, spd, tdt, iters, rt, datestr(now,'yyyy-mm-ddTHH:MM:SS'));
    fclose(fid);
    fid = fopen(logFile,'a');
    fprintf(fid,'%s | %-9s | %-26s | %-22s | %6.1f min | %s\n', datestr(now), tag, cond, status, rt, emsg);
    fclose(fid);
    fprintf('### %s -> %s (%.1f min)  out=%s\n', tag, status, rt, local_bn(outFile));
end
fprintf('\n=== N=100 Pareto sweep finished. checkpoint=%s ===\n', ckptFile);
end

% ------------------------------------------------------------------ helpers
function p = local_find_strict(resultsDir, pat, N, needDuals)
% newest strict (Solve_Succeeded) result matching pat at mesh N (optionally with saved duals)
d = dir(fullfile(resultsDir, ['pred_sprinting_data_' pat]));
p = ''; best = -inf;
for i = 1:numel(d)
    try
        t = load(fullfile(d(i).folder,d(i).name),'optimumOutput'); o = t.optimumOutput;
        ok = isfield(o,'options') && o.options.N==N && isfield(o,'stats') && ...
             isfield(o.stats,'return_status') && strcmp(o.stats.return_status,'Solve_Succeeded');
        if needDuals; ok = ok && isfield(o,'lam_x_opt') && isfield(o,'lam_g_opt'); end
        if ok && d(i).datenum > best; best = d(i).datenum; p = fullfile(d(i).folder,d(i).name); end
    catch
    end
end
end

function [p, status, spd, tdt, iters] = local_newest_result(resultsDir, cond)
tok = cond; if tok(1)=='_'; tok = tok(2:end); end
d = dir(fullfile(resultsDir, ['pred_sprinting_data_*' tok '.mat']));
p = ''; status = 'unknown'; spd = NaN; tdt = NaN; iters = -1; best = -inf;
for i = 1:numel(d)
    if d(i).datenum > best; best = d(i).datenum; p = fullfile(d(i).folder,d(i).name); end
end
if ~isempty(p)
    try
        t = load(p,'optimumOutput'); o = t.optimumOutput;
        if isfield(o,'stats') && isfield(o.stats,'return_status'); status = o.stats.return_status; end
        if isfield(o,'stats') && isfield(o.stats,'iter_count'); iters = o.stats.iter_count; end
        if isfield(o,'ave_speed'); spd = o.ave_speed; end
        if isfield(o,'optVars_nsc') && isfield(o.optVars_nsc,'q'); tdt = rad2deg(o.optVars_nsc.q(1,1)); end
    catch
    end
end
end

function tags = local_done_tags(ckptFile, resume)
tags = {};
if ~resume; return; end
try
    fid = fopen(ckptFile,'r'); C = textscan(fid,'%s','Delimiter','\n'); fclose(fid); L = C{1};
    for i = 2:numel(L)
        parts = strsplit(L{i}, ',');
        if numel(parts) >= 6 && strcmp(parts{6},'Solve_Succeeded'); tags{end+1} = parts{1}; end %#ok<AGROW>
    end
catch
end
end

function s = local_bn(p)
if isempty(p); s = ''; else; [~,n,e] = fileparts(p); s = [n e]; end
end
