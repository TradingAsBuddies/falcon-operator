#!/bin/bash
# Paper Trading Management Script for One Candle Strategy

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/paper_trading.pid"
LOG_FILE="$SCRIPT_DIR/paper_trading.log"
PYTHON="$SCRIPT_DIR/backtest/bin/python3"
TICKER="${1:-TSLA}"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Paper trading is already running (PID: $PID)"
            return 1
        else
            echo "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi

    echo "Starting paper trading for $TICKER..."
    nohup "$PYTHON" "$SCRIPT_DIR/paper_trade_one_candle.py" --ticker "$TICKER" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 2

    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "✓ Paper trading started (PID: $(cat "$PID_FILE"))"
        echo "✓ Log: $LOG_FILE"
        echo ""
        echo "Monitor with:"
        echo "  tail -f $LOG_FILE"
        echo "  ./manage_paper_trading.sh status"
        echo ""
        echo "Dashboard:"
        echo "  http://192.168.1.162/dashboard"
    else
        echo "✗ Failed to start paper trading"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Paper trading is not running"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Stopping paper trading (PID: $PID)..."
        kill "$PID"

        # Wait for process to stop
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done

        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Force killing..."
            kill -9 "$PID"
        fi

        rm -f "$PID_FILE"
        echo "✓ Paper trading stopped"
    else
        echo "Paper trading is not running (stale PID file)"
        rm -f "$PID_FILE"
    fi
}

status() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Status: NOT RUNNING"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Status: RUNNING"
        echo "PID: $PID"
        echo "Ticker: $TICKER"
        echo "Log: $LOG_FILE"
        echo ""
        echo "Recent activity:"
        tail -20 "$LOG_FILE"
    else
        echo "Status: NOT RUNNING (stale PID file)"
        rm -f "$PID_FILE"
        return 1
    fi
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "No log file found: $LOG_FILE"
    fi
}

case "${2:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 2
        start
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "Usage: $0 [TICKER] {start|stop|restart|status|logs}"
        echo ""
        echo "Examples:"
        echo "  $0 TSLA start    # Start paper trading for TSLA"
        echo "  $0 TSLA stop     # Stop paper trading"
        echo "  $0 TSLA status   # Check status"
        echo "  $0 TSLA logs     # Follow logs"
        exit 1
        ;;
esac
