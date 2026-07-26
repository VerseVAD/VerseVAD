#!/bin/bash

set -eu

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This setup helper is for macOS."
  echo "On Windows, use setup_windows.bat instead."
  exit 1
fi

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
UV_VERSION="0.11.30"
UV_DIRECTORY="$PROJECT_ROOT/.tools/uv"
UV_EXECUTABLE="$UV_DIRECTORY/uv"
RUNTIME_DIRECTORY="$PROJECT_ROOT/.runtime"
DOWNLOAD_DIRECTORY="$RUNTIME_DIRECTORY/downloads"
VIRTUAL_ENVIRONMENT="$PROJECT_ROOT/.venv"
TEMPORARY_DIRECTORY=""

cleanup() {
  if [ -n "$TEMPORARY_DIRECTORY" ] && [ -d "$TEMPORARY_DIRECTORY" ]; then
    rm -rf -- "$TEMPORARY_DIRECTORY"
  fi
}
trap cleanup EXIT HUP INT TERM

echo "VerseVAD local setup for macOS"
echo "This creates a private Python environment inside the project folder."
echo "It does not require administrator access or change system-wide Python settings."
echo "Setup may download the pinned Python runtime and dependencies."
echo "Poems and lexicons are not uploaded."
echo

mkdir -p "$UV_DIRECTORY" "$DOWNLOAD_DIRECTORY" "$RUNTIME_DIRECTORY"

if [ ! -x "$UV_EXECUTABLE" ]; then
  echo "Downloading the pinned project setup tool (uv $UV_VERSION)..."
  TEMPORARY_DIRECTORY=$(mktemp -d "$DOWNLOAD_DIRECTORY/uv-installer.XXXXXX")
  INSTALLER="$TEMPORARY_DIRECTORY/install.sh"
  curl --fail --location --silent --show-error \
    "https://astral.sh/uv/$UV_VERSION/install.sh" \
    --output "$INSTALLER"
  env UV_UNMANAGED_INSTALL="$UV_DIRECTORY" sh "$INSTALLER"
fi

if [ ! -x "$UV_EXECUTABLE" ]; then
  echo "The local setup tool is still missing after setup."
  echo "Please copy or photograph this message and report it."
  exit 1
fi

export UV_CACHE_DIR="$RUNTIME_DIRECTORY/uv-cache"
export UV_PYTHON_INSTALL_DIR="$RUNTIME_DIRECTORY/python"
export UV_NO_MODIFY_PATH=1
export UV_PYTHON_PREFERENCE=only-managed

# A copied or moved virtual environment can contain absolute paths from a
# different computer or operating system. Rebuild only this disposable folder.
if [ -d "$VIRTUAL_ENVIRONMENT" ]; then
  REBUILD_ENVIRONMENT=0
  if [ ! -x "$VIRTUAL_ENVIRONMENT/bin/python" ]; then
    REBUILD_ENVIRONMENT=1
  elif ! "$VIRTUAL_ENVIRONMENT/bin/python" -c \
    "import sys; raise SystemExit(0 if sys.prefix else 1)" >/dev/null 2>&1; then
    REBUILD_ENVIRONMENT=1
  fi

  if [ "$REBUILD_ENVIRONMENT" -eq 1 ]; then
    case "$VIRTUAL_ENVIRONMENT" in
      "$PROJECT_ROOT/.venv") ;;
      *)
        echo "Refusing to rebuild an environment outside the VerseVAD folder."
        exit 1
        ;;
    esac
    echo "Rebuilding the disposable local environment for this Mac..."
    rm -rf -- "$VIRTUAL_ENVIRONMENT"
  fi
fi

cd "$PROJECT_ROOT"
echo "Creating or checking the locked project environment..."
"$UV_EXECUTABLE" sync --locked --python 3.12

echo "Running VerseVAD's core local diagnostic checks..."
"$UV_EXECUTABLE" run --frozen --offline versevad-diagnose \
  --quick --runtime-only

chmod u+x \
  "$PROJECT_ROOT/setup_macos.command" \
  "$PROJECT_ROOT/start_versevad.command" \
  "$PROJECT_ROOT/diagnose_macos.command"

echo
echo "VerseVAD setup completed successfully."
echo "Research lexicons are installed separately; see docs/resource-installation.md."
echo "You can now double-click start_versevad.command."
