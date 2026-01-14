#!/usr/bin/env python3
"""
Paper Trading - One Candle Strategy
Live trading with real-time 1-minute bars from Polygon.io

Deploys the One Candle Rule strategy to paper trading for specified ticker(s)
"""
import os
import sys
import time
import requests
import sqlite3
from datetime import datetime, time as dt_time, timedelta
from collections import deque
import signal


class OneCandlePaperTrader:
    """Paper trading implementation of One Candle Rule strategy"""

    def __init__(self, ticker, api_key, db_path='paper_trading.db'):
        self.ticker = ticker
        self.api_key = api_key
        self.db_path = db_path
        self.running = False

        # Strategy parameters (from successful TSLA backtest)
        self.lookback_period = 20
        self.breakout_threshold = 0.001  # 0.1%
        self.retest_tolerance = 0.003    # 0.3%
        self.risk_reward_ratio = 2.0
        self.position_size_pct = 0.20    # 20% of capital
        self.stop_loss_pct = 0.02        # 2%

        # Trading window (9:30 AM - 11:00 AM ET)
        self.trade_start_time = dt_time(9, 30)
        self.trade_end_time = dt_time(11, 0)

        # State tracking
        self.bars = deque(maxlen=100)  # Keep last 100 bars
        self.swing_highs = []
        self.swing_lows = []
        self.breakout_level = None
        self.waiting_for_retest = False

        # Position tracking
        self.position = None
        self.entry_price = None
        self.stop_price = None
        self.target_price = None

        # Initialize database connection
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        print(f"\n{'='*70}")
        print(f"ONE CANDLE STRATEGY - PAPER TRADING")
        print(f"{'='*70}")
        print(f"Ticker: {ticker}")
        print(f"Database: {db_path}")
        print(f"Trading Window: 9:30 AM - 11:00 AM ET")
        print(f"Parameters: Breakout={self.breakout_threshold*100:.1f}%, "
              f"Retest={self.retest_tolerance*100:.1f}%, R:R=1:{self.risk_reward_ratio}")
        print(f"{'='*70}\n")

    def get_account_balance(self):
        """Get current cash balance"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT cash FROM account LIMIT 1")
        result = cursor.fetchone()
        return float(result[0]) if result else 10000.0

    def get_current_position(self):
        """Check if we have an open position"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT symbol, quantity, entry_price
            FROM positions
            WHERE symbol = ? AND quantity > 0
        """, (self.ticker,))
        return cursor.fetchone()

    def place_order(self, side, quantity, price, reason=""):
        """Place a paper trading order"""
        cursor = self.conn.cursor()
        order_type = 'buy' if side == 'BUY' else 'sell'

        # Insert order
        cursor.execute("""
            INSERT INTO orders (symbol, order_type, quantity, price, status, timestamp)
            VALUES (?, ?, ?, ?, 'filled', ?)
        """, (self.ticker, order_type, quantity, price, datetime.now().isoformat()))

        # Update positions
        if side == 'BUY':
            # Check if position exists
            cursor.execute("SELECT * FROM positions WHERE symbol = ?", (self.ticker,))
            pos = cursor.fetchone()

            if pos:
                # Update existing position
                new_qty = pos['quantity'] + quantity
                new_avg = ((pos['quantity'] * pos['entry_price']) + (quantity * price)) / new_qty
                cursor.execute("""
                    UPDATE positions
                    SET quantity = ?, entry_price = ?, last_updated = ?
                    WHERE symbol = ?
                """, (new_qty, new_avg, datetime.now().isoformat(), self.ticker))
            else:
                # Create new position
                cursor.execute("""
                    INSERT INTO positions (symbol, quantity, entry_price, last_updated)
                    VALUES (?, ?, ?, ?)
                """, (self.ticker, quantity, price, datetime.now().isoformat()))

            # Deduct cash
            cash = self.get_account_balance()
            new_cash = cash - (quantity * price)
            cursor.execute("UPDATE account SET cash = ?, last_updated = ?",
                          (new_cash, datetime.now().isoformat()))

            print(f"[{datetime.now().strftime('%H:%M:%S')}] BUY {quantity} {self.ticker} @ ${price:.2f} - {reason}")

        else:  # SELL
            cursor.execute("SELECT * FROM positions WHERE symbol = ?", (self.ticker,))
            pos = cursor.fetchone()

            if pos:
                new_qty = pos['quantity'] - quantity

                if new_qty <= 0:
                    # Close position
                    cursor.execute("DELETE FROM positions WHERE symbol = ?", (self.ticker,))
                else:
                    # Reduce position
                    cursor.execute("""
                        UPDATE positions
                        SET quantity = ?, last_updated = ?
                        WHERE symbol = ?
                    """, (new_qty, datetime.now().isoformat(), self.ticker))

                # Add cash
                cash = self.get_account_balance()
                pnl = (price - pos['entry_price']) * quantity
                new_cash = cash + (quantity * price)
                cursor.execute("UPDATE account SET cash = ?, last_updated = ?",
                              (new_cash, datetime.now().isoformat()))

                print(f"[{datetime.now().strftime('%H:%M:%S')}] SELL {quantity} {self.ticker} @ ${price:.2f} - {reason}")
                print(f"    P&L: ${pnl:.2f} ({(pnl/pos['entry_price']/quantity)*100:.2f}%)")

        self.conn.commit()

    def get_latest_bar(self):
        """Fetch latest 1-minute bar from Polygon"""
        try:
            # Get current date
            today = datetime.now().strftime('%Y-%m-%d')

            # Polygon aggregates endpoint for 1-minute bars
            url = f"https://api.polygon.io/v2/aggs/ticker/{self.ticker}/range/1/minute/{today}/{today}"
            params = {
                'adjusted': 'true',
                'sort': 'desc',
                'limit': 1,
                'apiKey': self.api_key
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 'OK' and data.get('results'):
                    bar = data['results'][0]
                    return {
                        'timestamp': datetime.fromtimestamp(bar['t'] / 1000),
                        'open': float(bar['o']),
                        'high': float(bar['h']),
                        'low': float(bar['l']),
                        'close': float(bar['c']),
                        'volume': int(bar['v'])
                    }

            return None

        except Exception as e:
            print(f"Error fetching bar: {e}")
            return None

    def is_trading_hours(self):
        """Check if current time is within trading window"""
        now = datetime.now().time()
        return self.trade_start_time <= now <= self.trade_end_time

    def identify_swing_levels(self):
        """Identify swing highs from recent bars"""
        if len(self.bars) < self.lookback_period:
            return

        recent_bars = list(self.bars)[-self.lookback_period:]
        highs = [b['high'] for b in recent_bars]

        # Find local maxima
        self.swing_highs = []
        for i in range(2, len(highs) - 2):
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and
                highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                self.swing_highs.append(highs[i])

        self.swing_highs = self.swing_highs[-10:]  # Keep last 10

    def detect_breakout(self, current_bar):
        """Detect breakout above resistance"""
        if not self.swing_highs or self.waiting_for_retest:
            return False

        resistance = max(self.swing_highs)
        current_close = current_bar['close']
        breakout_price = resistance * (1 + self.breakout_threshold)

        if current_close > breakout_price:
            self.breakout_level = resistance
            self.waiting_for_retest = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] BREAKOUT detected: ${current_close:.2f} > ${breakout_price:.2f}")
            return True

        return False

    def detect_retest(self, current_bar):
        """Detect retest of broken resistance"""
        if not self.waiting_for_retest or not self.breakout_level:
            return False

        current_low = current_bar['low']
        retest_upper = self.breakout_level * (1 + self.retest_tolerance)
        retest_lower = self.breakout_level * (1 - self.retest_tolerance)

        if retest_lower <= current_low <= retest_upper:
            return True

        return False

    def check_entry_signal(self, current_bar):
        """Check for entry signal"""
        if self.position:
            return False

        # Update swing levels
        self.identify_swing_levels()

        # Detect breakout
        self.detect_breakout(current_bar)

        # Detect retest and enter
        if self.detect_retest(current_bar):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] RETEST detected at ${current_bar['low']:.2f}")

            # Calculate entry
            entry_price = current_bar['close']
            stop_distance = entry_price * self.stop_loss_pct
            stop_price = entry_price - stop_distance
            target_price = entry_price + (stop_distance * self.risk_reward_ratio)

            # Calculate position size
            cash = self.get_account_balance()
            position_value = cash * self.position_size_pct
            quantity = int(position_value / entry_price)

            if quantity > 0:
                # Enter trade
                self.place_order('BUY', quantity, entry_price,
                                reason=f"Entry (Stop: ${stop_price:.2f}, Target: ${target_price:.2f})")

                self.entry_price = entry_price
                self.stop_price = stop_price
                self.target_price = target_price
                self.waiting_for_retest = False

                return True

        return False

    def check_exit_signal(self, current_bar):
        """Check for exit signal"""
        pos = self.get_current_position()
        if not pos:
            return False

        current_price = current_bar['close']

        # Check stop loss
        if current_price <= self.stop_price:
            self.place_order('SELL', pos['quantity'], current_price, reason="Stop Loss")
            self.entry_price = None
            self.stop_price = None
            self.target_price = None
            return True

        # Check target
        if current_price >= self.target_price:
            self.place_order('SELL', pos['quantity'], current_price, reason="Target Hit")
            self.entry_price = None
            self.stop_price = None
            self.target_price = None
            return True

        # Check end of trading window
        if not self.is_trading_hours():
            self.place_order('SELL', pos['quantity'], current_price, reason="End of Trading Window")
            self.entry_price = None
            self.stop_price = None
            self.target_price = None
            return True

        return False

    def run(self):
        """Main trading loop"""
        self.running = True

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Paper trading started")
        print(f"Account balance: ${self.get_account_balance():,.2f}\n")

        last_bar_time = None

        try:
            while self.running:
                # Only trade during market hours
                if not self.is_trading_hours():
                    time.sleep(60)
                    continue

                # Fetch latest bar
                bar = self.get_latest_bar()

                if bar and (not last_bar_time or bar['timestamp'] > last_bar_time):
                    last_bar_time = bar['timestamp']
                    self.bars.append(bar)

                    # Check position
                    self.position = self.get_current_position()

                    if self.position:
                        # Check exit signals
                        self.check_exit_signal(bar)
                    else:
                        # Check entry signals
                        self.check_entry_signal(bar)

                # Sleep for 60 seconds (1-minute bars)
                time.sleep(60)

        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Shutting down...")
        finally:
            self.conn.close()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Paper trading stopped")


def load_api_key():
    """Load API key from .env file"""
    env_path = os.path.expanduser('~/.local/.env')

    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('MASSIVE_API_KEY='):
                    return line.strip().split('=', 1)[1]

    return os.getenv('MASSIVE_API_KEY')


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Paper trade the One Candle strategy')
    parser.add_argument('--ticker', type=str, default='TSLA', help='Ticker symbol (default: TSLA)')
    parser.add_argument('--db', type=str, default='paper_trading.db', help='Database path')

    args = parser.parse_args()

    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("ERROR: MASSIVE_API_KEY not found in ~/.local/.env")
        sys.exit(1)

    # Create trader
    trader = OneCandlePaperTrader(args.ticker, api_key, args.db)

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        trader.running = False

    signal.signal(signal.SIGINT, signal_handler)

    # Run trading
    trader.run()


if __name__ == '__main__':
    main()
