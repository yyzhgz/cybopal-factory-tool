#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_HOST="127.0.0.1"
BACKEND_PORT="8000"
FRONTEND_PORT="5173"
MOCK_MESSAGE_STATE="${CYBOPAL_MOCK_MESSAGE_STATE:-${1:-ready}}"
MOCK_ERROR_AFTER_SECONDS="${CYBOPAL_MOCK_ERROR_AFTER_SECONDS:-${2:-6}}"

if [[ -x "$ROOT_DIR/.venv/Scripts/python.exe" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/Scripts/python.exe"
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "Python not found. Please install Python and backend dependencies first."
  exit 1
fi

if command -v npm >/dev/null 2>&1; then
  NPM_BIN="npm"
elif command -v npm.cmd >/dev/null 2>&1; then
  NPM_BIN="npm.cmd"
else
  echo "npm not found. Please install Node.js dependencies first."
  exit 1
fi

cleanup() {
  echo
  echo "Stopping CyboPal mock services..."
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

echo "Starting CyboPal mock backend..."
(
  cd "$ROOT_DIR"
  export PYTHONPATH="$BACKEND_DIR"
  export CYBOPAL_SSH_MOCK="true"
  export CYBOPAL_MOCK_MESSAGE_STATE="$MOCK_MESSAGE_STATE"
  export CYBOPAL_MOCK_ERROR_AFTER_SECONDS="$MOCK_ERROR_AFTER_SECONDS"
  "$PYTHON_BIN" -m uvicorn app.main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

echo "Starting CyboPal frontend..."
(
  cd "$FRONTEND_DIR"
  "$NPM_BIN" run dev -- --host "$BACKEND_HOST" --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

echo
echo "Mock mode is starting."
echo "Mock state: $MOCK_MESSAGE_STATE"
if [[ "$MOCK_MESSAGE_STATE" == "ready_then_error" ]]; then
  echo "Mock error after: ${MOCK_ERROR_AFTER_SECONDS}s"
fi
echo "Backend:  http://$BACKEND_HOST:$BACKEND_PORT/api/health"
echo "Frontend: http://$BACKEND_HOST:$FRONTEND_PORT/"
echo
echo "Press Ctrl+C to stop both services."

wait
