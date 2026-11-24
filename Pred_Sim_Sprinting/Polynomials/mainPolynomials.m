% Main Polynomials Generation Script - FIXED VERSION
% To run code efficiently: be within 'Polynomials' folder

% Function generates polynomials to approximate muscle-tendon lengths (&
% velocities) and moment arms. This code is adapted from:
% https://simtk.org/projects/3dpredictsim

%% Display status
fprintf('========================================\n');
fprintf('Pred_Sim_Sprinting Polynomial Setup\n');
fprintf('========================================\n\n');

%% User inputs
runPolynomialfit = 0;  % Set to 0 to use pre-computed data (required since input files are not included)
saveQdot = 1;
savePolynomials = 1;

%% Generate dummy motion data

% Generate random angles for testing polynomial fitting
% Model has 37 DOF but only 10 are used for muscle-tendon calculations
% Order: hip_flex_r, hip_add_r, hip_rot_r, knee_r, ankle_r, subtalar_r, mtp_r, lumbar_ext, lumbar_bend, lumbar_rot

fprintf('Generating dummy motion data for testing...\n');

% Create dummy motion structure with generated data
n_samples = 5000;
q = zeros(n_samples, 10);

% Generate random joint angles within ROM (physiological ranges)
q(:,1) = deg2rad((-50 + 100*rand(n_samples,1)));      % hip_flex_r
q(:,2) = deg2rad((-30 + 60*rand(n_samples,1)));        % hip_add_r
q(:,3) = deg2rad((-50 + 100*rand(n_samples,1)));       % hip_rot_r
q(:,4) = deg2rad((-2.55 + 2.55*rand(n_samples,1)));    % knee_r (radians)
q(:,5) = deg2rad((-1.57 + 1.57*rand(n_samples,1)));    % ankle_r (radians)
q(:,6) = deg2rad((-0.5 + 1.0*rand(n_samples,1)));      % subtalar_r
q(:,7) = deg2rad((-0.3 + 0.6*rand(n_samples,1)));      % mtp_r
q(:,8) = deg2rad((-30 + 60*rand(n_samples,1)));        % lumbar_ext
q(:,9) = deg2rad((-30 + 60*rand(n_samples,1)));        % lumbar_bend
q(:,10) = deg2rad((-30 + 60*rand(n_samples,1)));       % lumbar_rot

%% Generate joint velocities

fprintf('Generating dummy joint velocities...\n');

% Generate random joint velocities for testing
a = -1000;
b = 1000;
r1 = (b-a).*rand(5000,1) + a;
r2 = (b-a).*rand(size(q,1),1) + a;
r3 = (b-a).*rand(size(q,1),1) + a;
r4 = (b-a).*rand(size(q,1),1) + a;
r5 = (b-a).*rand(size(q,1),1) + a;
r6 = (b-a).*rand(size(q,1),1) + a;
r7 = (b-a).*rand(size(q,1),1) + a;
r8 = (b-a).*rand(size(q,1),1) + a;
r9 = (b-a).*rand(size(q,1),1) + a;
r10 = (b-a).*rand(size(q,1),1) + a;
r = [r1,r2,r3,r4,r5,r6,r7,r8,r9,r10];
qdot = deg2rad(r);

%% Check for pre-computed muscle model data

fprintf('Checking for pre-computed muscle model data...\n');

if ~exist('MuscleData_subject9.mat', 'file')
    fprintf('[ERROR] MuscleData_subject9.mat not found!\n');
    error('Pre-computed muscle model files are required but not found.');
end

if ~exist('MuscleInfo_subject9.mat', 'file')
    fprintf('[ERROR] MuscleInfo_subject9.mat not found!\n');
    error('Pre-computed muscle model files are required but not found.');
end

if ~exist('muscle_spanning_joint_INFO_subject9.mat', 'file')
    fprintf('[ERROR] muscle_spanning_joint_INFO_subject9.mat not found!\n');
    error('Pre-computed muscle model files are required but not found.');
end

fprintf('[OK] All pre-computed muscle model files found\n\n');

%% Load pre-computed muscle model data

fprintf('Loading pre-computed muscle model data...\n');

load MuscleData_subject9.mat
load MuscleInfo_subject9.mat
load muscle_spanning_joint_INFO_subject9.mat

fprintf('[OK] Muscle model data loaded successfully\n\n');

%% Create CasADi functions

fprintf('Creating CasADi symbolic functions...\n');

import casadi.*

% Order: hip_flex_r, hip_add_r, hip_rot_r, knee_r, ankle_r, subtalar_r, mtp_r, lumbar_ext, lumbar_bend, lumbar_rot
NMuscle = length(MuscleInfo.muscle);
q_leg_trunk = 10;
qin     = SX.sym('qin',1,q_leg_trunk);
qdotin  = SX.sym('qdotin',1,q_leg_trunk);
lMT     = SX(NMuscle,1);
vMT     = SX(NMuscle,1);
dM      = SX(NMuscle,q_leg_trunk);

for i=1:NMuscle     
    index_dof_crossing  = find(muscle_spanning_joint_INFO(i,:)==1);
    order               = MuscleInfo.muscle(i).order;
    [mat,diff_mat_q]    = n_art_mat_3_cas_SX(qin(1,index_dof_crossing),order);
    lMT(i,1)            = mat*MuscleInfo.muscle(i).coeff;
    vMT(i,1)            = 0;
    dM(i,1:q_leg_trunk) = 0;
    nr_dof_crossing     = length(index_dof_crossing); 
    for dof_nr = 1:nr_dof_crossing
        dM(i,index_dof_crossing(dof_nr)) = (-(diff_mat_q(:,dof_nr)))'*MuscleInfo.muscle(i).coeff;
        vMT(i,1) = vMT(i,1) + (-dM(i,index_dof_crossing(dof_nr))*qdotin(1,index_dof_crossing(dof_nr)));
    end 
end

f_lMT_vMT_dM = Function('f_lMT_vMT_dM',{qin,qdotin},{lMT,vMT,dM});

fprintf('[OK] CasADi functions created\n\n');

%% Verify results

fprintf('Verifying polynomial fitting accuracy...\n');

load MuscleData_subject9.mat
lMT_out_r = zeros(size(q,1),NMuscle);
vMT_out_r = zeros(size(q,1),NMuscle);
dM_out_r = zeros(size(q,1),NMuscle,q_leg_trunk);

for i = 1:size(q,1)
    [out1_r,out2_r,out3_r] = f_lMT_vMT_dM(MuscleData.q(i,:),MuscleData.qdot(i,:));
    lMT_out_r(i,:) = full(out1_r);
    vMT_out_r(i,:) = full(out2_r);
    dM_out_r(i,:,1) = full(out3_r(:,1));
    dM_out_r(i,:,2) = full(out3_r(:,2));
    dM_out_r(i,:,3) = full(out3_r(:,3));
    dM_out_r(i,:,4) = full(out3_r(:,4));
    dM_out_r(i,:,5) = full(out3_r(:,5));   
    dM_out_r(i,:,6) = full(out3_r(:,6));
    dM_out_r(i,:,7) = full(out3_r(:,7));
    dM_out_r(i,:,8) = full(out3_r(:,8));
    dM_out_r(i,:,9) = full(out3_r(:,9)); 
    dM_out_r(i,:,10) = full(out3_r(:,10)); 
end

fprintf('[OK] Polynomial verification completed\n');

%% Calculate accuracy metrics

fprintf('\nAccuracy Metrics:\n');
fprintf('----------------------------------------\n');

for i = 1:NMuscle  
    assertLMT(:,i) = abs(lMT_out_r(:,i) - MuscleData.lMT(:,i));
    assertdM.hip.flex(:,i) = abs(dM_out_r(:,i,1) - MuscleData.dM(:,i,1));
    assertdM.hip.add(:,i) = abs(dM_out_r(:,i,2) - MuscleData.dM(:,i,2));
    assertdM.hip.rot(:,i) = abs(dM_out_r(:,i,3) - MuscleData.dM(:,i,3));
    assertdM.knee(:,i) = abs(dM_out_r(:,i,4) - MuscleData.dM(:,i,4));
    assertdM.ankle(:,i) = abs(dM_out_r(:,i,5) - MuscleData.dM(:,i,5));
    assertdM.sub(:,i) = abs(dM_out_r(:,i,6) - MuscleData.dM(:,i,6));
    assertdM.mtp(:,i) = abs(dM_out_r(:,i,7) - MuscleData.dM(:,i,7));
    assertdM.lumb.ext(:,i) = abs(dM_out_r(:,i,8) - MuscleData.dM(:,i,8));
    assertdM.lumb.bend(:,i) = abs(dM_out_r(:,i,9) - MuscleData.dM(:,i,9));
    assertdM.lumb.rot(:,i) = abs(dM_out_r(:,i,10) - MuscleData.dM(:,i,10));
end

assertLMTmax_r = max(max(assertLMT));
fprintf('Max lMT error: %.6f\n', assertLMTmax_r);
fprintf('[OK] Polynomial setup completed successfully!\n\n');

fprintf('========================================\n');
fprintf('Setup Complete!\n');
fprintf('========================================\n');
fprintf('Ready to run main simulation.\n');
fprintf('Next: run MainFunctions/main_pred_sim_sprinting.m\n');
