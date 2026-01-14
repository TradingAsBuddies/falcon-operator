#!/bin/bash
#
# Stop Falcon Orchestrator Daemon
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PID_FILE="./orchestrator_daemon.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "No PID file found. Daemon may not be running."
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p $PID > /dev/null 2>&1; then
    echo "Process $PID is not running"
    rm -f "$PID_FILE"
    exit 1
fi

echo "Stopping orchestrator daemon (PID: $PID)..."
kill $PID

# Wait for graceful shutdown
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "✓ Orchestrator daemon stopped"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# Force kill if still running
if ps -p $PID > /dev/null 2>&1; then
    echo "Force stopping..."
    kill -9 $PID
    sleep 1
fi

rm -f "$PID_FILE"
echo "✓ Orchestrator daemon stopped"
