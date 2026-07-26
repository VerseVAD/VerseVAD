@echo off
setlocal
cd /d "%~dp0"

set "VERSEVAD_UV=%~dp0.tools\uv\uv.exe"
set "VERSEVAD_OUTPUT=%~dp0phase1_demo_output"
set "UV_CACHE_DIR=%~dp0.runtime\uv-cache"
set "UV_PYTHON_INSTALL_DIR=%~dp0.runtime\python"
set "UV_PYTHON_INSTALL_REGISTRY=0"
set "UV_PYTHON_PREFERENCE=only-managed"

if not exist "%VERSEVAD_UV%" (
  echo VerseVAD's project-local setup tool is missing.
  echo No files were changed.
  echo Please report this message so the setup can be repaired.
  pause
  exit /b 1
)

echo Running the VerseVAD Phase 1 validation demonstration...
echo.
"%VERSEVAD_UV%" run --frozen --offline versevad-phase1-demo --output "%VERSEVAD_OUTPUT%"

if errorlevel 1 (
  echo.
  echo The validation did not complete successfully.
  echo Please copy or photograph the message above and report it.
  pause
  exit /b 1
)

echo.
echo Success. The calculated CSV files are in:
echo %VERSEVAD_OUTPUT%
echo.
pause
