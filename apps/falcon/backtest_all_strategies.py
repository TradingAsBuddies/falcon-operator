#!/usr/bin/env python3
"""
Comprehensive Strategy Backtesting Suite
Tests multiple strategies across different tickers and timeframes
"""
import sys
import os
from pathlib import Path

# Add strategies directory to path
strategies_dir = Path(__file__).parent / "strategies"
sys.path.insert(0, str(strategies_dir))

from strategy_manager import StrategyManager


# Strategy configurations
STRATEGIES = [
    {
        'name': 'Current Active (RSI Mean Reversion)',
        'file': 'active_strategy.py',
        'description': 'AI-optimized RSI mean reversion'
    },
    {
        'name': 'Momentum Breakout',
        'file': 'strategies/momentum_breakout_strategy.py',
        'description': '20-day breakout with volume confirmation'
    },
    {
        'name': 'Moving Average Crossover',
        'file': 'strategies/moving_average_crossover_strategy.py',
        'description': '10/30 MA crossover with trend filter'
    },
    {
        'name': 'Bollinger Mean Reversion',
        'file': 'strategies/bollinger_mean_reversion_strategy.py',
        'description': 'Bollinger Band oversold/overbought'
    },
    {
        'name': 'MACD Momentum',
        'file': 'strategies/macd_momentum_strategy.py',
        'description': 'MACD crossover with trailing stop'
    },
    {
        'name': 'Hybrid Multi-Indicator',
        'file': 'strategies/hybrid_multi_indicator_strategy.py',
        'description': 'RSI + MACD + Volume combined'
    },
]

# Test configurations
TICKERS = ['SPY', 'QQQ', 'AAPL', 'MSFT']
TIMEFRAMES = [
    {'days': 365, 'label': '1 Year'},
    {'days': 730, 'label': '2 Years'},
]


def run_backtest(strategy_file: str, ticker: str, days: int) -> dict:
    """Run a single backtest"""
    manager = StrategyManager()

    # Read strategy code
    with open(strategy_file, 'r') as f:
        code = f.read()

    # Run backtest
    success, results = manager.run_backtest(code, ticker, days)

    if success:
        return results
    else:
        return {'error': results.get('error', 'Unknown error')}


def format_result(result: dict) -> str:
    """Format backtest result for display"""
    if 'error' in result:
        return f"ERROR: {result['error'][:50]}"

    # Handle None values by defaulting to 0
    return_pct = result.get('return_pct') or 0
    sharpe = result.get('sharpe_ratio') or 0
    max_dd = result.get('max_drawdown') or 0
    trades = result.get('total_trades') or 0
    win_rate = result.get('win_rate') or 0

    return (f"Return: {return_pct:>6.2f}% | "
            f"Sharpe: {sharpe:>5.2f} | "
            f"MaxDD: {max_dd:>5.2f}% | "
            f"Trades: {trades:>3} | "
            f"WinRate: {win_rate:>5.1f}%")


def rank_strategies(results: dict) -> list:
    """Rank strategies by overall performance"""
    scores = {}

    for strategy_name, strategy_results in results.items():
        total_score = 0
        count = 0

        for ticker_results in strategy_results.values():
            for timeframe_result in ticker_results.values():
                if 'error' not in timeframe_result:
                    # Scoring: weighted combination of metrics
                    return_score = timeframe_result.get('return_pct', 0) * 0.4
                    sharpe_score = timeframe_result.get('sharpe_ratio', 0) * 30 * 0.3  # Scale Sharpe
                    dd_score = -timeframe_result.get('max_drawdown', 0) * 0.2  # Negative is better
                    winrate_score = timeframe_result.get('win_rate', 0) * 0.1

                    total_score += return_score + sharpe_score + dd_score + winrate_score
                    count += 1

        if count > 0:
            scores[strategy_name] = total_score / count

    # Sort by score descending
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def main():
    """Main backtesting suite"""
    print("=" * 100)
    print("FALCON COMPREHENSIVE STRATEGY BACKTEST")
    print("=" * 100)
    print(f"Testing {len(STRATEGIES)} strategies across {len(TICKERS)} tickers and {len(TIMEFRAMES)} timeframes")
    print(f"Total backtests: {len(STRATEGIES) * len(TICKERS) * len(TIMEFRAMES)}")
    print("=" * 100)
    print()

    results = {}
    total_tests = len(STRATEGIES) * len(TICKERS) * len(TIMEFRAMES)
    current_test = 0

    # Run all backtests
    for strategy in STRATEGIES:
        strategy_name = strategy['name']
        strategy_file = strategy['file']

        print(f"\n{'=' * 100}")
        print(f"STRATEGY: {strategy_name}")
        print(f"Description: {strategy['description']}")
        print(f"{'=' * 100}\n")

        results[strategy_name] = {}

        for ticker in TICKERS:
            results[strategy_name][ticker] = {}

            for timeframe in TIMEFRAMES:
                current_test += 1
                days = timeframe['days']
                label = timeframe['label']

                print(f"[{current_test}/{total_tests}] Testing {ticker} ({label})... ", end='', flush=True)

                try:
                    result = run_backtest(strategy_file, ticker, days)
                    results[strategy_name][ticker][label] = result
                    print(format_result(result))
                except Exception as e:
                    error_result = {'error': str(e)}
                    results[strategy_name][ticker][label] = error_result
                    print(f"ERROR: {str(e)[:50]}")

    # Print summary comparison
    print("\n\n")
    print("=" * 100)
    print("SUMMARY COMPARISON")
    print("=" * 100)

    for ticker in TICKERS:
        print(f"\n{ticker} Performance:")
        print("-" * 100)
        print(f"{'Strategy':<30} {'1 Year':<50} {'2 Years':<50}")
        print("-" * 100)

        for strategy in STRATEGIES:
            strategy_name = strategy['name']
            year1 = results[strategy_name][ticker].get('1 Year', {})
            year2 = results[strategy_name][ticker].get('2 Years', {})

            print(f"{strategy_name:<30} {format_result(year1):<50} {format_result(year2):<50}")

    # Print rankings
    print("\n\n")
    print("=" * 100)
    print("OVERALL RANKINGS (Weighted Score)")
    print("=" * 100)
    rankings = rank_strategies(results)

    for rank, (strategy_name, score) in enumerate(rankings, 1):
        print(f"{rank}. {strategy_name:<40} Score: {score:>7.2f}")

    # Print best strategy recommendation
    if rankings:
        best_strategy = rankings[0][0]
        print("\n")
        print("=" * 100)
        print(f"RECOMMENDED STRATEGY: {best_strategy}")
        print("=" * 100)

        # Show best strategy's detailed results
        print("\nDetailed Performance:")
        for ticker in TICKERS:
            print(f"\n  {ticker}:")
            for timeframe in TIMEFRAMES:
                label = timeframe['label']
                result = results[best_strategy][ticker].get(label, {})
                if 'error' not in result:
                    print(f"    {label}: {format_result(result)}")

    print("\n" + "=" * 100)
    print("Backtest complete!")
    print("=" * 100)


if __name__ == '__main__':
    main()
