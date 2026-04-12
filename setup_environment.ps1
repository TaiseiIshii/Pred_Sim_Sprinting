#!/usr/bin/env powershell
<#
.SYNOPSIS
    Automated setup script for Pred_Sim_Sprinting project
.DESCRIPTION
    Sets up Conda environment and verifies all dependencies
.AUTHOR
    Pred_Sim_Sprinting Setup
.DATE
    2026-02-03
.EXAMPLE
    .\setup_environment.ps1
#>

#Requires -RunAsAdministrator

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Colors
$Success = "Green"
$Warning = "Yellow"
$Error_Color = "Red"
$Info = "Cyan"

Write-Host "========================================" -ForegroundColor $Info
Write-Host "Pred_Sim_Sprinting Automated Setup" -ForegroundColor $Info
Write-Host "========================================`n" -ForegroundColor $Info

# Get project root
$ProjectRoot = Split-Path -Parent $PSCommandPath
Write-Host "Project Root: $ProjectRoot`n" -ForegroundColor $Info

# Check Conda installation
Write-Host "Checking Conda installation..." -ForegroundColor $Info
try {
    $CondaVersion = conda --version
    Write-Host "[OK] $CondaVersion`n" -ForegroundColor $Success
} catch {
    Write-Host "[ERROR] Conda not found!" -ForegroundColor $Error_Color
    Write-Host "Please install Miniconda or Anaconda from:" -ForegroundColor $Warning
    Write-Host "https://docs.conda.io/en/latest/miniconda.html`n" -ForegroundColor $Warning
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if environment exists
Write-Host "Checking existing environment..." -ForegroundColor $Info
$EnvExists = (conda env list | Select-String "pred_sim_sprinting") -ne $null

if ($EnvExists) {
    Write-Host "[WARN] Environment pred_sim_sprinting already exists" -ForegroundColor $Warning
    $Response = Read-Host "Remove and recreate? (y/n)"
    if ($Response -eq "y") {
        Write-Host "Removing old environment..." -ForegroundColor $Info
        conda deactivate 2>$null
        conda env remove -n pred_sim_sprinting -y
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to remove environment" -ForegroundColor $Error_Color
            Read-Host "Press Enter to exit"
            exit 1
        }
    } else {
        Write-Host "Skipping environment recreation" -ForegroundColor $Info
    }
}

Write-Host ""

# Create environment
Write-Host "========================================" -ForegroundColor $Info
Write-Host "Creating Conda environment..." -ForegroundColor $Info
Write-Host "========================================`n" -ForegroundColor $Info

Push-Location $ProjectRoot
$EnvironmentFile = Join-Path $ProjectRoot "environment.yml"

if (-not (Test-Path $EnvironmentFile)) {
    Write-Host "[ERROR] environment.yml not found!" -ForegroundColor $Error_Color
    Write-Host "Expected location: $EnvironmentFile`n" -ForegroundColor $Error_Color
    Pop-Location
    Read-Host "Press Enter to exit"
    exit 1
}

conda env create -f $EnvironmentFile
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to create environment" -ForegroundColor $Error_Color
    Pop-Location
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] Environment created successfully`n" -ForegroundColor $Success

# Test packages
Write-Host "========================================" -ForegroundColor $Info
Write-Host "Testing installed packages..." -ForegroundColor $Info
Write-Host "========================================`n" -ForegroundColor $Info

$TestCode = @"
import numpy
import pandas
import matplotlib
import scipy
try:
    import casadi
    print('[OK] CasADi available for Python')
except:
    print('[WARN] CasADi Python bindings not available (OK - only needed for post-processing)')
print('[OK] All core packages imported successfully')
"@

conda run -n pred_sim_sprinting python -c $TestCode
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Package import test failed" -ForegroundColor $Error_Color
    Pop-Location
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check DLL compatibility
Write-Host "========================================" -ForegroundColor $Info
Write-Host "Checking DLL compatibility..." -ForegroundColor $Info
Write-Host "========================================`n" -ForegroundColor $Info

$DllScript = Join-Path $ProjectRoot "check_dll_architecture.ps1"
if (Test-Path $DllScript) {
    & $DllScript
} else {
    Write-Host "[WARN] DLL check script not found" -ForegroundColor $Warning
}

Pop-Location

Write-Host ""
Write-Host "========================================" -ForegroundColor $Success
Write-Host "Setup Complete!" -ForegroundColor $Success
Write-Host "========================================`n" -ForegroundColor $Success

Write-Host "Next steps:" -ForegroundColor $Info
Write-Host ""
Write-Host "1. Install CasADi MATLAB Toolbox (v3.3.0+)" -ForegroundColor $Info
Write-Host "   Download: https://web.casadi.org/get/" -ForegroundColor $Info
Write-Host ""
Write-Host "2. Open MATLAB R2017b and run:" -ForegroundColor $Info
Write-Host "   cd `"$ProjectRoot`"" -ForegroundColor $Info
Write-Host "   test_initial_setup" -ForegroundColor $Info
Write-Host ""
Write-Host "3. Generate polynomial data (first time only):" -ForegroundColor $Info
Write-Host "   run Polynomials/mainPolynomials.m" -ForegroundColor $Info
Write-Host ""
Write-Host "4. Run main simulation:" -ForegroundColor $Info
Write-Host "   run MainFunctions/main_pred_sim_sprinting.m" -ForegroundColor $Info
Write-Host ""
Write-Host "5. Post-process results:" -ForegroundColor $Info
Write-Host "   conda activate pred_sim_sprinting" -ForegroundColor $Info
Write-Host "   cd `"$ProjectRoot`"" -ForegroundColor $Info
Write-Host "   python post_process_results.py" -ForegroundColor $Info
Write-Host ""
Write-Host "========================================" -ForegroundColor $Info
Write-Host "To activate Conda environment in future:" -ForegroundColor $Info
Write-Host "   conda activate pred_sim_sprinting" -ForegroundColor $Info
Write-Host ""
Write-Host "To deactivate:" -ForegroundColor $Info
Write-Host "   conda deactivate" -ForegroundColor $Info
Write-Host "========================================`n" -ForegroundColor $Info

Write-Host "Press Enter to continue..." -ForegroundColor $Info
Read-Host
