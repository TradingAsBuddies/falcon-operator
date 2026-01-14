#!/usr/bin/env python3
"""
Test script for Strategy Router

Tests routing decisions on various stock types
"""
import yaml
import sys
from orchestrator.routers.strategy_router import StrategyRouter


def print_separator(char='=', length=80):
    """Print a separator line"""
    print(char * length)


def print_decision(decision, verbose=False):
    """Pretty print a routing decision"""
    profile = decision.profile

    print(f"\n{decision.symbol}:")
    print(f"  Strategy:        {decision.selected_strategy}")
    print(f"  Classification:  {profile.classification}")
    print(f"  Confidence:      {decision.confidence:.1%}")
    print(f"  Reason:          {decision.reason}")

    if verbose:
        print(f"\n  Stock Details:")
        print(f"    Price:         ${profile.price:.2f}")
        print(f"    Volatility:    {profile.volatility:.1%}")
        print(f"    Market Cap:    ${profile.market_cap/1e9:.2f}B" if profile.market_cap > 0 else "    Market Cap:    Unknown")
        print(f"    Sector:        {profile.sector}")
        print(f"    Is ETF:        {profile.is_etf}")
        print(f"    Avg Volume:    {profile.avg_volume:,}" if profile.avg_volume > 0 else "    Avg Volume:    Unknown")

        if decision.alternatives:
            print(f"\n  Alternative Strategies:")
            for alt in decision.alternatives[:3]:  # Top 3
                print(f"    {alt['strategy']}: {alt['score']:.2f}")


def test_basic_routing(router):
    """Test basic routing with mock data"""
    print_separator()
    print("STRATEGY ROUTER - BASIC ROUTING TEST (Mock Data)")
    print_separator()

    test_symbols = [
        'SPY',    # ETF
        'QQQ',    # ETF
        'MU',     # High volatility semiconductor
        'NVDA',   # High volatility tech
        'ABTC',   # Penny stock
        'AAPL',   # Stable large cap
        'MSFT',   # Stable large cap
        'TSLA'    # Volatile large cap
    ]

    print("\nTesting with MOCK data (no API calls)...")

    for symbol in test_symbols:
        try:
            decision = router.route(symbol, use_yfinance=False)
            print_decision(decision, verbose=False)
        except Exception as e:
            print(f"\n{symbol}: ERROR - {e}")

    print("\n" + "=" * 80)
    print("BASIC TEST COMPLETE")
    print("=" * 80)


def test_detailed_routing(router, symbol):
    """Test detailed routing for a single symbol"""
    print_separator()
    print(f"DETAILED ROUTING TEST: {symbol}")
    print_separator()

    try:
        decision = router.route(symbol, use_yfinance=False)
        print_decision(decision, verbose=True)

        # Get strategy description
        strategy_desc = router.get_strategy_description(decision.selected_strategy)
        print(f"\n  Strategy Details:")
        print(f"    Name:          {strategy_desc.get('name', 'N/A')}")
        print(f"    Best For:      {strategy_desc.get('best_for', 'N/A')}")
        print(f"    Expected:      {strategy_desc.get('expected_return', 'N/A')}")
        print(f"    Win Rate:      {strategy_desc.get('win_rate', 'N/A')}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)


def test_yfinance_routing(router, symbols):
    """Test routing with real yfinance data"""
    print_separator()
    print("STRATEGY ROUTER - YFINANCE DATA TEST")
    print_separator()

    print("\nTesting with REAL yfinance data (requires internet)...")
    print("Note: This may take 10-30 seconds...")

    for symbol in symbols:
        try:
            print(f"\nFetching data for {symbol}...")
            decision = router.route(symbol, use_yfinance=True)
            print_decision(decision, verbose=True)
        except Exception as e:
            print(f"\n{symbol}: ERROR - {e}")

    print("\n" + "=" * 80)
    print("YFINANCE TEST COMPLETE")
    print("=" * 80)


def test_edge_cases(router):
    """Test edge cases and error handling"""
    print_separator()
    print("EDGE CASE TESTS")
    print_separator()

    edge_cases = [
        ('INVALID', 'Non-existent symbol'),
        ('', 'Empty symbol'),
    ]

    for symbol, description in edge_cases:
        print(f"\nTest: {description} ('{symbol}')")
        try:
            decision = router.route(symbol, use_yfinance=False)
            print(f"  Result: {decision.selected_strategy} (confidence: {decision.confidence:.1%})")
            print(f"  Reason: {decision.reason}")
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 80)


def main():
    """Main test function"""
    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create router
    router = StrategyRouter(config)

    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == '--yfinance':
            # Test with real yfinance data
            symbols = sys.argv[2:] if len(sys.argv) > 2 else ['SPY', 'AAPL', 'NVDA']
            test_yfinance_routing(router, symbols)

        elif command == '--detailed':
            # Detailed test for specific symbol
            symbol = sys.argv[2] if len(sys.argv) > 2 else 'MU'
            test_detailed_routing(router, symbol)

        elif command == '--edges':
            # Test edge cases
            test_edge_cases(router)

        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python3 test_strategy_router.py                    # Basic test (mock data)")
            print("  python3 test_strategy_router.py --detailed MU      # Detailed test for MU")
            print("  python3 test_strategy_router.py --yfinance SPY MU  # Test with real data")
            print("  python3 test_strategy_router.py --edges            # Test edge cases")

    else:
        # Default: Run basic test with mock data
        test_basic_routing(router)

        # Show usage
        print("\nFor more tests, run:")
        print("  python3 test_strategy_router.py --detailed MU")
        print("  python3 test_strategy_router.py --yfinance SPY AAPL")


if __name__ == "__main__":
    main()
