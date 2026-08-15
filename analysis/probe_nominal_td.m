% PROBE_NOMINAL_TD  Quick diagnostic for the v3 (TDPT) study.
% Reports every available _Nominal solution's mesh size, IPOPT status, the
% touchdown (first-node) pelvis_tilt in deg, the stride-mean pelvis_tilt, and
% top speed. The N=50 strictly-converged Nominal supplies the nominalTD
% reference that v3's single touchdown equality is applied to.
%
% Run headless:
%   matlab -nosplash -nodesktop -wait -r "cd('<analysis>'); probe_nominal_td; exit"

scriptDir = fileparts(mfilename('fullpath'));     % analysis
projRoot  = fileparts(scriptDir);
resDir    = fullfile(projRoot,'Results');
nomFiles  = dir(fullfile(resDir,'pred_sprinting_data_*Nominal.mat'));

fprintf('=== probe_nominal_td: %d Nominal file(s) ===\n', numel(nomFiles));
for i=1:numel(nomFiles)
    try
        S=load(fullfile(nomFiles(i).folder,nomFiles(i).name),'optimumOutput');
        o=S.optimumOutput;
        st='?'; if isfield(o,'stats')&&isfield(o.stats,'return_status'); st=o.stats.return_status; end
        N=NaN; if isfield(o,'options')&&isfield(o.options,'N'); N=o.options.N; end
        td = rad2deg(o.optVars_nsc.q(1,1));
        mn = rad2deg(mean(o.optVars_nsc.q(1,:)));
        fprintf('%-58s | N=%-4d | %-22s | td=%8.4f deg | mean=%8.4f deg | speed=%.4f\n', ...
            nomFiles(i).name, N, st, td, mn, o.ave_speed);
    catch ME
        fprintf('%-58s | ERROR %s\n', nomFiles(i).name, ME.message);
    end
end
fprintf('=== probe done ===\n');
