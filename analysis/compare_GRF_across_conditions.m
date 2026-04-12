function [] = compare_GRF_across_conditions()
% COMPARE_GRF_ACROSS_CONDITIONS
% 複数の走り方条件における地面反力（GRF）を抽出・比較・可視化
%
% Usage:
%   run compare_GRF_across_conditions.m
%
% Output:
%   - GRF 比較プロット（時系列）
%   - GRF ピーク値統計
%   - CSV 比較レポート

clc; close all;

%% Setup
scriptDir = fileparts(mfilename('fullpath'));
projectRoot = scriptDir;  % Script is in project root
pathResults = fullfile(projectRoot, 'Results');

fprintf('===== GRF Comparison Across Conditions =====\n\n');
fprintf('Project root: %s\n', projectRoot);
fprintf('Results path: %s\n', pathResults);
fprintf('Searching for: %s (prefer _GRF_Single.mot)\n\n', fullfile(pathResults, '*_GRF_Single.mot'));

%% Find all GRF files (prefer the summed Single files)
grf_files = dir(fullfile(pathResults, '*_GRF_Single.mot'));
if isempty(grf_files)
    % Fall back to the full per-sphere GRF files if no Single files exist
    grf_files = dir(fullfile(pathResults, '*_GRF.mot'));
end
if isempty(grf_files)
    fprintf('ERROR: No GRF .mot files found.\n');
    fprintf('Checked path: %s\n', pathResults);
    fprintf('Does Results folder exist? %d\n', exist(pathResults, 'dir'));
    error('No GRF .mot files found in Results folder');
end

fprintf('Found %d GRF files:\n', length(grf_files));

%% Extract condition names and load data
conditions = {};
grf_data = {};
time_data = {};

for i = 1:length(grf_files)
    filename = grf_files(i).name;
    fprintf('  [%d] %s\n', i, filename);
    
    % Extract condition from filename (e.g., "Nominal", "HTD_Plus_4", etc.)
    parts = strsplit(filename, '___');
    if length(parts) >= 2
        condition = strrep(parts{2}, '_GRF.mot', '');
    else
        condition = sprintf('Cond_%d', i);
    end
    
    conditions{i} = condition;
    
    % Load .mot file
    filepath = fullfile(pathResults, filename);
    motdata = readMOT(filepath);
    
    % Store data
    time_data{i} = motdata.data(:, 1);
    grf_data{i} = motdata.data(:, 2:end);
    
end

fprintf('\nConditions identified: %s\n\n', strjoin(conditions, ' | '));

%% Extract key GRF components
% Assumption: first columns are total force components (vx, vy, vz)
% and force positions (px, py, pz)
% See main_pred_sim_sprinting.m for detailed header

fprintf('=== GRF Statistics ===\n\n');

grf_stats = table();
for i = 1:length(conditions)
    % Extract vertical GRF (typically column 2, assuming vy or ground_force_vy)
    vert_grf = grf_data{i}(:, 2);  % Vertical component
    
    % Extract horizontal GRF components (typically columns 1 and 3)
    horiz_grf_x = grf_data{i}(:, 1);
    horiz_grf_z = grf_data{i}(:, 3);
    
    % Compute resultant
    resultant_grf = sqrt(horiz_grf_x.^2 + vert_grf.^2 + horiz_grf_z.^2);
    
    % Statistics
    vert_max = max(vert_grf);
    vert_mean = mean(vert_grf);
    horiz_max = max(sqrt(horiz_grf_x.^2 + horiz_grf_z.^2));
    resultant_max = max(resultant_grf);
    
    time = time_data{i};
    duration = time(end) - time(1);
    
    % Add to table
    grf_stats = [grf_stats; table(conditions(i), duration, vert_max, horiz_max, resultant_max, ...
        'VariableNames', {'Condition', 'Duration_s', 'VertGRF_Max_N', 'HorizGRF_Max_N', 'ResultantGRF_Max_N'})];
    
    fprintf('%s:\n', conditions{i});
    fprintf('  Duration: %.3f s\n', duration);
    fprintf('  Vertical GRF max: %.1f N (mean: %.1f N)\n', vert_max, vert_mean);
    fprintf('  Horizontal GRF max: %.1f N\n', horiz_max);
    fprintf('  Resultant GRF max: %.1f N\n\n', resultant_max);
end

%% Plot 1: Vertical GRF Comparison
figure('Name', 'GRF Comparison - Vertical Component', 'NumberTitle', 'off');
hold on;
colors = jet(length(conditions));

for i = 1:length(conditions)
    time = time_data{i};
    vert_grf = grf_data{i}(:, 2);
    plot(time, vert_grf, '-', 'Color', colors(i,:), 'LineWidth', 1.5, 'DisplayName', conditions{i});
end

hold off;
xlabel('Time (s)', 'FontSize', 11);
ylabel('Vertical GRF (N)', 'FontSize', 11);
title('Vertical Ground Reaction Force - Multiple Conditions', 'FontSize', 12, 'FontWeight', 'bold');
legend('Location', 'best');
grid on;
xlim([min(cellfun(@min, time_data)) max(cellfun(@max, time_data))]);

%% Plot 2: Horizontal GRF Comparison (magnitude)
figure('Name', 'GRF Comparison - Horizontal Component', 'NumberTitle', 'off');
hold on;

for i = 1:length(conditions)
    time = time_data{i};
    horiz_grf_x = grf_data{i}(:, 1);
    horiz_grf_z = grf_data{i}(:, 3);
    horiz_mag = sqrt(horiz_grf_x.^2 + horiz_grf_z.^2);
    plot(time, horiz_mag, '-', 'Color', colors(i,:), 'LineWidth', 1.5, 'DisplayName', conditions{i});
end

hold off;
xlabel('Time (s)', 'FontSize', 11);
ylabel('Horizontal GRF Magnitude (N)', 'FontSize', 11);
title('Horizontal Ground Reaction Force - Multiple Conditions', 'FontSize', 12, 'FontWeight', 'bold');
legend('Location', 'best');
grid on;
xlim([min(cellfun(@min, time_data)) max(cellfun(@max, time_data))]);

%% Plot 3: GRF Peak Values Bar Chart
figure('Name', 'GRF Peak Values Comparison', 'NumberTitle', 'off');

x_pos = 1:length(conditions);
subplot(2, 2, 1);
bar(x_pos, grf_stats.VertGRF_Max_N);
set(gca, 'XTickLabel', conditions, 'XTickLabelRotation', 45);
ylabel('Max Vertical GRF (N)', 'FontSize', 10);
title('Peak Vertical GRF', 'FontSize', 11, 'FontWeight', 'bold');
grid on; grid minor;

subplot(2, 2, 2);
bar(x_pos, grf_stats.HorizGRF_Max_N, 'FaceColor', [1 0.5 0.5]);
set(gca, 'XTickLabel', conditions, 'XTickLabelRotation', 45);
ylabel('Max Horizontal GRF (N)', 'FontSize', 10);
title('Peak Horizontal GRF', 'FontSize', 11, 'FontWeight', 'bold');
grid on; grid minor;

subplot(2, 2, 3);
bar(x_pos, grf_stats.ResultantGRF_Max_N, 'FaceColor', [0.5 0.5 1]);
set(gca, 'XTickLabel', conditions, 'XTickLabelRotation', 45);
ylabel('Max Resultant GRF (N)', 'FontSize', 10);
title('Peak Resultant GRF', 'FontSize', 11, 'FontWeight', 'bold');
grid on; grid minor;

subplot(2, 2, 4);
bar(x_pos, grf_stats.Duration_s, 'FaceColor', [0.5 1 0.5]);
set(gca, 'XTickLabel', conditions, 'XTickLabelRotation', 45);
ylabel('Duration (s)', 'FontSize', 10);
title('Step/Cycle Duration', 'FontSize', 11, 'FontWeight', 'bold');
grid on; grid minor;

%% Save comparison table
output_csv = fullfile(pathResults, sprintf('GRF_Comparison_%s.csv', datestr(now, 'yyyymmdd_HHMMSS')));
writetable(grf_stats, output_csv);
fprintf('\nSaved GRF comparison table: %s\n\n', output_csv);

%% Summary
fprintf('===== Summary =====\n');
fprintf('Conditions analyzed: %d\n', length(conditions));
fprintf('GRF statistics exported to: %s\n', output_csv);
fprintf('Plots created: 3 figures\n');
fprintf('\nNotes:\n');
fprintf('  - Vertical GRF: Column 2 (ground_force_vy assumed)\n');
fprintf('  - Horizontal GRF: Columns 1,3 (ground_force_vx, _vz)\n');
fprintf('  - Resultant = sqrt(vx^2 + vy^2 + vz^2)\n');

end


function motdata = readMOT(filepath)
% Read OpenSim .mot file
% Returns structure with 'data', 'labels', 'units'

fid = fopen(filepath, 'r');
if fid == -1
    error('Cannot open file: %s', filepath);
end

% Read header
header_done = false;
n_rows = 0;
n_cols = 0;
row_count = 0;

while ~header_done && ~feof(fid)
    line = fgetl(fid);
    if contains(line, 'endheader')
        header_done = true;
        break;
    end
    if contains(line, 'nRows=')
        n_rows = str2double(strrep(line, 'nRows=', ''));
    end
    if contains(line, 'nColumns=')
        n_cols = str2double(strrep(line, 'nColumns=', ''));
    end
end

% Read column labels
labels_line = fgetl(fid);
labels = strsplit(labels_line, char(9));  % Tab-separated

% Read data
data = [];
while ~feof(fid)
    line = fgetl(fid);
    if ischar(line) && ~isempty(line)
        values = str2double(strsplit(line, char(9)));
        data = [data; values];
    end
end

fclose(fid);

motdata.labels = labels;
motdata.data = data;
motdata.n_rows = size(data, 1);
motdata.n_cols = size(data, 2);

end
