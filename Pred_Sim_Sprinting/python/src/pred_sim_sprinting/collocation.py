"""
Collocation scheme for direct collocation optimal control.

Python port of CollocationScheme.m and control_extrapolation.m
Original MATLAB code by Antoine Falisse (2018).
"""
import numpy as np
import casadi as ca


def collocation_scheme(d: int, method: str = "radau"):
    """
    Returns matrices needed for the direct-collocation NLP.

    Parameters
    ----------
    d      : degree of interpolating polynomial
    method : 'radau' or 'legendre'

    Returns
    -------
    tau_root : collocation points (length d+1, first entry 0)
    C        : (d+1) x (d+1) coefficients of the collocation equation
    D        : (d+1,)       coefficients of the continuity equation
    B        : (d+1,)       coefficients of the quadrature function
    """
    tau_root = np.concatenate(([0.0], ca.collocation_points(d, method)))

    C = np.zeros((d + 1, d + 1))
    D = np.zeros(d + 1)
    B = np.zeros(d + 1)

    for j in range(d + 1):
        # Lagrange polynomial coefficients
        coeff = np.array([1.0])
        for r in range(d + 1):
            if r != j:
                coeff = np.polymul(coeff, [1.0, -tau_root[r]])
                coeff /= tau_root[j] - tau_root[r]

        # Continuity equation coefficient (evaluate at tau=1)
        D[j] = np.polyval(coeff, 1.0)

        # Collocation equation coefficients (derivative at each tau_root)
        pder = np.polyder(coeff)
        for r in range(d + 1):
            C[j, r] = np.polyval(pder, tau_root[r])

        # Quadrature coefficient (integral over [0,1])
        pint = np.polyint(coeff)
        B[j] = np.polyval(pint, 1.0)

    return tau_root, C, D, B


def control_extrapolation(tau_roots_col: np.ndarray) -> np.ndarray:
    """
    Coefficients to extrapolate control variables to the start of each
    mesh interval (tau=0) using the collocation-point values.

    Parameters
    ----------
    tau_roots_col : collocation points (excluding tau=0), length d

    Returns
    -------
    D_control : (d,) extrapolation weights
    """
    d = len(tau_roots_col)
    D_control = np.zeros(d)

    for j in range(d):
        coeff = np.array([1.0])
        for r in range(d):
            if r != j:
                coeff = np.polymul(coeff, [1.0, -tau_roots_col[r]])
                coeff /= tau_roots_col[j] - tau_roots_col[r]
        # Evaluate at tau=0
        D_control[j] = np.polyval(coeff, 0.0)

    return D_control
