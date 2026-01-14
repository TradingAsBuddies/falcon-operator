#!/usr/bin/env python3
"""
Backtest One Candle strategy with ALL available intraday data
"""
import sys
import backtrader as bt
import pandas as pd
import glob
import gzip


def load_all_intraday_data(ticker):
    """Load ALL available intraday data for ticker"""
    files = sorted(glob.glob('market_data/intraday_bars/intraday_bars_*.csv.gz'))
    if not files:
        print("ERROR: No intraday data files found")
        return None

    print(f"Found {len(files)} data files")

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
        print(f"ERROR: No data for {ticker}")
        return None

    df = pd.concat(dfs, ignore_index=True)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')

    trading_days = df['datetime'].dt.date.nunique()
    print(f"Loaded {len(df):,} bars across {trading_days} trading days")
    print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")

    return df


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'SPY'

    print(f"\n{'='*80}")
    print(f"ONE CANDLE RULE - FULL BACKTEST (All Available Intraday Data)")
    print(f"{'='*80}")
    print(f"Ticker: {ticker}")
    print(f"{'='*80}\n")

    df = load_all_intraday_data(ticker)
    if df is None or df.empty:
        sys.exit(1)

    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    df['openinterest'] = 0
    df.set_index('datetime', inplace=True)

    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    from strategies.one_candle_strategy import OneCandleStrategy

    cerebro.addstrategy(
        OneCandleStrategy,
        lookback_period=20,
        breakout_threshold=0.001,
        retest_tolerance=0.003,
        risk_reward_ratio=2.0,
        position_size_pct=0.20,
        require_confirmation=False,
        stop_loss_pct=0.02,
        trade_start_hour=9,
        trade_start_minute=30,
        trade_end_hour=11,
        trade_end_minute=0,
        debug=True  # Show trades
    )

    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    start_value = cerebro.broker.getvalue()
    print(f'\nStarting Value: ${start_value:,.2f}\n')
    print("Running backtest (this may take 30-60 seconds)...\n")

    results = cerebro.run()
    strat = results[0]

    end_value = cerebro.broker.getvalue()
    total_return = ((end_value - start_value) / start_value) * 100

    trades = strat.analyzers.trades.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    sharpe = strat.analyzers.sharpe.get_analysis()

    total_trades = trades.get('total', {}).get('closed', 0)
    won = trades.get('won', {}).get('total', 0)
    lost = trades.get('lost', {}).get('total', 0)
    win_rate = (won / total_trades * 100) if total_trades > 0 else 0

    print(f"\n{'='*80}")
    print("FINAL RESULTS")
    print(f"{'='*80}")
    print(f"Starting Value: ${start_value:,.2f}")
    print(f"Final Value: ${end_value:,.2f}")
    print(f"Total Return: {total_return:.2f}%")
    print(f"Total P&L: ${end_value - start_value:,.2f}")

    sharpe_val = sharpe.get('sharperatio') or 0
    print(f"\nSharpe Ratio: {sharpe_val:.2f}")
    print(f"Max Drawdown: {drawdown.get('max', {}).get('drawdown', 0):.2f}%")

    print(f"\nTrade Statistics:")
    print(f"  Total Trades: {total_trades}")
    print(f"  Winning Trades: {won}")
    print(f"  Losing Trades: {lost}")
    print(f"  Win Rate: {win_rate:.1f}%")

    if won > 0:
        avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
        total_win = trades.get('won', {}).get('pnl', {}).get('total', 0)
        print(f"  Average Win: ${avg_win:.2f}")
        print(f"  Total Wins: ${total_win:.2f}")

    if lost > 0:
        avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
        total_loss = trades.get('lost', {}).get('pnl', {}).get('total', 0)
        print(f"  Average Loss: ${avg_loss:.2f}")
        print(f"  Total Losses: ${total_loss:.2f}")

    if won > 0 and lost > 0:
        avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
        avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
        pf = abs((avg_win * won) / (avg_loss * lost)) if avg_loss != 0 else 0
        print(f"  Profit Factor: {pf:.2f}")

    print(f"{'='*80}")

    print(f"\n{'='*80}")
    print("COMPARISON TO CREATOR'S CLAIMS")
    print(f"{'='*80}")
    print(f"Creator's Win Rate: 60-80%")
    print(f"Our Win Rate: {win_rate:.1f}%")

    if win_rate >= 60:
        print("\nSUCCESS: Win rate meets creator's performance!")
    elif win_rate >= 50:
        print("\nGOOD: Win rate is decent (50%+)")
    elif total_trades < 10:
        print(f"\nNOTE: Only {total_trades} trades - need more for validation")
    else:
        print("\nNOTE: Win rate below creator's claims")

    print(f"{'='*80}\n")

    if total_trades > 0:
        print(f"SUCCESS: Strategy generated {total_trades} trades")
        if total_trades >= 30:
            print("Sample size sufficient for statistical analysis")
        elif total_trades >= 10:
            print("Moderate sample size - consider more data")
        else:
            print("Small sample size - need more data for validation")
    else:
        print("WARN: No trades generated")

    return total_trades > 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
