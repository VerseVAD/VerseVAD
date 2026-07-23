@echo off
setlocal
cd /d "%~dp0"

echo VerseVAD will create or check its project-local environment.
echo No administrator access or system-wide Python installation is required.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_windows.ps1"

if errorlevel 1 (
  echo.
  echo VerseVAD setup did not complete.
  echo Please copy or photograph the message above and report it.
  pause
  exit /b 1
)

echo.
pause
