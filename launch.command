#!/bin/bash
# StorageScout — Mac Desktop Launcher
# Double-click this file from your Desktop (or anywhere) to start the app.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# If the server is already running on port 8000, just open the browser
if lsof -i:8000 -t >/dev/null 2>&1; then
  echo "Server already running — opening browser…"
  open http://127.0.0.1:8000
  exit 0
fi

# Check if venv exists
if [ ! -f "$DIR/.venv/bin/activate" ]; then
  echo "ERROR: Virtual environment not found at $DIR/.venv"
  echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

echo "Starting StorageScout…"
source "$DIR/.venv/bin/activate"

# Launch uvicorn in the background, logging to server.log
nohup uvicorn app.main:app --app-dir "$DIR" --host 127.0.0.1 --port 8000 \
  > "$DIR/server.log" 2>&1 &

SERVER_PID=$!
echo $SERVER_PID > "$DIR/server.pid"
echo "Server starting (PID $SERVER_PID) — waiting for it to be ready…"

# Poll until server is ready (max 10 seconds)
MAX_WAIT=10
COUNT=0
until curl -s http://127.0.0.1:8000 >/dev/null 2>&1; do
  sleep 1
  COUNT=$((COUNT + 1))
  if [ $COUNT -ge $MAX_WAIT ]; then
    echo "ERROR: Server did not start within ${MAX_WAIT}s. Check $DIR/server.log"
    exit 1
  fi
done

echo "Server ready!"
open http://127.0.0.1:8000
echo "Done. Logs: $DIR/server.log"
