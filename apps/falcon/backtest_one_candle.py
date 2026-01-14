#!/usr/bin/env python3
"""
Backtest the One Candle Rule Strategy

Usage:
    python3 backtest_one_candle.py --ticker SPY --days 365
    python3 backtest_one_candle.py --ticker QQQ --days 180 --debug
"""

import sys
import argparse
import backtrader as bt
from datetime import datetime, timedelta
import pandas as pd

# Import the strategy
from strategies.one_candle_strategy import OneCandleStrategy


def load_data_from_flat_files(ticker, days):
    """Load historical data from flat files"""
    try:
        import glob
        import gzip

        # Find all daily bar files
        files = sorted(glob.glob('market_data/daily_bars/daily_bars_*.csv.gz'))

        if not files:
            print("ERROR: No market data files found in market_data/daily_bars/")
            print("Run: python3 massive_flat_files.py --download")
            return None

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Load and concatenate data
        dfs = []
        for file in files[-days:]:  # Only load recent files
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
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Filter date range
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

        print(f"Loaded {len(df)} bars for {ticker} from {df['date'].min()} to {df['date'].max()}")

        return df

    except Exception as e:
        print(f"ERROR loading data: {e}")
        return None


def run_backtest(ticker='SPY', days=365, initial_cash=10000.0, debug=False):
    """Run backtest with One Candle Strategy"""

    print(f"\n{'='*80}")
    print(f"ONE CANDLE RULE STRATEGY - BACKTEST")
    print(f"{'='*80}")
    print(f"Ticker: {ticker}")
    print(f"Period: {days} days")
    print(f"Initial Cash: ${initial_cash:,.2f}")
    print(f"{'='*80}\n")

    # Load data
    df = load_data_from_flat_files(ticker, days)
    if df is None or df.empty:
        print("ERROR: Could not load market data")
        return None

    # Prepare data for backtrader
    df = df.rename(columns={
        'date': 'datetime',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume'
    })

    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    df['openinterest'] = 0
    df.set_index('datetime', inplace=True)

    # Create backtrader cerebro
    cerebro = bt.Cerebro()

    # Add data
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    # Add strategy with debug mode
    cerebro.addstrategy(OneCandleStrategy, debug=debug)

    # Set initial cash
    cerebro.broker.setcash(initial_cash)

    # Set commission (0.1% per trade, typical for stocks)
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
    print("\nRunning backtest...\n")
    results = cerebro.run()
    strat = results[0]

    # Print ending value
    end_value = cerebro.broker.getvalue()
    print(f'\nFinal Portfolio Value: ${end_value:,.2f}')

    # Calculate results
    total_return = ((end_value - start_value) / start_value) * 100

    # Get analyzer results
    sharpe = strat.analyzers.sharpe.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    returns = strat.analyzers.returns.get_analysis()

    # Print summary
    print(f"\n{'='*80}")
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

    print(f"\nTrade Statistics:")
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

    print(f"{'='*80}\n")

    # Determine if strategy passes validation
    passes_validation = (
        total_return > -10 and  # Return better than -10%
        drawdown.get('max', {}).get('drawdown', 0) < 30 and  # Drawdown less than 30%
        total_trades > 0  # At least some trades
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
    print(f"\n{'='*80}")
    print("COMPARISON TO CREATOR'S PERFORMANCE")
    print(f"{'='*80}")
    print(f"Creator's Win Rate: 60-80%")
    print(f"Our Win Rate: {win_rate:.1f}%")
    print(f"Creator's Risk-Reward: 1:2")
    print(f"Our Implementation: 1:2 (hardcoded)")

    if win_rate >= 60:
        print("\nOK Win rate meets or exceeds creator's performance!")
    elif win_rate >= 50:
        print("\nWARN Win rate is decent but below creator's 60-80% range")
    else:
        print("\nFAIL Win rate is below expectations - strategy may need tuning")

    print(f"{'='*80}\n")

    return {
        'ticker': ticker,
        'days': days,
        'start_value': start_value,
        'end_value': end_value,
        'total_return': total_return,
        'sharpe_ratio': sharpe.get('sharperatio', 0),
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
        description='Backtest the One Candle Rule Strategy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backtest SPY for 1 year
  python3 backtest_one_candle.py --ticker SPY --days 365

  # Backtest QQQ for 6 months with debug output
  python3 backtest_one_candle.py --ticker QQQ --days 180 --debug

  # Backtest multiple tickers
  for ticker in SPY QQQ AAPL; do
      python3 backtest_one_candle.py --ticker $ticker --days 365
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
        default=365,
        help='Number of days to backtest (default: 365)'
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
