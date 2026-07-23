@echo off
setlocal
cd /d "%~dp0"

set "VERSEVAD_UV=%~dp0.tools\uv\uv.exe"
set "UV_CACHE_DIR=%~dp0.runtime\uv-cache"
set "UV_PYTHON_INSTALL_DIR=%~dp0.runtime\python"
set "UV_PYTHON_INSTALL_REGISTRY=0"

if not exist "%VERSEVAD_UV%" (
  echo VerseVAD has not been set up in this folder.
  echo Double-click setup_windows.bat first, then retry.
  pause
  exit /b 1
)

echo Starting VerseVAD locally at http://127.0.0.1:8501
echo Your browser should open automatically.
echo Keep this window open while using VerseVAD.
echo To stop the application, close this window or press Ctrl+C here.
echo.
"%VERSEVAD_UV%" run --frozen --offline streamlit run "src\versevad\ui\app.py" --server.address 127.0.0.1 --server.port 8501 --server.headless false --browser.gatherUsageStats false

if errorlevel 1 (
  echo.
  echo VerseVAD stopped because of an error.
  echo Run diagnose_windows.bat and report any failed checks.
  pause
  exit /b 1
)
