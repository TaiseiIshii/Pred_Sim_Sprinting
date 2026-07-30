# Pred_Sim_Sprinting

**Predictive Simulations of Sprinting — Optimal Control Framework**

> _Simulations reveal how touchdown kinematic variables affect top sprinting speed: implications for coaching_
>
> BioRxiv: <https://www.biorxiv.org/content/10.1101/2024.10.08.617292v1>

---

## Overview

This repository contains the full optimal control framework for predictive simulations of human sprinting. It uses **direct collocation** with **CasADi** to solve musculoskeletal optimal control problems that predict sprinting kinematics and kinetics.

The framework investigates how **horizontal touchdown distance (HTD)** and **inter-knee touchdown distance (IKTD)** affect top sprinting speed through systematic perturbation analysis.

### Key Features

- 3D musculoskeletal model (modified Hamner model with foot contact)
- Hill-type muscle model with polynomial approximations of muscle-tendon properties
- Implicit dynamics formulation with custom ground contact model
- Adjustable mesh resolution (N=50, 100, 500)
- Warm-start capability across mesh resolutions
- Comprehensive post-processing and visualization tools

---

## Repository Structure

```
Pred_Sim_Sprinting/
├── MainFunctions/           # Simulation entry points
│   ├── main_pred_sim_sprinting.m       # Base simulation (N=50)
│   ├── main_pred_sim_sprinting_N100.m  # Mesh convergence (N=100)
│   ├── main_pred_sim_sprinting_N500.m  # Fine resolution (N=500)
│   ├── checkSimulationType.m
│   └── ExperimentalData/    # Reference kinematics (IK splines)
├── ExternalFunctions/       # C++ source & compiled DLLs (dynamics)
├── MuscleModel/             # Hill-type muscle parameters & functions
├── Polynomials/             # Polynomial fits for muscle-tendon lengths
├── CollocationScheme/       # Direct collocation implementation
├── UtilityFunctions/        # Signal processing, I/O, stride generation
├── OpenSimModel/            # Scaled OpenSim musculoskeletal model (.osim)
├── Results/                 # Simulation outputs (not tracked in git)
├── Videos/                  # Visualization outputs (not tracked in git)
├── analysis/                # Python post-processing & visualization scripts
├── docs/                    # Setup guides and troubleshooting
├── environment.yml          # Conda environment specification
├── setup_paths.m            # MATLAB path initialization
└── README.md
```

---

## Requirements

| Software | Version | Notes |
|----------|---------|-------|
| **MATLAB** | 2022b (tested on 2017b+) | Core simulation engine |
| **CasADi** | 3.3.0+ | Symbolic framework for optimal control |
| **Python** | 3.9+ | Post-processing & visualization (optional) |

### Hardware

Simulations were performed on a Dell laptop:
- CPU: Intel Core i9-11900H @ 2.50GHz (8 cores)
- RAM: 32 GB
- OS: Windows 10/11

---

## Quick Start

### 1. Install CasADi for MATLAB

Download from <https://web.casadi.org/get/> and add the folder to your MATLAB path.

### 2. Clone & set up paths

```matlab
cd('path/to/Pred_Sim_Sprinting')
setup_paths   % Adds all subdirectories to MATLAB path
```

### 3. Generate polynomial approximations (one-time)

```matlab
cd Polynomials
mainPolynomials
```

### 4. Run a simulation

```matlab
cd MainFunctions
main_pred_sim_sprinting   % Runs nominal (optimal) sprinting simulation
```

To change the simulation condition, edit `simulation_type` in the script:

| `simulation_type` | Description |
|-------------------|-------------|
| `'_Nominal'` | Optimal/nominal sprinting |
| `'_HTD_Plus_6'` | HTD increased by 6 cm |
| `'_HTD_Minus_6'` | HTD decreased by 6 cm |
| `'_IKTD_Plus_6'` | IKTD increased by 6 cm |
| `'_IKTD_Minus_6'` | IKTD decreased by 6 cm |

Supported ranges: `±1, ±2, ±4, ±6, ±8, ±10` cm for both HTD and IKTD.

### 5. Mesh convergence (optional)

After the N=50 baseline completes, run higher-resolution simulations that use the N=50 solution as a warm start:

```matlab
main_pred_sim_sprinting_N100   % N=100 mesh intervals
main_pred_sim_sprinting_N500   % N=500 mesh intervals
```

---

## Simulation Outputs

Results are saved to `Results/` with the naming convention:

```
pred_sprinting_data_DD-Month-YYYY__HH-MM-SS___<SimType>.mat   % Full solution data
pred_sprinting_coords_...___<SimType>.mot                      % Joint coordinates (OpenSim)
pred_sprinting_acts_...___<SimType>.sto                        % Muscle activations
pred_sprinting_...__<SimType>_GRF.mot                          % Ground reaction forces
```

---

## Post-Processing & Visualization

Python scripts for analysis are in the `analysis/` directory. Set up the environment first:

```bash
conda env create -f environment.yml
conda activate pred_sim_sprinting
```

Key scripts:

| Script | Description |
|--------|-------------|
| `post_process_results.py` | Export results to CSV and generate overview plots |
| `analyze_com_vertical.py` | Center of mass trajectory analysis |
| `compare_experimental_vs_simulation.py` | Experimental vs. simulation comparison |
| `visualize_form_comparison_v2.py` | Stick figure overlay visualization |
| `overlay_N50_vs_N100.py` | Mesh convergence overlay comparison |

### Pelvic-tilt strain study visualizations (new)

| Script | Description |
|--------|-------------|
| `analyze_pelvic_shift.m` | Cross-condition hamstring strain metrics + dose-response slopes |
| `compute_osim_muscle_paths.py` | **Precompute** (OpenSim Python API): anatomically-correct **wrapped** muscle paths + body transforms + activation/force + GRF → `_muscle_cache.pkl` |
| `visualize_pelvic_shift_musculoskeletal.py` | **Rich 3D**: real OpenSim bones + full-body wrapped muscles + GRF arrows. `--color strain` (hamstring stretch) or `--color activation` (EMG-like) |
| `visualize_pelvic_shift_smpl.py` | **3D human**: SMPL-style skinned body (soft-body; real-SMPL hook via `--smpl_model`, license required) |
| `visualize_pelvic_shift_motion.py` | Lightweight stick-figure comparison (all 7 conditions) |
| `probe_pelvic_shift.py` / `probe_ham_metrics.py` | Quick Python verification of the manipulation & strain |

> Muscle visualization is two-step: run `compute_osim_muscle_paths.py` once in an
> **OpenSim-enabled** Python env (provides wrapped muscle geometry), then render with
> `visualize_pelvic_shift_musculoskeletal.py` in a **pyvista** env.

---

## Pelvic-tilt hamstring strain study

## Documentation

Additional guides are available in `docs/`:

| Document | Content |
| --- | --- |
| [QUICKSTART.md](docs/QUICKSTART.md) | Step-by-step beginner's guide (日本語) |
| [SETUP_GUIDE_JP.md](docs/SETUP_GUIDE_JP.md) | Detailed setup instructions (日本語) |
| [DETAILED_EXECUTION_GUIDE.md](docs/DETAILED_EXECUTION_GUIDE.md) | Execution walkthrough with expected outputs |
| [TROUBLESHOOTING_GUIDE.md](docs/TROUBLESHOOTING_GUIDE.md) | Common issues and solutions |
| [Conference_Poster_Plan.md](docs/Conference_Poster_Plan.md) | Conference/poster hypothesis, validation, figure, and Q&A plan |

---

## Pelvic-tilt hamstring strain study

A causal study applying this framework to ask **how anterior/posterior pelvic tilt
(`pelvis_tilt`) affects sprinting speed and hamstring strain-injury risk**. The pelvis
tilt waveform is rigidly shifted by a fixed offset (±6°, 2° steps; 7 conditions) and the
task is re-optimized, then hamstring stretch metrics are compared across conditions.

- **Plain-language summary (日本語):** [Results/PelvicShift_Study/SUMMARY_JP.md](Results/PelvicShift_Study/SUMMARY_JP.md)
- **Full report:** [Results/PelvicShift_Study/REPORT.md](Results/PelvicShift_Study/REPORT.md)
- **Rich videos & figures:** `Results/PelvicShift_Study/` (musculoskeletal / SMPL / stick-figure MP4s, dose-response figures)

Key finding: increasing anterior pelvic tilt monotonically increases the peak normalized
fiber length and passive force of the **biarticular** hamstrings (semimembranosus most),
while the monoarticular biceps femoris short head is unchanged — with a small speed cost.

---

## Injury-minimising optimal-technique study (speed–safety Pareto, RQ3+RQ4)

A **prescriptive** extension that moves the framework from *why is it risky* to *how should
you run*. A smooth biarticular-hamstring fascicle-overstretch penalty (new objective weight
`wJ(13)`) is added to the maximal-sprint cost and its weight is swept to trace the
**top-speed vs peak-fascicle-strain Pareto frontier**, on the nominal athlete (RQ3) and on
at-risk virtual athletes (short fascicle / weak) to compare **technique change vs training
adaptation** (RQ4).

- **Full report:** [docs/Hamstring_Pareto_Study_Report.md](docs/Hamstring_Pareto_Study_Report.md)
- **3D musculoskeletal render:** `Results/HamPareto_Study/ham_pareto_musculoskeletal_hero.png`
  (real OpenSim bones + wrapped hamstrings colored by fascicle strain + GRF; running animation
  `_sidebyside.mp4` and inline `_sidebyside.gif` via `--gif`). Two-step like the pelvic study:
  `compute_osim_muscle_paths_pareto.py` (OpenSim env) → `visualize_ham_pareto_musculoskeletal.py`
  (pyvista env). A stick-figure + joint-angle view (`visualize_ham_pareto_motion.py`) complements it.
- **Figures & animation:** `Results/HamPareto_Study/` (`pareto_frontier.png`,
  `technique_vs_training.png`, `permuscle_vs_weight.png`, `anim_pareto_sweep.gif`,
  `pareto_frontier.csv`)

Key findings: (1) a **"free-lunch" region** exists — the nominal athlete can cut peak
fascicle strain ~3.9% for only ~0.24% speed loss (up to −12% for −2.2%); (2) the frontier
is far **steeper for the short-fascicle athlete** (reaching safety costs ~6–15% speed),
whereas **fascicle-lengthening training reduces strain *and* raises speed** — so for
architectural risk, fix the architecture, not the technique; (3) for the weak athlete,
strengthening and technique are **orthogonal levers** (speed vs strain).

Run it (from repo root):
```bat
run_ham_pareto.bat pilot      REM nominal w0000/w0200/w0800 (de-risk)
run_ham_pareto.bat nominal    REM full nominal frontier (8 weights)
run_ham_pareto.bat athletes   REM short + weak athletes (RQ4)
run_ham_pareto.bat analyze    REM Pareto frontier analysis (Python)
```

---

## External Functions (Dynamics)

The dynamics are computed via compiled C++ functions (DLLs) using the CasADi code generation interface. The primary function used is:

- **`Spr_Imp_GRFs_ownCont_V21.dll`** — Implicit dynamics with custom ground contact model and GRF computation

Source code for all variants is provided in `ExternalFunctions/`.

> **Note:** Pre-compiled DLLs are for **Windows x64**. To use on other platforms, recompile from the `.cpp` source files using CasADi's code generation tools.

---

## Citation

If you use this framework, please cite:

```
Simulations reveal how touchdown kinematic variables affect top sprinting speed:
implications for coaching
BioRxiv: https://www.biorxiv.org/content/10.1101/2024.10.08.617292v1
```

---

## License

Please refer to the license file or contact the authors for usage terms.
