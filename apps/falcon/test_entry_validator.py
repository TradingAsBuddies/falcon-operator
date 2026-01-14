#!/usr/bin/env python3
"""
Test script for Entry Validator

Tests entry validation against AI screener recommendations
"""
import yaml
from orchestrator.validators.entry_validator import EntryValidator


def print_separator(char='=', length=80):
    """Print a separator line"""
    print(char * length)


def test_basic_validation():
    """Test basic entry validation"""
    print_separator()
    print("ENTRY VALIDATOR - BASIC VALIDATION TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    validator = EntryValidator(config)

    # Test cases based on real screener data
    test_cases = [
        {
            'symbol': 'ACI',
            'current_price': 16.30,
            'proposed_stop': 15.50,
            'expected': True,
            'description': 'ACI - Price in range, good stop buffer'
        },
        {
            'symbol': 'ABTC',
            'current_price': 1.91,
            'proposed_stop': 1.90,
            'expected': False,
            'description': 'ABTC - Price below range, tight stop'
        },
        {
            'symbol': 'ACH',
            'current_price': 1.97,
            'proposed_stop': 1.85,
            'expected': False,
            'description': 'ACH - Price in range, but data is stale (>24hrs)'
        },
        {
            'symbol': 'INVALID',
            'current_price': 100.00,
            'proposed_stop': 95.00,
            'expected': True,
            'description': 'INVALID - No recommendation (allow by default)'
        }
    ]

    print("\nRunning validation tests...\n")

    for test in test_cases:
        print(f"Test: {test['description']}")
        print(f"  Symbol: {test['symbol']}")
        print(f"  Current Price: ${test['current_price']:.2f}")
        print(f"  Proposed Stop: ${test['proposed_stop']:.2f}")

        result = validator.validate_entry(
            test['symbol'],
            test['current_price'],
            test['proposed_stop']
        )

        print(f"  Result: {'PASS' if result.is_valid else 'FAIL'}")
        print(f"  Reason: {result.reason}")

        if result.is_valid != test['expected']:
            print(f"  [WARNING] Expected {test['expected']}, got {result.is_valid}")

        print()

    print_separator()


def test_detailed_validation():
    """Test detailed validation with all checks"""
    print_separator()
    print("DETAILED VALIDATION TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    validator = EntryValidator(config)

    # Test ABTC in detail (the problematic stock from analysis)
    symbol = 'ABTC'
    current_price = 1.91
    proposed_stop = 1.90

    print(f"\nDetailed test for {symbol}:")
    print(f"Current Price: ${current_price:.2f}")
    print(f"Proposed Stop: ${proposed_stop:.2f}")

    # Get recommendation
    recommendation = validator.get_ai_recommendation(symbol)

    if recommendation:
        print(f"\nAI Recommendation:")
        print(f"  Entry Range: {recommendation.get('entry_range', 'N/A')}")
        print(f"  Target: {recommendation.get('target', 'N/A')}")
        print(f"  Stop Loss: {recommendation.get('stop_loss', 'N/A')}")
        print(f"  Confidence: {recommendation.get('confidence', 'UNKNOWN')}")

    # Validate entry
    result = validator.validate_entry(symbol, current_price, proposed_stop)

    print(f"\nValidation Result:")
    print(f"  Is Valid: {result.is_valid}")
    print(f"  Reason: {result.reason}")

    if result.details and 'checks' in result.details:
        print(f"\n  Individual Checks:")
        for check in result.details['checks']:
            status = 'PASS' if check['passed'] else 'FAIL'
            print(f"    [{status}] {check['check']}: {check['reason']}")

    # Check if we should wait
    wait_result = validator.should_wait_for_better_entry(symbol, current_price)

    print(f"\nShould Wait for Better Entry:")
    print(f"  Wait: {wait_result['should_wait']}")
    print(f"  Reason: {wait_result['reason']}")
    if wait_result['target_range']:
        print(f"  Target Range: {wait_result['target_range']}")

    # Get recommended stop-loss
    recommended_stop = validator.get_recommended_stop_loss(symbol, current_price)

    print(f"\nRecommended Stop-Loss:")
    print(f"  AI Stop: {recommendation.get('stop_loss', 'N/A') if recommendation else 'N/A'}")
    print(f"  Proposed Stop: ${proposed_stop:.2f}")
    print(f"  Recommended Stop: ${recommended_stop:.2f}")
    print(f"  Difference: ${abs(recommended_stop - proposed_stop):.2f}")

    print("\n" + "=" * 80)


def test_price_scenarios():
    """Test various price scenarios"""
    print_separator()
    print("PRICE SCENARIO TESTS")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    validator = EntryValidator(config)

    symbol = 'ACI'

    scenarios = [
        (15.50, "Below entry range"),
        (16.00, "Low end of range"),
        (16.30, "Mid range"),
        (16.50, "High end of range"),
        (17.00, "Above entry range")
    ]

    print(f"\nTesting {symbol} at different price points:\n")

    for price, description in scenarios:
        result = validator.validate_entry(symbol, price)
        wait_result = validator.should_wait_for_better_entry(symbol, price)

        print(f"Price: ${price:.2f} ({description})")
        print(f"  Valid: {result.is_valid}")
        print(f"  Should Wait: {wait_result['should_wait']}")
        print(f"  Reason: {wait_result['reason']}")
        print()

    print("=" * 80)


def test_stop_loss_buffers():
    """Test stop-loss buffer validation"""
    print_separator()
    print("STOP-LOSS BUFFER TESTS")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    validator = EntryValidator(config)

    entry_price = 100.00

    stop_scenarios = [
        (99.50, 0.5, "Tight stop (0.5%)"),
        (97.00, 3.0, "Moderate stop (3%)"),
        (95.00, 5.0, "Minimum buffer (5%)"),
        (92.00, 8.0, "Conservative stop (8%)"),
        (90.00, 10.0, "Wide stop (10%)")
    ]

    print(f"\nTesting stop-loss buffers with entry at ${entry_price:.2f}:\n")
    print(f"Minimum Required Buffer: {validator.min_stop_buffer:.1%}\n")

    for stop, buffer_pct, description in stop_scenarios:
        result = validator.validate_entry('TEST', entry_price, stop)

        # Extract stop-loss check result
        stop_check_passed = True
        if result.details and 'checks' in result.details:
            for check in result.details['checks']:
                if check['check'] == 'stop_loss_buffer':
                    stop_check_passed = check['passed']
                    break

        status = "PASS" if stop_check_passed else "FAIL"
        print(f"[{status}] Stop: ${stop:.2f} ({buffer_pct:.1%}) - {description}")

    print("\n" + "=" * 80)


def test_with_real_screener_data():
    """Test with actual screener recommendations"""
    print_separator()
    print("REAL SCREENER DATA TEST")
    print_separator()

    # Load config
    with open('orchestrator/orchestrator_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    validator = EntryValidator(config)

    # Get some real recommendations
    print("\nChecking stocks from AI screener:\n")

    test_symbols = ['ACI', 'ACH', 'ABTC', 'AKBA', 'AMC']

    for symbol in test_symbols:
        recommendation = validator.get_ai_recommendation(symbol)

        if recommendation:
            print(f"{symbol}:")
            print(f"  Entry Range: {recommendation.get('entry_range', 'N/A')}")
            print(f"  Target: {recommendation.get('target', 'N/A')}")
            print(f"  Stop: {recommendation.get('stop_loss', 'N/A')}")
            print(f"  Confidence: {recommendation.get('confidence', 'UNKNOWN')}")
        else:
            print(f"{symbol}: No recommendation found")

        print()

    print("=" * 80)


def main():
    """Main test function"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == '--detailed':
            test_detailed_validation()
        elif command == '--prices':
            test_price_scenarios()
        elif command == '--stops':
            test_stop_loss_buffers()
        elif command == '--real':
            test_with_real_screener_data()
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python3 test_entry_validator.py                # Run all tests")
            print("  python3 test_entry_validator.py --detailed     # Detailed ABTC test")
            print("  python3 test_entry_validator.py --prices       # Price scenario tests")
            print("  python3 test_entry_validator.py --stops        # Stop-loss buffer tests")
            print("  python3 test_entry_validator.py --real         # Real screener data test")

    else:
        # Run all tests
        test_basic_validation()
        print()
        test_with_real_screener_data()

        print("\nFor more tests, run:")
        print("  python3 test_entry_validator.py --detailed")
        print("  python3 test_entry_validator.py --prices")
        print("  python3 test_entry_validator.py --stops")


if __name__ == "__main__":
    main()
