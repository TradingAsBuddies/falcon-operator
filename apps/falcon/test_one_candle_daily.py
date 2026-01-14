#!/usr/bin/env python3
"""
Test the One Candle strategy with parameters optimized for daily data
"""
import sys
import backtrader as bt
from datetime import datetime, timedelta
import pandas as pd

# Import the base strategy
from strategies.one_candle_strategy import OneCandleStrategy


def load_data_from_flat_files(ticker, days):
    """Load historical data from flat files"""
    try:
        import glob
        import gzip

        files = sorted(glob.glob('market_data/daily_bars/daily_bars_*.csv.gz'))
        if not files:
            print("ERROR: No market data files found")
            return None

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        dfs = []
        for file in files[-days:]:
            try:
                df = pd.read_csv(file, compression='gzip')
                df = df[df['ticker'] == ticker]
                if not df.empty:
                    dfs.append(df)
            except:
                continue

        if not dfs:
            print(f"ERROR: No data found for {ticker}")
            return None

        df = pd.concat(dfs, ignore_index=True)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

        print(f"Loaded {len(df)} bars for {ticker}")
        return df

    except Exception as e:
        print(f"ERROR loading data: {e}")
        return None


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'SPY'

    print(f"\nTesting One Candle Strategy (Daily Data Optimized)")
    print(f"Ticker: {ticker}")
    print("="*60)

    # Load data
    df = load_data_from_flat_files(ticker, 180)
    if df is None or df.empty:
        sys.exit(1)

    # Prepare for backtrader
    df = df.rename(columns={'date': 'datetime'})
    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    df['openinterest'] = 0
    df.set_index('datetime', inplace=True)

    # Create cerebro
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    # Add strategy with DAILY-OPTIMIZED parameters
    cerebro.addstrategy(
        OneCandleStrategy,
        lookback_period=10,              # Shorter lookback for daily
        breakout_threshold=0.005,        # 0.5% breakout (daily moves are bigger)
        retest_tolerance=0.01,           # 1% retest zone (more volatility)
        risk_reward_ratio=2.0,           # Keep 1:2 R:R
        position_size_pct=0.20,          # 20% position size
        require_confirmation=False,       # Disable strict confirmation for daily
        stop_loss_pct=0.03,              # 3% stop (wider for daily volatility)
        trade_start_hour=0,              # Trade all day (no intraday filter)
        trade_end_hour=23,
        debug=True                        # Enable logging
    )

    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

    print(f"Starting Value: ${cerebro.broker.getvalue():,.2f}\n")

    results = cerebro.run()
    strat = results[0]

    end_value = cerebro.broker.getvalue()
    total_return = ((end_value - 10000) / 10000) * 100

    print(f"\n{'='*60}")
    print(f"Final Value: ${end_value:,.2f}")
    print(f"Return: {total_return:.2f}%")

    trades = strat.analyzers.trades.get_analysis()
    total = trades.get('total', {}).get('closed', 0)
    won = trades.get('won', {}).get('total', 0)

    print(f"Total Trades: {total}")
    print(f"Win Rate: {(won/total*100):.1f}%" if total > 0 else "Win Rate: N/A")
    print("="*60)

    if total == 0:
        print("\nNOTE: No trades executed - daily data may not have enough")
        print("      breakout/retest patterns for this strategy.")
        print("      Consider using intraday data (1min, 5min) for better results.")


if __name__ == '__main__':
    main()
