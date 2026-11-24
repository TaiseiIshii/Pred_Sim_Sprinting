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

## Validation, reproducibility & claim policy

Beyond the base framework, this repository includes a **reproducible validation suite** and the
governance documents behind an MSc-thesis / conference study on **pelvic posture and hamstring
mechanical-load surrogates**. All quantitative claims are calibrated: the evaluated quantity is an
**injury-related mechanical-load surrogate** (normalized fiber length, active/passive/tendon force,
fiber lengthening velocity, negative fiber work) — **not** injury probability or prevention. See
[docs/CLAIM_CALIBRATION.md](docs/CLAIM_CALIBRATION.md).

### Reproducible analysis engine (`analysis/validation/`)
Single-source-of-truth metrics on the true non-uniform collocation grid, in physical units
([`ham_load_metrics.py`](analysis/validation/ham_load_metrics.py) v1.0.0). Tests run from a fresh clone:

```bash
python analysis/validation/test_unit_metrics.py       # 22/22 unit (offline, no .mat needed)
python analysis/validation/test_ham_load_metrics.py    # 18/18 integration (skips cleanly if no data)
```

### Key supported findings (strict `Solve_Succeeded`, mesh-checked)
- **Touchdown pelvic tilt → biarticular hamstring fiber length** (8 conditions, N=50 & N=100): more
  anterior tilt robustly raises terminal-swing peak normalized fiber length in semimem/semiten/bifemlh
  (mesh |Δ|<1.6%); the mono-articular bifemsh is flat → hip-crossing-specific.
- **Boundary-condition decomposition:** the apparent "direct effect = 0" is a tree-rigid artefact; a
  femur-fixed counterfactual explains ~85–90% of the adaptive lengthening (hip flexion ≈−1.07 deg/deg).
- **Speed–load Pareto (SUPPORTED, N=100 multi-start):** a near-matched-speed candidate at w=0.1
  (−0.34% speed, −5.2% load surrogate) reproduces across 3/3 initializations under pre-declared gates.
- **Load-objective study (Phase D):** four objectives (fiber-length / active-eccentric / passive /
  composite) dissociate; an equal-mix composite lowers all surrogates at once near matched speed.

Passive force and negative work are **direction-robust but mesh-conditional in magnitude** (reported as
such). Outputs (CSVs + figures) are in `Results/Validation_Master/`; each is hashed in
`output_hashes.csv` and mapped to a source-MAT SHA256 in `manifest_provenance.csv`.

### Governance & thesis documents (`docs/`)
| Document | Purpose |
|---|---|
| [PAPER_RESULTS_FREEZE.md](docs/PAPER_RESULTS_FREEZE.md) | frozen numbers, provenance, claim ledger, figure↔CSV map |
| [CLAIM_CALIBRATION.md](docs/CLAIM_CALIBRATION.md) · [CLAIM_EVIDENCE_MATRIX.md](docs/CLAIM_EVIDENCE_MATRIX.md) | language policy · claim → evidence |
| [PROVENANCE.md](docs/PROVENANCE.md) · [DATA_AVAILABILITY.md](docs/DATA_AVAILABILITY.md) | commit / data traceability |
| [THESIS_OUTLINE_JP.md](docs/THESIS_OUTLINE_JP.md) · [ABSTRACTS.md](docs/ABSTRACTS.md) | 11-chapter outline · JP/EN abstracts |
| [PHASE_A_MUSCLE_TENSION_REPORT.md](docs/PHASE_A_MUSCLE_TENSION_REPORT.md) · [PER_MUSCLE_CONCLUSIONS.md](docs/PER_MUSCLE_CONCLUSIONS.md) | per-muscle 8-condition results |
| [OPT_ON_OFF_INTERPRETATION.md](docs/OPT_ON_OFF_INTERPRETATION.md) · [LITERATURE_QUANTITATIVE_COMPARISON.md](docs/LITERATURE_QUANTITATIVE_COMPARISON.md) | counterfactual scope · literature |
| [PHASE_D_E_FINDINGS.md](docs/PHASE_D_E_FINDINGS.md) · [FINAL_STUDY_PLAN.md](docs/FINAL_STUDY_PLAN.md) | load-objective study · master plan |

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
│   └── validation/          # Reproducible metrics engine + unit/integration tests
├── docs/                    # Setup/troubleshooting + validation & thesis governance docs
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

**Study conditions** (batch runners in `MainFunctions/`): `_PelvisTD_m6…p6` touchdown pelvic tilt
(`run_pelvic_td_sweep`); `_HamPareto_Nom_wXXXX` speed–load Pareto (`run_ham_pareto_sweep`,
`run_ham_pareto_N100` for N=100 multi-start); `_HamEcc_/_HamPasv_/_HamCompEQ_wXXXX` Phase D load
objectives (`run_ham_obj_sweep`). `wXXXX=0000` disables the penalty (byte-identical to baseline).

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
| [Presentation_Audience_Strategy_Report.md](docs/Presentation_Audience_Strategy_Report.md) | Visual presentation storyboards for expert and non-expert audiences |

---

## Pelvic-tilt hamstring load-surrogate study

A manipulation study applying this framework to ask **how anterior/posterior pelvic tilt
(`pelvis_tilt`) affects hamstring mechanical-load surrogates** at near-matched sprint performance
(**surrogates, not injury probability**; see [docs/CLAIM_CALIBRATION.md](docs/CLAIM_CALIBRATION.md)).
The pelvis tilt waveform is rigidly shifted by a fixed offset (±6°, 2° steps; 7 conditions) and the
task is re-optimized, then hamstring stretch metrics are compared across conditions.

- **Plain-language summary (日本語):** [Results/PelvicShift_Study/SUMMARY_JP.md](Results/PelvicShift_Study/SUMMARY_JP.md)
- **Full report:** [Results/PelvicShift_Study/REPORT.md](Results/PelvicShift_Study/REPORT.md)
- **Rich videos & figures:** `Results/PelvicShift_Study/` (musculoskeletal / SMPL / stick-figure MP4s, dose-response figures)

Key finding: increasing anterior pelvic tilt monotonically increases the peak normalized
fiber length and passive force of the **biarticular** hamstrings (semimembranosus most),
while the monoarticular biceps femoris short head is unchanged — with a small speed cost.

---

## Hamstring load-surrogate speed–load Pareto study (RQ3+RQ4)

An extension that moves the framework from *why is load higher* to *what candidate motion lowers the
load surrogate at maintained speed* (**not** a prescription of how to run; see
[docs/CLAIM_CALIBRATION.md](docs/CLAIM_CALIBRATION.md)). A smooth biarticular-hamstring
fascicle-overstretch penalty (new objective weight `wJ(13)`) is added to the maximal-sprint cost and
its weight is swept to trace the **top-speed vs peak-fascicle-load-surrogate Pareto frontier**, on the
nominal athlete (RQ3) and on virtual athletes (short fascicle / weak) to compare **technique change vs
training adaptation** as an **exploratory** analysis (RQ4; morphology×pelvis is confounded).

- **Full report:** [docs/Hamstring_Pareto_Study_Report.md](docs/Hamstring_Pareto_Study_Report.md)
- **3D musculoskeletal render:** `Results/HamPareto_Study/ham_pareto_musculoskeletal_hero.png`
  (real OpenSim bones + wrapped hamstrings colored by fascicle strain + GRF; running animation
  `_sidebyside.mp4` and inline `_sidebyside.gif` via `--gif`). Two-step like the pelvic study:
  `compute_osim_muscle_paths_pareto.py` (OpenSim env) → `visualize_ham_pareto_musculoskeletal.py`
  (pyvista env). A stick-figure + joint-angle view (`visualize_ham_pareto_motion.py`) complements it.
- **Figures & animation:** `Results/HamPareto_Study/` (`pareto_frontier.png`,
  `technique_vs_training.png`, `permuscle_vs_weight.png`, `anim_pareto_sweep.gif`,
  `pareto_frontier.csv`)

Key findings: (1) a **low-cost ("free-lunch") region** exists — the nominal athlete can cut the peak
fascicle-load surrogate ~3.9% for only ~0.24% speed loss (up to −12% for −2.2%; **N=50, N=100
multi-start verification in progress**); (2) **[exploratory, morphology×pelvis confounded]** the
frontier is far **steeper for the short-fascicle athlete** (reaching load costs ~6–15% speed),
whereas **fascicle-lengthening training lowers the surrogate *and* raises speed**; (3) for the weak
athlete, strengthening and technique are **orthogonal levers** (speed vs load surrogate).

Run it (from repo root):
```bat
run_ham_pareto.bat pilot      REM nominal w0000/w0200/w0800 (de-risk)
run_ham_pareto.bat nominal    REM full nominal frontier (8 weights)
run_ham_pareto.bat athletes   REM short + weak athletes (RQ4)
run_ham_pareto.bat analyze    REM Pareto frontier analysis (Python)
```

---

## Mechanistic force / eccentric analysis, robustness & individual-difference cross study (latest)

This layer answers four requests: (a) compute muscle **force** (not just fibre length),
(b) separate the pelvic-tilt **angle effect** from the **re-optimization** effect,
(c) control for **running speed**, and (d) test **individual differences**.

### Reports — start here
- **Beginner-friendly full explainer (日本語, with figures + GIFs):**
  [docs/Hamstring_Study_Complete_Explainer_JP.md](docs/Hamstring_Study_Complete_Explainer_JP.md)
  — also `.html` (GIFs animate) and `.pdf` (print-ready, images embedded).
- **Researcher technical report (A–J deliverables):**
  [docs/Hamstring_Force_Mechanistic_Report.md](docs/Hamstring_Force_Mechanistic_Report.md)

### New analyses (Python, saved `.mat` only — no re-simulation)
| Script | What it does | Output |
|---|---|---|
| `analysis/analyze_pelvic_force_eccentric.py` | Peak muscle force (Fce/FT/Fpass, **N**), activation, eccentric metrics, timing, tilt regression, mediation chain | `Results/PelvicShift_Study/pelvic_force_eccentric.csv` |
| `analysis/analyze_opt_on_off_pelvis.py`, `_probe_osim_ham.py` | opt-ON vs opt-OFF via OpenSim (direct tilt effect on ham MTU length) | `fig4_opt_on_vs_off.png`, `opt_on_off_pelvis.csv` |
| `analysis/analyze_individual_force.py` | Nom/Sh/Wk on the speed–safety frontier; Fmax recovered as `Fpass/Fpetilde` | `Results/HamPareto_Study/fig7_individual_optima.png`, `individual_force.csv` |
| `analysis/analyze_imposition_robustness.py` | PelvisShift vs PelvisTD agreement (rules out constraint artifact) | `imposition_robustness.png` |
| `analysis/analyze_athlete_tilt_interaction.py`, `analyze_pelvic_athlete_cross.py` | Individual × pelvic-tilt 2×2 interaction (cross experiment) | `Results/PelvicAthlete_Study/athlete_tilt_interaction.png` |
| `analysis/visualize_framework.py`, `visualize_exp1_doseresponse.py`, `visualize_pelvic_force_timeseries.py`, `visualize_tradeoff.py` | Figures 1, 2, 3, 5, 6 | `Results/PelvicShift_Study/`, `Results/HamPareto_Study/` |

### New simulation condition — virtual athlete × pelvic tilt (cross experiment)
Combine a virtual at-risk athlete with the pelvic-tilt manipulation. The hook is additive and
reversible — every non-combined condition stays byte-identical:
- `_PelvisShift_mNN_athSh` — short fascicle (hamstring optimal fibre length ×0.80) + tilt offset
- `_PelvisShift_mNN_athWk` — weak (hamstring max isometric force ×0.80) + tilt offset

```matlab
setup_paths
run_pelvic_athlete_sweep({'_PelvisShift_m02_athSh'})   % pilot (~20–30 min, N=50)
run_pelvic_athlete_sweep                                % Sh/Wk × several tilts
```
Then analyse: `python analysis/analyze_pelvic_athlete_cross.py`.

### Key results
- **Direct pelvic-tilt effect on hamstring length = 0** (OpenSim: 0.000 mm). The stretch is
  entirely mediated by re-optimized **hip flexion** (tilt→hip r = −1.00).
- Fibre length rises with anterior tilt for all biarticular hamstrings (R²>0.99), but **peak
  contractile force rises clearly only for semimembranosus** (R²0.97) — length↑ ≠ force↑.
- A speed–safety **"free-lunch"** exists for the nominal athlete; the **short-fascicle athlete
  needs training, not technique**.
- Everything is framed as a **mechanical-loading surrogate ≠ injury risk** (biceps femoris long
  head is the most-injured muscle epidemiologically; see report §H).

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
