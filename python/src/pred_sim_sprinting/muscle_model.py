"""
Hill-type muscle-tendon model.

Python port of ForceEquilibrium_FtildeState_all_tendon_M.m
Original MATLAB code by Antoine Falisse (2018),
based on De Groote et al. (2016) DOI: 10.1007/s10439-016-1591-9
"""
import casadi as ca


def force_equilibrium_Ftilde_all_tendon(
    a, fse, dfse, lMT, vMT, params,
    Fvparam, Fpparam, Faparam,
    tension, aTendon, shift,
    m_oMFl, m_tSL, m_vmax
):
    """
    Hill-type muscle equilibrium using normalised tendon force as state.

    All inputs are CasADi SX/MX scalars (called inside a loop per muscle).

    Parameters
    ----------
    a        : muscle activation
    fse      : normalised tendon force (state)
    dfse     : time-derivative of normalised tendon force (control)
    lMT      : muscle-tendon unit length
    vMT      : muscle-tendon unit velocity
    params   : [FMo, pennation_angle]  (row vector / 2-element)
    Fvparam  : (4,) force-velocity curve parameters
    Fpparam  : (2,) passive force-length parameters
    Faparam  : (8,) active force-length parameters
    tension  : specific tension (scalar, used for mass)
    aTendon  : tendon stiffness coefficient
    shift    : tendon force-length shift
    m_oMFl   : optimal muscle fibre length (symbolic)
    m_tSL    : tendon slack length (symbolic)
    m_vmax   : max shortening velocity (symbolic)

    Returns
    -------
    err, FT, Fce, Fpass, Fiso, vMmax_val,
    lTtilde, lM, lMtilde, FMvtilde, vMtilde, Fpetilde
    """
    FMo    = params[0]
    alphao = params[1]

    Atendonsc = aTendon

    # Inverse tendon force-length characteristic
    lTtilde = ca.log(5.0 * (fse + 0.25 - shift)) / Atendonsc + 0.995

    # Geometric relationships
    lM      = ca.sqrt((m_oMFl * ca.sin(alphao)) ** 2 + (lMT - m_tSL * lTtilde) ** 2)
    lMtilde = lM / m_oMFl

    # Active force-length characteristic
    b11, b21, b31, b41 = Faparam[0], Faparam[1], Faparam[2], Faparam[3]
    b12, b22, b32, b42 = Faparam[4], Faparam[5], Faparam[6], Faparam[7]
    b13, b23, b33, b43 = 0.1, 1.0, 0.5 * (0.5 ** 0.5), 0.0

    def gauss_term(b1, b2, b3, b4):
        num = lMtilde - b2
        den = b3 + b4 * lMtilde
        return b1 * ca.exp(-0.5 * (num / den) ** 2)

    FMltilde = gauss_term(b11, b21, b31, b41) \
             + gauss_term(b12, b22, b32, b42) \
             + gauss_term(b13, b23, b33, b43)
    Fiso = FMltilde

    # Active force-velocity characteristic
    vT      = m_tSL * dfse / (0.2 * Atendonsc * ca.exp(Atendonsc * (lTtilde - 0.995)))
    cos_alpha = (lMT - m_tSL * lTtilde) / lM
    vM      = (vMT - vT) * cos_alpha
    vMmax_val = m_vmax
    vMtilde = vM / vMmax_val

    e1, e2, e3, e4 = Fvparam[0], Fvparam[1], Fvparam[2], Fvparam[3]
    FMvtilde = e1 * ca.log((e2 * vMtilde + e3) + ca.sqrt((e2 * vMtilde + e3) ** 2 + 1)) + e4

    # Active muscle force
    d_damp  = 0.01
    Fcetilde = a * FMltilde * FMvtilde + d_damp * vMtilde
    Fce     = FMo * Fcetilde

    # Passive force-length characteristic
    e0  = 0.6
    kpe = 4.0
    t5  = ca.exp(kpe * (lMtilde - 1.0) / e0)
    Fpetilde = ((t5 - 1.0) - Fpparam[0]) / Fpparam[1]
    Fpass   = FMo * Fpetilde

    # Tendon force
    FT = fse * FMo

    # Equilibrium (normalised)
    err = (Fcetilde + Fpetilde) * cos_alpha - fse

    return err, FT, Fce, Fpass, Fiso, vMmax_val, lTtilde, lM, lMtilde, FMvtilde, vMtilde, Fpetilde
