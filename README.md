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

---

## Documentation

Additional guides are available in `docs/`:

| Document | Content |
|----------|---------|
| [QUICKSTART.md](docs/QUICKSTART.md) | Step-by-step beginner's guide (日本語) |
| [SETUP_GUIDE_JP.md](docs/SETUP_GUIDE_JP.md) | Detailed setup instructions (日本語) |
| [DETAILED_EXECUTION_GUIDE.md](docs/DETAILED_EXECUTION_GUIDE.md) | Execution walkthrough with expected outputs |
| [TROUBLESHOOTING_GUIDE.md](docs/TROUBLESHOOTING_GUIDE.md) | Common issues and solutions |

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
