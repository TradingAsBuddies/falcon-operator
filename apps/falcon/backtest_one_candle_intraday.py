#!/usr/bin/env python3
"""
Backtest the One Candle Rule Strategy with Intraday (1-minute) Data

This script is specifically designed for intraday data with timestamps.

Usage:
    python3 backtest_one_candle_intraday.py --ticker SPY --days 30
    python3 backtest_one_candle_intraday.py --ticker TSLA --days 30 --debug
"""
import sys
import argparse
import backtrader as bt
from datetime import datetime, timedelta
import pandas as pd
import glob
import gzip


def load_intraday_data(ticker, days):
    """Load intraday data from compressed CSV files"""
    try:
        # Find all intraday bar files
        files = sorted(glob.glob('market_data/intraday_bars/intraday_bars_*.csv.gz'))

        if not files:
            print("ERROR: No intraday data files found in market_data/intraday_bars/")
            print("Run: python3 download_intraday_data.py --ticker", ticker)
            return None

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Load and concatenate data
        dfs = []
        for file in files:
            try:
                df = pd.read_csv(file, compression='gzip')
                df = df[df['ticker'] == ticker]
                if not df.empty:
                    dfs.append(df)
            except Exception as e:
                continue

        if not dfs:
            print(f"ERROR: No data found for {ticker}")
            return None

        # Combine all data
        df = pd.concat(dfs, ignore_index=True)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')

        # Filter date range
        df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]

        if df.empty:
            print(f"ERROR: No data in date range")
            return None

        print(f"Loaded {len(df)} intraday bars for {ticker}")
        print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")

        # Count trading days
        trading_days = df['datetime'].dt.date.nunique()
        avg_bars_per_day = len(df) / trading_days if trading_days > 0 else 0
        print(f"Trading days: {trading_days}")
        print(f"Avg bars/day: {avg_bars_per_day:.0f}")

        return df

    except Exception as e:
        print(f"ERROR loading data: {e}")
        return None


def run_backtest(ticker='SPY', days=30, initial_cash=10000.0, debug=False):
    """Run backtest with One Candle Strategy on intraday data"""

    print(f"\n{'='*80}")
    print(f"ONE CANDLE RULE STRATEGY - INTRADAY BACKTEST")
    print(f"{'='*80}")
    print(f"Ticker: {ticker}")
    print(f"Period: {days} days")
    print(f"Initial Cash: ${initial_cash:,.2f}")
    print(f"{'='*80}\n")

    # Load intraday data
    df = load_intraday_data(ticker, days)
    if df is None or df.empty:
        print("ERROR: Could not load intraday data")
        return None

    # Prepare data for backtrader
    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    df['openinterest'] = 0
    df.set_index('datetime', inplace=True)

    # Create backtrader cerebro
    cerebro = bt.Cerebro()

    # Add data
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    # Import strategy
    from strategies.one_candle_strategy import OneCandleStrategy

    # Add strategy with original parameters (designed for intraday)
    cerebro.addstrategy(
        OneCandleStrategy,
        lookback_period=20,              # Original parameter
        breakout_threshold=0.001,        # 0.1% breakout
        retest_tolerance=0.003,          # 0.3% retest zone
        risk_reward_ratio=2.0,           # 1:2 R:R
        position_size_pct=0.20,          # 20% per trade
        require_confirmation=True,        # Require patterns
        stop_loss_pct=0.02,              # 2% stop
        trade_start_hour=9,              # 9:30 AM
        trade_start_minute=30,
        trade_end_hour=11,               # 11:00 AM
        trade_end_minute=0,
        debug=debug
    )

    # Set initial cash
    cerebro.broker.setcash(initial_cash)

    # Set commission (0.1% per trade)
    cerebro.broker.setcommission(commission=0.001)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    # Print starting value
    start_value = cerebro.broker.getvalue()
    print(f'Starting Portfolio Value: ${start_value:,.2f}')

    # Run backtest
    print("\\nRunning backtest...\\n")
    results = cerebro.run()
    strat = results[0]

    # Print ending value
    end_value = cerebro.broker.getvalue()
    print(f'\\nFinal Portfolio Value: ${end_value:,.2f}')

    # Calculate results
    total_return = ((end_value - start_value) / start_value) * 100

    # Get analyzer results
    sharpe = strat.analyzers.sharpe.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    returns = strat.analyzers.returns.get_analysis()

    # Print summary
    print(f"\\n{'='*80}")
    print("BACKTEST RESULTS")
    print(f"{'='*80}")
    print(f"Total Return: {total_return:,.2f}%")
    print(f"Total Profit/Loss: ${end_value - start_value:,.2f}")

    sharpe_val = sharpe.get('sharperatio') or 0
    print(f"Sharpe Ratio: {sharpe_val:.2f}")
    print(f"Max Drawdown: {drawdown.get('max', {}).get('drawdown', 0):.2f}%")

    # Trade statistics
    total_trades = trades.get('total', {}).get('closed', 0)
    won = trades.get('won', {}).get('total', 0)
    lost = trades.get('lost', {}).get('total', 0)
    win_rate = (won / total_trades * 100) if total_trades > 0 else 0

    print(f"\\nTrade Statistics:")
    print(f"  Total Trades: {total_trades}")
    print(f"  Winning Trades: {won}")
    print(f"  Losing Trades: {lost}")
    print(f"  Win Rate: {win_rate:.1f}%")

    if won > 0:
        avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
        print(f"  Average Win: ${avg_win:.2f}")

    if lost > 0:
        avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
        print(f"  Average Loss: ${avg_loss:.2f}")

    if won > 0 and lost > 0:
        avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
        avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
        profit_factor = abs(avg_win * won / (avg_loss * lost)) if avg_loss != 0 else 0
        print(f"  Profit Factor: {profit_factor:.2f}")

    print(f"{'='*80}\\n")

    # Determine if strategy passes validation
    passes_validation = (
        total_return > -10 and
        drawdown.get('max', {}).get('drawdown', 0) < 30 and
        total_trades > 0
    )

    if passes_validation:
        print("OK Strategy PASSES validation criteria")
    else:
        print("FAIL Strategy FAILS validation criteria")
        if total_return <= -10:
            print(f"   - Return {total_return:.2f}% is below -10% threshold")
        if drawdown.get('max', {}).get('drawdown', 0) >= 30:
            print(f"   - Drawdown {drawdown.get('max', {}).get('drawdown', 0):.2f}% exceeds 30% limit")
        if total_trades == 0:
            print("   - No trades executed")

    # Comparison to creator's claims
    print(f"\\n{'='*80}")
    print("COMPARISON TO CREATOR'S PERFORMANCE")
    print(f"{'='*80}")
    print(f"Creator's Win Rate: 60-80%")
    print(f"Our Win Rate: {win_rate:.1f}%")
    print(f"Creator's Risk-Reward: 1:2")
    print(f"Our Implementation: 1:2 (hardcoded)")

    if win_rate >= 60:
        print("\\nOK Win rate meets or exceeds creator's performance!")
    elif win_rate >= 50:
        print("\\nWARN Win rate is decent but below creator's 60-80% range")
    else:
        print("\\nFAIL Win rate is below expectations - strategy may need tuning")

    print(f"{'='*80}\\n")

    return {
        'ticker': ticker,
        'days': days,
        'start_value': start_value,
        'end_value': end_value,
        'total_return': total_return,
        'sharpe_ratio': sharpe_val,
        'max_drawdown': drawdown.get('max', {}).get('drawdown', 0),
        'total_trades': total_trades,
        'won': won,
        'lost': lost,
        'win_rate': win_rate,
        'passes_validation': passes_validation
    }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Backtest the One Candle Rule Strategy with Intraday Data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backtest SPY for 30 days
  python3 backtest_one_candle_intraday.py --ticker SPY --days 30

  # Backtest TSLA with debug output
  python3 backtest_one_candle_intraday.py --ticker TSLA --days 30 --debug

  # Backtest multiple tickers
  for ticker in SPY QQQ AAPL; do
      python3 backtest_one_candle_intraday.py --ticker $ticker --days 30
  done
        """
    )

    parser.add_argument(
        '--ticker',
        type=str,
        default='SPY',
        help='Stock ticker to backtest (default: SPY)'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to backtest (default: 30)'
    )

    parser.add_argument(
        '--cash',
        type=float,
        default=10000.0,
        help='Initial cash (default: 10000)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output (shows every trade)'
    )

    args = parser.parse_args()

    # Run backtest
    results = run_backtest(
        ticker=args.ticker,
        days=args.days,
        initial_cash=args.cash,
        debug=args.debug
    )

    if results is None:
        sys.exit(1)

    # Exit with appropriate code
    sys.exit(0 if results['passes_validation'] else 1)


if __name__ == '__main__':
    main()
