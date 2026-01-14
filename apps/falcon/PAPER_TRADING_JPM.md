# Paper Trading - JPM Deployment

**Date**: 2026-01-12 1:45 PM ET
**Status**: ✅ ACTIVE
**Ticker**: JPM (JPMorgan Chase)
**Previous**: TSLA (stopped)

---

## Change Summary

### Action Taken
- ✅ Stopped: TSLA paper trading (PID 135820)
- ✅ Started: JPM paper trading (PID 138278)
- ✅ Strategy: One Candle Rule

### Current Status

```
Ticker: JPM (JPMorgan Chase)
Process: RUNNING (PID 138278)
Account Balance: $4,784.95
Trading Window: 9:30 AM - 11:00 AM ET
Strategy: One Candle Rule
```

---

## JPM vs TSLA Characteristics

### JPM (JPMorgan Chase)
**Type**: Large-cap financial (bank)
**Typical Characteristics**:
- Lower volatility than TSLA
- Stable, predictable price action
- High liquidity
- Less prone to extreme moves
- Good for testing risk management

**Trading Profile**:
- Price range: ~$200-250
- Daily moves: 0.5% - 2%
- Volume: Very high (20M+ shares/day)
- Patterns: Cleaner technical setups

### TSLA (Tesla) - Previous
**Type**: Large-cap tech/automotive
**Characteristics**:
- High volatility
- Large intraday swings
- More prone to gaps
- Emotional/news-driven

**Backtest Results**:
- Win Rate: 66.7%
- Profit Factor: 4.79
- Return: +1.48%

---

## Expected Performance with JPM

### Anticipated Differences

**Compared to TSLA backtests**:

| Metric | TSLA | JPM (Expected) |
|--------|------|----------------|
| **Volatility** | High | Lower |
| **Trade Frequency** | 1-2/week | 1-2/week |
| **Win Rate** | 66.7% | 50-60% (est) |
| **Average Win** | $93.69 | $50-70 (est) |
| **Average Loss** | -$39.10 | -$30-40 (est) |
| **Profit Factor** | 4.79 | 1.5-2.5 (est) |

### Why JPM May Perform Differently

**Advantages**:
- More predictable breakout patterns
- Less gap risk
- Cleaner retests
- Better for learning strategy behavior

**Disadvantages**:
- Smaller percentage moves
- Lower absolute dollar gains per trade
- Fewer volatility opportunities

---

## Strategy Parameters

### One Candle Rule Settings

```python
Ticker: JPM
Lookback Period: 20 bars
Breakout Threshold: 0.1% above resistance
Retest Tolerance: 0.3% zone
Risk-Reward Ratio: 1:2
Position Size: 20% of capital (~$950)
Stop Loss: 2% below entry
Trading Window: 9:30 AM - 11:00 AM ET
```

### Position Sizing for JPM

**With $4,784.95 capital**:
- Position size: 20% = $956.99
- At JPM ~$240/share: ~3-4 shares per trade
- Stop loss (2%): ~$4.80/share = $14.40-19.20 per trade
- Target (1:2): ~$9.60/share = $28.80-38.40 per trade

---

## Management Commands

### Check Status
```bash
./manage_paper_trading.sh JPM status
```

### View Logs
```bash
./manage_paper_trading.sh JPM logs
# or
tail -f paper_trading.log
```

### Stop Trading
```bash
./manage_paper_trading.sh JPM stop
```

### Switch to Different Ticker
```bash
# Stop current
./manage_paper_trading.sh JPM stop

# Start new ticker (e.g., back to TSLA)
./manage_paper_trading.sh TSLA start
```

---

## Monitoring

### Dashboard
```
http://192.168.1.162/dashboard
```

### Database Queries

**Check JPM positions**:
```bash
python3 -c "import sqlite3; conn = sqlite3.connect('paper_trading.db'); cursor = conn.cursor(); cursor.execute('SELECT * FROM positions WHERE symbol=\"JPM\"'); print(cursor.fetchone())"
```

**Check recent JPM orders**:
```bash
python3 -c "import sqlite3; conn = sqlite3.connect('paper_trading.db'); cursor = conn.cursor(); cursor.execute('SELECT * FROM orders WHERE symbol=\"JPM\" ORDER BY timestamp DESC LIMIT 5'); [print(row) for row in cursor.fetchall()]"
```

---

## Trading Schedule

### Daily Schedule (Eastern Time)

| Time | Activity |
|------|----------|
| 9:30 AM | Trading window opens |
| 9:30-11:00 AM | Active trading - monitor for signals |
| 11:00 AM | Trading window closes, exit all positions |
| 11:00 AM - 9:30 AM | Bot idle |

### Next Trading Session

**Today**: Outside trading hours (current time: 1:45 PM ET)
**Tomorrow (Jan 13, 2026)**:
- Start: 9:30 AM ET
- End: 11:00 AM ET
- JPM will be monitored for breakout/retest patterns

---

## Expected Activity Log

### During Trading Hours (9:30-11 AM)

```
[09:30:15] Paper trading started
Account balance: $4,784.95

[09:45:23] BREAKOUT detected: $242.50 > $242.25
[09:52:10] RETEST detected at $242.30
[09:52:10] BUY 3 JPM @ $242.35 - Entry (Stop: $237.50, Target: $252.05)

[10:28:30] Target checking... Current: $245.20
[10:45:12] SELL 3 JPM @ $252.10 - Target Hit
    P&L: $29.25 (4.02%)
```

### Outside Trading Hours

```
[13:45:00] Paper trading started
Account balance: $4,784.95

(No activity - waiting for 9:30 AM ET tomorrow)
```

---

## Why JPM for Paper Trading?

### Rationale for Switch

1. **Testing Strategy on Different Asset Type**
   - Financial sector vs tech/automotive
   - Different volatility profile
   - Validates strategy across sectors

2. **Risk Assessment**
   - JPM more stable than TSLA
   - Better for understanding base strategy performance
   - Clearer pattern recognition

3. **Diversification Testing**
   - See how strategy performs on different stocks
   - Identify which stock types work best
   - Build confidence in strategy robustness

---

## Performance Comparison Plan

### Tracking Both Tickers

After 2-4 weeks of JPM trading:
- Compare JPM results to TSLA backtest
- Evaluate which ticker performs better
- Consider running both simultaneously

**Decision Matrix**:

| JPM Results | Next Action |
|-------------|-------------|
| Win rate > 60%, profitable | Continue JPM, add capital |
| Win rate 50-60%, profitable | Continue JPM, monitor |
| Win rate 40-50%, break-even | Switch back to TSLA |
| Win rate < 40%, losing | Re-evaluate strategy parameters |

---

## Success Criteria

### Short-Term (1-2 weeks)

- [ ] 3-5 trades executed
- [ ] No catastrophic losses
- [ ] Strategy logic working correctly
- [ ] Win rate > 40%

### Medium-Term (3-4 weeks)

- [ ] 10-15 trades executed
- [ ] Win rate > 50%
- [ ] Profitable overall
- [ ] Max drawdown < 10%

### Long-Term (1-2 months)

- [ ] 20+ trades
- [ ] Win rate approaching 60%
- [ ] Profit factor > 1.5
- [ ] Ready for larger position sizes or live trading

---

## Notes

- JPM is currently outside trading hours (1:45 PM ET)
- Bot will activate tomorrow at 9:30 AM ET
- Account balance preserved from previous TSLA trading: $4,784.95
- Same strategy parameters as TSLA (proven to work)
- Monitor dashboard for first JPM trade

---

## Quick Reference

```bash
# Check status
./manage_paper_trading.sh JPM status

# View live logs
tail -f paper_trading.log

# Check account
python3 -c "import sqlite3; conn = sqlite3.connect('paper_trading.db'); cursor = conn.cursor(); cursor.execute('SELECT cash FROM account'); print(f'Balance: \${cursor.fetchone()[0]:,.2f}')"

# Dashboard
http://192.168.1.162/dashboard
```

---

**Deployed**: 2026-01-12 1:45 PM ET
**Ticker**: JPM (JPMorgan Chase)
**Strategy**: One Candle Rule
**Status**: ✅ ACTIVE AND READY FOR TOMORROW'S SESSION
**Next Trade Window**: Jan 13, 2026 9:30-11:00 AM ET
