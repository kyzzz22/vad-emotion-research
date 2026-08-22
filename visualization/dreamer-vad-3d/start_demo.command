#!/bin/bash

set -u
cd "$(dirname "$0")"

PORT=8765
while lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; do
  PORT=$((PORT + 1))
done

URL="http://127.0.0.1:${PORT}/?v=guided-ja-20260822-4"
SERVER_PID=""

cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

if command -v python3 >/dev/null 2>&1; then
  python3 -m http.server "$PORT" --bind 127.0.0.1 &
  SERVER_PID=$!
elif command -v python >/dev/null 2>&1; then
  python -m http.server "$PORT" --bind 127.0.0.1 &
  SERVER_PID=$!
elif command -v ruby >/dev/null 2>&1; then
  ruby -run -e httpd . -p "$PORT" -b 127.0.0.1 &
  SERVER_PID=$!
elif command -v php >/dev/null 2>&1; then
  php -S "127.0.0.1:${PORT}" &
  SERVER_PID=$!
else
  echo "No local web server runtime was found."
  echo "Install Python 3, then run this file again."
  echo "https://www.python.org/downloads/macos/"
  read -r -p "Press Return to close..."
  exit 1
fi

sleep 1
if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
  echo "The local server could not start."
  read -r -p "Press Return to close..."
  exit 1
fi

echo ""
echo "VAD 3D demo is running:"
echo "$URL"
echo "Keep this window open. Press Control+C to stop."
echo ""

open "$URL"
wait "$SERVER_PID"
