#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON="${PYTHON:-python3}"
VENV=".venv-build"
PYTHON_BIN="$ROOT_DIR/$VENV/bin/python"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python was not found: $PYTHON" >&2
    exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Creating build virtual environment..."
    "$PYTHON" -m venv "$VENV"
fi

echo "Installing build dependencies..."
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r requirements.txt pyinstaller

rm -rf build dist TracePince.spec

echo "Building TracePince..."
"$PYTHON_BIN" -m PyInstaller \
    --noconfirm \
    --clean \
    --onefile \
    --windowed \
    --name TracePince \
    main.py

mkdir -p dist/logs
chmod +x dist/TracePince

echo
echo "Build complete: $ROOT_DIR/dist/TracePince"
