#!/bin/zsh
# Double-click launcher: starts the server (if not already running) and opens
# the host page. Keep this window open during the service — closing it or
# pressing Ctrl+C stops the server.
cd "$(dirname "$0")"

PORT=8000
URL="http://127.0.0.1:$PORT"

if curl -s -o /dev/null "$URL/health"; then
    echo "Server already running at $URL"
    open "$URL/host.html"
    exit 0
fi

.venv/bin/uvicorn server.main:app --port "$PORT" &
SERVER_PID=$!
trap "kill $SERVER_PID 2>/dev/null" EXIT

for _ in {1..40}; do
    curl -s -o /dev/null "$URL/health" && break
    sleep 0.25
done

open "$URL/host.html"
echo ""
echo "Host page: $URL/host.html"
echo "Viewers:   $URL/"
echo "Close this window (or Ctrl+C) to stop the server."
wait $SERVER_PID
