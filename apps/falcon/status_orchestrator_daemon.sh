#!/bin/bash
#
# Check Falcon Orchestrator Daemon Status
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PID_FILE="./orchestrator_daemon.pid"
LOG_FILE="./orchestrator_daemon.log"

echo "========================================="
echo "Falcon Orchestrator Daemon - Status"
echo "========================================="
echo ""

if [ ! -f "$PID_FILE" ]; then
    echo "Status: NOT RUNNING"
    echo "No PID file found"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ps -p $PID > /dev/null 2>&1; then
    echo "Status: RUNNING"
    echo "PID: $PID"
    echo ""

    # Show process info
    ps -fp $PID

    echo ""
    echo "Log file: $LOG_FILE"
    echo "Log size: $(du -h $LOG_FILE | cut -f1)"

    echo ""
    echo "Recent activity (last 20 lines):"
    echo "-----------------------------------------"
    tail -20 "$LOG_FILE"
else
    echo "Status: NOT RUNNING"
    echo "PID file exists but process $PID is not running"
    rm -f "$PID_FILE"
    exit 1
fi
