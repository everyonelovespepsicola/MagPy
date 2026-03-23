@echo off
setlocal

:: --- Configuration ---
:: Set the explicit path to your Python DLL
set PYTHON_DLL_PATH=C:\Users\Administrator\Desktop\projects\mag\.venv\Scripts\python313.dll :: <--- VERIFY THIS PATH CAREFULLY

:: --- Build Process ---

echo.
echo --- Starting MagPy Build Process ---
echo.

:: 1. Navigate to the project directory
cd /d "%~dp0"
color 07

:: 2. Activate the Python virtual environment and check for errors
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment. Exiting.
    goto :eof
)

:: 3. Clean up previous PyInstaller builds and check for errors
echo Cleaning up previous PyInstaller builds...
pyinstaller --clean magnifier.py
pyinstaller --clean magpy_settings.py
rmdir /s /q build dist

:: 4. Build magnifier.exe
echo Building magnifier.exe with PyInstaller, explicitly adding python313.dll to _internal... 
pyinstaller --noconsole --add-binary "%PYTHON_DLL_PATH%;_internal" magnifier.py 
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo ERROR: PyInstaller failed for magnifier.exe with code %ERRORLEVEL%!
    color 07
    goto :eof
)

:: 5. Build magpy_settings.exe
echo Building magpy_settings.exe with PyInstaller, explicitly adding python313.dll to _internal...
pyinstaller --noconsole --add-binary "%PYTHON_DLL_PATH%;_internal" magpy_settings.py
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo ERROR: PyInstaller failed for magpy_settings.exe with code %ERRORLEVEL%!
    color 07
    goto :eof
)

echo.
echo --- MagPy Executables Build Complete ---
echo.
echo Executables are available in the "dist" folder: %~dp0dist\
echo You can find magnifier.exe in %~dp0dist\magnifier\
echo You can find magpy_settings.exe in %~dp0dist\magpy_settings\

endlocal
pause