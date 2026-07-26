#!/bin/bash

set -u

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This launcher is for macOS. On Windows, use start_versevad.bat."
  exit 1
fi

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
UV_EXECUTABLE="$PROJECT_ROOT/.tools/uv/uv"
RUNTIME_DIRECTORY="$PROJECT_ROOT/.runtime"

if [ ! -x "$UV_EXECUTABLE" ]; then
  echo "VerseVAD has not been set up in this folder."
  echo "Open Terminal in this folder and run: bash setup_macos.command"
  echo
  read -r -p "Press Return to close this window." _
  exit 1
fi

export UV_CACHE_DIR="$RUNTIME_DIRECTORY/uv-cache"
export UV_PYTHON_INSTALL_DIR="$RUNTIME_DIRECTORY/python"
export UV_NO_MODIFY_PATH=1
export UV_PYTHON_PREFERENCE=only-managed

cd "$PROJECT_ROOT"
echo "Starting VerseVAD locally at http://127.0.0.1:8501"
echo "Safari or Chrome should open automatically, following your Mac default."
echo "Keep this window open while using VerseVAD."
echo "To stop the application, close this window or press Control-C here."
echo

"$UV_EXECUTABLE" run --frozen --offline streamlit run \
  "$PROJECT_ROOT/src/versevad/ui/app.py" \
  --server.address 127.0.0.1 \
  --server.port 8501 \
  --server.headless false \
  --browser.gatherUsageStats false
STATUS=$?

if [ "$STATUS" -ne 0 ]; then
  echo
  echo "VerseVAD stopped because of an error."
  echo "Run diagnose_macos.command and report any failed checks."
  read -r -p "Press Return to close this window." _
fi
exit "$STATUS"
