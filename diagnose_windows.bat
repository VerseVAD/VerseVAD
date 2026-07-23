@echo off
setlocal
cd /d "%~dp0"

set "VERSEVAD_UV=%~dp0.tools\uv\uv.exe"
set "UV_CACHE_DIR=%~dp0.runtime\uv-cache"
set "UV_PYTHON_INSTALL_DIR=%~dp0.runtime\python"
set "UV_PYTHON_INSTALL_REGISTRY=0"

if not exist "%VERSEVAD_UV%" (
  echo VerseVAD's local setup tool is missing.
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)

"%VERSEVAD_UV%" run --frozen --offline versevad-diagnose

if errorlevel 1 (
  echo.
  echo One or more checks failed. Please report the lines marked FAIL.
) else (
  echo.
  echo Diagnostics completed successfully.
)
echo.
pause
