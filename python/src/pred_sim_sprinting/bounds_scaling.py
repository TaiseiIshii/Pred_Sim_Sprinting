"""
Bounds, scaling, initial guess, and objective range helpers.

Python port of createScaledBounds(), createGuess(), calcObjRange()
in main_pred_sim_sprinting.m
"""
from __future__ import annotations
import numpy as np


def create_scaled_bounds(statesF: dict, nq, Options: dict, d: int, NMuscle: int, jointi):
    """
    Create scaled variable bounds and scaling factors.

    Returns (bounds_sc, scaling) dicts.
    """
    N = Options["N"]

    # ----- Non-scaled bounds from experimental data -----
    q_min = statesF["q_aux"].min(axis=0)
    q_max = statesF["q_aux"].max(axis=0)
    qd_min = statesF["qdot_aux"].min(axis=0)
    qd_max = statesF["qdot_aux"].max(axis=0)
    qdd_min = statesF["qddot_aux"].min(axis=0)
    qdd_max = statesF["qddot_aux"].max(axis=0)

    q_lb = (q_min - np.abs(q_min) * 0.25)
    q_ub = (q_max + np.abs(q_max) * 0.25)
    q_ub[3] = 5.0

    # Arm bounds (0-based)
    q_lb[jointi.sh_flex_r] = np.deg2rad(-75);  q_lb[jointi.sh_flex_l] = np.deg2rad(-75)
    q_lb[jointi.sh_rot_r]  = np.deg2rad(-15);  q_lb[jointi.sh_rot_l]  = np.deg2rad(-15)
    q_ub[jointi.sh_flex_r] = np.deg2rad(90);   q_ub[jointi.sh_flex_l] = np.deg2rad(90)
    q_ub[jointi.sh_rot_r]  = np.deg2rad(0);    q_ub[jointi.sh_rot_l]  = np.deg2rad(0)
    q_ub[jointi.pro_r]     = np.deg2rad(90);   q_ub[jointi.pro_l]     = np.deg2rad(90)

    # Symmetrify leg bounds
    def sym_lb(arr, sl_r, sl_l):
        combined = np.minimum(arr[sl_r], arr[sl_l])
        arr[sl_r] = combined;  arr[sl_l] = combined

    def sym_ub(arr, sl_r, sl_l):
        combined = np.maximum(arr[sl_r], arr[sl_l])
        arr[sl_r] = combined;  arr[sl_l] = combined

    leg_r = slice(jointi.hip_flex_r, jointi.mtp_r + 1)
    leg_l = slice(jointi.hip_flex_l, jointi.mtp_l + 1)
    arm_r = slice(jointi.sh_flex_r,  jointi.wri_dev_r + 1)
    arm_l = slice(jointi.sh_flex_l,  jointi.wri_dev_l + 1)

    for sym_fn, arr in [(sym_lb, q_lb), (sym_ub, q_ub),
                        (sym_lb, qd_min), (sym_ub, qd_max),
                        (sym_lb, qdd_min), (sym_ub, qdd_max)]:
        sym_fn(arr, leg_r, leg_l)
        sym_fn(arr, arm_r, arm_l)

    # Pelvis/trunk symmetry
    pel  = slice(jointi.pelvis_tilt, jointi.pelvis_rot + 1)
    trnk = slice(jointi.trunk_ext, jointi.trunk_rot + 1)
    for sl in [pel, trnk]:
        bound = np.maximum(np.abs(q_lb[sl]), np.abs(q_ub[sl]))
        q_lb[sl] = -bound;  q_ub[sl] = bound

    for arr_lb, arr_ub in [(qd_min, qd_max), (qdd_min, qdd_max)]:
        for sl in [pel, trnk]:
            bound = np.maximum(np.abs(arr_lb[sl]), np.abs(arr_ub[sl]))
            arr_lb[sl] = -bound;  arr_ub[sl] = bound

    # Scaling factors
    scaling = {}
    scaling["q"]    = np.maximum(np.abs(q_lb),   np.abs(q_ub))
    scaling["qdot"] = np.maximum(np.abs(qd_min),  np.abs(qd_max))
    scaling["uAcc"] = np.maximum(np.abs(qdd_min), np.abs(qdd_max))

    npts = (d + 1) * N
    npts_ctrl = d * N

    bounds_sc = {"q": {}, "qdot": {}, "uAcc": {}}
    for key, lb, ub in [("q", q_lb, q_ub), ("qdot", qd_min, qd_max)]:
        sc = scaling[key]
        bounds_sc[key]["lower"] = np.tile((lb / sc)[:, None], (1, npts))
        bounds_sc[key]["upper"] = np.tile((ub / sc)[:, None], (1, npts))

    sc_acc = scaling["uAcc"]
    bounds_sc["uAcc"]["lower"] = np.tile((qdd_min / sc_acc)[:, None], (1, npts_ctrl))
    bounds_sc["uAcc"]["upper"] = np.tile((qdd_max / sc_acc)[:, None], (1, npts_ctrl))

    # Arm torques / activations
    scaling["uArms"] = 100.0
    bounds_sc["eArms"] = {"lower": -np.ones(nq.arms), "upper": np.ones(nq.arms)}
    bounds_sc["aArms"] = {"lower": -np.ones(nq.arms), "upper": np.ones(nq.arms)}

    # Muscle activations
    tact   = 0.015
    tdeact = 0.06
    scaling["act"]       = np.ones(NMuscle)
    scaling["uActdot"]   = 100.0 * np.ones(NMuscle)
    scaling["FTtilde"]   = 5.0 * np.ones(NMuscle)
    scaling["dFTtilde"]  = 100.0 * np.ones(NMuscle)
    scaling["uReserves"] = 40.0 * np.ones(2)

    bounds_sc["act"]      = {"lower": np.zeros(NMuscle), "upper": np.ones(NMuscle)}
    bounds_sc["uActdot"]  = {
        "lower": (-1.0 / 100.0 * np.ones(NMuscle)) / tdeact,
        "upper": (1.0 / 100.0 * np.ones(NMuscle)) / tact,
    }
    bounds_sc["FTtilde"]  = {"lower": np.zeros(NMuscle),    "upper": np.ones(NMuscle)}
    bounds_sc["dFTtilde"] = {"lower": -np.ones(NMuscle),    "upper": np.ones(NMuscle)}
    bounds_sc["uReserves"]= {"lower": -np.ones(2),          "upper": np.ones(2)}

    return bounds_sc, scaling


def create_guess(scaling: dict, statesF: dict, nq, NMuscle: int,
                 Options: dict, d: int, bounds_sc: dict,
                 prevSol, timeGrid: np.ndarray, timeNodes: np.ndarray) -> dict:
    """Create initial guess for NLP decision variables."""
    N = Options["N"]
    guess = {}

    if prevSol is None:
        guess["q"]    = statesF["q_aux"] / scaling["q"]
        guess["qdot"] = statesF["qdot_aux"] / scaling["qdot"]

        # Remove mesh-point rows from acceleration guess
        all_rows = np.arange((d + 1) * N)
        mesh_rows = np.arange(0, (d + 1) * N, d + 1)
        ctrl_rows = np.delete(all_rows, mesh_rows)
        guess["uAcc"] = statesF["qddot_aux"][ctrl_rows, :] / scaling["uAcc"]
    else:
        opt = prevSol["optimumOutput"]["optVars_nsc"]
        guess["q"]    = opt["q"].T / scaling["q"]
        guess["qdot"] = opt["qdot"].T / scaling["qdot"]
        guess["uAcc"] = opt["uAcc"][:, 1:].T / scaling["uAcc"]

    # Shoulder bounds clipping
    for side in ["sh_flex_r", "sh_flex_l", "sh_rot_r", "sh_rot_l"]:
        idx = getattr(nq, side, None)
        if idx is not None:
            lb = bounds_sc["q"]["lower"][idx, 0]
            ub = bounds_sc["q"]["upper"][idx, 0]
            guess["q"][:, idx] = np.clip(guess["q"][:, idx], lb, ub)

    guess["act"]      = 0.5 * np.ones((NMuscle, (d + 1) * N))
    guess["uActdot"]  = 0.01 * np.ones((NMuscle, d * N))
    guess["FTtilde"]  = 0.5 * np.ones((NMuscle, (d + 1) * N))
    guess["dFTtilde"] = 0.01 * np.ones((NMuscle, d * N))
    guess["aArms"]    = np.zeros((nq.arms, (d + 1) * N))
    guess["eArms"]    = np.zeros((nq.arms, d * N))
    guess["uReserves"]= np.zeros((2, d * N))

    if prevSol is not None:
        opt = prevSol["optimumOutput"]["optVars_nsc"]
        guess["act"]       = opt["act"]
        guess["uActdot"]   = opt["uActdot"][:, 1:] / scaling["uActdot"]
        guess["FTtilde"]   = opt["FTtilde"] / scaling["FTtilde"]
        guess["dFTtilde"]  = opt["dFTtilde"][:, 1:] / scaling["dFTtilde"]
        guess["aArms"]     = opt["armActs"]
        guess["eArms"]     = opt["armExcts"][:, 1:]
        guess["uReserves"] = opt["uReserves"][:, 1:] / scaling["uReserves"][:, None]

    return guess


def calc_obj_range(nq, statesF: dict, percent_tol: float, scaling: dict, prevSol) -> dict:
    """Compute objective function scaling ranges."""
    obj_range = {}
    obj_range["q"]       = (statesF["q_aux"].max(0) - statesF["q_aux"].min(0)) * percent_tol
    obj_range["qdot"]    = (statesF["qdot_aux"].max(0) - statesF["qdot_aux"].min(0)) * percent_tol
    obj_range["uAcc"]    = scaling["uAcc"]
    obj_range["act"]     = scaling["act"]
    obj_range["uActdot"] = scaling["uActdot"]
    obj_range["FTtilde"] = scaling["FTtilde"]
    obj_range["dFTtilde"]= scaling["dFTtilde"]
    obj_range["uReserves"]= scaling["uReserves"]
    obj_range["uArms"]   = scaling["uArms"]
    return obj_range
