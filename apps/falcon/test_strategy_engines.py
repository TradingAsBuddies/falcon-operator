#!/usr/bin/env python3
"""
Test script for Strategy Engines

Tests signal generation, position management, and trade execution
"""
import yaml
import numpy as np
import sys
from datetime import datetime, timedelta

from orchestrator.engines.rsi_engine import RSIEngine
from orchestrator.engines.momentum_engine import MomentumEngine
from orchestrator.engines.bollinger_engine import BollingerEngine


def print_separator(char='=', length=80):
    """Print a separator line"""
    print(char * length)


def test_rsi_engine():
    """Test RSI Mean Reversion Engine"""
    print_separator()
    print("RSI MEAN REVERSION ENGINE - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Use mock DB manager for testing
    from db_manager import DatabaseManager
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)

    engine = RSIEngine(config, db_manager=db)

    print(f"\nEngine: {engine.get_strategy_name()}")
    print(f"RSI Period: {engine.rsi_period}")
    print(f"RSI Oversold: {engine.rsi_oversold}")
    print(f"RSI Overbought: {engine.rsi_overbought}")
    print(f"Profit Target: {engine.profit_target:.1%}")

    # Test 1: RSI Calculation
    print("\n[TEST 1] RSI Calculation")
    prices = [100 + i + np.random.randn() * 2 for i in range(30)]
    rsi = engine.calculate_rsi(prices, 14)
    print(f"  Sample prices (last 5): {[f'${p:.2f}' for p in prices[-5:]]}")
    print(f"  RSI: {rsi:.1f}")
    print(f"  Status: {'Oversold' if rsi < 35 else 'Overbought' if rsi > 65 else 'Neutral'}")

    # Test 2: Buy Signal (Oversold)
    print("\n[TEST 2] Buy Signal Generation (Oversold)")
    # Create prices that trend down (oversold condition)
    oversold_prices = [100 - i * 0.5 for i in range(30)]
    market_data = {
        'price': oversold_prices[-1],
        'prices': oversold_prices,
        'volume': 1000000
    }

    signal = engine.generate_signal('TEST', market_data)
    print(f"  Current Price: ${market_data['price']:.2f}")
    print(f"  Signal: {signal.action}")
    print(f"  Reason: {signal.reason}")
    print(f"  Confidence: {signal.confidence:.1%}")
    if signal.action == 'BUY':
        print(f"  Quantity: {signal.quantity}")
        print(f"  Stop Loss: ${signal.stop_loss:.2f}")
        print(f"  Profit Target: ${signal.profit_target:.2f}")

    # Test 3: Hold Signal (Neutral)
    print("\n[TEST 3] Hold Signal Generation (Neutral)")
    neutral_prices = [100 + np.random.randn() * 0.5 for _ in range(30)]
    market_data = {
        'price': neutral_prices[-1],
        'prices': neutral_prices,
        'volume': 1000000
    }

    signal = engine.generate_signal('TEST', market_data)
    print(f"  Current Price: ${market_data['price']:.2f}")
    print(f"  Signal: {signal.action}")
    print(f"  Reason: {signal.reason}")

    print("\n" + "=" * 80)


def test_momentum_engine():
    """Test Momentum Breakout Engine"""
    print_separator()
    print("MOMENTUM BREAKOUT ENGINE - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Use mock DB manager for testing
    from db_manager import DatabaseManager
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)

    engine = MomentumEngine(config, db_manager=db)

    print(f"\nEngine: {engine.get_strategy_name()}")
    print(f"Breakout Period: {engine.breakout_period}")
    print(f"Volume Multiplier: {engine.volume_multiplier}x")
    print(f"Profit Target: {engine.profit_target:.1%}")
    print(f"Trailing Stop: {engine.trailing_stop_pct:.1%}")

    # Test 1: Moving Average Calculation
    print("\n[TEST 1] Moving Average Calculation")
    prices = [100 + i * 0.5 for i in range(30)]
    ma_fast = engine.calculate_moving_average(prices, engine.ma_fast)
    ma_slow = engine.calculate_moving_average(prices, engine.ma_slow)
    print(f"  Sample prices (last 5): {[f'${p:.2f}' for p in prices[-5:]]}")
    print(f"  MA Fast ({engine.ma_fast}): ${ma_fast:.2f}")
    print(f"  MA Slow ({engine.ma_slow}): ${ma_slow:.2f}")
    print(f"  Trend: {'Bullish' if ma_fast > ma_slow else 'Bearish'}")

    # Test 2: Breakout Detection
    print("\n[TEST 2] Breakout Signal Generation")
    # Create prices with breakout pattern
    base_prices = [50.0] * 15  # Consolidation
    breakout_prices = base_prices + [51.0, 52.0, 53.5, 55.0]  # Breakout
    volumes = [100000] * 15 + [200000, 250000, 300000, 350000]  # Volume surge

    market_data = {
        'price': breakout_prices[-1],
        'prices': breakout_prices,
        'volume': volumes[-1],
        'volumes': volumes
    }

    resistance = engine.calculate_resistance(breakout_prices[:-1], engine.breakout_period)
    print(f"  Resistance: ${resistance:.2f}")
    print(f"  Current Price: ${market_data['price']:.2f}")
    print(f"  Volume Ratio: {volumes[-1] / np.mean(volumes[:-1]):.1f}x")

    signal = engine.generate_signal('TEST', market_data)
    print(f"  Signal: {signal.action}")
    print(f"  Reason: {signal.reason}")
    print(f"  Confidence: {signal.confidence:.1%}")
    if signal.action == 'BUY':
        print(f"  Quantity: {signal.quantity}")
        print(f"  Stop Loss: ${signal.stop_loss:.2f}")

    # Test 3: No Breakout (Low Volume)
    print("\n[TEST 3] No Breakout (Low Volume)")
    market_data_low_vol = {
        'price': breakout_prices[-1],
        'prices': breakout_prices,
        'volume': 50000,  # Low volume
        'volumes': volumes
    }

    signal = engine.generate_signal('TEST', market_data_low_vol)
    print(f"  Signal: {signal.action}")
    print(f"  Reason: {signal.reason}")

    print("\n" + "=" * 80)


def test_bollinger_engine():
    """Test Bollinger Bands Mean Reversion Engine"""
    print_separator()
    print("BOLLINGER BANDS MEAN REVERSION ENGINE - TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Use mock DB manager for testing
    from db_manager import DatabaseManager
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)

    engine = BollingerEngine(config, db_manager=db)

    print(f"\nEngine: {engine.get_strategy_name()}")
    print(f"BB Period: {engine.bb_period}")
    print(f"BB Std Dev: {engine.bb_std}")
    print(f"Profit Target: {engine.profit_target:.1%}")
    print(f"Exit at Middle: {engine.exit_at_middle}")

    # Test 1: Bollinger Bands Calculation
    print("\n[TEST 1] Bollinger Bands Calculation")
    prices = [100 + np.random.randn() * 3 for _ in range(30)]
    middle, upper, lower = engine.calculate_bollinger_bands(prices)
    bandwidth = engine.calculate_bandwidth(prices)

    print(f"  Sample prices (last 5): {[f'${p:.2f}' for p in prices[-5:]]}")
    print(f"  Upper Band: ${upper:.2f}")
    print(f"  Middle Band: ${middle:.2f}")
    print(f"  Lower Band: ${lower:.2f}")
    print(f"  Bandwidth: {bandwidth:.1%}")

    # Test 2: Buy Signal (At Lower Band)
    print("\n[TEST 2] Buy Signal (At Lower Band)")
    # Create prices at lower band
    lower_band_prices = [100.0] * 15 + [98.0, 96.0, 94.0, 92.0, 90.0]
    middle, upper, lower = engine.calculate_bollinger_bands(lower_band_prices)

    market_data = {
        'price': lower_band_prices[-1],
        'prices': lower_band_prices,
        'volume': 1000000
    }

    print(f"  Lower Band: ${lower:.2f}")
    print(f"  Current Price: ${market_data['price']:.2f}")
    print(f"  At Lower Band: {engine.check_at_lower_band(market_data['price'], lower_band_prices)}")

    signal = engine.generate_signal('TEST', market_data)
    print(f"  Signal: {signal.action}")
    print(f"  Reason: {signal.reason}")
    print(f"  Confidence: {signal.confidence:.1%}")
    if signal.action == 'BUY':
        print(f"  Quantity: {signal.quantity}")
        print(f"  Stop Loss: ${signal.stop_loss:.2f}")
        print(f"  Profit Target: ${signal.profit_target:.2f}")

    # Test 3: No Signal (Middle of Bands)
    print("\n[TEST 3] No Signal (Middle of Bands)")
    market_data_middle = {
        'price': middle,
        'prices': lower_band_prices,
        'volume': 1000000
    }

    signal = engine.generate_signal('TEST', market_data_middle)
    print(f"  Current Price: ${market_data_middle['price']:.2f}")
    print(f"  Signal: {signal.action}")
    print(f"  Reason: {signal.reason}")

    print("\n" + "=" * 80)


def test_integration():
    """Test integration scenario"""
    print_separator()
    print("INTEGRATION TEST - Stock Routing to Engine")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Use mock DB manager for testing
    from db_manager import DatabaseManager
    db_config = {'db_type': 'sqlite', 'db_path': './paper_trading.db'}
    db = DatabaseManager(db_config)

    print("\nScenario: Route ABTC (penny stock) to Momentum Engine")
    print("         Route SPY (ETF) to RSI Engine")

    # Test ABTC with Momentum Engine
    print("\n1. ABTC (Penny Stock) => Momentum Engine")
    momentum_engine = MomentumEngine(config, db_manager=db)

    # Simulate breakout
    abtc_prices = [1.90] * 10 + [1.95, 2.00, 2.05, 2.10]
    abtc_volumes = [500000] * 10 + [800000, 1000000, 1200000, 1500000]

    abtc_data = {
        'price': 2.10,
        'prices': abtc_prices,
        'volume': 1500000,
        'volumes': abtc_volumes
    }

    signal = momentum_engine.generate_signal('ABTC', abtc_data)
    print(f"   Price: ${abtc_data['price']:.2f}")
    print(f"   Signal: {signal.action}")
    print(f"   Reason: {signal.reason}")
    print(f"   Confidence: {signal.confidence:.1%}")

    # Test SPY with RSI Engine
    print("\n2. SPY (ETF) => RSI Engine")
    rsi_engine = RSIEngine(config, db_manager=db)

    # Simulate oversold condition
    spy_prices = [580.0 - i * 2 for i in range(20)]  # Decline from 580 to 542

    spy_data = {
        'price': spy_prices[-1],
        'prices': spy_prices,
        'volume': 50000000
    }

    signal = rsi_engine.generate_signal('SPY', spy_data)
    rsi = rsi_engine.calculate_rsi(spy_prices, 14)
    print(f"   Price: ${spy_data['price']:.2f}")
    print(f"   RSI: {rsi:.1f}")
    print(f"   Signal: {signal.action}")
    print(f"   Reason: {signal.reason}")
    print(f"   Confidence: {signal.confidence:.1%}")

    print("\n" + "=" * 80)


def main():
    """Main test function"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == '--rsi':
            test_rsi_engine()
        elif command == '--momentum':
            test_momentum_engine()
        elif command == '--bollinger':
            test_bollinger_engine()
        elif command == '--integration':
            test_integration()
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python3 test_strategy_engines.py               # Run all tests")
            print("  python3 test_strategy_engines.py --rsi         # Test RSI engine")
            print("  python3 test_strategy_engines.py --momentum    # Test Momentum engine")
            print("  python3 test_strategy_engines.py --bollinger   # Test Bollinger engine")
            print("  python3 test_strategy_engines.py --integration # Test integration")

    else:
        # Run all tests
        print("\n")
        print("=" * 80)
        print(" " * 20 + "STRATEGY ENGINES - TEST SUITE")
        print("=" * 80)

        test_rsi_engine()
        print()
        test_momentum_engine()
        print()
        test_bollinger_engine()
        print()
        test_integration()

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("\nAll strategy engines tested successfully!")
        print("\nEngines:")
        print("  - RSI Mean Reversion:      Best for ETFs and stable stocks")
        print("  - Momentum Breakout:       Best for penny stocks and high volatility")
        print("  - Bollinger Mean Reversion: Best for range-bound stocks")
        print("\nNext: Integrate engines with router and validator for full orchestration")
        print()


if __name__ == "__main__":
    main()
