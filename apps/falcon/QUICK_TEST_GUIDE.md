# Quick Test Guide - Falcon Trading System

## Running Tests

### Run All P&L Tests
```bash
pytest tests/unit/test_pnl_calculations.py -v
```

### Run Specific Test Class
```bash
# Position P&L tests only
pytest tests/unit/test_pnl_calculations.py::TestPositionPnL -v

# FIFO tests only
pytest tests/unit/test_pnl_calculations.py::TestFIFORealizedPnL -v

# Win rate tests only
pytest tests/unit/test_pnl_calculations.py::TestWinRateCalculations -v
```

### Run Single Test
```bash
pytest tests/unit/test_pnl_calculations.py::TestPositionPnL::test_profitable_position -v
```

### Run All Unit Tests
```bash
pytest tests/unit/ -v
```

### Run All Tests (Including Import Tests)
```bash
pytest tests/ -v
```

## Test Output Options

### Verbose Output
```bash
pytest tests/unit/test_pnl_calculations.py -v
```

### Show Print Statements
```bash
pytest tests/unit/test_pnl_calculations.py -v -s
```

### Stop on First Failure
```bash
pytest tests/unit/test_pnl_calculations.py -v -x
```

### Run Last Failed Tests Only
```bash
pytest tests/unit/test_pnl_calculations.py -v --lf
```

## Code Coverage

### Generate HTML Coverage Report
```bash
pytest tests/unit/test_pnl_calculations.py --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

### Show Coverage in Terminal
```bash
pytest tests/unit/test_pnl_calculations.py --cov=. --cov-report=term-missing
```

### Coverage for Specific Module
```bash
pytest tests/unit/test_pnl_calculations.py --cov=check_pnl --cov=dashboard_server
```

## Continuous Testing

### Watch Mode (requires pytest-watch)
```bash
# Install first: pip install pytest-watch
ptw tests/unit/test_pnl_calculations.py
```

### Run Tests on File Save
```bash
# Using entr (Linux/Mac)
ls tests/unit/*.py | entr pytest tests/unit/test_pnl_calculations.py -v
```

## Test Status Summary

### Current Test Files:
- ✓ `tests/test_imports.py` - Dependency tests (6 tests, 5 passing)
- ✓ `tests/unit/test_pnl_calculations.py` - P&L calculations (30 tests, all passing)

### Total: 36 tests, 35 passing (97% pass rate)

## Quick Examples

### Example 1: Verify Position P&L
```python
# Test that a $30 gain on 100 shares = $3,000 profit (20%)
pytest tests/unit/test_pnl_calculations.py::TestPositionPnL::test_profitable_position -v
```

### Example 2: Verify FIFO Logic
```python
# Test that FIFO correctly matches oldest buys first
pytest tests/unit/test_pnl_calculations.py::TestFIFORealizedPnL::test_fifo_multiple_buys_single_sell -v
```

### Example 3: Verify Win Rate
```python
# Test 50% win rate calculation
pytest tests/unit/test_pnl_calculations.py::TestWinRateCalculations::test_fifty_percent_win_rate -v
```

## Adding to CI/CD

### GitHub Actions
Add to `.github/workflows/tests.yml`:
```yaml
- name: Run P&L Tests
  run: |
    pytest tests/unit/test_pnl_calculations.py -v --cov=. --cov-report=xml
```

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
pytest tests/unit/test_pnl_calculations.py -v
if [ $? -ne 0 ]; then
    echo "P&L tests failed. Commit aborted."
    exit 1
fi
```

## Troubleshooting

### Test Discovery Issues
```bash
# Verify pytest can find tests
pytest --collect-only tests/unit/test_pnl_calculations.py
```

### Import Errors
```bash
# Run from project root
cd /home/ospartners/src/falcon
pytest tests/unit/test_pnl_calculations.py -v
```

### Missing Dependencies
```bash
pip install pytest pytest-cov
```

## Expected Output

```
============================== test session starts ===============================
platform linux -- Python 3.11.2, pytest-7.2.1, pluggy-1.0.0+repack -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/ospartners/src/falcon
plugins: anyio-4.12.0
collected 30 items

tests/unit/test_pnl_calculations.py::TestPositionPnL::test_profitable_position PASSED [  3%]
tests/unit/test_pnl_calculations.py::TestPositionPnL::test_losing_position PASSED [  6%]
...
tests/unit/test_pnl_calculations.py::TestEdgeCases::test_negative_quantity_handled PASSED [100%]

============================== 30 passed in 0.07s =================================
```

## Test Files Summary

| File | Tests | Status | Coverage |
|------|-------|--------|----------|
| `test_pnl_calculations.py` | 30 | ✓ All Pass | P&L calculations |
| `test_imports.py` | 6 | 5 Pass, 1 Fail | Dependencies |

**Total**: 36 tests, 35 passing (97%)
