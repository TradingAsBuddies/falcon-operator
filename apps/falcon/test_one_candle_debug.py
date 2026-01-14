#!/usr/bin/env python3
"""
Debug version - trace exactly why no trades are happening
"""
import sys
import backtrader as bt
from datetime import datetime, timedelta
import pandas as pd
import glob
import gzip


# Create a debug version of the strategy
class OneCandleDebug(bt.Strategy):
    params = (
        ('lookback_period', 20),
        ('breakout_threshold', 0.001),
        ('retest_tolerance', 0.003),
        ('risk_reward_ratio', 2.0),
        ('position_size_pct', 0.20),
        ('require_confirmation', False),
        ('stop_loss_pct', 0.02),
        ('trade_start_hour', 9),
        ('trade_start_minute', 30),
        ('trade_end_hour', 11),
        ('trade_end_minute', 0),
    )

    def __init__(self):
        self.order = None
        self.entry_price = None
        self.stop_price = None
        self.target_price = None
        self.swing_highs = []
        self.swing_lows = []
        self.breakout_level = None
        self.breakout_bar = None
        self.waiting_for_retest = False
        self.trade_attempts = 0

    def is_trading_hours(self):
        if len(self.data) == 0:
            return False
        current_time = self.data.datetime.time(0)
        if current_time is None:
            return True
        from datetime import time
        start_time = time(self.params.trade_start_hour, self.params.trade_start_minute)
        end_time = time(self.params.trade_end_hour, self.params.trade_end_minute)
        return start_time <= current_time <= end_time

    def identify_swing_levels(self):
        if len(self.data) < self.params.lookback_period:
            return
        highs = [self.data.high[-i] for i in range(self.params.lookback_period)]
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                self.swing_highs.append(highs[i])
        self.swing_highs = self.swing_highs[-10:]

    def detect_breakout(self):
        if not self.swing_highs or self.waiting_for_retest:
            return False
        resistance = max(self.swing_highs)
        current_close = self.data.close[0]
        breakout_price = resistance * (1 + self.params.breakout_threshold)
        if current_close > breakout_price:
            self.breakout_level = resistance
            self.breakout_bar = len(self.data)
            self.waiting_for_retest = True
            print(f"  BREAKOUT: {current_close:.2f} > {breakout_price:.2f}")
            return True
        return False

    def detect_retest(self):
        if not self.waiting_for_retest or not self.breakout_level:
            return False
        current_low = self.data.low[0]
        retest_upper = self.breakout_level * (1 + self.params.retest_tolerance)
        retest_lower = self.breakout_level * (1 - self.params.retest_tolerance)
        if retest_lower <= current_low <= retest_upper:
            return True
        return False

    def next(self):
        if self.order:
            return
        if not self.is_trading_hours():
            return

        self.identify_swing_levels()

        if not self.position:
            # Detect breakout
            self.detect_breakout()

            # Detect retest and enter
            if self.detect_retest():
                self.trade_attempts += 1

                # Simple entry - no confirmation needed
                size = int((self.broker.getvalue() * self.params.position_size_pct) / self.data.close[0])
                size = max(size, 1)

                entry_price = self.data.close[0]
                stop_distance = entry_price * self.params.stop_loss_pct
                stop_price = entry_price - stop_distance
                target_price = entry_price + (stop_distance * self.params.risk_reward_ratio)

                self.entry_price = entry_price
                self.stop_price = stop_price
                self.target_price = target_price

                self.order = self.buy(size=size)
                print(f"  ENTRY: Buy {size} shares at {entry_price:.2f}, Stop: {stop_price:.2f}, Target: {target_price:.2f}")

                self.waiting_for_retest = False
        else:
            current_price = self.data.close[0]
            if current_price <= self.stop_price:
                self.order = self.close()
                print(f"  EXIT: Stop loss at {current_price:.2f}")
            elif current_price >= self.target_price:
                self.order = self.close()
                print(f"  EXIT: Target hit at {current_price:.2f}")
            elif not self.is_trading_hours():
                self.order = self.close()
                print(f"  EXIT: End of trading window at {current_price:.2f}")

    def notify_order(self, order):
        if order.status in [order.Completed]:
            pass
        self.order = None

    def stop(self):
        print(f"\nStrategy Summary:")
        print(f"  Trade attempts: {self.trade_attempts}")
        print(f"  Final value: ${self.broker.getvalue():,.2f}")


def load_data(ticker):
    files = sorted(glob.glob('market_data/intraday_bars/intraday_bars_*.csv.gz'))
    if not files:
        return None
    dfs = []
    for file in files[:5]:  # Only first 5 days for quick test
        try:
            df = pd.read_csv(file, compression='gzip')
            df = df[df['ticker'] == ticker]
            if not df.empty:
                dfs.append(df)
        except:
            continue
    if not dfs:
        return None
    df = pd.concat(dfs, ignore_index=True)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')
    print(f"Loaded {len(df)} bars ({df['datetime'].dt.date.nunique()} days)")
    return df


def main():
    ticker = 'SPY'
    print(f"\nOne Candle Strategy - Debug Trace")
    print("="*70)

    df = load_data(ticker)
    if df is None or df.empty:
        print("ERROR: No data")
        sys.exit(1)

    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    df['openinterest'] = 0
    df.set_index('datetime', inplace=True)

    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(OneCandleDebug)
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)

    print(f"Starting: ${cerebro.broker.getvalue():,.2f}\n")
    print("Running...\n")

    results = cerebro.run()

    print(f"\nFinal: ${cerebro.broker.getvalue():,.2f}")
    print("="*70)


if __name__ == '__main__':
    main()
