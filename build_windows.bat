@echo off
setlocal

cd /d "%~dp0"
set "VENV=.venv-build"
set "PYTHON=%VENV%\Scripts\python.exe"

where py >nul 2>&1
if errorlevel 1 (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Python was not found. Install Python 3 and try again.
        exit /b 1
    )
    set "BOOTSTRAP=python"
) else (
    set "BOOTSTRAP=py -3"
)

if not exist "%PYTHON%" (
    echo Creating build virtual environment...
    %BOOTSTRAP% -m venv "%VENV%"
    if errorlevel 1 exit /b 1
)

echo Installing build dependencies...
"%PYTHON%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"%PYTHON%" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist TracePince.spec del /q TracePince.spec

 echo Building TracePince.exe...
"%PYTHON%" -m PyInstaller --noconfirm --clean --onefile --windowed --name TracePince main.py
if errorlevel 1 exit /b 1

if not exist dist\logs mkdir dist\logs

echo.
echo Build complete: %CD%\dist\TracePince.exe
endlocal
