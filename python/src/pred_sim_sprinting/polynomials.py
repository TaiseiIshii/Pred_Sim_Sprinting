"""
Polynomial muscle-tendon length / velocity / moment-arm approximations.

Python port of n_art_mat_3_cas_SX.m and loadMuscleModelFunctions (polynomial part).
Original MATLAB code by Wouter Aerts, adapted by Antoine Falisse (2018).
"""
import numpy as np
import casadi as ca
import scipy.io


def n_art_mat_3_cas_SX(q, order: int):
    """
    Build the polynomial basis matrix and its joint-angle derivatives
    for up to 4 DOFs, using CasADi SX symbolics.

    Parameters
    ----------
    q     : (1, n_dof) CasADi SX row vector of joint angles
    order : polynomial order

    Returns
    -------
    mat        : (1, nr_coeff) SX - polynomial basis evaluated at q
    diff_mat_q : (nr_coeff, 4) SX - partial derivatives w.r.t. each DOF
    """
    n_dof = q.shape[1]

    # Pad q to 4 DOFs with zeros
    q_all = ca.SX.zeros(1, 4)
    for i in range(n_dof):
        q_all[0, i] = q[0, i]

    # Count coefficients
    nr_coeff = 0
    for n1 in range(order + 1):
        n2s = range(order - n1 + 1) if n_dof >= 2 else [0]
        for n2 in n2s:
            n3s = range(order - n1 - n2 + 1) if n_dof >= 3 else [0]
            for n3 in n3s:
                n4s = range(order - n1 - n2 - n3 + 1) if n_dof >= 4 else [0]
                for _ in n4s:
                    nr_coeff += 1

    mat        = ca.SX.zeros(1, nr_coeff)
    diff_mat_q = ca.SX.zeros(nr_coeff, 4)

    idx = 0
    for n1 in range(order + 1):
        n2s = range(order - n1 + 1) if n_dof >= 2 else [0]
        for n2 in n2s:
            n3s = range(order - n1 - n2 + 1) if n_dof >= 3 else [0]
            for n3 in n3s:
                n4s = range(order - n1 - n2 - n3 + 1) if n_dof >= 4 else [0]
                for n4 in n4s:
                    q1, q2, q3, q4 = q_all[0, 0], q_all[0, 1], q_all[0, 2], q_all[0, 3]

                    mat[0, idx] = q1**n1 * q2**n2 * q3**n3 * q4**n4

                    # Partial derivatives (treat 0^(-1) as 0)
                    def safe_pow(base, exp):
                        return ca.SX(0) if exp == 0 else base**exp

                    diff_mat_q[idx, 0] = n1 * safe_pow(q1, n1 - 1) * q2**n2 * q3**n3 * q4**n4
                    diff_mat_q[idx, 1] = q1**n1 * n2 * safe_pow(q2, n2 - 1) * q3**n3 * q4**n4
                    diff_mat_q[idx, 2] = q1**n1 * q2**n2 * n3 * safe_pow(q3, n3 - 1) * q4**n4
                    diff_mat_q[idx, 3] = q1**n1 * q2**n2 * q3**n3 * n4 * safe_pow(q4, n4 - 1)

                    idx += 1

    return mat, diff_mat_q


def build_lMT_vMT_dM_function(
    musInd: np.ndarray,
    NMuscle: int,
    pathpolynomial: str,
    nq_leg: int,
):
    """
    Build CasADi function for muscle-tendon lengths, velocities, and moment arms.

    Returns f_lMT_vMT_dM(qin, qdotin) -> (lMT, vMT, dM)
    """
    # Load polynomial data
    joint_data   = scipy.io.loadmat(f"{pathpolynomial}/muscle_spanning_joint_INFO_subject9.mat")
    muscle_data  = scipy.io.loadmat(f"{pathpolynomial}/MuscleInfo_subject9.mat", simplify_cells=True)

    muscle_spanning_joint_INFO = joint_data["muscle_spanning_joint_INFO"]
    MuscleInfo = muscle_data["MuscleInfo"]

    # Back muscles are indices 46,47,48 (0-based, correspond to MATLAB 47,48,49)
    # musInd is already 0-based
    back_idx = [46, 47, 48]
    musi_pol = np.concatenate([musInd, back_idx])
    NMuscle_pol = NMuscle // 2 + 3

    muscle_spanning_info_m = muscle_spanning_joint_INFO[musi_pol, :]
    muscles_pol = [MuscleInfo["muscle"][i] for i in musi_pol]

    qin    = ca.SX.sym("qin",    1, nq_leg)
    qdotin = ca.SX.sym("qdotin", 1, nq_leg)

    lMT = ca.SX.zeros(NMuscle_pol, 1)
    vMT = ca.SX.zeros(NMuscle_pol, 1)
    dM  = ca.SX.zeros(NMuscle_pol, nq_leg)

    for i in range(NMuscle_pol):
        crossing = np.where(muscle_spanning_info_m[i, :] == 1)[0]
        order    = int(muscles_pol[i]["order"])
        coeff    = muscles_pol[i]["coeff"].flatten()

        q_cross  = qin[0, crossing]
        mat, diff_mat_q = n_art_mat_3_cas_SX(q_cross, order)

        lMT[i, 0] = mat @ coeff
        vMT[i, 0] = ca.SX(0)

        for k, dof in enumerate(crossing):
            dm_val = -(diff_mat_q[:, k].T @ coeff)
            dM[i, dof] = dm_val
            vMT[i, 0]  = vMT[i, 0] + (-dM[i, dof] * qdotin[0, dof])

    f_lMT_vMT_dM = ca.Function(
        "f_lMT_vMT_dM",
        [qin, qdotin],
        [lMT, vMT, dM]
    )
    return f_lMT_vMT_dM
