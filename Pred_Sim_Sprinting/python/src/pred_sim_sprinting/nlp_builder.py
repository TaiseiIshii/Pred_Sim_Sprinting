"""
NLP builder for the sprinting direct-collocation optimal control problem.

Python port of buildNLP() in main_pred_sim_sprinting.m
"""
from __future__ import annotations
import numpy as np
import casadi as ca

# Polynomial function muscle row indices (0-based) that correspond to each
# bilateral side.  Must match _get_lMT_vMT indexing below.
_LEFT_IDX  = list(range(43)) + [46, 47, 48]   # 46 muscles (0..42 + back)
_RIGHT_IDX = list(range(46))                   # 46 muscles


def build_nlp(
    guess:         dict,
    bounds_sc:     dict,
    scaling:       dict,
    nq:            object,
    Options:       dict,
    h:             ca.MX,          # symbolic mesh interval length
    F:             ca.Function,    # external dynamics function
    statesF:       dict,
    contPrms_nsc:  np.ndarray,
    C:             np.ndarray,
    D:             np.ndarray,
    B:             np.ndarray,
    wJ:            np.ndarray,
    costFunctions: dict,
    oMFL_2_nsc:    np.ndarray,
    TSL_2_nsc:     np.ndarray,
    NMuscle:       int,
    vMaxMult:      float,
    outInd:        dict,
    prevSol,
    finalTime_nsc: ca.MX,
    D_controls:    np.ndarray,
    f_lMT_vMT_dM:  ca.Function,
    f_hill:        ca.Function,
    mai:           list,
    file_ext:      str,
    jointi:        object,
):
    """
    Formulate the direct-collocation NLP.

    Returns
    -------
    w, w0, lbw, ubw, J, g, lbg, ubg, g_names, change_disp
    """
    d   = 3          # polynomial degree (Radau)
    N   = Options["N"]

    tensions  = np.ones(NMuscle)
    aTendon   = 35.0 * np.ones(NMuscle)
    shift_arr = np.zeros(NMuscle)
    tact   = 0.015
    tdeact = 0.06
    bodyMass = 72.2

    # NLP containers
    w:    list = []
    w0:   list = []
    lbw:  list = []
    ubw:  list = []
    J         = ca.MX(0)
    g:    list = []
    lbg:  list = []
    ubg:  list = []
    g_names:  list = []

    # Storage for initial/final state references
    Xk_nsc_ini       = None
    actk_nsc_ini     = None
    FTtildek_nsc_ini = None
    armActsk_nsc_ini = None
    dFTtilde_nsc_ini = None
    uActdot_nsc_ini  = None
    uAcc_nsc_ini     = None
    uReserves_nsc_ini = None
    armExct_nsc_ini  = None
    outputF_ini      = None
    knee_pos_R_ini   = None
    knee_pos_L_ini   = None
    change_disp      = None

    def _idx(k, j=None):
        """0-based collocation column index."""
        if j is None:
            return k * (d + 1)
        return k * (d + 1) + j

    for k in range(N):
        # ---- States at mesh point k ----
        Xk = ca.MX.sym(f"X_{k}", 2 * nq.all)
        w.append(Xk)
        lbw += list(bounds_sc["q"]["lower"][:, _idx(k)]) + \
               list(bounds_sc["qdot"]["lower"][:, _idx(k)])
        ubw += list(bounds_sc["q"]["upper"][:, _idx(k)]) + \
               list(bounds_sc["qdot"]["upper"][:, _idx(k)])
        w0  += list(guess["q"][_idx(k), :]) + list(guess["qdot"][_idx(k), :])

        Xk_nsc = Xk * ca.vertcat(scaling["q"], scaling["qdot"])

        # Muscle activations at k
        actk = ca.MX.sym(f"act_{k}", NMuscle)
        w.append(actk);  lbw += list(bounds_sc["act"]["lower"]);  ubw += list(bounds_sc["act"]["upper"])
        w0 += list(guess["act"][:, _idx(k)])
        actk_nsc = actk * scaling["act"]

        # Tendon forces at k
        FTtildek = ca.MX.sym(f"FTtilde_{k}", NMuscle)
        w.append(FTtildek);  lbw += list(bounds_sc["FTtilde"]["lower"]);  ubw += list(bounds_sc["FTtilde"]["upper"])
        w0 += list(guess["FTtilde"][:, _idx(k)])
        FTtildek_nsc = FTtildek * scaling["FTtilde"]

        # Arm activations at k
        armActsk = ca.MX.sym(f"armActs_{k}", nq.arms)
        w.append(armActsk);  lbw += list(bounds_sc["aArms"]["lower"]);  ubw += list(bounds_sc["aArms"]["upper"])
        w0 += list(guess["aArms"][:, _idx(k)])
        armActsk_nsc = armActsk

        if k == 0:
            Xk_nsc_ini       = Xk_nsc
            actk_nsc_ini     = actk_nsc
            FTtildek_nsc_ini = FTtildek_nsc
            armActsk_nsc_ini = armActsk_nsc

        # ---- States at collocation points k,j ----
        Xkj_nsc     = []
        actkj_nsc   = []
        FTtildekj_nsc = []
        armActskj_nsc = []

        for j in range(1, d + 1):
            Xkj_j = ca.MX.sym(f"X_{k}_{j}", 2 * nq.all)
            w.append(Xkj_j)
            lbw += list(bounds_sc["q"]["lower"][:, _idx(k, j)]) + \
                   list(bounds_sc["qdot"]["lower"][:, _idx(k, j)])
            ubw += list(bounds_sc["q"]["upper"][:, _idx(k, j)]) + \
                   list(bounds_sc["qdot"]["upper"][:, _idx(k, j)])
            w0  += list(guess["q"][_idx(k, j), :]) + list(guess["qdot"][_idx(k, j), :])
            Xkj_nsc.append(Xkj_j * ca.vertcat(scaling["q"], scaling["qdot"]))

            actj = ca.MX.sym(f"act_{k}_{j}", NMuscle)
            w.append(actj);  lbw += list(bounds_sc["act"]["lower"]);  ubw += list(bounds_sc["act"]["upper"])
            w0 += list(guess["act"][:, _idx(k, j)])
            actkj_nsc.append(actj * scaling["act"])

            FTj = ca.MX.sym(f"FTtilde_{k}_{j}", NMuscle)
            w.append(FTj);  lbw += list(bounds_sc["FTtilde"]["lower"]);  ubw += list(bounds_sc["FTtilde"]["upper"])
            w0 += list(guess["FTtilde"][:, _idx(k, j)])
            FTtildekj_nsc.append(FTj * scaling["FTtilde"])

            aaj = ca.MX.sym(f"armActs_{k}_{j}", nq.arms)
            w.append(aaj);  lbw += list(bounds_sc["aArms"]["lower"]);  ubw += list(bounds_sc["aArms"]["upper"])
            w0 += list(guess["aArms"][:, _idx(k, j)])
            armActskj_nsc.append(aaj)

        # ---- Controls at collocation points ----
        dFTtildekj_nsc  = []
        uActdotkj_nsc   = []
        uAcckj_nsc      = []
        uReserveskj_nsc = []
        armExctkj_nsc   = []

        for j in range(d):
            col_idx = k * d + j  # 0-based control index

            dFTj = ca.MX.sym(f"dFTtilde_{k}_{j+1}", NMuscle)
            w.append(dFTj);  lbw += list(bounds_sc["dFTtilde"]["lower"]);  ubw += list(bounds_sc["dFTtilde"]["upper"])
            w0 += list(guess["dFTtilde"][:, col_idx])
            dFTtildekj_nsc.append(dFTj * scaling["dFTtilde"])

            uAdj = ca.MX.sym(f"uActdot_{k}_{j+1}", NMuscle)
            w.append(uAdj);  lbw += list(bounds_sc["uActdot"]["lower"]);  ubw += list(bounds_sc["uActdot"]["upper"])
            w0 += list(guess["uActdot"][:, col_idx])
            uActdotkj_nsc.append(uAdj * scaling["uActdot"])

            uAj = ca.MX.sym(f"uAcc_{k}_{j+1}", nq.all)
            w.append(uAj);  lbw += list(bounds_sc["uAcc"]["lower"][:, col_idx]);  ubw += list(bounds_sc["uAcc"]["upper"][:, col_idx])
            w0 += list(guess["uAcc"][col_idx, :])
            uAcckj_nsc.append(uAj * scaling["uAcc"])

            uRj = ca.MX.sym(f"uReserves_{k}_{j+1}", 2)
            w.append(uRj);  lbw += list(bounds_sc["uReserves"]["lower"]);  ubw += list(bounds_sc["uReserves"]["upper"])
            w0 += list(guess["uReserves"][:, col_idx])
            uReserveskj_nsc.append(uRj * scaling["uReserves"])

            aej = ca.MX.sym(f"armExct_{k}_{j+1}", nq.arms)
            w.append(aej);  lbw += list(bounds_sc["eArms"]["lower"]);  ubw += list(bounds_sc["eArms"]["upper"])
            w0 += list(guess["eArms"][:, col_idx])
            armExctkj_nsc.append(aej)

        # ---- Extrapolate controls to start of mesh interval (k==0) ----
        if k == 0:
            dFTtilde_nsc_ini  = sum(D_controls[j] * dFTtildekj_nsc[j]  for j in range(d))
            uActdot_nsc_ini   = sum(D_controls[j] * uActdotkj_nsc[j]   for j in range(d))
            uAcc_nsc_ini      = sum(D_controls[j] * uAcckj_nsc[j]      for j in range(d))
            uReserves_nsc_ini = sum(D_controls[j] * uReserveskj_nsc[j] for j in range(d))
            armExct_nsc_ini   = sum(D_controls[j] * armExctkj_nsc[j]   for j in range(d))

            # Reorder X: [q1, qdot1, q2, qdot2, ...]
            Xk_nsc_ORD = _reorder_states(Xk_nsc, nq.all)

            outputF_ini = F(ca.vertcat(Xk_nsc_ORD, uAcc_nsc_ini,
                                       ca.DM(contPrms_nsc)))
            knee_pos_R_ini = outputF_ini[_s(outInd["knee_r_pos_XYZ_F"])]
            knee_pos_L_ini = outputF_ini[_s(outInd["knee_l_pos_XYZ_F"])]

            # MTU at initial point
            lMTk_lr_ini, vMTk_lr_ini, _, _ = _get_lMT_vMT(
                Xk_nsc, nq, f_lMT_vMT_dM, mai)

            # Hill equilibrium at initial point
            (_, FT_ini, *_) = f_hill(
                actk_nsc_ini, FTtildek_nsc_ini,
                dFTtilde_nsc_ini,
                lMTk_lr_ini, vMTk_lr_ini,
                ca.DM(tensions), ca.DM(aTendon), ca.DM(shift_arr),
                ca.DM(oMFL_2_nsc), ca.DM(TSL_2_nsc),
                ca.DM(oMFL_2_nsc * vMaxMult),
            )

        # ---- Continuity constraints (k > 0) ----
        if k > 0:
            _add_eq(g, lbg, ubg, (Xk_nsc_end - Xk_nsc),           2 * nq.all, g_names, "continuity_X")
            _add_eq(g, lbg, ubg, (actk_nsc_end - actk_nsc),        NMuscle,    g_names, "continuity_act")
            _add_eq(g, lbg, ubg, (FTtildek_nsc_end - FTtildek_nsc) / scaling["FTtilde"],
                    NMuscle, g_names, "continuity_FT")
            _add_eq(g, lbg, ubg, (armActsk_nsc_end - armActsk_nsc), nq.arms,   g_names, "continuity_armActs")

        # ---- End-of-interval prediction (D matrix) ----
        Xk_nsc_end       = D[0] * Xk_nsc
        actk_nsc_end     = D[0] * actk_nsc
        FTtildek_nsc_end = D[0] * FTtildek_nsc
        armActsk_nsc_end = D[0] * armActsk_nsc

        # ---- Loop over collocation points j ----
        for j in range(d):
            # State derivatives via collocation
            Xp_nsc       = C[0, j + 1] * Xk_nsc
            actp_nsc     = C[0, j + 1] * actk_nsc
            FTtildep_nsc = C[0, j + 1] * FTtildek_nsc
            armActsp_nsc = C[0, j + 1] * armActsk_nsc
            for r in range(d):
                Xp_nsc       += C[r + 1, j + 1] * Xkj_nsc[r]
                actp_nsc     += C[r + 1, j + 1] * actkj_nsc[r]
                FTtildep_nsc += C[r + 1, j + 1] * FTtildekj_nsc[r]
                armActsp_nsc += C[r + 1, j + 1] * armActskj_nsc[r]

            # Collocation equations
            _add_eq(g, lbg, ubg, h * uActdotkj_nsc[j] - actp_nsc,
                    NMuscle, g_names, f"col_actdyn_{k}_{j}")
            _add_eq(g, lbg, ubg,
                    (h * dFTtildekj_nsc[j] - FTtildep_nsc) / scaling["FTtilde"],
                    NMuscle, g_names, f"col_FTdyn_{k}_{j}")
            fj_nsc = ca.vertcat(Xkj_nsc[j][nq.all:], uAcckj_nsc[j])
            _add_eq(g, lbg, ubg,
                    (h * fj_nsc - Xp_nsc) / ca.vertcat(scaling["q"], scaling["qdot"]),
                    2 * nq.all, g_names, f"col_skeldyn_{k}_{j}")
            dadt = (armExctkj_nsc[j] - armActskj_nsc[j]) / 0.035
            _add_eq(g, lbg, ubg, h * dadt - armActsp_nsc,
                    nq.arms, g_names, f"col_armdyn_{k}_{j}")

            # Update end-of-interval state
            Xk_nsc_end       += D[j + 1] * Xkj_nsc[j]
            actk_nsc_end     += D[j + 1] * actkj_nsc[j]
            FTtildek_nsc_end += D[j + 1] * FTtildekj_nsc[j]
            armActsk_nsc_end += D[j + 1] * armActskj_nsc[j]

            # Evaluate external dynamics
            Xkj_nsc_ORD = _reorder_states(Xkj_nsc[j], nq.all)
            outputF = F(ca.vertcat(Xkj_nsc_ORD, uAcckj_nsc[j],
                                   ca.DM(contPrms_nsc)))

            # MTU lengths/velocities/moment arms
            lMTk_lr, vMTk_lr, dM_l, dM_r = _get_lMT_vMT(
                Xkj_nsc[j], nq, f_lMT_vMT_dM, mai)

            # Hill equilibrium
            (Hilldiffkj, FTkj, *_) = f_hill(
                actkj_nsc[j], FTtildekj_nsc[j], dFTtildekj_nsc[j],
                lMTk_lr, vMTk_lr,
                ca.DM(tensions), ca.DM(aTendon), ca.DM(shift_arr),
                ca.DM(oMFL_2_nsc), ca.DM(TSL_2_nsc),
                ca.DM(oMFL_2_nsc * vMaxMult),
            )

            # Path constraints: pelvis residuals
            g.append(outputF[0:6] / (bodyMass * 9.81))
            lbg += [0.0] * 6;  ubg += [0.0] * 6
            g_names += ["pelvis_resids"] * 6

            # Arm torques
            arm_slice = slice(jointi.sh_flex_r, jointi.wri_dev_r + 1)
            g.append((outputF[arm_slice] - armActskj_nsc[j] * scaling["uArms"]) / (bodyMass * 9.81))
            lbg += [0.0] * nq.arms;  ubg += [0.0] * nq.arms
            g_names += ["arm_torques"] * nq.arms

            # Muscle-joint moment constraints
            _add_muscle_moment_constraints(
                g, lbg, ubg, g_names,
                outputF, FTkj, mai, jointi, Xkj_nsc[j],
                nq, Options,
                uReserveskj_nsc[j],
                dM_l, dM_r,
            )

            # Contact frame distance constraints
            mag_idx = [outInd["tibia_l_calc_r_mag"], outInd["tibia_r_calc_l_mag"]]
            g.append(outputF[mag_idx])
            lbg += [0.12, 0.12];  ubg += [5.0, 5.0]
            g_names += ["tibia_calc_dist"] * 2

            # Activation dynamics path constraints
            act1 = uActdotkj_nsc[j] + actkj_nsc[j] / tdeact
            act2 = uActdotkj_nsc[j] + actkj_nsc[j] / tact
            g.append(act1);  lbg += [0.0] * NMuscle;  ubg += [np.inf] * NMuscle
            g.append(act2);  lbg += [-np.inf] * NMuscle;  ubg += [1.0 / tact] * NMuscle
            g_names += ["act_path1"] * NMuscle + ["act_path2"] * NMuscle

            # Contraction dynamics path constraint (Hill == 0)
            g.append(Hilldiffkj)
            lbg += [0.0] * NMuscle;  ubg += [0.0] * NMuscle
            g_names += ["hill_eq"] * NMuscle

            # Objective function contributions
            qrow = statesF["q_aux"][_idx(k, j + 1), :]
            J += (
                wJ[0] * B[j + 1] * costFunctions["f_J_gPelOri"](qrow[0:3], Xkj_nsc[j][0:3]) * h
              + wJ[1] * B[j + 1] * costFunctions["f_J_gPelTra"](qrow[4:6], Xkj_nsc[j][4:6]) * h
              + wJ[2] * B[j + 1] * costFunctions["f_J_lljAngs"](
                    np.concatenate([qrow[6:13], qrow[13:20]]),
                    ca.vertcat(Xkj_nsc[j][6:13], Xkj_nsc[j][13:20])) * h
              + wJ[3] * B[j + 1] * costFunctions["f_J_uljAngs"](qrow[20:37], Xkj_nsc[j][20:37]) * h
              + wJ[4] * B[j + 1] * costFunctions["f_J_accs"](uAcckj_nsc[j]) * h
              + wJ[5] * B[j + 1] * costFunctions["f_J_muscle_act"](actkj_nsc[j]) * h
              + wJ[6] * B[j + 1] * costFunctions["f_J_dmuscle_act"](uActdotkj_nsc[j]) * h
              + wJ[7] * B[j + 1] * costFunctions["f_J_FT"](FTtildekj_nsc[j]) * h
              + wJ[8] * B[j + 1] * costFunctions["f_J_dFT"](dFTtildekj_nsc[j]) * h
              + wJ[9] * B[j + 1] * costFunctions["f_J_reserves"](uReserveskj_nsc[j]) * h
              + wJ[10] * B[j + 1] * costFunctions["f_J_arms"](armActskj_nsc[j]) * h
            )

        # ---- Initial constraints (k == 0) ----
        if k == 0:
            # Pose matching
            idx_pose = list(range(0, 3)) + list(range(6, 37))
            g.append(Xk_nsc_ini[idx_pose] - ca.DM(statesF["q_aux"][0, idx_pose]))
            lb_pose = [-np.deg2rad(15)] * 34;  ub_pose = [np.deg2rad(15)] * 34
            lbg += lb_pose;  ubg += ub_pose
            g_names += ["init_pose"] * 34

            # Horizontal pelvis = 0
            g.append(Xk_nsc_ini[3:4])
            lbg += [0.0];  ubg += [0.0]
            g_names += ["init_pelvis_tx"]

            # Vertical GRF on stance foot
            yGRF_r = sum(outputF_ini[outInd["r_contGRF"][i]]
                         for i in range(1, len(outInd["r_contGRF"]), 3))
            g.append(yGRF_r)
            lbg += [20.0];  ubg += [40.0]
            g_names += ["init_yGRF"]

            # HTD / IKTD constraints
            HTD_nom = 0.328890590509637
            IKTD_nom = 0.040824168566493

            if "HTD" in file_ext:
                offset = _parse_offset(file_ext) / 100.0
                sign   = +1 if "Plus" in file_ext else -1
                htd_constraint = (
                    outputF_ini[outInd["r_toes_pos"][0]]
                    - outputF_ini[outInd["posCOM"][0]]
                    - HTD_nom - sign * offset
                )
                _add_eq(g, lbg, ubg, htd_constraint, 1, g_names, "HTD")

            if "IKTD" in file_ext:
                offset = _parse_offset(file_ext) / 100.0
                sign   = +1 if "Plus" in file_ext else -1
                iktd_constraint = (
                    knee_pos_R_ini[0] - knee_pos_L_ini[0]
                    - IKTD_nom - sign * offset
                )
                _add_eq(g, lbg, ubg, iktd_constraint, 1, g_names, "IKTD")

        # ---- Symmetry constraints (k == N-1, last interval) ----
        if k == N - 1:
            Xk_nsc_fin       = Xkj_nsc[j]
            actk_nsc_fin     = actkj_nsc[j]
            FTtildek_nsc_fin = FTtildekj_nsc[j]
            armActsk_nsc_fin = armActskj_nsc[j]

            change_disp = Xk_nsc_fin[3] - Xk_nsc_ini[3]

            # Horizontal displacement bound
            g.append(Xk_nsc_fin[3:4])
            lbg += [0.0];  ubg += [2.47]
            g_names += ["final_tx"]

            _add_symmetry_constraints(
                g, lbg, ubg, g_names,
                Xk_nsc_ini, Xk_nsc_fin,
                actk_nsc_ini, actk_nsc_fin,
                FTtildek_nsc_ini, FTtildek_nsc_fin,
                armActsk_nsc_ini, armActsk_nsc_fin,
                dFTtilde_nsc_ini, dFTtildekj_nsc[j],
                uActdot_nsc_ini, uActdotkj_nsc[j],
                uAcc_nsc_ini, uAcckj_nsc[j],
                uReserves_nsc_ini, uReserveskj_nsc[j],
                armExct_nsc_ini, armExctkj_nsc[j],
                NMuscle, nq,
            )

    return w, w0, lbw, ubw, J, g, lbg, ubg, g_names, change_disp


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _s(idx_range):
    """Convert a MATLAB-style inclusive range to a Python slice (0-based input expected)."""
    if hasattr(idx_range, "__len__"):
        return list(idx_range)
    return idx_range


def _add_eq(g, lbg, ubg, expr, n, g_names, name):
    g.append(expr)
    lbg += [0.0] * n
    ubg += [0.0] * n
    g_names += [name] * n


def _reorder_states(X_nsc, nq_all):
    """Reorder [q1..qN, qdot1..qdotN] -> [q1, qdot1, q2, qdot2, ...]."""
    out = ca.MX.zeros(nq_all * 2, 1)
    for i in range(nq_all):
        out[2 * i,     0] = X_nsc[i]
        out[2 * i + 1, 0] = X_nsc[nq_all + i]
    return out


def _get_lMT_vMT(X_nsc, nq, f_lMT_vMT_dM, mai):
    """
    Compute bilateral muscle-tendon lengths, velocities, and moment arm matrices.

    Returns (lMTk_lr, vMTk_lr, dM_l, dM_r).
    dM_l / dM_r shape: (NMuscle_pol, nq_leg) – polynomial-indexed moment arms.
    """
    j = nq  # shorthand
    # Left leg joints (0-based)
    leg_l = [j.hip_flex_l, j.hip_add_l, j.hip_rot_l, j.knee_l,
             j.ankle_l, j.subt_l, j.mtp_l,
             j.trunk_ext, j.trunk_ben, j.trunk_rot]
    leg_r = [j.hip_flex_r, j.hip_add_r, j.hip_rot_r, j.knee_r,
             j.ankle_r, j.subt_r, j.mtp_r,
             j.trunk_ext, j.trunk_ben, j.trunk_rot]

    qin_l    = ca.horzcat(*[X_nsc[i] for i in leg_l])
    qdotin_l = ca.horzcat(*[X_nsc[j.all + i] for i in leg_l])
    qin_r    = ca.horzcat(*[X_nsc[i] for i in leg_r])
    qdotin_r = ca.horzcat(*[X_nsc[j.all + i] for i in leg_r])

    lMTk_l, vMTk_l, dM_l = f_lMT_vMT_dM(qin_l, qdotin_l)
    lMTk_r, vMTk_r, dM_r = f_lMT_vMT_dM(qin_r, qdotin_r)

    lMTk_lr = ca.vertcat(lMTk_l[_LEFT_IDX], lMTk_r[_RIGHT_IDX])
    vMTk_lr = ca.vertcat(vMTk_l[_LEFT_IDX], vMTk_r[_RIGHT_IDX])
    return lMTk_lr, vMTk_lr, dM_l, dM_r


def _add_muscle_moment_constraints(
    g, lbg, ubg, g_names,
    outputF, FTkj, mai, jointi, Xkj_nsc,
    nq, Options, uReserveskj_nsc,
    dM_l, dM_r,
):
    """
    Add equality constraints: muscle moments == joint moments from dynamics.

    Moment arm sign convention follows the polynomial: MA = -dLMT/dq.
    dM_l / dM_r : (NMuscle_pol, nq_leg) CasADi DM from f_lMT_vMT_dM.
    """
    MTP_stiff = Options["MTP_stiff"]
    ji = jointi
    n_one_leg = len(_LEFT_IDX)   # 46

    def _poly_ma_l(mus_l_idx, poly_joint_col):
        """Moment arms for left-side muscles crossing poly joint col."""
        poly_rows = [_LEFT_IDX[m] for m in mus_l_idx]
        return ca.vertcat(*[dM_l[r, poly_joint_col] for r in poly_rows])

    def _poly_ma_r(mus_r_idx, poly_joint_col):
        """Moment arms for right-side muscles crossing poly joint col (r indices are offset by n_one_leg)."""
        poly_rows = [_RIGHT_IDX[m - n_one_leg] for m in mus_r_idx]
        return ca.vertcat(*[dM_r[r, poly_joint_col] for r in poly_rows])

    # poly_joint_col: column in dM corresponding to each anatomical joint
    # Order: 0=hip_flex, 1=hip_add, 2=hip_rot, 3=knee, 4=ankle,
    #        5=subt,     6=mtp,      7=trunk_ext, 8=trunk_ben, 9=trunk_rot
    joint_defs = [
        # (poly_col, mai_idx, l_dof, r_dof, reserve_idx)
        (0,  0,  ji.hip_flex_l, ji.hip_flex_r, None),
        (1,  1,  ji.hip_add_l,  ji.hip_add_r,  None),
        (2,  2,  ji.hip_rot_l,  ji.hip_rot_r,  None),
        (3,  3,  ji.knee_l,     ji.knee_r,     None),
        (4,  4,  ji.ankle_l,    ji.ankle_r,    None),
        (5,  5,  ji.subt_l,     ji.subt_r,     None),
        (6,  6,  ji.mtp_l,      ji.mtp_r,      (0, 1)),
    ]

    for poly_col, mai_idx, l_dof, r_dof, res_idx in joint_defs:
        for side, dof, ma_fn, mus_key, res_i in [
            ("l", l_dof, _poly_ma_l, "l", res_idx[0] if res_idx else None),
            ("r", r_dof, _poly_ma_r, "r", res_idx[1] if res_idx else None),
        ]:
            mus_idx  = mai[mai_idx]["mus"][mus_key]
            Ft_side  = FTkj[mus_idx]
            MA_side  = ma_fn(mus_idx, poly_col)
            T_side   = ca.dot(MA_side, Ft_side)

            resid_term = ca.MX(0)
            if res_i is not None:
                resid_term = uReserveskj_nsc[res_i] - MTP_stiff * Xkj_nsc[dof]
            g.append(T_side - outputF[dof] + resid_term)
            lbg += [0.0];  ubg += [0.0]
            g_names += [f"joint_{dof}_moment_{side}"]

    # Trunk joints (use bilateral stacking)
    trunk_defs = [
        (7,  7,  8,  ji.trunk_ext, "trunk_ext"),
        (8,  8,  9,  ji.trunk_ben, "trunk_ben"),
        (9,  9,  10, ji.trunk_rot, "trunk_rot"),
    ]
    for poly_col, mai_l_idx, mai_r_idx, dof, name in trunk_defs:
        mus_l  = mai[mai_l_idx]["mus"]["l"]
        mus_r  = mai[mai_r_idx]["mus"]["r"]
        MA_l   = _poly_ma_l(mus_l, poly_col)
        MA_r   = _poly_ma_r(mus_r, poly_col)
        Ft_l   = FTkj[mus_l]
        Ft_r   = FTkj[mus_r]
        T      = ca.dot(MA_l, Ft_l) + ca.dot(MA_r, Ft_r)
        g.append(T - outputF[dof])
        lbg += [0.0];  ubg += [0.0]
        g_names += [f"{name}_moment"]


def _add_symmetry_constraints(
    g, lbg, ubg, g_names,
    X_ini, X_fin,
    act_ini, act_fin,
    FT_ini,  FT_fin,
    armActs_ini, armActs_fin,
    dFT_ini,     dFT_fin,
    uActdot_ini, uActdot_fin,
    uAcc_ini,    uAcc_fin,
    uRes_ini,    uRes_fin,
    armExct_ini, armExct_fin,
    NMuscle, nq,
):
    """Symmetry constraints between first and last collocation point."""
    def _eq(expr, n, name):
        g.append(expr);  lbg += [0.0]*n;  ubg += [0.0]*n;  g_names += [name]*n

    # Leg joint positions (right ini = left fin, left ini = right fin)
    _eq(X_ini[6:13]   - X_fin[13:20], 7, "sym_q_leg_r2l")
    _eq(X_ini[13:20]  - X_fin[6:13],  7, "sym_q_leg_l2r")
    # Pelvis vertical/lateral
    _eq(X_ini[4:6]    - X_fin[4:6],   2, "sym_q_pelvis_yz")
    # Sagittal/symmetric DOFs
    _eq(X_ini[[0, 20]] - X_fin[[0, 20]], 2, "sym_q_tilt_trunk")
    _eq(X_ini[[1, 2, 21, 22]] + X_fin[[1, 2, 21, 22]], 4, "sym_q_asym")
    # Arms
    _eq(X_ini[23:30]  - X_fin[30:37], 7, "sym_q_arm_r2l")
    _eq(X_ini[30:37]  - X_fin[23:30], 7, "sym_q_arm_l2r")

    # Velocities (offset by nq.all)
    off = nq.all
    _eq(X_ini[off+6:off+13]  - X_fin[off+13:off+20], 7, "sym_qdot_leg_r2l")
    _eq(X_ini[off+13:off+20] - X_fin[off+6:off+13],  7, "sym_qdot_leg_l2r")
    _eq(X_ini[off+3:off+5]   - X_fin[off+3:off+5],   2, "sym_qdot_pelvis_yz")
    _eq(X_ini[off+5:off+6]   + X_fin[off+5:off+6],   1, "sym_qdot_pelvis_tz")
    _eq(X_ini[[off+0, off+20]] - X_fin[[off+0, off+20]], 2, "sym_qdot_tilt_trunk")
    _eq(X_ini[[off+1, off+2, off+21, off+22]] + X_fin[[off+1, off+2, off+21, off+22]], 4, "sym_qdot_asym")
    _eq(X_ini[off+23:off+30] - X_fin[off+30:off+37], 7, "sym_qdot_arm_r2l")
    _eq(X_ini[off+30:off+37] - X_fin[off+23:off+30], 7, "sym_qdot_arm_l2r")

    # Muscle activations / tendon forces
    half = NMuscle // 2
    _eq(act_ini[:half]    - act_fin[half:], half, "sym_act_r2l")
    _eq(act_ini[half:]    - act_fin[:half], half, "sym_act_l2r")
    _eq(FT_ini[:half]     - FT_fin[half:],  half, "sym_FT_r2l")
    _eq(FT_ini[half:]     - FT_fin[:half],  half, "sym_FT_l2r")

    # Arm activations/excitations
    half_a = nq.arms // 2
    _eq(armActs_ini[:half_a]  - armActs_fin[half_a:],   half_a, "sym_armActs_r2l")
    _eq(armActs_ini[half_a:]  - armActs_fin[:half_a],   half_a, "sym_armActs_l2r")
    _eq(armExct_ini[:half_a]  - armExct_fin[half_a:],   half_a, "sym_armExct_r2l")
    _eq(armExct_ini[half_a:]  - armExct_fin[:half_a],   half_a, "sym_armExct_l2r")

    # Derivative tendon forces / activations
    _eq(dFT_ini[:half]     - dFT_fin[half:],      half, "sym_dFT_r2l")
    _eq(dFT_ini[half:]     - dFT_fin[:half],       half, "sym_dFT_l2r")
    _eq(uActdot_ini[:half] - uActdot_fin[half:],   half, "sym_dact_r2l")
    _eq(uActdot_ini[half:] - uActdot_fin[:half],   half, "sym_dact_l2r")

    # Reserve actuators
    _eq(uRes_ini[0:1] - uRes_fin[1:2], 1, "sym_res_r2l")
    _eq(uRes_ini[1:2] - uRes_fin[0:1], 1, "sym_res_l2r")

    # Accelerations
    _eq(uAcc_ini[6:13]   - uAcc_fin[13:20], 7, "sym_uAcc_leg_r2l")
    _eq(uAcc_ini[13:20]  - uAcc_fin[6:13],  7, "sym_uAcc_leg_l2r")
    _eq(uAcc_ini[3:5]    - uAcc_fin[3:5],   2, "sym_uAcc_pel_yz")
    _eq(uAcc_ini[5:6]    + uAcc_fin[5:6],   1, "sym_uAcc_pel_tz")
    _eq(uAcc_ini[[0, 20]] - uAcc_fin[[0, 20]], 2, "sym_uAcc_tilt")
    _eq(uAcc_ini[[1, 2, 21, 22]] + uAcc_fin[[1, 2, 21, 22]], 4, "sym_uAcc_asym")
    _eq(uAcc_ini[23:30]  - uAcc_fin[30:37], 7, "sym_uAcc_arm_r2l")
    _eq(uAcc_ini[30:37]  - uAcc_fin[23:30], 7, "sym_uAcc_arm_l2r")


def _parse_offset(file_ext: str) -> int:
    """Extract numeric offset from simulation type string, e.g. '_HTD_Plus_6' -> 6."""
    import re
    m = re.search(r"(\d+)$", file_ext)
    if m:
        val = int(m.group(1))
        return val if val > 0 else 10  # handle trailing 0 edge case
    return 0
