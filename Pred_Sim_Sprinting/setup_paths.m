%% ============================================================================
% setup_paths.m
% MATLAB Path Setup for Pred_Sim_Sprinting Project
% ============================================================================
% This script initializes all necessary paths for the predictive simulation
% of sprinting. Run this before executing main_pred_sim_sprinting.m
%
% Usage: 
%   1. In MATLAB Command Window, navigate to project root
%   2. Type: setup_paths
%   3. All paths will be automatically configured
%
% Date Created: 2026-02-03
% Compatible with MATLAB 2017b and above
% ============================================================================

% Get the project root directory
project_root = pwd;

% Display project root
fprintf('========================================\n');
fprintf('Pred_Sim_Sprinting Path Setup\n');
fprintf('========================================\n');
fprintf('Project Root: %s\n\n', project_root);

% Define all subdirectories
paths_to_add = {
    project_root                          % Project root
    fullfile(project_root, 'MainFunctions')
    fullfile(project_root, 'ExternalFunctions')
    fullfile(project_root, 'MuscleModel')
    fullfile(project_root, 'Polynomials')
    fullfile(project_root, 'CollocationScheme')
    fullfile(project_root, 'UtilityFunctions')
    fullfile(project_root, 'OpenSimModel')
};

% Add paths to MATLAB
for i = 1:length(paths_to_add)
    path_to_add = paths_to_add{i};
    if isfolder(path_to_add)
        addpath(path_to_add);
        fprintf('[OK] Added: %s\n', path_to_add);
    else
        fprintf('[WARN] Folder not found: %s\n', path_to_add);
    end
end

% Import CasADi
fprintf('\n----------------------------------------\n');
fprintf('Importing CasADi...\n');
try
    import casadi.*
    fprintf('[OK] CasADi imported successfully\n');
catch ME
    fprintf('[ERROR] Failed to import CasADi: %s\n', ME.message);
    fprintf('Make sure CasADi MATLAB toolbox is installed.\n');
    fprintf('Download from: https://web.casadi.org/get/\n');
end

% Display current MATLAB version
matlab_version = version;
fprintf('\n----------------------------------------\n');
fprintf('MATLAB Version: %s\n', matlab_version);
fprintf('========================================\n\n');
