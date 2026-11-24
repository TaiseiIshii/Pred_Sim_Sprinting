"""
Joint indices, DOF counts, and muscle index helpers.

Python port of the jointi / nq / musInd / mai setup in main_pred_sim_sprinting.m
and MuscleIndices.m / MomentArmIndices.m
"""
from __future__ import annotations
import numpy as np
import scipy.io
from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Joint index definitions (1-based in MATLAB → 0-based here, stored as int)
# ---------------------------------------------------------------------------

@dataclass
class JointIndices:
    """Joint indices (0-based)."""
    # pelvis
    pelvis_tilt: int = 0
    pelvis_list: int = 1
    pelvis_rot:  int = 2
    pelvis_tx:   int = 3
    pelvis_ty:   int = 4
    pelvis_tz:   int = 5
    # right leg
    hip_flex_r:  int = 6
    hip_add_r:   int = 7
    hip_rot_r:   int = 8
    knee_r:      int = 9
    ankle_r:     int = 10
    subt_r:      int = 11
    mtp_r:       int = 12
    # left leg
    hip_flex_l:  int = 13
    hip_add_l:   int = 14
    hip_rot_l:   int = 15
    knee_l:      int = 16
    ankle_l:     int = 17
    subt_l:      int = 18
    mtp_l:       int = 19
    # trunk
    trunk_ext:   int = 20
    trunk_ben:   int = 21
    trunk_rot:   int = 22
    # right arm
    sh_flex_r:   int = 23
    sh_add_r:    int = 24
    sh_rot_r:    int = 25
    elb_r:       int = 26
    pro_r:       int = 27
    wri_flex_r:  int = 28
    wri_dev_r:   int = 29
    # left arm
    sh_flex_l:   int = 30
    sh_add_l:    int = 31
    sh_rot_l:    int = 32
    elb_l:       int = 33
    pro_l:       int = 34
    wri_flex_l:  int = 35
    wri_dev_l:   int = 36


@dataclass
class NQ:
    """Degree-of-freedom counts."""
    all:   int = 37   # total
    abs:   int = 6    # ground-pelvis (0..5)
    trunk: int = 3    # trunk (20..22)
    arms:  int = 14   # arms (23..36)
    leg:   int = 10   # joints needed for polynomials


def make_nq() -> NQ:
    return NQ()


# ---------------------------------------------------------------------------
# Muscle names
# ---------------------------------------------------------------------------

MUSCLE_NAMES_R = [
    'glut_med1_r','glut_med2_r','glut_med3_r',
    'glut_min1_r','glut_min2_r','glut_min3_r','semimem_r',
    'semiten_r','bifemlh_r','bifemsh_r','sar_r','add_long_r',
    'add_brev_r','add_mag1_r','add_mag2_r','add_mag3_r','tfl_r',
    'pect_r','grac_r','glut_max1_r','glut_max2_r','glut_max3_r',
    'iliacus_r','psoas_r','quad_fem_r','gem_r','peri_r',
    'rect_fem_r','vas_med_r','vas_int_r','vas_lat_r','med_gas_r',
    'lat_gas_r','soleus_r','tib_post_r','flex_dig_r','flex_hal_r',
    'tib_ant_r','per_brev_r','per_long_r','per_tert_r','ext_dig_r',
    'ext_hal_r','ercspn_r','intobl_r','extobl_r',
]

# The 3 back muscles (ercspn_l, intobl_l, extobl_l) appended last
MUSCLE_NAMES_BACK_L = ['ercspn_l', 'intobl_l', 'extobl_l']

ALL_MUSCLE_NAMES = MUSCLE_NAMES_R + MUSCLE_NAMES_BACK_L  # 49 total


def muscle_indices(names: List[str]) -> np.ndarray:
    """
    Return 0-based indices of muscles that belong to one leg & back
    (exclude the duplicated left back muscles at the end).

    Equivalent to MuscleIndices.m in the MATLAB code.
    """
    return np.arange(len(names))


def moment_arm_indices(muscle_names: List[str], spanning_info: np.ndarray):
    """
    Build moment-arm index struct.

    spanning_info : (nMuscles, nJoints) boolean matrix, 1 = muscle crosses joint
    Returns a list of dicts with keys 'mus' -> {'l': array, 'r': array}
    (0-based indices within the full bilateral muscle vector)

    Equivalent to MomentArmIndices.m.

    DOF order for polynomials (0-based, 0..9):
      0=hip_flex, 1=hip_add, 2=hip_rot, 3=knee, 4=ankle,
      5=subt, 6=mtp, 7=trunk_ext, 8=trunk_ben, 9=trunk_rot
    """
    n_one_leg = len(muscle_names)  # muscles for one leg + back
    n_joints  = spanning_info.shape[1]
    mai = []
    for j in range(n_joints):
        crossing_l = np.where(spanning_info[:, j] == 1)[0]  # 0-based
        crossing_r = crossing_l.copy()
        # right side is the second half (offset by n_one_leg)
        crossing_r_full = crossing_l + n_one_leg
        mai.append({"mus": {"l": crossing_l, "r": crossing_r_full}})
    return mai
