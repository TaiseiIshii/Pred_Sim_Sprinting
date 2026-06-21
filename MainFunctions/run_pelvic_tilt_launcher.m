function run_pelvic_tilt_launcher(mode)
% RUN_PELVIC_TILT_LAUNCHER  Headless entry point for the pelvic-tilt study.
%   mode = 'validate' -> single condition _PelvisTilt_m10 (machinery check)
%   mode = 'sweep'    -> full N=50 sweep (default)
%   mode = '<a sim_type string>' -> run just that one condition
if nargin < 1 || isempty(mode); mode = 'sweep'; end

thisDir = fileparts(mfilename('fullpath'));   % MainFunctions
projRoot = fileparts(thisDir);

% Ensure all framework folders are on the path (fresh headless sessions do
% not run setup_paths). Mirrors setup_paths.m but recursive for safety.
addpath(projRoot);
addpath(genpath(fullfile(projRoot,'MainFunctions')));
addpath(genpath(fullfile(projRoot,'ExternalFunctions')));
addpath(genpath(fullfile(projRoot,'MuscleModel')));
addpath(genpath(fullfile(projRoot,'Polynomials')));
addpath(genpath(fullfile(projRoot,'CollocationScheme')));
addpath(genpath(fullfile(projRoot,'UtilityFunctions')));
addpath(genpath(fullfile(projRoot,'OpenSimModel')));

cd(thisDir);

switch mode
    case 'validate'
        run_pelvic_tilt_sweep({'_PelvisTilt_m10'});
    case 'sweep'
        run_pelvic_tilt_sweep();   % default 5-condition N=50 sweep
    otherwise
        run_pelvic_tilt_sweep({mode});
end
end
