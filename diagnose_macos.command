#!/bin/bash

set -u

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This diagnostic helper is for macOS."
  exit 1
fi

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
UV_EXECUTABLE="$PROJECT_ROOT/.tools/uv/uv"
RUNTIME_DIRECTORY="$PROJECT_ROOT/.runtime"

if [ ! -x "$UV_EXECUTABLE" ]; then
  echo "VerseVAD has not been set up in this folder."
  echo "Open Terminal in this folder and run: bash setup_macos.command"
  read -r -p "Press Return to close this window." _
  exit 1
fi

export UV_CACHE_DIR="$RUNTIME_DIRECTORY/uv-cache"
export UV_PYTHON_INSTALL_DIR="$RUNTIME_DIRECTORY/python"
export UV_NO_MODIFY_PATH=1
export UV_PYTHON_PREFERENCE=only-managed

cd "$PROJECT_ROOT"
"$UV_EXECUTABLE" run --frozen --offline versevad-diagnose
STATUS=$?
echo
read -r -p "Press Return to close this window." _
exit "$STATUS"
