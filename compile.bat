@echo off
title silver's Anti-AFK Compiler

echo ========================================
echo       silver's Anti-AFK Compiler
echo ========================================
echo.

REM --- Step 1: Check for Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python from python.org and ensure it's added to your PATH.
    pause
    exit /b 1
)

REM --- Step 2: Update Pip and Install Dependencies ---
echo Updating pip installer...
python -m pip install --upgrade pip --quiet

echo Checking for required Python packages...
python -m pip install --upgrade pywin32 pyinstaller pillow pystray keyboard vgamepad --quiet
if errorlevel 1 (
    echo ERROR: Failed to install required Python packages.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

REM --- Step 3: Run the Python Build Script ---
echo.
echo Starting the build process using build.py...
python build.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed! Check the output above for details.
    pause
    exit /b 1
)

echo.
echo ========================================
echo         Compilation Successful!
echo ========================================
echo.
echo Your executable is located in: "dist\silver's Anti-AFK.exe"
echo.
echo Cleaning up temporary build files...
rmdir /s /q build 2>nul
del "silver's Anti-AFK.spec" 2>nul

echo.
echo Done!
echo.
pause