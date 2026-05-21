#!/bin/zsh
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
URL="http://localhost:5000/visualize.html"

stop_server_on_port() {
  PORT="$1"

  OLD_SERVER_PIDS=$(lsof -nP -tiTCP:$PORT -sTCP:LISTEN || true)

  if [ -n "$OLD_SERVER_PIDS" ]; then
    echo "Stopping old server on port $PORT..."
    echo "$OLD_SERVER_PIDS" | xargs kill
    sleep 1
  fi

  OLD_SERVER_PIDS=$(lsof -nP -tiTCP:$PORT -sTCP:LISTEN || true)

  if [ -n "$OLD_SERVER_PIDS" ]; then
    echo "Force stopping old server on port $PORT..."
    echo "$OLD_SERVER_PIDS" | xargs kill -9
  fi
}

stop_server_on_port 5000
stop_server_on_port 3000

if ! docker info >/dev/null 2>&1; then
  open -a Docker || true
  echo "Waiting for Docker Desktop..."
  for i in {1..60}; do
    if docker info >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done
fi

if ! docker image inspect cpp-tutor/opt-cpp-backend-cpp20-sb:local >/dev/null 2>&1; then
  echo "Missing cpp-tutor/opt-cpp-backend-cpp20-sb:local image."
  echo "Build it first using the C++20 setup command."
  exit 1
fi

DOCKER_BIN="$(command -v docker)"
export DOCKER_BIN

(
  cd "$PROJECT_DIR/v4-cokapi"
  node cokapi.js http3000
) &

BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting local C/C++ backend on port 3000..."
echo "Using local Docker image: cpp-tutor/opt-cpp-backend-cpp20-sb:local"
sleep 2

(
  for i in {1..40}; do
    if curl -fsS "$URL" >/dev/null 2>&1; then
      open "$URL"
      exit 0
    fi
    sleep 0.25
  done
  open "$URL"
) &

echo "Starting cpp-tutor local frontend..."
echo "Browser will open automatically at:"
echo "$URL"
echo
echo "C/C++ execution is local through Docker + v4-cokapi."

"$PROJECT_DIR/start-cpp-tutor.sh"
