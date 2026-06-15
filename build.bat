@echo off
echo ===================================================
echo   Vault 404 RPG: Windows Executable Build Utility
echo ===================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your Windows PATH.
    echo Please install Python 3 (from python.org) and try again.
    pause
    exit /b 1
)

echo [1/4] Creating build environment...
python -m venv .build_venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/4] Activating environment and installing pyinstaller/dependencies...
call .build_venv\Scripts\activate
python -m pip install --upgrade pip
pip install pygame requests pyinstaller
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [3/4] Compiling standalone Windows .exe via PyInstaller...
:: --onefile packages everything into a single binary
:: --noconsole prevents the command prompt window from popping up
:: --add-data "assets;assets" bundles the pixel art sprites into the binary
pyinstaller --onefile --noconsole --add-data "assets;assets" --name "Vault404_RPG" main.py
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller compilation failed.
    pause
    exit /b 1
)

echo [4/4] Finalizing build and cleaning up temporary files...
if exist dist\Vault404_RPG.exe (
    copy /y dist\Vault404_RPG.exe .\Vault404_RPG.exe >nul
    echo.
    echo ===================================================
    echo  SUCCESS! 'Vault404_RPG.exe' is ready in this folder.
    echo  You can send this file to your friend to play!
    echo ===================================================
) else (
    echo [ERROR] Build completed but output binary could not be located.
)

:: Deactivate and cleanup build venv folders to save space
call deactivate
echo.
echo Cleaning up build temporary folders...
rd /s /q build
rd /s /q dist
rd /s /q .build_venv
del /q Vault404_RPG.spec

pause
