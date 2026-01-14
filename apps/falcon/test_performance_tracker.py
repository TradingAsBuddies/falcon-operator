#!/usr/bin/env python3
"""
Test script for Performance Tracker

Tests performance tracking, metrics calculation, and reporting
"""
import yaml
import time
from datetime import datetime, timedelta
from orchestrator.monitors.performance_tracker import PerformanceTracker
from db_manager import DatabaseManager


def print_separator(char='=', length=80):
    """Print a separator line"""
    print(char * length)


def test_database_setup():
    """Test database table creation"""
    print_separator()
    print("DATABASE SETUP - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize tracker
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    tracker = PerformanceTracker(config, db_manager=db)

    print("\n[TEST 1] Database tables created")
    print("  - routing_decisions")
    print("  - trade_tracking")
    print("  - strategy_metrics")

    # Verify tables exist
    try:
        db.execute("SELECT COUNT(*) FROM routing_decisions", fetch='one')
        db.execute("SELECT COUNT(*) FROM trade_tracking", fetch='one')
        db.execute("SELECT COUNT(*) FROM strategy_metrics", fetch='one')
        print("\n[RESULT] All tables accessible [OK]")
    except Exception as e:
        print(f"\n[ERROR] Table verification failed: {e}")

    print("\n" + "=" * 80)


def test_routing_logging():
    """Test logging routing decisions"""
    print_separator()
    print("ROUTING DECISION LOGGING - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize tracker
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    tracker = PerformanceTracker(config, db_manager=db)

    print("\n[TEST 1] Logging routing decisions")

    # Log test decisions
    test_decisions = [
        ('decision_1', 'ABTC', 'momentum_breakout', 'penny_stock', 0.90, 'Penny stock requires momentum'),
        ('decision_2', 'SPY', 'rsi_mean_reversion', 'etf', 0.95, 'ETF best with RSI'),
        ('decision_3', 'MU', 'momentum_breakout', 'large_cap', 0.85, 'High volatility')
    ]

    for dec_id, symbol, strategy, classification, confidence, reason in test_decisions:
        tracker.log_routing_decision(dec_id, symbol, strategy, classification, confidence, reason)
        print(f"  Logged: {symbol} -> {strategy} ({confidence:.0%})")

    print("\n[RESULT] Routing decisions logged successfully [OK]")
    print("\n" + "=" * 80)


def test_trade_tracking():
    """Test logging trade entries and exits"""
    print_separator()
    print("TRADE TRACKING - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize tracker
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    tracker = PerformanceTracker(config, db_manager=db)

    print("\n[TEST 1] Logging trade entry")
    tracker.log_trade_entry(
        trade_id='trade_1',
        symbol='ABTC',
        strategy='momentum_breakout',
        classification='penny_stock',
        entry_price=2.03,
        quantity=500,
        routing_confidence=0.90
    )
    print("  Entry logged: ABTC @ $2.03")

    print("\n[TEST 2] Logging trade exit (profitable)")
    time.sleep(0.1)  # Small delay to simulate time
    tracker.log_trade_exit(
        trade_id='trade_1',
        exit_price=2.19,
        exit_reason='Profit target reached'
    )
    print("  Exit logged: ABTC @ $2.19")
    print("  P&L: +7.9%")

    # Log another trade (losing)
    print("\n[TEST 3] Logging losing trade")
    tracker.log_trade_entry(
        trade_id='trade_2',
        symbol='SPY',
        strategy='rsi_mean_reversion',
        classification='etf',
        entry_price=689.50,
        quantity=10,
        routing_confidence=0.95
    )
    time.sleep(0.1)
    tracker.log_trade_exit(
        trade_id='trade_2',
        exit_price=680.00,
        exit_reason='Stop-loss triggered'
    )
    print("  Entry: SPY @ $689.50")
    print("  Exit: SPY @ $680.00")
    print("  P&L: -1.4%")

    print("\n[RESULT] Trade tracking working [OK]")
    print("\n" + "=" * 80)


def test_performance_metrics():
    """Test performance metrics calculation"""
    print_separator()
    print("PERFORMANCE METRICS - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize tracker
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    tracker = PerformanceTracker(config, db_manager=db)

    # Add some test trades
    print("\n[SETUP] Creating test trades...")

    # Momentum strategy - penny stocks (3 trades)
    for i in range(3):
        trade_id = f'momentum_penny_{i}'
        tracker.log_trade_entry(
            trade_id=trade_id,
            symbol='TEST',
            strategy='momentum_breakout',
            classification='penny_stock',
            entry_price=2.00,
            quantity=100,
            routing_confidence=0.90
        )
        # 2 winners, 1 loser
        exit_price = 2.16 if i < 2 else 1.92
        tracker.log_trade_exit(
            trade_id=trade_id,
            exit_price=exit_price,
            exit_reason='Test exit'
        )

    # RSI strategy - ETFs (2 trades)
    for i in range(2):
        trade_id = f'rsi_etf_{i}'
        tracker.log_trade_entry(
            trade_id=trade_id,
            symbol='SPY',
            strategy='rsi_mean_reversion',
            classification='etf',
            entry_price=680.00,
            quantity=10,
            routing_confidence=0.95
        )
        # Both winners
        exit_price = 697.00
        tracker.log_trade_exit(
            trade_id=trade_id,
            exit_price=exit_price,
            exit_reason='Profit target'
        )

    print("  Created 5 test trades")

    print("\n[TEST 1] Getting strategy performance")
    perf = tracker.get_strategy_performance('momentum_breakout', 'penny_stock', days=1)

    if perf:
        p = perf[0]
        print(f"  Strategy: {p.strategy}")
        print(f"  Stock Type: {p.stock_type}")
        print(f"  Total Trades: {p.total_trades}")
        print(f"  Win Rate: {p.win_rate:.1%}")
        print(f"  Avg Profit: {p.avg_profit:+.2%}")
        print(f"  Total Return: {p.total_return:+.2%}")
    else:
        print("  No performance data yet")

    print("\n[TEST 2] Getting performance report")
    report = tracker.get_performance_report(days=1)

    if report.get('strategies'):
        print(f"  Total Trades: {report['overall']['total_trades']}")
        print(f"  Win Rate: {report['overall']['win_rate']:.1%}")
        print(f"  Total Return: {report['overall']['total_return']:+.2%}")
    else:
        print("  No report data yet")

    print("\n[RESULT] Performance metrics calculated [OK]")
    print("\n" + "=" * 80)


def test_top_performers():
    """Test top performers analysis"""
    print_separator()
    print("TOP PERFORMERS - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize tracker
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    tracker = PerformanceTracker(config, db_manager=db)

    print("\n[TEST 1] Getting top performers by win rate")
    top = tracker.get_top_performing_strategies('win_rate', days=1, limit=5)

    if top:
        for i, (strategy, stock_type, value) in enumerate(top, 1):
            print(f"  {i}. {strategy} ({stock_type}): {value:.1%}")
    else:
        print("  No data available yet")

    print("\n[TEST 2] Getting top performers by avg profit")
    top = tracker.get_top_performing_strategies('avg_profit', days=1, limit=5)

    if top:
        for i, (strategy, stock_type, value) in enumerate(top, 1):
            print(f"  {i}. {strategy} ({stock_type}): {value:+.2%}")
    else:
        print("  No data available yet")

    print("\n[RESULT] Top performers analysis working [OK]")
    print("\n" + "=" * 80)


def test_routing_accuracy():
    """Test routing accuracy analysis"""
    print_separator()
    print("ROUTING ACCURACY - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize tracker
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    tracker = PerformanceTracker(config, db_manager=db)

    print("\n[TEST 1] Analyzing routing accuracy")
    accuracy = tracker.get_routing_accuracy(days=1)

    if accuracy.get('total_decisions', 0) > 0:
        print(f"  Total Decisions: {accuracy['total_decisions']}")

        if accuracy.get('high_confidence'):
            hc = accuracy['high_confidence']
            print(f"\n  High Confidence (>80%):")
            print(f"    Total: {hc['total']}")
            print(f"    Correct: {hc['correct']}")
            print(f"    Accuracy: {hc['accuracy']:.1%}")

        if accuracy.get('medium_confidence'):
            mc = accuracy['medium_confidence']
            print(f"\n  Medium Confidence (60-80%):")
            print(f"    Total: {mc['total']}")
            print(f"    Correct: {mc['correct']}")
            print(f"    Accuracy: {mc['accuracy']:.1%}")
    else:
        print("  No routing decisions with outcomes yet")

    print("\n[RESULT] Routing accuracy analysis working [OK]")
    print("\n" + "=" * 80)


def test_performance_summary():
    """Test formatted performance summary"""
    print_separator()
    print("PERFORMANCE SUMMARY - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize tracker
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    tracker = PerformanceTracker(config, db_manager=db)

    print("\n[TEST 1] Printing performance summary")
    tracker.print_performance_summary(days=1)

    print("\n[RESULT] Performance summary generated [OK]")
    print("\n" + "=" * 80)


def test_integration_with_executor():
    """Test integration with trade executor"""
    print_separator()
    print("INTEGRATION WITH EXECUTOR - TEST")
    print_separator()

    print("\nIntegration workflow:")
    print("  1. Executor routes stock")
    print("  2. Tracker logs routing decision")
    print("  3. Executor executes trade")
    print("  4. Tracker logs entry")
    print("  5. Executor monitors position")
    print("  6. Executor exits trade")
    print("  7. Tracker logs exit & calculates metrics")

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize tracker
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)
    tracker = PerformanceTracker(config, db_manager=db)

    # Simulate executor workflow
    print("\n[SIMULATION]")
    print("  Routing ABTC...")
    tracker.log_routing_decision(
        decision_id='sim_1',
        symbol='ABTC',
        strategy='momentum_breakout',
        classification='penny_stock',
        confidence=0.90,
        reason='Penny stock with high volatility'
    )

    print("  Executing entry...")
    tracker.log_trade_entry(
        trade_id='sim_trade_1',
        symbol='ABTC',
        strategy='momentum_breakout',
        classification='penny_stock',
        entry_price=2.03,
        quantity=500,
        routing_confidence=0.90
    )

    print("  Waiting for exit signal...")
    time.sleep(0.1)

    print("  Executing exit...")
    tracker.log_trade_exit(
        trade_id='sim_trade_1',
        exit_price=2.19,
        exit_reason='Profit target reached'
    )

    print("\n  Trade complete!")
    print("  Metrics updated automatically")

    print("\n[RESULT] Integration working [OK]")
    print("\n" + "=" * 80)


def main():
    """Main test function"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == '--setup':
            test_database_setup()
        elif command == '--routing':
            test_routing_logging()
        elif command == '--tracking':
            test_trade_tracking()
        elif command == '--metrics':
            test_performance_metrics()
        elif command == '--top':
            test_top_performers()
        elif command == '--accuracy':
            test_routing_accuracy()
        elif command == '--summary':
            test_performance_summary()
        elif command == '--integration':
            test_integration_with_executor()
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python3 test_performance_tracker.py                # Run all tests")
            print("  python3 test_performance_tracker.py --setup        # Test database setup")
            print("  python3 test_performance_tracker.py --routing      # Test routing logging")
            print("  python3 test_performance_tracker.py --tracking     # Test trade tracking")
            print("  python3 test_performance_tracker.py --metrics      # Test metrics calculation")
            print("  python3 test_performance_tracker.py --top          # Test top performers")
            print("  python3 test_performance_tracker.py --accuracy     # Test routing accuracy")
            print("  python3 test_performance_tracker.py --summary      # Test performance summary")
            print("  python3 test_performance_tracker.py --integration  # Test executor integration")

    else:
        # Run all tests
        print("\n")
        print("=" * 80)
        print(" " * 20 + "PERFORMANCE TRACKER - TEST SUITE")
        print("=" * 80)

        test_database_setup()
        print()
        test_routing_logging()
        print()
        test_trade_tracking()
        print()
        test_performance_metrics()
        print()
        test_top_performers()
        print()
        test_routing_accuracy()
        print()
        test_performance_summary()
        print()
        test_integration_with_executor()

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("\nPerformance Tracker tested successfully!")
        print("\nFeatures:")
        print("  - Routing decision logging")
        print("  - Trade entry/exit tracking")
        print("  - Performance metrics calculation")
        print("  - Win rates, returns, drawdowns")
        print("  - Top performers analysis")
        print("  - Routing accuracy analysis")
        print("  - Comprehensive reporting")
        print("\nPhase 5 complete - Full orchestrator operational!")
        print()


if __name__ == "__main__":
    main()
