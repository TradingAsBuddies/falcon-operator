#!/usr/bin/env python3
"""
Simple example of using the Strategy Router

This shows how to integrate the router into your trading workflow
"""
import yaml
from orchestrator.routers.strategy_router import StrategyRouter


def simple_example():
    """Simplest possible usage"""
    print("=" * 60)
    print("SIMPLE EXAMPLE - Route a single stock")
    print("=" * 60)

    # 1. Load configuration
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 2. Create router
    router = StrategyRouter(config)

    # 3. Route a stock
    decision = router.route('ABTC')

    # 4. Use the decision
    print(f"\nSymbol: {decision.symbol}")
    print(f"Strategy: {decision.selected_strategy}")
    print(f"Confidence: {decision.confidence:.1%}")
    print(f"Reason: {decision.reason}")

    if decision.confidence > 0.75:
        print(f"\n[OK] High confidence - ready to trade with {decision.selected_strategy}")
    else:
        print(f"\n[WARNING] Low confidence - manual review recommended")


def batch_routing_example():
    """Route multiple stocks from AI screener"""
    print("\n" + "=" * 60)
    print("BATCH EXAMPLE - Route AI screener stocks")
    print("=" * 60)

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    router = StrategyRouter(config)

    # Simulate AI screener output
    ai_screener_stocks = [
        'ABTC',  # Penny stock
        'SPY',   # ETF
        'MU',    # High volatility
        'AAPL'   # Stable large cap
    ]

    print("\nRouting AI screener recommendations...")

    for symbol in ai_screener_stocks:
        decision = router.route(symbol)
        print(f"\n{symbol}:")
        print(f"  => {decision.selected_strategy} ({decision.confidence:.0%})")
        print(f"  Reason: {decision.reason}")


def integration_example():
    """Show how to integrate with existing trading system"""
    print("\n" + "=" * 60)
    print("INTEGRATION EXAMPLE - Full trading workflow")
    print("=" * 60)

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    router = StrategyRouter(config)

    # Stock from AI screener
    symbol = 'MU'
    ai_entry_range = '$95.00-$100.00'
    current_price = 95.50

    print(f"\nAI Screener Recommendation:")
    print(f"  Symbol: {symbol}")
    print(f"  Entry Range: {ai_entry_range}")
    print(f"  Current Price: ${current_price:.2f}")

    # Route to strategy
    decision = router.route(symbol)

    print(f"\nRouting Decision:")
    print(f"  Selected Strategy: {decision.selected_strategy}")
    print(f"  Confidence: {decision.confidence:.1%}")
    print(f"  Classification: {decision.profile.classification}")
    print(f"  Volatility: {decision.profile.volatility:.1%}")

    # Get strategy details
    strategy_info = router.get_strategy_description(decision.selected_strategy)

    print(f"\nStrategy Details:")
    print(f"  Name: {strategy_info['name']}")
    print(f"  Best For: {strategy_info['best_for']}")
    print(f"  Expected Return: {strategy_info['expected_return']}")
    print(f"  Win Rate: {strategy_info['win_rate']}")

    # Simulate trade execution decision
    print(f"\nTrade Decision:")
    if decision.confidence > 0.80:
        print(f"  [EXECUTE] Trade using {decision.selected_strategy}")
        print(f"  Entry: ${current_price:.2f}")
        print(f"  Strategy file: strategies/{decision.selected_strategy}_strategy.py")
    else:
        print(f"  [SKIP] Trade - confidence too low ({decision.confidence:.1%})")


def comparison_example():
    """Compare routing decisions for different stock types"""
    print("\n" + "=" * 60)
    print("COMPARISON - How different stocks get routed")
    print("=" * 60)

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    router = StrategyRouter(config)

    # Different stock types
    stocks = {
        'SPY': 'ETF (S&P 500)',
        'ABTC': 'Penny Stock',
        'MU': 'Volatile Semiconductor',
        'AAPL': 'Stable Large Cap',
        'TSLA': 'Volatile Large Cap'
    }

    print("\n{:<8} {:<25} {:<25} {:>10}".format(
        "Symbol", "Type", "Strategy", "Confidence"
    ))
    print("-" * 70)

    for symbol, description in stocks.items():
        decision = router.route(symbol)
        print("{:<8} {:<25} {:<25} {:>9.0%}".format(
            symbol,
            description,
            decision.selected_strategy,
            decision.confidence
        ))


def main():
    """Run all examples"""
    print("\n")
    print("=" * 60)
    print(" " * 10 + "STRATEGY ROUTER - USAGE EXAMPLES")
    print("=" * 60)

    # Run examples
    simple_example()
    batch_routing_example()
    integration_example()
    comparison_example()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\nThe Strategy Router intelligently routes stocks to optimal")
    print("strategies based on their characteristics:")
    print("")
    print("  - Penny stocks (<$5)      -> Momentum Breakout")
    print("  - ETFs                    -> RSI Mean Reversion")
    print("  - High volatility (>30%)  -> Momentum Breakout")
    print("  - Stable large caps       -> RSI Mean Reversion")
    print("")
    print("This eliminates the ABTC breakeven problem by ensuring each")
    print("stock uses the strategy that works best for its profile.")
    print("")
    print("Next steps:")
    print("  1. Integrate with AI screener (screened_stocks.json)")
    print("  2. Add entry validation (Phase 2)")
    print("  3. Implement strategy engines (Phase 3)")
    print("")


if __name__ == "__main__":
    main()
