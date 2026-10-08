"""
I/O utilities: read OpenSim .mot files, load .mat data, extract muscle properties.

Python port of readMOT.m, extractMuscProperties.m, and write_motionFile.m
"""
from __future__ import annotations
import re
import numpy as np
import scipy.io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# MOT file reader
# ---------------------------------------------------------------------------

@dataclass
class MotFile:
    labels: list[str]
    data:   np.ndarray
    nr:     int = 0
    nc:     int = 0
    inDeg:  str = "yes"


def read_mot(fname: str | Path) -> MotFile:
    """
    Read an OpenSim .mot / .sto storage file.

    Returns a MotFile with .labels and .data attributes.
    """
    path = Path(fname)
    if not path.exists():
        raise FileNotFoundError(f"MOT file not found: {fname}")

    with path.open("r", encoding="utf-8", errors="replace") as fid:
        lines = fid.readlines()

    nr, nc = 0, 0
    in_deg = "yes"
    header_end = 0

    for i, line in enumerate(lines):
        line_s = line.strip()
        if line_s.lower().startswith("endheader"):
            header_end = i
            break
        m = re.match(r"datacolumns\s+(\d+)", line_s, re.IGNORECASE)
        if m:
            nc = int(m.group(1))
        m = re.match(r"datarows\s+(\d+)", line_s, re.IGNORECASE)
        if m:
            nr = int(m.group(1))
        m = re.match(r"nColumns\s*=\s*(\d+)", line_s, re.IGNORECASE)
        if m:
            nc = int(m.group(1))
        m = re.match(r"nRows\s*=\s*(\d+)", line_s, re.IGNORECASE)
        if m:
            nr = int(m.group(1))
        m = re.match(r"inDegrees\s*=\s*(\S+)", line_s, re.IGNORECASE)
        if m:
            in_deg = m.group(1).strip()

    # Column labels line follows endheader (possibly after a blank line)
    label_line_idx = header_end + 1
    while label_line_idx < len(lines) and lines[label_line_idx].strip() == "":
        label_line_idx += 1

    labels = lines[label_line_idx].split()

    # Parse numeric data
    data_lines = lines[label_line_idx + 1:]
    data_rows = []
    for line in data_lines:
        line = line.strip()
        if not line:
            continue
        vals = line.split()
        try:
            data_rows.append([float(v) for v in vals])
        except ValueError:
            continue

    data = np.array(data_rows)
    if data.ndim == 1:
        data = data.reshape(-1, 1)

    return MotFile(
        labels=labels,
        data=data,
        nr=data.shape[0],
        nc=data.shape[1],
        inDeg=in_deg,
    )


def write_mot(fname: str | Path, labels: list[str], data: np.ndarray):
    """Write data as an OpenSim .mot storage file."""
    path = Path(fname)
    path.parent.mkdir(parents=True, exist_ok=True)
    nr, nc = data.shape
    with path.open("w") as f:
        f.write(f"{path.stem}\n")
        f.write("version=1\n")
        f.write(f"nRows={nr}\n")
        f.write(f"nColumns={nc}\n")
        f.write("inDegrees=yes\n")
        f.write("endheader\n")
        f.write("\t".join(labels) + "\n")
        for row in data:
            f.write("\t".join(f"{v:.10f}" for v in row) + "\n")


# ---------------------------------------------------------------------------
# MAT file helpers
# ---------------------------------------------------------------------------

def load_mat(path: str | Path) -> dict:
    """Load a MATLAB .mat file and return a dict."""
    return scipy.io.loadmat(str(path), simplify_cells=True)


def load_contact_params(util_dir: str | Path) -> np.ndarray:
    """
    Load contact model parameters from UtilityFunctions folder.

    Returns contPrms_nsc = [simultOptContPrms; mu_s; mu_d; mu_v; tv]
    """
    mat = load_mat(
        Path(util_dir) / "Sph_Plane_simultOptContPrms_Fmax_2_Vmax_12.mat"
    )
    params = mat["simultOptContPrms"].flatten()
    mu_s, mu_d, mu_v, tv = 0.95, 0.3, 0.3, 0.001
    return np.concatenate([params, [mu_s, mu_d, mu_v, tv]])


def load_muscle_curve_params(muscle_model_dir: str | Path) -> tuple:
    """Load Fvparam, Fpparam, Faparam from MuscleModel directory."""
    d = Path(muscle_model_dir)
    Fv = load_mat(d / "Fvparam.mat")["Fvparam"].flatten()
    Fp = load_mat(d / "Fpparam.mat")["Fpparam"].flatten()
    Fa = load_mat(d / "Faparam.mat")["Faparam"].flatten()
    return Fv, Fp, Fa


# ---------------------------------------------------------------------------
# Muscle property extraction
# ---------------------------------------------------------------------------

def extract_musc_properties(model_file: str | Path, muscle_names: list[str]) -> np.ndarray:
    """
    Extract muscle-tendon properties from an OpenSim .osim model file.

    Requires the `opensim` Python package (opensim-core).
    Falls back to XML parsing if opensim is not installed.

    Returns a (5, nMuscles+3) array:
        row 0: max isometric force
        row 1: optimal fibre length
        row 2: tendon slack length
        row 3: pennation angle at optimal fibre length
        row 4: max contraction velocity (= 10 * optimal fibre length)
    """
    try:
        import opensim
        return _extract_with_opensim(model_file, muscle_names)
    except ImportError:
        return _extract_with_xml(model_file, muscle_names)


def _extract_with_opensim(model_file, muscle_names):
    import opensim
    model = opensim.Model(str(model_file))
    model.initSystem()
    muscles = model.getMuscles()
    n = len(muscle_names)
    props = np.zeros((5, n + 3))
    for i, name in enumerate(muscle_names):
        m = muscles.get(name)
        props[0, i] = m.getMaxIsometricForce()
        props[1, i] = m.getOptimalFiberLength()
        props[2, i] = m.getTendonSlackLength()
        props[3, i] = m.getPennationAngleAtOptimalFiberLength()
        props[4, i] = props[1, i] * 10.0
    # Last 3 = back muscles repeated (ercspn, intobl, extobl)
    props[:, -3] = props[:, -6]
    props[:, -2] = props[:, -5]
    props[:, -1] = props[:, -4]
    return props


def _extract_with_xml(model_file, muscle_names):
    """
    Parse .osim XML directly for muscle properties without OpenSim Python.
    """
    import xml.etree.ElementTree as ET

    tree = ET.parse(str(model_file))
    root = tree.getroot()

    # Build lookup: muscle_name -> element
    muscle_dict = {}
    for m in root.iter():
        if m.tag in ("Millard2012EquilibriumMuscle", "Thelen2003Muscle",
                     "RigidTendonMuscle"):
            name = m.get("name", "")
            muscle_dict[name] = m

    def get_val(elem, tag, default=0.0):
        child = elem.find(tag)
        if child is not None and child.text:
            try:
                return float(child.text.strip())
            except ValueError:
                pass
        return default

    n = len(muscle_names)
    props = np.zeros((5, n + 3))
    for i, name in enumerate(muscle_names):
        elem = muscle_dict.get(name)
        if elem is None:
            raise ValueError(
                f"Muscle '{name}' not found in {model_file}.\n"
                "Install opensim Python package for robust property extraction:\n"
                "  conda install -c opensim-org opensim"
            )
        props[0, i] = get_val(elem, "max_isometric_force")
        props[1, i] = get_val(elem, "optimal_fiber_length")
        props[2, i] = get_val(elem, "tendon_slack_length")
        props[3, i] = get_val(elem, "pennation_angle_at_optimal")
        props[4, i] = props[1, i] * 10.0

    props[:, -3] = props[:, -6]
    props[:, -2] = props[:, -5]
    props[:, -1] = props[:, -4]
    return props
