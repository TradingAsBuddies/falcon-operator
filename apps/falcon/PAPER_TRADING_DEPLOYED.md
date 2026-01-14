# One Candle Strategy - Paper Trading Deployed

**Date**: 2026-01-12 11:36 AM ET
**Status**: ✅ DEPLOYED AND RUNNING
**Ticker**: TSLA
**Process ID**: 135820

---

## Deployment Summary

The One Candle Rule strategy has been successfully deployed to paper trading for **TSLA**.

### System Status

```
✓ Paper trading bot: RUNNING (PID 135820)
✓ Database: paper_trading.db
✓ Account balance: $4,784.95
✓ Trading window: 9:30 AM - 11:00 AM ET
✓ Current time: 11:36 AM ET (outside trading hours)
```

**Note**: The bot is currently idle because market trading hours (9:30-11:00 AM ET) have passed. It will automatically resume trading tomorrow during the 9:30-11:00 AM ET window.

---

## Strategy Configuration

### Parameters (from successful TSLA backtest)

```python
Ticker: TSLA
Lookback Period: 20 bars
Breakout Threshold: 0.1% above resistance
Retest Tolerance: 0.3% zone
Risk-Reward Ratio: 1:2
Position Size: 20% of capital
Stop Loss: 2% below entry
Trading Window: 9:30 AM - 11:00 AM ET (1.5 hours)
```

### Expected Performance (from backtest)

```
Win Rate: 66.7% (2 wins, 1 loss in 3 trades)
Profit Factor: 4.79
Return: +1.48% over 40 days
Average Win: $93.69
Average Loss: -$39.10
```

---

## Management Commands

### Check Status
```bash
./manage_paper_trading.sh TSLA status
```

### View Live Logs
```bash
./manage_paper_trading.sh TSLA logs
# or
tail -f paper_trading.log
```

### Stop Trading
```bash
./manage_paper_trading.sh TSLA stop
```

### Start Trading
```bash
./manage_paper_trading.sh TSLA start
```

### Restart
```bash
./manage_paper_trading.sh TSLA restart
```

---

## Monitoring

### Real-Time Log
```bash
# Follow live activity
tail -f paper_trading.log

# Show recent activity
./manage_paper_trading.sh TSLA status
```

### Web Dashboard
```
http://192.168.1.162/dashboard
```

The dashboard shows:
- Account balance
- Open positions
- Recent trades
- P&L performance

### Database Queries

**Check Account**:
```bash
python3 -c "import sqlite3; conn = sqlite3.connect('paper_trading.db'); cursor = conn.cursor(); cursor.execute('SELECT * FROM account'); print(cursor.fetchone())"
```

**Check Positions**:
```bash
python3 -c "import sqlite3; conn = sqlite3.connect('paper_trading.db'); cursor = conn.cursor(); cursor.execute('SELECT * FROM positions WHERE symbol=\"TSLA\"'); print(cursor.fetchone())"
```

**Check Recent Orders**:
```bash
python3 -c "import sqlite3; conn = sqlite3.connect('paper_trading.db'); cursor = conn.cursor(); cursor.execute('SELECT * FROM orders WHERE symbol=\"TSLA\" ORDER BY timestamp DESC LIMIT 5'); [print(row) for row in cursor.fetchall()]"
```

---

## How It Works

### Trading Flow

1. **Market Hours Detection** (9:30-11:00 AM ET)
   - Bot activates during trading window
   - Fetches 1-minute bars from Polygon.io every 60 seconds

2. **Signal Detection**
   - Identifies swing highs (resistance levels)
   - Detects breakouts above resistance
   - Waits for retest (pullback to broken level)
   - Enters long when retest confirmed

3. **Position Management**
   - Entry: Buy at retest confirmation
   - Stop Loss: 2% below entry
   - Target: 2x stop distance (1:2 risk-reward)
   - Time Exit: Closes all positions at 11:00 AM

4. **Order Execution**
   - Places orders in paper_trading.db
   - Updates account balance
   - Tracks positions
   - Logs all activity

---

## Expected Log Output

### During Trading Hours (9:30-11 AM ET)

```
[09:30:15] Paper trading started
Account balance: $4,784.95

[09:45:23] BREAKOUT detected: $485.67 > $485.18
[09:52:10] RETEST detected at $485.42
[09:52:10] BUY 19 TSLA @ $485.50 - Entry (Stop: $475.79, Target: $504.92)

[10:15:45] Target checking... Current: $490.23
[10:28:30] Target checking... Current: $495.15
[10:45:12] SELL 19 TSLA @ $505.10 - Target Hit
    P&L: $374.40 (4.04%)
```

### Outside Trading Hours

```
[11:36:40] Paper trading started
Account balance: $4,784.95

(No activity - waiting for 9:30 AM ET tomorrow)
```

---

## Trading Schedule

### Daily Schedule (Eastern Time)

| Time | Activity |
|------|----------|
| 9:30 AM | Trading window opens |
| 9:30-11:00 AM | Active trading (1.5 hours) |
| 11:00 AM | Trading window closes, exit all positions |
| 11:00 AM - 9:30 AM | Bot idle, waiting for next session |

### Next Trading Session

**Tomorrow (Jan 13, 2026)**:
- Start: 9:30 AM ET
- End: 11:00 AM ET
- Duration: 1.5 hours

The bot will automatically activate at 9:30 AM ET and begin monitoring TSLA for trading signals.

---

## Performance Tracking

### What to Monitor

1. **Trade Frequency**
   - Expected: 1-2 trades per week
   - Backtest showed 3 trades in 40 days
   - Check: Are trades being generated?

2. **Win Rate**
   - Target: 60-80% (creator's claim)
   - Backtest: 66.7% on TSLA
   - Check: Are we maintaining good win rate?

3. **Profit Factor**
   - Backtest: 4.79 (excellent)
   - Target: > 1.5
   - Check: Are winners larger than losers?

4. **Drawdown**
   - Backtest: 0.61% max
   - Target: < 5%
   - Check: Are losses controlled?

### Weekly Review Checklist

- [ ] Check total trades executed
- [ ] Calculate current win rate
- [ ] Review P&L performance
- [ ] Check max drawdown
- [ ] Compare to backtest results
- [ ] Verify system is running correctly

---

## Troubleshooting

### Bot Not Trading

**Symptoms**: No trades being executed

**Possible Causes**:
1. Outside trading hours (9:30-11 AM ET)
2. No breakout/retest setups found
3. Process crashed

**Solution**:
```bash
# Check if process is running
./manage_paper_trading.sh TSLA status

# Check logs for errors
tail -100 paper_trading.log

# Restart if needed
./manage_paper_trading.sh TSLA restart
```

### API Connection Issues

**Symptoms**: "Error fetching bar" in logs

**Possible Causes**:
1. Polygon API rate limit (5 req/min on free tier)
2. Network connectivity
3. Invalid API key

**Solution**:
```bash
# Check API key
grep MASSIVE_API_KEY ~/.local/.env

# Test API manually
curl "https://api.polygon.io/v2/aggs/ticker/TSLA/range/1/minute/2026-01-12/2026-01-12?apiKey=YOUR_KEY&limit=1"

# Check network
ping -c 3 api.polygon.io
```

### Database Errors

**Symptoms**: "Error inserting order" or "Error updating position"

**Solution**:
```bash
# Check database file
ls -lh paper_trading.db

# Verify tables exist
python3 -c "import sqlite3; conn = sqlite3.connect('paper_trading.db'); print(conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())"

# Check permissions
chmod 644 paper_trading.db
```

---

## Safety Features

### Risk Management

1. **Position Sizing**: Fixed 20% of capital per trade
2. **Stop Loss**: Automatic 2% stop on every position
3. **Max Positions**: Only 1 position at a time
4. **Time-Based Exit**: All positions closed at 11:00 AM
5. **Account Protection**: Cannot trade more than available cash

### Safeguards

- ✓ Paper trading only (no real money)
- ✓ Database-backed (all trades recorded)
- ✓ Automatic stop losses
- ✓ Limited trading window (1.5 hours/day)
- ✓ Single position limit
- ✓ API rate limit handling

---

## Next Steps

### Week 1: Monitor and Validate

1. **Daily**: Check if bot is running and trading
2. **Weekly**: Review performance vs backtest
3. **Track**: Win rate, profit factor, drawdown
4. **Compare**: Paper trading results to backtest expectations

### Week 2-4: Evaluate Performance

**If performing well** (win rate > 50%, profitable):
- Continue paper trading
- Track 20+ trades for statistical significance
- Consider adding more capital to paper account

**If underperforming** (win rate < 40%, losing money):
- Review parameters
- Check if market conditions changed
- Consider adjusting breakout_threshold or retest_tolerance
- Test 5-minute bars instead of 1-minute

### Month 2: Production Decision

**Criteria for live trading**:
- [ ] 50+ paper trades executed
- [ ] Win rate > 50%
- [ ] Profit factor > 1.5
- [ ] Max drawdown < 10%
- [ ] Consistent performance over 30+ days

**If all criteria met**:
- Consider moving to live trading with small capital
- Start with $500-1000 real money
- Scale up gradually as confidence builds

---

## Files Created

```
paper_trade_one_candle.py      # Paper trading bot (live trading logic)
manage_paper_trading.sh        # Management script (start/stop/status)
paper_trading.log              # Activity log
paper_trading.pid              # Process ID file
PAPER_TRADING_DEPLOYED.md      # This document
```

---

## Summary

✅ **Status**: One Candle strategy successfully deployed to paper trading
✅ **Ticker**: TSLA (best backtest performer - 66.7% win rate)
✅ **Process**: Running (PID 135820)
✅ **Account**: $4,784.95 available
✅ **Next Trading**: Tomorrow 9:30-11:00 AM ET
✅ **Monitoring**: Dashboard at http://192.168.1.162/dashboard

**The bot will automatically resume trading tomorrow at 9:30 AM ET and begin looking for TSLA breakout/retest setups.**

---

**Deployed**: 2026-01-12 11:36 AM ET
**Strategy**: One Candle Rule by Scarface Trades
**Expected Win Rate**: 60-70% (based on TSLA backtest)
**Risk-Reward**: 1:2
**Status**: ✅ LIVE IN PAPER TRADING
