%% ============================================================================
% test_initial_setup.m
% Initial MATLAB Setup Test and Verification
% ============================================================================
% This script verifies that all required paths, CasADi, and data files
% are properly configured before running main_pred_sim_sprinting.m
%
% Date Created: 2026-02-03
% Compatible with MATLAB 2017b and above
% ============================================================================

clear all; close all; clc;

fprintf('========================================\n');
fprintf('Pred_Sim_Sprinting Initial Setup Test\n');
fprintf('========================================\n\n');

% Get project root
project_root = fileparts(mfilename('fullpath'));
cd(project_root);

fprintf('Project Root: %s\n\n', project_root);

% ========== TEST 1: Run setup_paths ==========
fprintf('TEST 1: Path Setup\n');
fprintf('----------------------------------------\n');
try
    run setup_paths.m
    fprintf('[OK] Path setup successful\n\n');
catch ME
    fprintf('[ERROR] Path setup failed: %s\n', ME.message);
    return;
end

% ========== TEST 2: Check CasADi Import ==========
fprintf('TEST 2: CasADi Import\n');
fprintf('----------------------------------------\n');
try
    import casadi.*
    fprintf('[OK] CasADi imported successfully\n');
    fprintf('     Available CasADi functions can be used\n\n');
catch ME
    fprintf('[ERROR] CasADi import failed: %s\n', ME.message);
    fprintf('[WARN] Continue testing other components...\n\n');
end

% ========== TEST 3: Check Required Folders ==========
fprintf('TEST 3: Required Folders\n');
fprintf('----------------------------------------\n');

required_folders = {
    'MainFunctions'
    'ExternalFunctions'
    'MuscleModel'
    'Polynomials'
    'OpenSimModel'
    'CollocationScheme'
    'UtilityFunctions'
    'Results'
};

all_folders_ok = true;
for i = 1:length(required_folders)
    folder_path = fullfile(project_root, required_folders{i});
    if isfolder(folder_path)
        fprintf('[OK] %s\n', required_folders{i});
    else
        fprintf('[ERROR] Missing folder: %s\n', required_folders{i});
        all_folders_ok = false;
    end
end
fprintf('\n');

% ========== TEST 4: Check Critical Data Files ==========
fprintf('TEST 4: Critical Data Files\n');
fprintf('----------------------------------------\n');

critical_files = {
    fullfile('MuscleModel', 'Faparam.mat')
    fullfile('MuscleModel', 'Fpparam.mat')
    fullfile('MuscleModel', 'Fvparam.mat')
    fullfile('Polynomials', 'muscle_spanning_joint_INFO_subject9.mat')
    fullfile('OpenSimModel', 'Scaled_FullBody_HamnerModel_Muscle_withContact.osim')
};

all_files_ok = true;
for i = 1:length(critical_files)
    file_path = fullfile(project_root, critical_files{i});
    if isfile(file_path)
        fprintf('[OK] %s\n', critical_files{i});
    else
        fprintf('[WARN] Missing file: %s\n', critical_files{i});
        all_files_ok = false;
    end
end
fprintf('\n');

% ========== TEST 5: Check DLL Files ==========
fprintf('TEST 5: External DLL Files\n');
fprintf('----------------------------------------\n');

dll_folder = fullfile(project_root, 'ExternalFunctions');
dll_files = dir(fullfile(dll_folder, '*.dll'));

if isempty(dll_files)
    fprintf('[WARN] No DLL files found in ExternalFunctions\n');
else
    fprintf('[OK] Found %d DLL file(s):\n', length(dll_files));
    for i = 1:min(5, length(dll_files))
        fprintf('     - %s\n', dll_files(i).name);
    end
    if length(dll_files) > 5
        fprintf('     ... and %d more\n', length(dll_files) - 5);
    end
end
fprintf('\n');

% ========== TEST 6: Check Main Script ==========
fprintf('TEST 6: Main Script Availability\n');
fprintf('----------------------------------------\n');

main_script = fullfile(project_root, 'MainFunctions', 'main_pred_sim_sprinting.m');
if isfile(main_script)
    fprintf('[OK] main_pred_sim_sprinting.m found\n');
else
    fprintf('[ERROR] main_pred_sim_sprinting.m not found\n');
end
fprintf('\n');

% ========== SUMMARY ==========
fprintf('========================================\n');
fprintf('Setup Verification Summary\n');
fprintf('========================================\n');

if all_folders_ok
    fprintf('[OK] All required folders present\n');
else
    fprintf('[WARN] Some folders are missing\n');
end

if all_files_ok
    fprintf('[OK] All critical data files present\n');
else
    fprintf('[WARN] Some data files are missing\n');
end

fprintf('\n');
fprintf('Next Steps:\n');
fprintf('1. Ensure CasADi MATLAB toolbox is installed\n');
fprintf('   Download: https://web.casadi.org/get/\n');
fprintf('2. Run mainPolynomials.m to generate missing polynomial data\n');
fprintf('3. Run main_pred_sim_sprinting.m to start the simulation\n');
fprintf('\n');

fprintf('========================================\n');
fprintf('Setup test completed!\n');
fprintf('========================================\n\n');
