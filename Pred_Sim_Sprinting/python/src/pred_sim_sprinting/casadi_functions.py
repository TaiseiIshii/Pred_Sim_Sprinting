"""
CasADi cost functions and muscle model functions.

Python port of loadCostFunctions() and loadMuscleModelFunctions()
in main_pred_sim_sprinting.m
"""
from __future__ import annotations
import numpy as np
import casadi as ca
import scipy.io
from pathlib import Path

from .muscle_model import force_equilibrium_Ftilde_all_tendon
from .polynomials import build_lMT_vMT_dM_function


# ---------------------------------------------------------------------------
# Muscle model CasADi functions
# ---------------------------------------------------------------------------

def build_muscle_model_functions(
    musInd:          np.ndarray,
    NMuscle:         int,
    m_oMFL:          ca.SX,
    m_TSL:           ca.SX,
    m_vmax:          ca.SX,
    pathpolynomial:  str,
    nq_leg:          int,
    MTparameters_m:  np.ndarray,
    Fvparam:         np.ndarray,
    Fpparam:         np.ndarray,
    Faparam:         np.ndarray,
):
    """
    Build and return:
      f_lMT_vMT_dM           : polynomial muscle-tendon function
      f_hill                 : Hill-equilibrium function
      calcMoms               : dict of dot-product moment functions
    """
    f_lMT_vMT_dM = build_lMT_vMT_dM_function(musInd, NMuscle, pathpolynomial, nq_leg)

    # --- Hill equilibrium ---
    FTtilde    = ca.SX.sym("FTtilde",    NMuscle)
    a          = ca.SX.sym("a",          NMuscle)
    dFTtilde   = ca.SX.sym("dFTtilde",   NMuscle)
    lMT_sym    = ca.SX.sym("lMT",        NMuscle)
    vMT_sym    = ca.SX.sym("vMT",        NMuscle)
    tension_SX = ca.SX.sym("tension",    NMuscle)
    atendon_SX = ca.SX.sym("atendon",    NMuscle)
    shift_SX   = ca.SX.sym("shift",      NMuscle)

    Hilldiff  = ca.SX.zeros(NMuscle, 1)
    FT_out    = ca.SX.zeros(NMuscle, 1)
    Fce_out   = ca.SX.zeros(NMuscle, 1)
    Fpass_out = ca.SX.zeros(NMuscle, 1)
    Fiso_out  = ca.SX.zeros(NMuscle, 1)
    vMmax_out = ca.SX.zeros(NMuscle, 1)
    lTt_out   = ca.SX.zeros(NMuscle, 1)
    lM_out    = ca.SX.zeros(NMuscle, 1)
    lMt_out   = ca.SX.zeros(NMuscle, 1)
    FMvt_out  = ca.SX.zeros(NMuscle, 1)
    vMt_out   = ca.SX.zeros(NMuscle, 1)
    Fpet_out  = ca.SX.zeros(NMuscle, 1)

    for m in range(NMuscle):
        (
            Hilldiff[m], FT_out[m], Fce_out[m], Fpass_out[m],
            Fiso_out[m], vMmax_out[m], lTt_out[m], lM_out[m],
            lMt_out[m], FMvt_out[m], vMt_out[m], Fpet_out[m],
        ) = force_equilibrium_Ftilde_all_tendon(
            a[m], FTtilde[m], dFTtilde[m],
            lMT_sym[m], vMT_sym[m],
            MTparameters_m[[0, 3], m],   # FMo, pennation
            Fvparam, Fpparam, Faparam,
            tension_SX[m], atendon_SX[m], shift_SX[m],
            m_oMFL[m], m_TSL[m], m_vmax[m],
        )

    f_hill = ca.Function(
        "f_forceEquilibrium_FtildeState_all_tendon_M",
        [a, FTtilde, dFTtilde, lMT_sym, vMT_sym,
         tension_SX, atendon_SX, shift_SX, m_oMFL, m_TSL, m_vmax],
        [Hilldiff, FT_out, Fce_out, Fpass_out, Fiso_out,
         vMmax_out, lTt_out, lM_out, lMt_out, FMvt_out, vMt_out, Fpet_out],
    )

    # --- Moment arm dot-product functions ---
    calcMoms = {}
    for n in [27, 13, 12, 4, 6]:
        ma = ca.SX.sym(f"ma{n}", n)
        ft = ca.SX.sym(f"ft{n}", n)
        calcMoms[f"f_T{n}"] = ca.Function(
            f"f_T{n}", [ma, ft], [ca.dot(ma, ft)]
        )

    return f_lMT_vMT_dM, f_hill, calcMoms


# ---------------------------------------------------------------------------
# Cost function CasADi functions
# ---------------------------------------------------------------------------

def build_cost_functions(
    obj_range:   dict,
    nq:          object,   # NQ instance
    NMuscle:     int,
    totalFmax:   float,
    indFmax:     np.ndarray,
):
    """Build all CasADi cost functions used in the NLP objective."""
    cf = {}

    # Pelvis orientations (indices 0..2)
    gpo_e = ca.MX.sym("gpo_e", nq.abs // 2)
    gpo_s = ca.MX.sym("gpo_s", nq.abs // 2)
    val = sum(
        ((gpo_e[i] - gpo_s[i]) / obj_range["q"][i]) ** 2
        for i in range(nq.abs // 2)
    )
    cf["f_J_gPelOri"] = ca.Function("f_J_gPelOri", [gpo_e, gpo_s], [val])

    # Pelvis translations (indices 4..5)
    gpt_e = ca.MX.sym("gpt_e", nq.abs // 2 - 1)
    gpt_s = ca.MX.sym("gpt_s", nq.abs // 2 - 1)
    val = sum(
        ((gpt_e[i] - gpt_s[i]) / obj_range["q"][4 + i]) ** 2
        for i in range(nq.abs // 2 - 1)
    )
    cf["f_J_gPelTra"] = ca.Function("f_J_gPelTra", [gpt_e, gpt_s], [val])

    # Lower-limb joint angles
    n_ll = nq.all - nq.abs - nq.trunk - nq.arms
    llj_e = ca.MX.sym("llj_e", n_ll)
    llj_s = ca.MX.sym("llj_s", n_ll)
    val = sum(
        ((llj_e[i] - llj_s[i]) / obj_range["q"][nq.abs + i]) ** 2
        for i in range(n_ll)
    )
    cf["f_J_lljAngs"] = ca.Function("f_J_lljAngs", [llj_e, llj_s], [val])

    # Upper-limb & trunk joint angles
    n_ul = nq.trunk + nq.arms
    ulj_e = ca.MX.sym("ulj_e", n_ul)
    ulj_s = ca.MX.sym("ulj_s", n_ul)
    val = sum(
        ((ulj_e[i] - ulj_s[i]) / obj_range["q"][20 + i]) ** 2
        for i in range(n_ul)
    )
    cf["f_J_uljAngs"] = ca.Function("f_J_uljAngs", [ulj_e, ulj_s], [val])

    # Accelerations
    accs = ca.MX.sym("accs", nq.all)
    val  = sum(
        (accs[i] / obj_range["uAcc"][i]) ** 2
        for i in range(nq.all)
    )
    cf["f_J_accs"] = ca.Function("f_J_accs", [accs], [val])

    # Muscle activations (weighted by max force fraction)
    act = ca.MX.sym("muscle_act", NMuscle)
    val = sum(
        (act[i] ** 2) * indFmax[i] / totalFmax
        for i in range(NMuscle)
    )
    cf["f_J_muscle_act"] = ca.Function("f_J_muscle_act", [act], [val])

    # Derivative of muscle activations
    dact = ca.MX.sym("dact", NMuscle)
    val  = sum(
        (dact[i] / obj_range["uActdot"][i]) ** 2
        for i in range(NMuscle)
    )
    cf["f_J_dmuscle_act"] = ca.Function("f_J_dmuscle_act", [dact], [val])

    # Tendon forces
    FT_var = ca.MX.sym("FT", NMuscle)
    val    = sum(
        (FT_var[i] / obj_range["FTtilde"][i]) ** 2
        for i in range(NMuscle)
    )
    cf["f_J_FT"] = ca.Function("f_J_FT", [FT_var], [val])

    # Derivative of tendon forces
    dFT = ca.MX.sym("dFT", NMuscle)
    val = sum(
        (dFT[i] / obj_range["dFTtilde"][i]) ** 2
        for i in range(NMuscle)
    )
    cf["f_J_dFT"] = ca.Function("f_J_dFT", [dFT], [val])

    # Reserve actuators
    res = ca.MX.sym("reserves", 2)
    val = sum(
        (res[i] / obj_range["uReserves"][i]) ** 2
        for i in range(2)
    )
    cf["f_J_reserves"] = ca.Function("f_J_reserves", [res], [val])

    # Arm activations
    arms = ca.MX.sym("arm_acts", nq.arms)
    val  = sum(arms[i] ** 2 for i in range(nq.arms))
    cf["f_J_arms"] = ca.Function("f_J_arms", [arms], [val])

    return cf
