function run_ham_obj_sweep(conditions, N)
% RUN_HAM_OBJ_SWEEP  Phase D/E driver: explore the tension/work-based objective variants
% (active-eccentric, passive-force, tendon, composite) at N=50, with per-condition CHECKPOINTING
% and PROVENANCE logging. Mirrors run_ham_pareto_N100 but for the new objStudy tokens.
%
% Tokens: _HamEcc_wXXXX (active-eccentric, PRIMARY), _HamPasv_wXXXX, _HamTdn_wXXXX,
%         _HamComp{EQ|ECC|PAS|LEN}_wXXXX. wXXXX=0000 => self-consistency (byte-identical baseline).
%
% Default = active-eccentric exploration with weights spanning 2 orders of magnitude so the
% near-matched-speed region is captured regardless of the provisional penalty scale. Forward
% continuation (each weight warm-starts from the previous). Baseline (w0000) validates the
% implementation first.
%
% Usage:  run_ham_obj_sweep                      % default ecc exploration, N=50
%         run_ham_obj_sweep({'_HamCompEQ_w0100','_HamCompEQ_w0500'})
%         run_ham_obj_sweep({'_HamPasv_w0200'}, 50)
%
% Convergence is read from optimumOutput.stats (never inferred). Continues past errors.

if nargin < 2 || isempty(N); N = 50; end
if nargin < 1 || isempty(conditions)
    conditions = {'_HamEcc_w0000','_HamEcc_w0100','_HamEcc_w0500','_HamEcc_w2000','_HamEcc_w8000'};
end

mainDir  = fileparts(mfilename('fullpath'));
projRoot = fileparts(mainDir);
addpath(projRoot); addpath(mainDir);
addpath(fullfile(projRoot,'ExternalFunctions')); addpath(fullfile(projRoot,'MuscleModel'));
addpath(fullfile(projRoot,'Polynomials'));       addpath(fullfile(projRoot,'CollocationScheme'));
addpath(fullfile(projRoot,'UtilityFunctions'));  addpath(fullfile(projRoot,'OpenSimModel'));
if isempty(which('casadiMEX'))
    for r = {'C:\casadi', fullfile(projRoot,'casadi'), fullfile(getenv('USERPROFILE'),'casadi')}
        if exist(fullfile(r{1},'+casadi'),'dir'); addpath(r{1}); break; end
    end
end
if isempty(which('casadiMEX')); error('CasADi not on path (looked in C:\\casadi etc).'); end

resultsDir = fullfile(projRoot,'Results');
outDir     = fullfile(resultsDir,'HamObj_Study');
if ~exist(outDir,'dir'); mkdir(outDir); end
ckptFile = fullfile(outDir,'checkpoint.csv');
logFile  = fullfile(outDir,'run_obj.log');

if nargin('main_pred_sim_sprinting') < 3
    error('main_pred_sim_sprinting must accept the 3rd (warmStartFile) arg; update main first.');
end
nomBase = local_find_strict(resultsDir, '*Nominal.mat', N, true);
if isempty(nomBase); error('No strict N=%d Nominal base with duals for warm-start.', N); end
fprintf('[precheck] CasADi ok; N=%d Nominal base = %s\n', N, nomBase);

if ~exist(ckptFile,'file')
    fid = fopen(ckptFile,'w');
    fprintf(fid,'tag,condition,mesh_N,out_file,solver_status,speed_mps,td_tilt_deg,iters,runtime_min,timestamp\n');
    fclose(fid);
end
done = local_done_tags(ckptFile);

fid = fopen(logFile,'a');
fprintf(fid,'\n===== Ham-objective sweep started %s (N=%d) =====\nConditions: %s\n', ...
    datestr(now), N, strjoin(conditions,', '));
fclose(fid);

for c = 1:numel(conditions)
    cond = conditions{c}; tag = cond;
    if any(strcmp(done, tag))
        fprintf('### [%d/%d] SKIP %s (already Solve_Succeeded)\n', c, numel(conditions), tag); continue;
    end
    fprintf('\n############################################################\n');
    fprintf('### [%d/%d] %s (N=%d)\n', c, numel(conditions), cond, N);
    fprintf('############################################################\n');
    t0 = tic; status='ERRORED'; outFile=''; spd=NaN; tdt=NaN; iters=-1; emsg='';
    try
        cd(mainDir);
        main_pred_sim_sprinting(cond, N);
        [outFile, status, spd, tdt, iters] = local_newest_result(resultsDir, cond);
    catch ME
        emsg = ME.message; fprintf('### ERROR %s: %s\n', tag, emsg);
    end
    rt = toc(t0)/60;
    fid = fopen(ckptFile,'a');
    fprintf(fid,'%s,%s,%d,%s,%s,%.5f,%.4f,%d,%.2f,%s\n', tag, cond, N, local_bn(outFile), ...
        status, spd, tdt, iters, rt, datestr(now,'yyyy-mm-ddTHH:MM:SS'));
    fclose(fid);
    fid = fopen(logFile,'a');
    fprintf(fid,'%s | %-22s | %-22s | %6.1f min | %s\n', datestr(now), cond, status, rt, emsg);
    fclose(fid);
    fprintf('### %s -> %s (%.1f min) speed=%.4f tilt=%.3f iters=%d\n', tag, status, rt, spd, tdt, iters);
end
fprintf('\n=== Ham-objective sweep finished. checkpoint=%s ===\n', ckptFile);
end

% ------------------------------------------------------------------ helpers
function p = local_find_strict(resultsDir, pat, N, needDuals)
d = dir(fullfile(resultsDir, ['pred_sprinting_data_' pat])); p=''; best=-inf;
for i=1:numel(d)
    try
        t=load(fullfile(d(i).folder,d(i).name),'optimumOutput'); o=t.optimumOutput;
        ok = isfield(o,'options') && o.options.N==N && isfield(o,'stats') && ...
             isfield(o.stats,'return_status') && strcmp(o.stats.return_status,'Solve_Succeeded');
        if needDuals; ok = ok && isfield(o,'lam_x_opt') && isfield(o,'lam_g_opt'); end
        if ok && d(i).datenum>best; best=d(i).datenum; p=fullfile(d(i).folder,d(i).name); end
    catch
    end
end
end

function [p,status,spd,tdt,iters] = local_newest_result(resultsDir, cond)
tok = cond; if tok(1)=='_'; tok=tok(2:end); end
d = dir(fullfile(resultsDir, ['pred_sprinting_data_*' tok '.mat']));
p=''; status='unknown'; spd=NaN; tdt=NaN; iters=-1; best=-inf;
for i=1:numel(d); if d(i).datenum>best; best=d(i).datenum; p=fullfile(d(i).folder,d(i).name); end; end
if ~isempty(p)
    try
        t=load(p,'optimumOutput'); o=t.optimumOutput;
        if isfield(o,'stats')&&isfield(o.stats,'return_status'); status=o.stats.return_status; end
        if isfield(o,'stats')&&isfield(o.stats,'iter_count'); iters=o.stats.iter_count; end
        if isfield(o,'ave_speed'); spd=o.ave_speed; end
        if isfield(o,'optVars_nsc')&&isfield(o.optVars_nsc,'q'); tdt=rad2deg(o.optVars_nsc.q(1,1)); end
    catch
    end
end
end

function tags = local_done_tags(ckptFile)
tags={};
try
    fid=fopen(ckptFile,'r'); C=textscan(fid,'%s','Delimiter','\n'); fclose(fid); L=C{1};
    for i=2:numel(L)
        parts=strsplit(L{i},','); if numel(parts)>=5 && strcmp(parts{5},'Solve_Succeeded'); tags{end+1}=parts{1}; end %#ok<AGROW>
    end
catch
end
end

function s = local_bn(p)
if isempty(p); s=''; else; [~,n,e]=fileparts(p); s=[n e]; end
end
