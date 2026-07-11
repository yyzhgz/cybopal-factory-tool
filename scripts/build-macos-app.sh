#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This build must run on macOS."
  echo "PyInstaller has to create a macOS backend sidecar, and electron-builder needs macOS tooling for DMG packaging."
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_RESOURCE_DIR="$FRONTEND_DIR/resources/backend"
PYTHON_BIN="${PYTHON_BIN:-python3}"
NODE_INSTALL_MODE="${NODE_INSTALL_MODE:-ci}"
MAC_TARGET="${MAC_TARGET:-dmg}"

echo "==> Building CyboPal Factory Tool for macOS ($(uname -m))"

echo "==> Installing backend dependencies"
cd "$BACKEND_DIR"
"$PYTHON_BIN" -m pip install -r requirements-build.txt

echo "==> Running backend tests"
export PYTHONPATH="$BACKEND_DIR"
"$PYTHON_BIN" -m unittest discover -s tests

echo "==> Bundling FastAPI backend sidecar"
cd "$BACKEND_DIR/packaging"
"$PYTHON_BIN" -m PyInstaller \
  --clean \
  --noconfirm \
  --distpath "$BACKEND_DIR/dist" \
  --workpath "$BACKEND_DIR/build" \
  cybopal_api.spec

if [[ ! -x "$BACKEND_DIR/dist/cybopal-api" ]]; then
  echo "Expected backend sidecar was not created: $BACKEND_DIR/dist/cybopal-api"
  exit 1
fi

if [[ "${CYBOPAL_SKIP_BACKEND_SMOKE:-false}" != "true" ]]; then
  echo "==> Smoke testing backend sidecar"
  SMOKE_PORT="$("$PYTHON_BIN" - <<'PY'
import socket

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)"
  SMOKE_LOG="$BACKEND_DIR/dist/cybopal-api-smoke.log"

  (
    export CYBOPAL_BACKEND_HOST="127.0.0.1"
    export CYBOPAL_BACKEND_PORT="$SMOKE_PORT"
    export CYBOPAL_SSH_MOCK="${CYBOPAL_SSH_MOCK:-true}"

    "$BACKEND_DIR/dist/cybopal-api" >"$SMOKE_LOG" 2>&1 &
    SMOKE_PID="$!"

    cleanup() {
      kill "$SMOKE_PID" >/dev/null 2>&1 || true
      wait "$SMOKE_PID" >/dev/null 2>&1 || true
    }
    trap cleanup EXIT

    for _ in $(seq 1 40); do
      if "$PYTHON_BIN" - "$SMOKE_PORT" <<'PY'
import sys
import urllib.request

port = sys.argv[1]
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1) as response:
        raise SystemExit(0 if response.status == 200 else 1)
except Exception:
    raise SystemExit(1)
PY
      then
        exit 0
      fi

      if ! kill -0 "$SMOKE_PID" >/dev/null 2>&1; then
        echo "Backend sidecar exited during smoke test."
        cat "$SMOKE_LOG"
        exit 1
      fi

      sleep 0.5
    done

    echo "Backend sidecar did not answer /api/health in time."
    cat "$SMOKE_LOG"
    exit 1
  )
fi

echo "==> Copying backend sidecar into Electron resources"
mkdir -p "$BACKEND_RESOURCE_DIR"
cp "$BACKEND_DIR/dist/cybopal-api" "$BACKEND_RESOURCE_DIR/cybopal-api"
chmod +x "$BACKEND_RESOURCE_DIR/cybopal-api"

echo "==> Installing frontend dependencies"
cd "$FRONTEND_DIR"
case "$NODE_INSTALL_MODE" in
  ci)
    npm ci
    ;;
  install)
    npm install
    ;;
  skip)
    echo "Skipping frontend dependency install"
    ;;
  *)
    echo "Unknown NODE_INSTALL_MODE: $NODE_INSTALL_MODE"
    echo "Use ci, install, or skip."
    exit 1
    ;;
esac

echo "==> Building Vue renderer"
npm run build

echo "==> Packaging macOS app"
npx electron-builder --mac "$MAC_TARGET" --config electron-builder.config.cjs "$@"

echo "==> Done"
echo "Installer output:"
find "$FRONTEND_DIR/release" -maxdepth 1 -type f -print
