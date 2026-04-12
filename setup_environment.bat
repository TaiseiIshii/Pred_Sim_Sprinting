@echo off
REM ============================================================================
REM setup_environment.bat
REM Automated Setup Script for Pred_Sim_Sprinting
REM ============================================================================
REM This batch script automates the Conda environment setup process
REM Run as Administrator
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Pred_Sim_Sprinting Automated Setup
echo ========================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script must be run as Administrator!
    echo.
    echo Please:
    echo 1. Right-click on this .bat file
    echo 2. Select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Get project root
for %%i in ("%~dp0.") do set PROJECT_ROOT=%%~fi
echo Project Root: %PROJECT_ROOT%
echo.

REM Check if Conda is installed
echo Checking Conda installation...
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Conda not found in PATH!
    echo.
    echo Please install Miniconda or Anaconda:
    echo https://docs.conda.io/en/latest/miniconda.html
    echo.
    pause
    exit /b 1
)
echo [OK] Conda found
echo.

REM Initialize Conda
echo Initializing Conda...
call conda init
if %errorlevel% neq 0 (
    echo [WARN] Conda init returned warning (may be normal)
)
echo.

REM Create Conda environment
echo ========================================
echo Creating Conda environment...
echo ========================================
echo.
cd /d "%PROJECT_ROOT%"

REM Check if environment already exists
conda env list | findstr "pred_sim_sprinting" >nul
if %errorlevel% equ 0 (
    echo [WARN] Environment pred_sim_sprinting already exists
    echo Removing old environment...
    conda deactivate
    conda env remove -n pred_sim_sprinting -y
)

REM Create new environment
echo Creating new environment from environment.yml...
conda env create -f environment.yml
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create Conda environment
    pause
    exit /b 1
)
echo [OK] Conda environment created successfully
echo.

REM Activate environment and test
echo ========================================
echo Testing environment...
echo ========================================
echo.

REM Note: We need to use conda run since batch doesn't support conda activate well
conda run -n pred_sim_sprinting python -c "import numpy, pandas, matplotlib, scipy, casadi; print('[OK] All packages imported successfully')"
if %errorlevel% neq 0 (
    echo [ERROR] Package import test failed
    pause
    exit /b 1
)
echo.

REM Check DLL compatibility
echo ========================================
echo Checking DLL compatibility...
echo ========================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\check_dll_architecture.ps1"
if %errorlevel% neq 0 (
    echo [WARN] DLL check returned warnings
)
echo.

REM Summary
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Install CasADi MATLAB Toolbox (v3.3.0+)
echo    Download: https://web.casadi.org/get/
echo.
echo 2. Open MATLAB R2017b and run:
echo    cd "%PROJECT_ROOT%"
echo    test_initial_setup
echo.
echo 3. Generate polynomial data (first time only):
echo    run Polynomials/mainPolynomials.m
echo.
echo 4. Run main simulation:
echo    run MainFunctions/main_pred_sim_sprinting.m
echo.
echo 5. Post-process results (from command prompt):
echo    conda activate pred_sim_sprinting
echo    cd "%PROJECT_ROOT%"
echo    python post_process_results.py
echo.
echo ========================================
echo To activate Conda environment in future:
echo    conda activate pred_sim_sprinting
echo.
echo To deactivate:
echo    conda deactivate
echo ========================================
echo.

pause
