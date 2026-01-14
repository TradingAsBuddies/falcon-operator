# One Candle Rule Strategy - Implementation Guide

**Date**: 2026-01-12
**Status**: ✅ Implemented and Ready for Backtesting
**Strategy Source**: Scarface Trades (Chart Fanatics)
**YouTube**: https://www.youtube.com/watch?v=ZwV-xkXoeuA

---

## 📊 Strategy Overview

The **One Candle Rule** is a price action-based strategy that focuses on trading breakouts and retests of key support/resistance levels using single candle confirmation.

### Creator's Performance Claims
- **Win Rate**: 60-80%
- **Risk-Reward**: 1:2 average
- **Total Profit**: $3 million to date
- **Trading Style**: Scalping/Day Trading (9:30 AM - 11:00 AM ET)
- **Instruments**: Stocks (works on any instrument)

---

## 🎯 Strategy Logic

### Entry Rules
1. **Identify Support/Resistance**: Uses swing highs/lows from 20-period lookback
2. **Detect Breakout**: Price closes above resistance with 0.1% threshold
3. **Wait for Retest**: Price pulls back to broken level (now support)
4. **Confirm with Candle Pattern**: Look for:
   - Hammer candle (long lower wick)
   - Bullish engulfing
   - Strong close in top 25% of range
5. **Enter Long**: Buy when all conditions met

### Exit Rules
1. **Take Profit**: 1:2 risk-reward ratio (2x risk distance)
2. **Stop Loss**: 2% below entry price
3. **Time-Based Exit**: Close positions at 11:00 AM (end of trading window)

### Risk Management
- **Position Size**: 20% of portfolio per trade
- **Max Positions**: 1 at a time
- **Stop Loss**: 2% of entry price
- **Risk-Reward**: 1:2 (target is 2x stop distance)

---

## 📁 Files Created

### 1. Strategy Implementation
**File**: `strategies/one_candle_strategy.py`

**Key Components**:
- `OneCandleStrategy` - Main backtrader strategy class
- `identify_swing_levels()` - Finds support/resistance
- `detect_breakout()` - Identifies resistance breaks
- `detect_retest()` - Waits for pullback
- `is_bullish_confirmation()` - Pattern recognition
- Comprehensive logging and performance tracking

**Parameters** (customizable):
```python
lookback_period = 20         # S/R identification period
breakout_threshold = 0.001   # 0.1% breakout confirmation
retest_tolerance = 0.003     # 0.3% retest zone
risk_reward_ratio = 2.0      # 1:2 risk-reward
position_size_pct = 0.20     # 20% per trade
```

### 2. Backtest Script
**File**: `backtest_one_candle.py`

**Features**:
- Loads data from flat files
- Runs backtest with configurable parameters
- Calculates performance metrics
- Compares to creator's claims
- Validates strategy criteria

---

## 🚀 How to Use

### Prerequisites

1. **Install backtrader** (already installed in venv):
   ```bash
   ./backtest/bin/pip3 install backtrader
   ```

2. **Download market data**:
   ```bash
   python3 massive_flat_files.py --download --days 365
   ```

### Running Backtests

#### Option 1: Using the Dedicated Backtest Script

```bash
# Basic backtest - SPY for 1 year
./backtest/bin/python3 backtest_one_candle.py --ticker SPY --days 365

# With debug output (see every trade)
./backtest/bin/python3 backtest_one_candle.py --ticker SPY --days 365 --debug

# Different ticker
./backtest/bin/python3 backtest_one_candle.py --ticker QQQ --days 180

# Custom initial cash
./backtest/bin/python3 backtest_one_candle.py --ticker AAPL --days 365 --cash 25000
```

#### Option 2: Using Strategy Manager

```bash
# Validate strategy syntax
python3 strategy_manager.py validate -f strategies/one_candle_strategy.py

# Run backtest
python3 strategy_manager.py backtest -f strategies/one_candle_strategy.py

# Deploy if successful
python3 strategy_manager.py deploy -f strategies/one_candle_strategy.py
```

#### Option 3: Batch Backtesting Multiple Tickers

```bash
# Test on multiple tickers
for ticker in SPY QQQ AAPL MSFT TSLA; do
    echo "=== Testing $ticker ==="
    ./backtest/bin/python3 backtest_one_candle.py --ticker $ticker --days 365
    echo ""
done
```

---

## 📊 Expected Output

### Sample Backtest Results

```
================================================================================
ONE CANDLE RULE STRATEGY - BACKTEST
================================================================================
Ticker: SPY
Period: 365 days
Initial Cash: $10,000.00
================================================================================

Starting Portfolio Value: $10,000.00

Running backtest...

Final Portfolio Value: $11,250.00

================================================================================
BACKTEST RESULTS
================================================================================
Total Return: 12.50%
Total Profit/Loss: $1,250.00
Sharpe Ratio: 1.45
Max Drawdown: 8.32%

Trade Statistics:
  Total Trades: 24
  Winning Trades: 16
  Losing Trades: 8
  Win Rate: 66.7%
  Average Win: $156.25
  Average Loss: -$62.50
================================================================================

✅ Strategy PASSES validation criteria

================================================================================
COMPARISON TO CREATOR'S PERFORMANCE
================================================================================
Creator's Win Rate: 60-80%
Our Win Rate: 66.7%
Creator's Risk-Reward: 1:2
Our Implementation: 1:2 (hardcoded)

✅ Win rate meets or exceeds creator's performance!
================================================================================
```

---

## 🎛️ Strategy Parameters

You can customize the strategy by modifying parameters in `strategies/one_candle_strategy.py`:

### Identification Parameters
```python
lookback_period = 20           # How far back to look for S/R levels
```

### Breakout Detection
```python
breakout_threshold = 0.001     # 0.1% - How much above resistance to confirm breakout
retest_tolerance = 0.003       # 0.3% - Width of retest zone
```

### Risk Management
```python
risk_reward_ratio = 2.0        # Target profit / risk (1:2 = 2.0)
position_size_pct = 0.20       # 20% of portfolio per trade
stop_loss_pct = 0.02          # 2% stop loss
```

### Pattern Recognition
```python
require_confirmation = True    # Require bullish candle pattern
min_body_size = 0.003         # Minimum 0.3% candle body
```

### Trading Hours
```python
trade_start_hour = 9           # 9:30 AM
trade_start_minute = 30
trade_end_hour = 11           # 11:00 AM
trade_end_minute = 0
```

---

## 🔧 Customization Examples

### More Aggressive (Higher Risk/Reward)
```python
risk_reward_ratio = 3.0        # Target 3x risk (1:3)
position_size_pct = 0.30       # 30% per trade
```

### More Conservative (Tighter Criteria)
```python
breakout_threshold = 0.002     # Require stronger breakout
require_confirmation = True    # Always require confirmation
position_size_pct = 0.10       # Only 10% per trade
```

### All-Day Trading (Remove Time Filter)
```python
trade_start_hour = 0
trade_start_minute = 0
trade_end_hour = 23
trade_end_minute = 59
```

---

## 📈 Validating Strategy Performance

### Validation Criteria

The strategy passes validation if:
1. ✅ **Total Return** > -10%
2. ✅ **Max Drawdown** < 30%
3. ✅ **Total Trades** > 0

### Performance Targets

**Minimum Acceptable**:
- Win Rate: > 50%
- Return: > 0%
- Sharpe Ratio: > 0.5

**Good Performance**:
- Win Rate: 55-65%
- Return: > 10% annually
- Sharpe Ratio: > 1.0
- Max Drawdown: < 15%

**Excellent Performance** (matching creator):
- Win Rate: 60-80%
- Return: > 15% annually
- Sharpe Ratio: > 1.5
- Max Drawdown: < 10%

---

## 🐛 Troubleshooting

### Issue: "No module named 'backtrader'"

**Solution**: Use the venv Python:
```bash
./backtest/bin/python3 backtest_one_candle.py --ticker SPY
```

### Issue: "No market data files found"

**Solution**: Download data first:
```bash
python3 massive_flat_files.py --download --days 365
```

### Issue: "No data found for ticker"

**Solution**: Check if ticker is in the dataset:
```bash
zcat market_data/daily_bars/daily_bars_*.csv.gz | head -100 | grep YOUR_TICKER
```

### Issue: "No trades executed"

**Possible Causes**:
1. **Not enough volatility** - Try more volatile tickers (TSLA, NVDA)
2. **Timeframe mismatch** - Strategy designed for intraday, but daily data may not work well
3. **Parameters too strict** - Try loosening breakout_threshold or retest_tolerance

**Solutions**:
```bash
# Try a volatile stock
./backtest/bin/python3 backtest_one_candle.py --ticker TSLA --days 365 --debug

# Adjust parameters in strategies/one_candle_strategy.py
breakout_threshold = 0.002   # More lenient
retest_tolerance = 0.005     # Wider retest zone
```

---

## 🔬 Testing & Validation

### Quick Validation Test

```bash
# Validate Python syntax
./backtest/bin/python3 -m py_compile strategies/one_candle_strategy.py

# Validate strategy class
./backtest/bin/python3 -c "
from strategies.one_candle_strategy import OneCandleStrategy
print('✅ Strategy validated successfully')
"
```

### Run Comprehensive Tests

```bash
# Test on liquid ETFs
for ticker in SPY QQQ DIA IWM; do
    ./backtest/bin/python3 backtest_one_candle.py --ticker $ticker --days 365
done

# Test different timeframes
for days in 90 180 365 730; do
    ./backtest/bin/python3 backtest_one_candle.py --ticker SPY --days $days
done
```

---

## 📝 Interpreting Results

### Win Rate Analysis

| Win Rate | Assessment | Action |
|----------|------------|--------|
| 0-40% | ❌ Poor | Review logic, parameters need tuning |
| 40-50% | ⚠️ Below Target | Adjust parameters, test different tickers |
| 50-60% | ✅ Acceptable | Good performance, monitor |
| 60-80% | ✅✅ Excellent | Matches creator's claims |
| 80%+ | ⚠️ Suspicious | May be overfitting, validate carefully |

### Return Analysis

| Annual Return | Assessment |
|---------------|------------|
| < 0% | ❌ Losing strategy |
| 0-5% | ⚠️ Below S&P 500 average |
| 5-10% | ✅ Acceptable |
| 10-20% | ✅✅ Good |
| 20%+ | ✅✅✅ Excellent |

### Sharpe Ratio

| Sharpe | Quality |
|--------|---------|
| < 0 | Poor (negative returns) |
| 0-0.5 | Below average |
| 0.5-1.0 | Acceptable |
| 1.0-2.0 | Good |
| 2.0+ | Excellent |

---

## 🚀 Deployment Options

### Option 1: Paper Trading (Recommended First)

```bash
# After successful backtest, use paper trading to validate
python3 paper_trading_bot.py --strategy one_candle
```

### Option 2: Live Trading via Orchestrator

```bash
# Add to orchestrator configuration
python3 orchestrator/strategy_router.py --add one_candle --symbols SPY,QQQ
```

### Option 3: Deploy as Active Strategy

```bash
# Deploy using strategy manager (validates + backtests first)
python3 strategy_manager.py deploy -f strategies/one_candle_strategy.py
```

---

## 📚 Additional Resources

### Related Files
- `YOUTUBE_STRATEGIES_ACCESS_GUIDE.md` - How to access strategy database
- `STRATEGY_URL_FIX.md` - Web interface for viewing strategies
- `strategy_manager.py` - Strategy deployment system
- `massive_flat_files.py` - Market data management

### Strategy Database
```bash
# View strategy details from database
python3 -c "
import sqlite3
conn = sqlite3.connect('paper_trading.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM youtube_strategies WHERE id = 2')
result = cursor.fetchone()
print('Strategy:', result[1])
print('Creator:', result[2])
print('Win Rate:', result[13])  # performance_metrics
"
```

### Web Interface
View strategy details in browser:
```
http://192.168.1.162/strategies/2.html
```

---

## ⚙️ Advanced Usage

### Custom Backtest with Python

```python
import backtrader as bt
from strategies.one_candle_strategy import OneCandleStrategy

# Create cerebro
cerebro = bt.Cerebro()

# Add data (your data loading code here)
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)

# Add strategy with custom parameters
cerebro.addstrategy(
    OneCandleStrategy,
    lookback_period=30,           # Longer lookback
    risk_reward_ratio=3.0,        # Higher target
    position_size_pct=0.15,       # Smaller positions
    debug=True                    # Show trades
)

# Run
cerebro.run()
```

### Integrate with Dashboard API

```python
# Get strategy from database
import requests
response = requests.get('http://192.168.1.162/api/youtube-strategies/2')
strategy_data = response.json()

# Extract rules for custom implementation
entry_rules = strategy_data['strategy']['entry_rules']
exit_rules = strategy_data['strategy']['exit_rules']
```

---

## ✅ Quick Start Checklist

- [ ] **Step 1**: Download market data
  ```bash
  python3 massive_flat_files.py --download --days 365
  ```

- [ ] **Step 2**: Validate strategy code
  ```bash
  python3 strategy_manager.py validate -f strategies/one_candle_strategy.py
  ```

- [ ] **Step 3**: Run first backtest
  ```bash
  ./backtest/bin/python3 backtest_one_candle.py --ticker SPY --days 365
  ```

- [ ] **Step 4**: Review results
  - Check win rate (target: 60-80%)
  - Check return (target: > 10%)
  - Check drawdown (target: < 15%)

- [ ] **Step 5**: If good results, test on other tickers
  ```bash
  for ticker in QQQ AAPL MSFT; do
      ./backtest/bin/python3 backtest_one_candle.py --ticker $ticker --days 365
  done
  ```

- [ ] **Step 6**: Deploy to paper trading
  ```bash
  python3 strategy_manager.py deploy -f strategies/one_candle_strategy.py
  ```

---

## 📊 Summary

✅ **Strategy Implemented**: One Candle Rule from Scarface Trades
✅ **Files Created**: Strategy class + backtest script
✅ **Validation**: Code validated successfully
✅ **Ready**: Ready for backtesting with market data
✅ **Customizable**: 12+ parameters for tuning
✅ **Well-Documented**: Complete guide with examples

**Next Step**: Download market data and run your first backtest!

```bash
# Quick start
python3 massive_flat_files.py --download --days 365
./backtest/bin/python3 backtest_one_candle.py --ticker SPY --days 365
```

---

**Document Created**: 2026-01-12
**Status**: ✅ Ready for Backtesting
**Strategy Source**: YouTube Strategy #2 (Database ID: 2)
