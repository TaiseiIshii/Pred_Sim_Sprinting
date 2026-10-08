"""
Main entry point for the Python/CasADi sprinting simulation.

Equivalent to MainFunctions/main_pred_sim_sprinting.m without MATLAB.

Usage
-----
    cd python
    uv run pred-sim
    # or
    uv run python -m pred_sim_sprinting.main

Simulation type can be passed as a CLI argument:
    uv run pred-sim --sim-type _Nominal
    uv run pred-sim --sim-type _HTD_Plus_6
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
import numpy as np
import scipy.io
import scipy.signal
import scipy.interpolate
import casadi as ca
from pathlib import Path

from .collocation import collocation_scheme, control_extrapolation
from .joint_muscle_indices import (
    JointIndices, NQ, MUSCLE_NAMES_R, MUSCLE_NAMES_BACK_L,
    ALL_MUSCLE_NAMES, muscle_indices, moment_arm_indices,
)
from .io_utils import (
    read_mot, write_mot, load_contact_params,
    load_muscle_curve_params, extract_musc_properties,
)
from .bounds_scaling import create_scaled_bounds, create_guess, calc_obj_range
from .casadi_functions import build_muscle_model_functions, build_cost_functions
from .nlp_builder import build_nlp


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # python/../Pred_Sim_Sprinting
SIM_ROOT  = REPO_ROOT / "Pred_Sim_Sprinting"

PATH_MAIN       = SIM_ROOT
PATH_RESULTS    = SIM_ROOT / "Results"
PATH_UTIL       = SIM_ROOT / "UtilityFunctions"
PATH_EXT_FUNC   = SIM_ROOT / "ExternalFunctions"
PATH_MUSCLE_MOD = SIM_ROOT / "MuscleModel"
PATH_OPENSIM    = SIM_ROOT / "OpenSimModel"
PATH_POLY       = SIM_ROOT / "Polynomials"
PATH_EXP_DATA   = SIM_ROOT / "MainFunctions" / "ExperimentalData"


# ---------------------------------------------------------------------------
# Valid simulation types
# ---------------------------------------------------------------------------

VALID_TYPES = (
    ["_Nominal"]
    + [f"_HTD_Plus_{i}"  for i in range(1, 11)]
    + [f"_HTD_Minus_{i}" for i in range(1, 11)]
    + [f"_IKTD_Plus_{i}" for i in range(1, 11)]
    + [f"_IKTD_Minus_{i}"for i in range(1, 11)]
)


def check_simulation_type(sim_type: str) -> str:
    if sim_type not in VALID_TYPES:
        raise ValueError(
            f"Unknown simulation type: '{sim_type}'\n"
            f"Valid options: {VALID_TYPES}"
        )
    return sim_type


# ---------------------------------------------------------------------------
# IK data processing
# ---------------------------------------------------------------------------

def process_ik_output(
    states_fname: str,
    kin_sf: int,
    Options: dict,
    tau_root: np.ndarray,
    d: int,
    nq,
) -> dict:
    """
    Load, filter, spline-interpolate IK data onto collocation grid.

    Equivalent to processIKoutput() in main_pred_sim_sprinting.m
    """
    N = Options["N"]

    mot = read_mot(PATH_EXP_DATA / "IK_Splined" / states_fname)
    orig_time = mot.data[:, 0]
    states_raw = mot.data[:, 1:]   # shape (T, nq.all)

    ti, tf = orig_time[0], orig_time[-1]
    time_nodes = np.linspace(ti, tf, N)
    h = (tf - ti) / N

    # Build collocation time grid
    time_grid_mat = np.zeros((N, d + 1))
    for i in range(N):
        for ii in range(d + 1):
            time_grid_mat[i, ii] = time_nodes[i] + h * tau_root[ii]
    time_grid = time_grid_mat.T.flatten()

    # Low-pass Butterworth filter (2nd order, fc=20 Hz)
    cf = 20.0
    b_coef, a_coef = scipy.signal.butter(2, cf / (kin_sf / 2.0), btype="low")
    states_filt = scipy.signal.filtfilt(b_coef, a_coef, states_raw, axis=0)

    # Spline interpolation onto collocation grid
    q_aux    = np.zeros((len(time_grid), nq.all))
    qdot_aux = np.zeros_like(q_aux)
    qddot_aux= np.zeros_like(q_aux)

    for i in range(nq.all):
        cs = scipy.interpolate.CubicSpline(orig_time, states_filt[:, i])
        q_aux[:, i]    = cs(time_grid)
        qdot_aux[:, i] = cs(time_grid, 1)
        qddot_aux[:,i] = cs(time_grid, 2)

    # Convert angular DOFs from degrees to radians
    ang_idx = list(range(0, 3)) + list(range(6, nq.all))
    q_aux[:, ang_idx]     = np.deg2rad(q_aux[:, ang_idx])
    qdot_aux[:, ang_idx]  = np.deg2rad(qdot_aux[:, ang_idx])
    qddot_aux[:, ang_idx] = np.deg2rad(qddot_aux[:, ang_idx])

    state_names = ["time"] + [
        "pelvis_tilt","pelvis_list","pelvis_rotation",
        "pelvis_tx","pelvis_ty","pelvis_tz",
        "hip_flexion_r","hip_adduction_r","hip_rotation_r",
        "knee_angle_r","ankle_angle_r","subtalar_angle_r","mtp_angle_r",
        "hip_flexion_l","hip_adduction_l","hip_rotation_l",
        "knee_angle_l","ankle_angle_l","subtalar_angle_l","mtp_angle_l",
        "lumbar_extension","lumbar_bending","lumbar_rotation",
        "arm_flex_r","arm_add_r","arm_rot_r","elbow_flex_r",
        "pro_sup_r","wrist_flex_r","wrist_dev_r",
        "arm_flex_l","arm_add_l","arm_rot_l","elbow_flex_l",
        "pro_sup_l","wrist_flex_l","wrist_dev_l",
    ]

    return {
        "q_aux":     q_aux,
        "qdot_aux":  qdot_aux,
        "qddot_aux": qddot_aux,
        "time_grid": time_grid,
        "time_nodes":time_nodes,
        "h":         h,
        "state_names": state_names,
    }


# ---------------------------------------------------------------------------
# External output indices (0-based)
# ---------------------------------------------------------------------------

def make_out_ind() -> dict:
    """0-based output indices for the external dynamics DLL."""
    oi = {}
    oi["resids_moments"]    = list(range(0, 37))
    oi["r_contGRF"]         = list(range(37, 58))
    oi["l_contGRF"]         = list(range(58, 79))
    oi["posCOM"]            = list(range(79, 82))
    oi["velCOM"]            = list(range(82, 85))
    oi["r_calc_pos"]        = list(range(85, 88))
    oi["r_calc_vel"]        = list(range(88, 91))
    oi["l_calc_pos"]        = list(range(91, 94))
    oi["l_calc_vel"]        = list(range(94, 97))
    oi["r_toes_pos"]        = list(range(97, 100))
    oi["r_toes_vel"]        = list(range(100, 103))
    oi["l_toes_pos"]        = list(range(103, 106))
    oi["l_toes_vel"]        = list(range(106, 109))
    oi["calc_mag"]          = 109
    oi["toes_mag"]          = 110
    oi["tibia_mag"]         = 111
    oi["radius_mag"]        = 112
    oi["hand_mag"]          = 113
    oi["tibia_l_calc_r_mag"]= 118
    oi["tibia_r_calc_l_mag"]= 119
    oi["tibia_l_toes_r_mag"]= 120
    oi["tibia_r_toes_l_mag"]= 121
    oi["knee_r_pos_XYZ_F"]  = list(range(143, 146))
    oi["knee_l_pos_XYZ_F"]  = list(range(146, 149))
    oi["knee_r_pos_XYZ"]    = list(range(203, 206))
    oi["knee_l_pos_XYZ"]    = list(range(206, 209))
    return oi


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Pred_Sim_Sprinting Python runner")
    parser.add_argument("--sim-type", default="_Nominal",
                        help="Simulation type (e.g. _Nominal, _HTD_Plus_6)")
    parser.add_argument("--N", type=int, default=50,
                        help="Number of mesh intervals")
    parser.add_argument("--solver", default="mumps",
                        help="Linear solver for IPOPT (mumps or ma57)")
    parser.add_argument("--tol", type=int, default=1,
                        help="Tolerance level: 1 -> 1e-5, other -> 1e-6")
    parser.add_argument("--prev-sol", default=None,
                        help="Path to previous solution .mat file for warm start")
    args = parser.parse_args()

    simulation_type = check_simulation_type(args.sim_type)
    file_ext        = simulation_type

    Options = {
        "solver":      args.solver,
        "tol":         args.tol,
        "N":           args.N,
        "MTP_stiff":   65.0,
        "timePercent": 0.15,
    }

    prevSol = None
    if args.prev_sol:
        prevSol = scipy.io.loadmat(args.prev_sol, simplify_cells=True)

    print("=" * 60)
    print("Pred_Sim_Sprinting  (Python/CasADi, no MATLAB)")
    print(f"Simulation type  : {simulation_type}")
    print(f"Mesh intervals N : {Options['N']}")
    print(f"Linear solver    : {Options['solver']}")
    print("=" * 60)

    # -- Collocation scheme --
    d      = 3
    method = "radau"
    tau_root, C, D, B = collocation_scheme(d, method)
    D_control = control_extrapolation(tau_root[1:])

    # -- Joint / DOF indices --
    jointi = JointIndices()
    nq     = NQ()

    # -- Muscle names & indices --
    muscle_names = MUSCLE_NAMES_R + MUSCLE_NAMES_BACK_L  # 49 total
    musInd = muscle_indices(muscle_names[:-3])             # 0-based, 46 muscles
    NMuscle = len(musInd) * 2                              # bilateral

    # -- Muscle-tendon parameters from OpenSim model --
    osim_model = "Scaled_FullBody_HamnerModel_Muscle_withContact.osim"
    musc_props = extract_musc_properties(
        PATH_OPENSIM / osim_model, muscle_names[:-3]
    )
    musc_props[0, :] *= 2.0          # scale Fmax x2
    musc_props[2, 24] += musc_props[2, 24] * 0.1  # quad_fem TSL correction
    vMaxMult = 12.0

    MTparameters_m = np.hstack([musc_props[:, musInd], musc_props[:, musInd]])
    totalFmax = MTparameters_m[0, :].sum()
    indFmax   = MTparameters_m[0, :]

    # CasADi symbolic muscle parameters
    m_oMFL = ca.SX.sym("m_oMFL", NMuscle)
    m_TSL  = ca.SX.sym("m_TSL",  NMuscle)
    m_vmax = ca.SX.sym("m_vmax", NMuscle)

    oMFL_2_nsc = MTparameters_m[1, :NMuscle]
    TSL_2_nsc  = MTparameters_m[2, :NMuscle]

    # -- Polynomial moment-arm indices --
    joint_info = scipy.io.loadmat(
        str(PATH_POLY / "muscle_spanning_joint_INFO_subject9.mat"),
        simplify_cells=True,
    )
    spanning_info = joint_info["muscle_spanning_joint_INFO"]
    mai = moment_arm_indices(muscle_names[:-3], spanning_info[:-3, :])

    # Tendon stiffness / shift
    aTendon = 35.0 * np.ones(NMuscle)
    shift   = np.zeros(NMuscle)
    tensions= np.ones(NMuscle)

    # -- Contact model parameters --
    contPrms_nsc = load_contact_params(PATH_UTIL)

    # -- Load external DLL --
    print("\nLoading external DLL functions...")
    os.chdir(str(PATH_EXT_FUNC))
    try:
        F_cont_v21 = ca.external("F_cont_v21", "Spr_Imp_GRFs_ownCont_V21.dll")
        print("[OK] F_cont_v21 loaded")
    except Exception as e:
        print(f"[WARNING] F_cont_v21: {e}")
        F_cont_v21 = None
    try:
        F_cont_ana21 = ca.external("F_cont_ana21", "Spr_Imp_GRFs_ownCont_V21an.dll")
        print("[OK] F_cont_ana21 loaded")
    except Exception as e:
        print(f"[WARNING] F_cont_ana21: {e}")
        F_cont_ana21 = None
    os.chdir(str(PATH_MAIN))

    outInd = make_out_ind()

    # -- Experimental IK data --
    states_fname = "p02_maxVel_01.mot"
    kin_sf = 250
    statesF = process_ik_output(states_fname, kin_sf, Options, tau_root, d, nq)

    # -- Bounds & scaling --
    bounds_sc, scaling = create_scaled_bounds(statesF, nq, Options, d, NMuscle, jointi)

    orig_total_time = statesF["time_grid"][-1] - statesF["time_grid"][0]
    pct = orig_total_time * Options["timePercent"]
    t_lb = orig_total_time - pct
    t_ub = orig_total_time + pct
    scaling["totalTime"] = np.array(
        [np.linalg.solve([[t_lb, 1.0], [t_ub, 1.0]], [-1.0, 1.0])]
    ).flatten()
    bounds_sc["totalTime"] = {
        "lower": scaling["totalTime"][0] * t_lb + scaling["totalTime"][1],
        "upper": scaling["totalTime"][0] * t_ub + scaling["totalTime"][1],
    }

    # -- Initial guess --
    guess = create_guess(
        scaling, statesF, nq, NMuscle, Options, d, bounds_sc,
        prevSol, statesF["time_grid"], statesF["time_nodes"],
    )
    guess["totalTime"] = (
        orig_total_time * scaling["totalTime"][0] + scaling["totalTime"][1]
    )
    if prevSol is not None:
        guess["totalTime"] = (
            prevSol["optimumOutput"]["optVars_nsc"]["totalTime"]
            * scaling["totalTime"][0] + scaling["totalTime"][1]
        )

    # -- Objective range --
    obj_range = calc_obj_range(nq, statesF, 0.1, scaling, prevSol)

    # -- Muscle curve parameters --
    Fvparam, Fpparam, Faparam = load_muscle_curve_params(PATH_MUSCLE_MOD)

    # -- CasADi muscle model functions --
    f_lMT_vMT_dM, f_hill, calcMoms = build_muscle_model_functions(
        musInd=musInd,
        NMuscle=NMuscle,
        m_oMFL=m_oMFL,
        m_TSL=m_TSL,
        m_vmax=m_vmax,
        pathpolynomial=str(PATH_POLY),
        nq_leg=nq.leg,
        MTparameters_m=MTparameters_m,
        Fvparam=Fvparam,
        Fpparam=Fpparam,
        Faparam=Faparam,
    )

    # -- Cost functions --
    costFunctions = build_cost_functions(obj_range, nq, NMuscle, totalFmax, indFmax)

    # -- Cost weights --
    wJ = np.array([
        0.00, 0.00, 0.00, 0.00,  # 0-3: tracking
        0.05,                    # 4: accelerations
        0.10,                    # 5: muscle activations
        0.01,                    # 6: d(activation)/dt
        0.00,                    # 7: tendon forces
        0.01,                    # 8: d(tendon force)/dt
        0.01,                    # 9: reserve actuators
        0.10,                    # 10: arm activations
        10.0,                    # 11: average speed (subtracted in obj)
    ])

    # -- Formulate NLP --
    finalTime = ca.MX.sym("finalTime", 1)
    finalTime_nsc = (finalTime - scaling["totalTime"][1]) / scaling["totalTime"][0]
    pred_h = finalTime_nsc / Options["N"]

    print("\nBuilding NLP...")
    (w1, w01, lbw1, ubw1, J1,
     g1, lbg1, ubg1, g_names1, change_disp) = build_nlp(
        guess, bounds_sc, scaling, nq, Options,
        pred_h, F_cont_v21, statesF, contPrms_nsc,
        C, D, B, wJ, costFunctions,
        oMFL_2_nsc, TSL_2_nsc,
        NMuscle, vMaxMult, outInd,
        prevSol, finalTime_nsc, D_control,
        f_lMT_vMT_dM, f_hill,
        mai, file_ext, jointi,
    )

    # Append final time variable
    w   = w1   + [finalTime]
    w0  = w01  + [guess["totalTime"]]
    lbw = lbw1 + [bounds_sc["totalTime"]["lower"]]
    ubw = ubw1 + [bounds_sc["totalTime"]["upper"]]
    J   = J1   - wJ[11] * (change_disp / finalTime_nsc)
    g, lbg, ubg = g1, lbg1, ubg1

    # -- Solve NLP --
    print("\nSolving NLP with IPOPT...")
    prob = {
        "f": J,
        "x": ca.vertcat(*w),
        "g": ca.vertcat(*g),
    }
    ipopt_opts = {
        "hessian_approximation": "limited-memory",
        "mu_strategy":           "adaptive",
        "linear_solver":         Options["solver"],
        "tol":                   1e-5 if Options["tol"] == 1 else 1e-6,
        "max_iter":              50_000,
        "print_level":           5,
    }
    solver = ca.nlpsol("solver", "ipopt", prob, {"ipopt": ipopt_opts})

    sol = solver(
        x0=w0,
        lbx=lbw, ubx=ubw,
        lbg=lbg, ubg=ubg,
    )
    w_opt  = np.array(sol["x"]).flatten()
    status = solver.stats()

    print(f"\nSolver status: {status['return_status']}")

    # -- Save results --
    PATH_RESULTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d__%H-%M-%S")
    out_file = PATH_RESULTS / f"pred_sprinting_{ts}_{simulation_type}_GRF.npz"
    np.savez(out_file, w_opt=w_opt, solver_status=status["return_status"])
    print(f"\nResults saved to: {out_file}")


if __name__ == "__main__":
    main()
