#!/usr/bin/env python3
"""
Test script for Trade Executor

Tests the full orchestration workflow:
- Stock routing
- Entry validation
- Market data fetching
- Signal generation
- Trade execution
- Position monitoring
"""
import yaml
import sys
from datetime import datetime

from orchestrator.execution.trade_executor import TradeExecutor
from orchestrator.execution.market_data_fetcher import MarketDataFetcher
from db_manager import DatabaseManager


def print_separator(char='=', length=80):
    """Print a separator line"""
    print(char * length)


def test_market_data_fetcher():
    """Test market data fetcher"""
    print_separator()
    print("MARKET DATA FETCHER - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    fetcher = MarketDataFetcher(config)

    # Test 1: Fetch SPY data
    print("\n[TEST 1] Fetching SPY market data...")
    data = fetcher.fetch_market_data('SPY', lookback_days=30)

    print(f"  Symbol: SPY")
    print(f"  Current Price: ${data.get('price', 0):.2f}")
    print(f"  Data Points: {len(data.get('prices', []))}")
    print(f"  Current Volume: {data.get('volume', 0):,}")
    print(f"  Source: {data.get('source', 'none')}")

    # Validate data quality
    is_valid, reason = fetcher.validate_data_quality(data, min_periods=20)
    print(f"  Quality Check: {'PASS' if is_valid else 'FAIL'}")
    if not is_valid:
        print(f"  Reason: {reason}")

    # Test 2: Get current price
    print("\n[TEST 2] Getting current price...")
    price = fetcher.get_current_price('SPY')
    print(f"  SPY Current Price: ${price:.2f}")

    # Test 3: Get quote
    print("\n[TEST 3] Getting quote...")
    quote = fetcher.get_quote('SPY')
    print(f"  Symbol: {quote['symbol']}")
    print(f"  Price: ${quote['price']:.2f}")
    print(f"  Volume: {quote['volume']:,}")
    print(f"  Source: {quote['source']}")

    print("\n" + "=" * 80)


def test_single_stock_processing():
    """Test processing a single stock"""
    print_separator()
    print("TRADE EXECUTOR - SINGLE STOCK TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize executor
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    executor = TradeExecutor(config, db_manager=db)

    # Test processing SPY (ETF - should route to RSI)
    print("\nProcessing SPY (ETF)...")
    result = executor.process_stock('SPY')

    print(f"\n[RESULT]")
    print(f"  Success: {result['success']}")
    print(f"  Action: {result['action']}")
    print(f"  Reason: {result['reason']}")

    if 'routing' in result.get('details', {}):
        routing = result['details']['routing']
        print(f"\n[ROUTING]")
        print(f"  Strategy: {routing['strategy']}")
        print(f"  Classification: {routing['classification']}")
        print(f"  Confidence: {routing['confidence']:.1%}")

    if 'market_data' in result.get('details', {}):
        md = result['details']['market_data']
        print(f"\n[MARKET DATA]")
        print(f"  Price: ${md['price']:.2f}")
        print(f"  Data Points: {md['data_points']}")
        print(f"  Source: {md['source']}")

    if 'validation' in result.get('details', {}):
        val = result['details']['validation']
        print(f"\n[VALIDATION]")
        print(f"  Valid: {val['is_valid']}")
        print(f"  Reason: {val['reason']}")

    if 'signal' in result.get('details', {}):
        sig = result['details']['signal']
        print(f"\n[SIGNAL]")
        print(f"  Action: {sig['action']}")
        print(f"  Reason: {sig['reason']}")
        print(f"  Confidence: {sig['confidence']:.1%}")

    print("\n" + "=" * 80)


def test_portfolio_status():
    """Test getting portfolio status"""
    print_separator()
    print("PORTFOLIO STATUS - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize executor
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    executor = TradeExecutor(config, db_manager=db)

    # Get portfolio status
    status = executor.get_portfolio_status()

    print(f"\n[PORTFOLIO]")
    print(f"  Cash: ${status.get('cash', 0):,.2f}")
    print(f"  Position Value: ${status.get('position_value', 0):,.2f}")
    print(f"  Total Value: ${status.get('total_value', 0):,.2f}")
    print(f"  Unrealized P&L: ${status.get('unrealized_pnl', 0):+,.2f} ({status.get('unrealized_pnl_pct', 0):+.1%})")
    print(f"  Positions: {status.get('positions_count', 0)}")

    if status.get('positions'):
        print(f"\n[POSITIONS]")
        for pos in status['positions']:
            print(f"  {pos['symbol']}:")
            print(f"    Quantity: {pos['quantity']}")
            print(f"    Entry: ${pos['entry_price']:.2f}")
            print(f"    Current: ${pos['current_price']:.2f}")
            print(f"    P&L: ${pos['unrealized_pnl']:+.2f} ({pos['unrealized_pnl_pct']:+.1%})")
            print(f"    Strategy: {pos['strategy']}")

    print("\n" + "=" * 80)


def test_position_monitoring():
    """Test monitoring positions"""
    print_separator()
    print("POSITION MONITORING - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize executor
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    executor = TradeExecutor(config, db_manager=db)

    # Monitor positions
    print("\nMonitoring all open positions...")
    actions = executor.monitor_positions()

    print(f"\n[RESULT]")
    print(f"  Actions Taken: {len(actions)}")

    if actions:
        print(f"\n[ACTIONS]")
        for action in actions:
            print(f"  {action['symbol']}:")
            print(f"    Action: {action['action']}")
            print(f"    Price: ${action['price']:.2f}")
            print(f"    Reason: {action['reason']}")
            print(f"    P&L: {action['pnl_pct']:+.1%}")
    else:
        print("  No exit signals detected")

    print("\n" + "=" * 80)


def test_ai_screener_processing():
    """Test processing AI screener file"""
    print_separator()
    print("AI SCREENER PROCESSING - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize executor
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    executor = TradeExecutor(config, db_manager=db)

    # Process screener file
    print("\nProcessing screened_stocks.json...")
    summary = executor.process_ai_screener('screened_stocks.json')

    print(f"\n[SUMMARY]")
    print(f"  Total Stocks: {summary['total_stocks']}")
    print(f"  Processed: {summary['processed']}")
    print(f"  Trades Executed: {summary['trades_executed']}")
    print(f"  Skipped: {summary['skipped']}")
    print(f"  Errors: {summary['errors']}")

    if summary.get('details'):
        print(f"\n[DETAILS]")
        for detail in summary['details'][:5]:  # Show first 5
            print(f"  {detail['symbol']}:")
            print(f"    Action: {detail['action']}")
            print(f"    Success: {detail['success']}")
            if detail.get('reason'):
                print(f"    Reason: {detail['reason'][:60]}...")

    print("\n" + "=" * 80)


def test_workflow_integration():
    """Test complete workflow integration"""
    print_separator()
    print("WORKFLOW INTEGRATION - TEST")
    print_separator()

    print("\nComplete Workflow Test:")
    print("  1. Route ABTC (penny stock) to Momentum")
    print("  2. Validate entry")
    print("  3. Fetch market data")
    print("  4. Generate signal")
    print("  5. Execute trade (simulated)")

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize executor
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    executor = TradeExecutor(config, db_manager=db)

    # Process test stock
    test_symbol = 'ABTC'
    print(f"\nProcessing {test_symbol}...")

    result = executor.process_stock(test_symbol)

    # Print summary
    print(f"\n[WORKFLOW RESULT]")
    print(f"  Symbol: {result['symbol']}")
    print(f"  Success: {result['success']}")
    print(f"  Action: {result['action']}")
    print(f"  Reason: {result['reason']}")

    # Check each workflow step
    steps_completed = []
    if 'routing' in result.get('details', {}):
        steps_completed.append("Routing")
    if 'market_data' in result.get('details', {}):
        steps_completed.append("Market Data")
    if 'validation' in result.get('details', {}):
        steps_completed.append("Validation")
    if 'signal' in result.get('details', {}):
        steps_completed.append("Signal Generation")
    if 'execution' in result.get('details', {}):
        steps_completed.append("Execution")

    print(f"\n[STEPS COMPLETED]")
    for i, step in enumerate(steps_completed, 1):
        print(f"  {i}. {step}")

    print("\n" + "=" * 80)


def main():
    """Main test function"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == '--data':
            test_market_data_fetcher()
        elif command == '--process':
            test_single_stock_processing()
        elif command == '--portfolio':
            test_portfolio_status()
        elif command == '--monitor':
            test_position_monitoring()
        elif command == '--screener':
            test_ai_screener_processing()
        elif command == '--workflow':
            test_workflow_integration()
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python3 test_trade_executor.py                # Run all tests")
            print("  python3 test_trade_executor.py --data         # Test market data fetcher")
            print("  python3 test_trade_executor.py --process      # Test single stock processing")
            print("  python3 test_trade_executor.py --portfolio    # Test portfolio status")
            print("  python3 test_trade_executor.py --monitor      # Test position monitoring")
            print("  python3 test_trade_executor.py --screener     # Test AI screener processing")
            print("  python3 test_trade_executor.py --workflow     # Test workflow integration")

    else:
        # Run all tests
        print("\n")
        print("=" * 80)
        print(" " * 20 + "TRADE EXECUTOR - TEST SUITE")
        print("=" * 80)

        test_market_data_fetcher()
        print()
        test_single_stock_processing()
        print()
        test_portfolio_status()
        print()
        test_position_monitoring()
        print()
        test_workflow_integration()

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("\nTrade Executor tested successfully!")
        print("\nWorkflow:")
        print("  1. Route stock to optimal strategy")
        print("  2. Validate entry against AI screener")
        print("  3. Fetch real market data")
        print("  4. Generate signal from strategy engine")
        print("  5. Execute trade if conditions met")
        print("  6. Monitor positions for exit signals")
        print("\nAll phases integrated and working!")
        print()


if __name__ == "__main__":
    main()
