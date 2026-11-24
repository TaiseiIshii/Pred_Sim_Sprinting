# DATA AVAILABILITY

Source result files (`pred_sprinting_data_*.mat`) are **not** committed to git (69 manifest-tracked
files ≈ 360 MB; ~4.9 MB each). They are pinned by **SHA256** in
[`Results/Validation_Master/manifest_provenance.csv`](../Results/Validation_Master/manifest_provenance.csv)
so that every output number remains traceable even when the binaries are held privately.

> Even without the `.mat` files, a third party can verify each published number: the output
> CSV/PNG hashes are in `output_hashes.csv`, and each output maps (via `manifest_provenance.csv`)
> to a source-MAT SHA256 + simulation/analysis commits. See [PROVENANCE.md](PROVENANCE.md).

## 1. Inventory (manifest-tracked source MATs)

| experiment | n | strict | meshes | sim_commit | size (MB) |
|---|---|---|---|---|---|
| HamPareto (Nom/Sh/Wk, speed–load Pareto) | 14 | 14 | 50 | 59877aa | 64.5 |
| Haralabidis_TD (touchdown-kinematics baseline) | 12 | 12 | 50 | 59877aa | 55.8 |
| Morphology_fascicle (HamFascicle ±) | 6 | 6 | 50 | 59877aa | 27.6 |
| Morphology_strength (HamStrength ±) | 5 | 5 | 50 | 59877aa | 23.0 |
| Nominal (baseline) | 2 | 2 | 50 & 100 | 59877aa | 13.8 |
| PelvicShift (mean-tilt manipulation) | 8 | **1** | 50 | 59877aa / bb0433a | 36.9 |
| PelvicTD / PelvisTDwide (touchdown pelvic tilt) | 20 | **18** | 50 & 100 | 59877aa | 128.7 |
| PelvicTilt (initial exploratory) | 2 | **1** | 50 | 59877aa | 9.2 |
| **TOTAL (manifest)** | **69** | — | — | — | **359.5** |

Per-file size + SHA256 + condition + solver status + achieved speed/tilt:
`manifest_provenance.csv` (regenerate with `python analysis/validation/data_inventory.py`).

## 2. Files required to reproduce the PAPER's primary results

The thesis/conference primary claims use the **strict, speed-matched** subsets only:

| Claim block | Required MATs | Mesh | Notes |
|---|---|---|---|
| 8-condition touchdown-pelvic-tilt dose–response (Phase A/E of plan) | `PelvisTD_{m2,p0,p2,p4,p6}` + `PelvisTDwide_{m2,m4,m6,p0,p2,p4,p6}` strict set | **50 and 100** | 18/20 strict; the 2 non-strict `PelvisTD_{m4,m6}` are excluded (speed collapse) |
| Speed–load Pareto (Nominal) | `HamPareto_Nom_{w0000,w0050,w0100,w0200,w0400,w0800,w1600,w3200}` | 50 (N=100 pending) | all strict `Solve_Succeeded` |
| Boundary-condition decomposition | `PelvisTD_m2/p0` (+ Nominal) | 50/100 | analysis is geometric (femur world-transform), reuses above |
| Morphology (exploratory chapter only) | `HamFascicle_{m30..p20}`, `HamStrength_{m30..p20}` | 50 | not a primary conclusion (see plan Phase 5) |

Excluded from primary analysis (kept for transparency): non-strict `PelvicShift` (7/8),
`PelvicTilt` (1/2), `PelvicTD_{m4,m6}` (infeasible, speed to ~9.2 m/s).

## 3. Regeneration commands (MATLAB R2017b + CasADi/IPOPT)

From the project root, `setup_paths` first, then:

| Dataset | Command |
|---|---|
| Nominal (N=50) | `main_pred_sim_sprinting('Nominal')` |
| Nominal (N=100) | `main_pred_sim_sprinting_N100('Nominal')` (in `MainFunctions/`) |
| Touchdown pelvic tilt sweep | `run_pelvic_td_sweep` (or `run_pelvic_td.bat`) |
| Hamstring speed–load Pareto | `run_ham_pareto_sweep` (or `run_ham_pareto.bat`) |
| Morphology (fascicle/strength) | `run_ham_arch_sweep` (or `run_ham_arch.bat`) |
| N=100 Pareto (new; this study) | `run_ham_pareto_N100` (see plan Phase 2 / `docs/RESUME_PROMPT.md`) |

Solver nondeterminism: IPOPT/BLAS may differ at the last digits across machines; the pinned SHA256
identifies the exact `.mat` used here. Re-solves are validated by matching achieved speed / tilt /
solver status in `manifest_provenance.csv` to within the pre-declared tolerances, not by byte-identity.

## 4. Publication plan for the data

| Option | Content | Status | DOI |
|---|---|---|---|
| Zenodo dataset | strict primary MATs + all output CSVs + manifests | candidate | _DOI: __________ (reserve on submission)_ |
| GitHub Release asset | zipped `Results/Validation_Master/` (CSVs + figures only, ~2 MB) | candidate | n/a |
| Institutional / lab storage | full 360 MB MAT set (if size/licence blocks public release) | fallback | n/a |

Release requires the human author's explicit action (no automated push/publish per task rules).
When a DOI is minted, fill the slot above and cite it in `README.md`, `PAPER_RESULTS_FREEZE.md`,
and the abstracts.

## 5. Licensing / consent
The underlying musculoskeletal model derives from the Haralabidis et al. sprinting framework
(single international-caliber male sprinter). No new human-subject data is introduced. Confirm the
model-redistribution licence before any public `.mat`/model release; if blocked, publish the
**output CSVs + manifests** (fully de-identified, model-free) which suffice to reproduce every figure.
