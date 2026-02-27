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

echo "Starting StorageScout…"
source "$DIR/.venv/bin/activate"

# Launch uvicorn in the background, logging to server.log
nohup uvicorn app.main:app --app-dir "$DIR" --host 127.0.0.1 --port 8000 \
  > "$DIR/server.log" 2>&1 &

echo "Server starting (PID $!) — waiting…"
sleep 2

open http://127.0.0.1:8000
echo "Done. Logs: $DIR/server.log"
