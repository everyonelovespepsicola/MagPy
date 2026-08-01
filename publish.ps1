# publish.ps1 - Automated Setup, Dependency Management, and Build Script for MagPy

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "       MagPy Publishing & Build Script    " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

# 1. Locate System CPython (prefer official Python install over Inkscape/other bundled pythons)
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
$pythonExec = $null
$possiblePythons = @(
    "$env:LocalAppData\Programs\Python\Python312\python.exe",
    "$env:LocalAppData\Programs\Python\Python311\python.exe",
    "$env:ProgramFiles\Python312\python.exe",
    "$env:ProgramFiles\Python311\python.exe"
)

foreach ($path in $possiblePythons) {
    if (Test-Path $path) {
        $pythonExec = $path
        break
    }
}

if (-not $pythonExec) {
    # Fallback to PATH python
    $cmdPath = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
    if ($cmdPath -and $cmdPath -notmatch "Inkscape") {
        $pythonExec = $cmdPath
    }
}

if (-not $pythonExec) {
    Write-Host "ERROR: Suitable CPython installation not found." -ForegroundColor Red
    exit 1
}
Write-Host "Found Python at: $pythonExec" -ForegroundColor Green

# 2. Virtual Environment Setup
Write-Host ""
Write-Host "[2/5] Setting up virtual environment (.venv)..." -ForegroundColor Yellow
$venvPython = "$PSScriptRoot\.venv\Scripts\python.exe"

# If .venv exists but has stale compiled binaries from another python version, clean it
if (Test-Path ".venv") {
    # Test if .venv python executes cleanly
    & $venvPython -c "import numpy" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Detecting broken/stale .venv dependencies. Re-creating clean .venv..." -ForegroundColor Yellow
        Remove-Item -Path ".venv" -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating clean virtual environment in .venv..."
    & $pythonExec -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Virtual environment .venv is ready." -ForegroundColor Green
}

$venvPip = "$PSScriptRoot\.venv\Scripts\pip.exe"

# Upgrade pip inside .venv silently
Write-Host "Ensuring pip is up to date inside .venv..."
& $venvPython -m pip install --upgrade pip | Out-Null

# 3. Install Frozen Dependencies
Write-Host ""
Write-Host "[3/5] Installing and verifying pip dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    Write-Host "Installing dependencies from requirements.txt..."
    & $venvPip install --no-compile -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install requirements from requirements.txt." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "requirements.txt not found. Installing default dependencies..."
    & $venvPip install --no-compile pygame PyOpenGL PyOpenGL_accelerate numpy Pillow pyinstaller
}

# 4. Freeze dependencies to ensure future-proofing
Write-Host ""
Write-Host "[4/5] Freezing dependencies to requirements.txt..." -ForegroundColor Yellow
& $venvPython -m pip freeze | Out-File -Encoding utf8 requirements.txt
Write-Host "Updated requirements.txt successfully:" -ForegroundColor Green
Get-Content requirements.txt | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }

# 5. Build Executables with PyInstaller
Write-Host ""
Write-Host "[5/5] Building MagPy executables..." -ForegroundColor Yellow

# Clean previous build artifacts
Remove-Item -Path "build", "dist" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Building MagPy.exe..."
& $venvPython -m PyInstaller --onefile --noconsole --name "MagPy" --icon "myicon.ico" --add-data "myicon.ico;." magnifier.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller failed to build MagPy.exe" -ForegroundColor Red
    exit 1
}

Write-Host "Building magpy_settings.exe..."
& $venvPython -m PyInstaller --onefile --noconsole --name "magpy_settings" --icon "myicon.ico" --add-data "myicon.ico;." magpy_settings.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller failed to build magpy_settings.exe" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "       Publishing Complete!               " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Executables generated in: $PSScriptRoot\dist\"
Write-Host " - MagPy.exe"
Write-Host " - magpy_settings.exe"
Write-Host ""
