# Strategy Quick Reference Guide

## 📊 Available Strategies

### 1. Momentum Breakout Strategy ⭐ **WINNER**
**File:** `strategies/momentum_breakout_strategy.py`
**Score:** 15.93
**Type:** Breakout with volume confirmation

**Best Performance:**
- AAPL 1yr: +20.73% (100% win rate)
- MSFT 1yr: +9.16%

**Use For:** Individual stocks (AAPL, MSFT)
**Avoid For:** ETFs until debugging complete

---

### 2. Current Active (RSI Mean Reversion) ✅ **RELIABLE**
**File:** `active_strategy.py`
**Score:** 14.39
**Type:** Mean reversion with RSI indicator

**Best Performance:**
- AAPL 2yr: +42.40%
- SPY 2yr: +20.33% (Sharpe 1.01)

**Use For:** ETFs (SPY, QQQ), consistent performance
**Currently:** Deployed in production

---

### 3. Bollinger Mean Reversion 🟡 **MODERATE**
**File:** `strategies/bollinger_mean_reversion_strategy.py`
**Score:** 8.66
**Type:** Mean reversion with Bollinger Bands

**Best Performance:**
- SPY 2yr: +14.75% (Sharpe 1.11)
- QQQ 1yr: +5.09%

**Use For:** SPY, QQQ
**Avoid For:** MSFT

---

### 4. Moving Average Crossover 🔴 **POOR**
**File:** `strategies/moving_average_crossover_strategy.py`
**Score:** 2.24
**Type:** Dual MA crossover

**Performance:** Mostly 0 trades (too conservative)
**Status:** Consider retiring

---

## 🚀 Quick Commands

### Backtest a Strategy
```bash
# Single backtest
./backtest/bin/python3 strategy_manager.py backtest -f strategies/momentum_breakout_strategy.py -t AAPL -d 365

# Compare multiple tickers
for ticker in SPY QQQ AAPL MSFT; do
  ./backtest/bin/python3 strategy_manager.py backtest -f strategies/momentum_breakout_strategy.py -t $ticker -d 365
done

# Run full comparison suite
./backtest/bin/python3 backtest_all_strategies.py
```

### Validate Strategy
```bash
./backtest/bin/python3 strategy_manager.py validate -f strategies/momentum_breakout_strategy.py
```

### Deploy Strategy
```bash
# Interactive deployment
./deploy_momentum_strategy.sh

# Manual deployment
./backtest/bin/python3 strategy_manager.py deploy -f strategies/momentum_breakout_strategy.py --force

# Restart services after deployment
sudo systemctl restart falcon-orchestrator.service
```

### View Strategy
```bash
# View current active
./backtest/bin/python3 strategy_manager.py show

# View specific strategy
cat strategies/momentum_breakout_strategy.py
```

### Rollback Strategy
```bash
# Rollback to previous version
./backtest/bin/python3 strategy_manager.py rollback

# Rollback to specific version
./backtest/bin/python3 strategy_manager.py list
./backtest/bin/python3 strategy_manager.py rollback -v strategy_20260105_165946.py
```

---

## 📈 Performance Comparison

| Strategy | SPY 2yr | QQQ 2yr | AAPL 2yr | MSFT 2yr | Overall |
|----------|---------|---------|----------|----------|---------|
| **Momentum Breakout** | +1.66% | Error | +27.04% | +8.28% | 15.93 ⭐ |
| **Current Active** | **+20.33%** | +14.06% | **+42.40%** | +6.07% | 14.39 ✅ |
| **Bollinger** | +14.75% | +8.42% | +25.19% | -3.19% | 8.66 🟡 |
| **MA Crossover** | +21.02% | +23.92% | +11.64% | +10.69% | 2.24 🔴 |

---

## 🎯 Strategy Selection Guide

### For ETFs (SPY, QQQ)
**Primary:** Current Active (RSI Mean Reversion)
- Proven consistent performance
- Good Sharpe ratios
- Moderate trade frequency

**Backup:** Bollinger Mean Reversion
- High Sharpe on SPY (1.11)
- Good win rates

---

### For Individual Stocks (AAPL, MSFT)
**Primary:** Momentum Breakout
- Best returns on AAPL (+20.73% 1yr)
- Best on MSFT (+9.16% 1yr)
- High win rates

**Backup:** Current Active
- Best AAPL 2yr (+42.40%)
- More consistent

---

### For Conservative Trading
**Use:** Current Active
- Most predictable
- Lower drawdowns on SPY
- High win rates (75-89%)

---

### For Aggressive Trading
**Use:** Momentum Breakout
- Higher returns potential
- Accepts lower trade frequency
- Higher risk tolerance needed

---

## 📊 Risk Metrics

### Maximum Drawdowns
- **Lowest:** Momentum Breakout on AAPL 1yr (-5.20%)
- **Highest:** Bollinger on AAPL 2yr (-19.06%)
- **Current Active:** Moderate (-8% to -15%)

### Sharpe Ratios
- **Best:** Bollinger on SPY 2yr (1.11)
- **Good:** Current Active on SPY 2yr (1.01)
- **Good:** Momentum Breakout on AAPL 2yr (1.02)

### Win Rates
- **Perfect:** Momentum Breakout on AAPL 1yr (100%)
- **Excellent:** Current Active on SPY 2yr (88.9%)
- **Good:** Bollinger on SPY 2yr (87.5%)

---

## 💡 Tips & Best Practices

### Before Deploying New Strategy
1. ✅ Validate syntax and structure
2. ✅ Backtest on multiple tickers (SPY, QQQ, AAPL, MSFT)
3. ✅ Check both 1yr and 2yr performance
4. ✅ Compare against current active strategy
5. ✅ Verify trade frequency is acceptable
6. ✅ Check maximum drawdown is tolerable

### After Deployment
1. 📊 Monitor first 5-10 trades closely
2. 📈 Compare live performance vs backtest
3. ⚠️ Set alerts for unexpected losses
4. 🔄 Be ready to rollback if needed
5. 📝 Document any issues or improvements

### Optimization Ideas
1. **Momentum Breakout:** Relax entry conditions to increase trades
2. **Current Active:** Adjust RSI thresholds for different markets
3. **Bollinger:** Add MSFT-specific parameters
4. **Hybrid:** Combine best elements of Momentum + Current Active

---

## 📁 Files & Documentation

- **Strategy Files:** `strategies/*.py` (28KB)
- **Backtest Script:** `backtest_all_strategies.py`
- **Deployment:** `deploy_momentum_strategy.sh`
- **Results:** `BACKTEST_RESULTS_SUMMARY.md`
- **Data:** `backtest_results.json`
- **This Guide:** `STRATEGY_QUICK_REFERENCE.md`

---

## 🔧 Troubleshooting

### Strategy Won't Deploy
```bash
# Check validation
./backtest/bin/python3 strategy_manager.py validate -f your_strategy.py

# Check for syntax errors
./backtest/bin/python3 -m py_compile your_strategy.py
```

### Backtest Fails
```bash
# Check if yfinance can download data
./backtest/bin/python3 -c "import yfinance as yf; print(yf.download('SPY', period='1y'))"

# Verify backtrader is installed
./backtest/bin/python3 -c "import backtrader; print(backtrader.__version__)"
```

### Low Trade Frequency
- Relax entry conditions
- Reduce required thresholds
- Remove strict filters
- Test on more volatile stocks

### High Drawdowns
- Add tighter stop losses
- Reduce position sizes
- Add volatility filters (ATR)
- Implement trailing stops

---

## 📞 Support

For issues or improvements:
1. Check backtesting logs
2. Review strategy validation output
3. Compare with working strategies
4. Test on different tickers/timeframes

---

*Last Updated: January 8, 2026*
*Strategies: 5 active*
*Storage: 310MB total (within policy)*
