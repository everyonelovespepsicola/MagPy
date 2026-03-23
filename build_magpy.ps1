# build_magpy.ps1

# --- Build Process ---

Write-Host ""
Write-Host "--- Starting MagPy Build Process ---" -ForegroundColor Cyan
Write-Host ""

# 1. Navigate to the project directory
Set-Location $PSScriptRoot

# 2. Activate the Python virtual environment and check for errors
Write-Host "Activating virtual environment..."
# Use .& to run the script in the current scope
. .venv\Scripts\Activate.ps1
if (-not $?) {
    Write-Host "Error: Failed to activate virtual environment. Please ensure '.venv\Scripts\Activate.ps1' exists and is functional." -ForegroundColor Red
    exit 1
}

# 3. Clean up previous PyInstaller builds
Write-Host "Cleaning up previous PyInstaller builds..."
# Use -ErrorAction SilentlyContinue to prevent errors if build/dist don't exist
Remove-Item -Path "build", "dist" -Recurse -Force -ErrorAction SilentlyContinue
# PyInstaller --clean also cleans up, but Remove-Item is more direct for folders.
pyinstaller --clean magnifier.py | Out-Null # Suppress PyInstaller clean output
pyinstaller --clean magpy_settings.py | Out-Null # Suppress PyInstaller clean output

# 4. Build magnifier.exe
Write-Host "Building standalone magnifier.exe with PyInstaller..."
pyinstaller --onefile --noconsole magnifier.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller failed for magnifier.exe with code $LASTEXITCODE! Please check the console output above for details." -ForegroundColor Red
    exit 1
}

# 5. Build magpy_settings.exe
Write-Host "Building standalone magpy_settings.exe with PyInstaller..."
pyinstaller --onefile --noconsole magpy_settings.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller failed for magpy_settings.exe with code $LASTEXITCODE! Please check the console output above for details." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "--- MagPy Executables Build Complete ---" -ForegroundColor Green
Write-Host ""
Write-Host "Executables are available in the 'dist' folder: $($PSScriptRoot)\dist\"
Write-Host "You can find magnifier.exe in $($PSScriptRoot)\dist\"
Write-Host "You can find magpy_settings.exe in $($PSScriptRoot)\dist\"

Read-Host -Prompt "Press any key to continue..."