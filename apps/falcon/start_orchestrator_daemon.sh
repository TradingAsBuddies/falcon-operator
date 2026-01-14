#!/bin/bash
#
# Start Falcon Orchestrator in Daemon Mode
# Monitors positions and processes AI screener results continuously
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PYTHON_BIN="./backtest/bin/python3"
ORCHESTRATOR="./run_orchestrator.py"
LOG_FILE="./orchestrator_daemon.log"
PID_FILE="./orchestrator_daemon.pid"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "Orchestrator daemon is already running (PID: $PID)"
        exit 1
    else
        echo "Removing stale PID file"
        rm -f "$PID_FILE"
    fi
fi

echo "Starting Falcon Orchestrator Daemon..."
echo "Log file: $LOG_FILE"

# Start daemon with unbuffered Python output
nohup $PYTHON_BIN -u "$ORCHESTRATOR" >> "$LOG_FILE" 2>&1 &
PID=$!

# Save PID
echo $PID > "$PID_FILE"

# Wait a moment to check if it started successfully
sleep 2

if ps -p $PID > /dev/null 2>&1; then
    echo "✓ Orchestrator daemon started successfully (PID: $PID)"
    echo ""
    echo "Commands:"
    echo "  tail -f orchestrator_daemon.log     # View live logs"
    echo "  cat orchestrator_daemon.pid          # Get PID"
    echo "  ./stop_orchestrator_daemon.sh        # Stop daemon"
    exit 0
else
    echo "✗ Failed to start orchestrator daemon"
    rm -f "$PID_FILE"
    exit 1
fi
