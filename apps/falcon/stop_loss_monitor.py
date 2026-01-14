#!/usr/bin/env python3
"""
Stop-Loss Monitor Service
Monitors positions and automatically executes sell orders when stop-loss is triggered
"""

import time
import json
import requests
from datetime import datetime
import signal
import sys
from db_manager import get_db_manager

CHECK_INTERVAL = 10  # Check every 10 seconds
API_BASE_URL = "http://localhost:5000/api"

# Initialize database manager
db = get_db_manager()

# Global flag for graceful shutdown
running = True

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global running
    print("\n[STOP-LOSS MONITOR] Shutdown signal received, stopping monitor...")
    running = False

def get_positions_with_stop_loss():
    """Get all positions that have a stop-loss set"""
    rows = db.execute('''
        SELECT symbol, quantity, entry_price, stop_loss
        FROM positions
        WHERE stop_loss IS NOT NULL AND stop_loss > 0
    ''', fetch='all') or []

    return [
        {
            'symbol': row[0],
            'quantity': float(row[1]),
            'entry_price': float(row[2]),
            'stop_loss': float(row[3])
        }
        for row in rows
    ]

def get_current_price(symbol):
    """Get current price for a symbol from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/positions", timeout=5)
        if response.status_code == 200:
            positions = response.json()
            for pos in positions:
                if pos['symbol'] == symbol:
                    return pos['currentPrice']
    except Exception as e:
        print(f"[ERROR] Failed to get current price for {symbol}: {e}")

    return None

def execute_stop_loss_sell(symbol, quantity, current_price, stop_loss, entry_price):
    """Execute a sell order due to stop-loss trigger"""
    try:
        order_data = {
            'symbol': symbol,
            'side': 'sell',
            'quantity': int(quantity),
            'order_type': 'market'
        }

        response = requests.post(
            f"{API_BASE_URL}/order",
            json=order_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            pnl = (current_price - entry_price) * quantity
            pnl_pct = ((current_price - entry_price) / entry_price * 100)

            print(f"[STOP-LOSS TRIGGERED] {symbol}")
            print(f"  Sold: {quantity} shares @ ${current_price:.2f}")
            print(f"  Stop-Loss: ${stop_loss:.2f}")
            print(f"  Entry: ${entry_price:.2f}")
            print(f"  P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
            print(f"  Order ID: {result.get('timestamp', 'N/A')}")

            return True
        else:
            print(f"[ERROR] Stop-loss sell failed for {symbol}: {response.text}")
            return False

    except Exception as e:
        print(f"[ERROR] Failed to execute stop-loss sell for {symbol}: {e}")
        return False

def check_stop_losses():
    """Check all positions with stop-loss and trigger sells if needed"""
    positions = get_positions_with_stop_loss()

    if not positions:
        return

    for position in positions:
        symbol = position['symbol']
        quantity = position['quantity']
        entry_price = position['entry_price']
        stop_loss = position['stop_loss']

        # Get current price
        current_price = get_current_price(symbol)

        if current_price is None:
            continue

        # Check if stop-loss is triggered
        if current_price <= stop_loss:
            print(f"\n[ALERT] Stop-loss triggered for {symbol}: ${current_price:.2f} <= ${stop_loss:.2f}")
            execute_stop_loss_sell(symbol, quantity, current_price, stop_loss, entry_price)

def main():
    """Main monitoring loop"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 80)
    print("FALCON STOP-LOSS MONITOR")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {db.db_type}")
    print(f"Check Interval: {CHECK_INTERVAL} seconds")
    print(f"API: {API_BASE_URL}")
    print("=" * 80)
    print("\nMonitoring positions for stop-loss triggers...")
    print("Press Ctrl+C to stop\n")

    iteration = 0

    while running:
        try:
            iteration += 1

            # Check stop-losses
            check_stop_losses()

            # Log status every 60 seconds (6 iterations at 10s interval)
            if iteration % 6 == 0:
                positions = get_positions_with_stop_loss()
                print(f"[STATUS] {datetime.now().strftime('%H:%M:%S')} - Monitoring {len(positions)} position(s) with stop-loss")

            # Wait for next check
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"[ERROR] Monitor loop error: {e}")
            time.sleep(CHECK_INTERVAL)

    print("\n[STOP-LOSS MONITOR] Stopped gracefully")
    sys.exit(0)

if __name__ == "__main__":
    main()
