#!/usr/bin/env python3
"""
Test One Candle strategy with relaxed parameters for real market testing
"""
import sys
import backtrader as bt
from datetime import datetime, timedelta
import pandas as pd
import glob
import gzip


def load_intraday_data(ticker, days):
    """Load intraday data from compressed CSV files"""
    try:
        files = sorted(glob.glob('market_data/intraday_bars/intraday_bars_*.csv.gz'))

        if not files:
            print("ERROR: No intraday data files found")
            return None

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        dfs = []
        for file in files:
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
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')
        df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]

        print(f"Loaded {len(df)} bars for {ticker}")
        return df

    except Exception as e:
        print(f"ERROR: {e}")
        return None


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'SPY'

    print(f"\nOne Candle Strategy - Relaxed Parameters Test")
    print(f"Ticker: {ticker}")
    print("="*70)

    df = load_intraday_data(ticker, 30)
    if df is None or df.empty:
        sys.exit(1)

    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    df['openinterest'] = 0
    df.set_index('datetime', inplace=True)

    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    from strategies.one_candle_strategy import OneCandleStrategy

    # RELAXED PARAMETERS for 1-minute SPY
    cerebro.addstrategy(
        OneCandleStrategy,
        lookback_period=20,
        breakout_threshold=0.001,     # 0.1% breakout
        retest_tolerance=0.003,       # 0.3% retest zone
        risk_reward_ratio=2.0,
        position_size_pct=0.20,
        require_confirmation=False,    # ← DISABLED (too strict for 1-min)
        min_body_size=0.0001,         # Relaxed from 0.003
        stop_loss_pct=0.02,
        trade_start_hour=9,
        trade_start_minute=30,
        trade_end_hour=11,
        trade_end_minute=0,
        debug=False  # Disable verbose logging
    )

    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')

    print(f"Starting Value: ${cerebro.broker.getvalue():,.2f}\n")
    print("Running backtest (this may take a moment)...")

    results = cerebro.run()
    strat = results[0]

    end_value = cerebro.broker.getvalue()
    total_return = ((end_value - 10000) / 10000) * 100

    trades = strat.analyzers.trades.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    sharpe = strat.analyzers.sharpe.get_analysis()

    total = trades.get('total', {}).get('closed', 0)
    won = trades.get('won', {}).get('total', 0)
    lost = trades.get('lost', {}).get('total', 0)

    print(f"\n{'='*70}")
    print("RESULTS (Confirmation Disabled)")
    print(f"{'='*70}")
    print(f"Final Value: ${end_value:,.2f}")
    print(f"Return: {total_return:.2f}%")
    print(f"Max Drawdown: {drawdown.get('max', {}).get('drawdown', 0):.2f}%")

    sharpe_val = sharpe.get('sharperatio') or 0
    print(f"Sharpe Ratio: {sharpe_val:.2f}")

    print(f"\nTrades: {total}")
    print(f"Won: {won} ({won/total*100:.1f}%)" if total > 0 else "Won: 0")
    print(f"Lost: {lost}")

    if won > 0:
        avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
        print(f"Avg Win: ${avg_win:.2f}")

    if lost > 0:
        avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
        print(f"Avg Loss: ${avg_loss:.2f}")

    if won > 0 and lost > 0:
        avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
        avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
        pf = abs((avg_win * won) / (avg_loss * lost)) if avg_loss != 0 else 0
        print(f"Profit Factor: {pf:.2f}")

    print(f"{'='*70}")

    if total > 0:
        print("\nSUCCESS: Strategy generated trades!")
        print("The issue was the confirmation requirement was too strict for 1-min bars.")
        print("Consider adjusting min_body_size or using 5-minute bars instead.")
    else:
        print("\nNOTE: Still no trades. The strategy may need further parameter tuning.")


if __name__ == '__main__':
    main()
