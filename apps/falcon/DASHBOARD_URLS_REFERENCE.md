# Falcon Dashboard - URL Reference Guide

**Date**: 2026-01-12
**Status**: ✅ ALL ROUTES WORKING
**Server**: Running on PID 131786

---

## 🌐 Main URLs

### Landing Page
```
http://192.168.1.162/
```
**Shows**:
- Links to all main sections
- AI Stock Recommendations preview
- Quick navigation cards

---

### Trading Dashboard (Main Dashboard)
```
http://192.168.1.162/dashboard
http://192.168.1.162/orchestrator
http://192.168.1.162/orchestrator.html
```
**Shows**:
- 💰 Account Summary (balance, cash, total value)
- 📊 Portfolio Performance (P&L, charts)
- ⚙️ Active Strategies
- 📈 Open Positions (with live P&L)
- 📝 Recent Orders (trade history)
- 🤖 AI Stock Recommendations

**This is the main trading dashboard you'll use most often!**

---

### YouTube Strategies
```
http://192.168.1.162/strategies.html
```
**Shows**:
- All captured YouTube trading strategies
- Strategy submission form
- Click on any strategy to see details

**Individual Strategy Details**:
```
http://192.168.1.162/strategies/1.html
http://192.168.1.162/strategies/2.html
```

---

## 📡 API Endpoints

### Account Information
```bash
curl http://192.168.1.162/api/account
```
Returns: Current balance, cash, total value, last updated

### Open Positions
```bash
curl http://192.168.1.162/api/positions
```
Returns: All current positions with P&L

### Trade History
```bash
curl http://192.168.1.162/api/trades
```
Returns: Recent buy/sell orders

### AI Recommendations
```bash
curl http://192.168.1.162/api/recommendations
```
Returns: Latest AI stock screening results

### YouTube Strategies
```bash
# List all strategies
curl http://192.168.1.162/api/youtube-strategies

# Get specific strategy
curl http://192.168.1.162/api/youtube-strategies/1
curl http://192.168.1.162/api/youtube-strategies/2
```

### Strategy Management
```bash
# Get current active strategy
curl http://192.168.1.162/api/strategy

# Validate strategy
curl -X POST http://192.168.1.162/api/strategy/validate \
  -H "Content-Type: application/json" \
  -d '{"code": "..."}'

# Run backtest
curl -X POST http://192.168.1.162/api/strategy/backtest \
  -H "Content-Type: application/json" \
  -d '{"code": "...", "ticker": "SPY", "days": 365}'
```

---

## 🔐 Access Methods

### From Chromium Browser (Same Subnet)

**HTTP** (Recommended):
```
http://192.168.1.162/dashboard
http://192.168.1.162/strategies.html
```

**HTTPS** (Self-signed cert, requires accepting warning):
```
https://192.168.1.162/dashboard
```

### From Command Line

**On Raspberry Pi**:
```bash
curl http://localhost/dashboard
curl http://localhost/api/account | python3 -m json.tool
```

**From Another Host**:
```bash
curl http://192.168.1.162/dashboard
curl http://192.168.1.162/api/positions | python3 -m json.tool
```

---

## 📋 Quick Access URLs Summary

| URL | Purpose | Content |
|-----|---------|---------|
| `/` | Landing page | Links to all sections |
| `/dashboard` | **Main trading dashboard** | Account, positions, trades, P&L |
| `/orchestrator` | Same as /dashboard | Trading dashboard |
| `/strategies.html` | YouTube strategies list | Browse all strategies |
| `/strategies/1.html` | Strategy #1 details | Universal Liquidity Playbook |
| `/strategies/2.html` | Strategy #2 details | One Candle Rule |
| `/api/account` | Account API | JSON account data |
| `/api/positions` | Positions API | JSON positions with P&L |
| `/api/trades` | Trades API | JSON order history |
| `/api/recommendations` | AI Recommendations | JSON screening results |
| `/api/youtube-strategies` | Strategies API | JSON all strategies |

---

## 🎯 Most Common URLs

**Daily Trading**:
1. Main Dashboard: `http://192.168.1.162/dashboard`
2. Positions: `http://192.168.1.162/dashboard` (scroll to positions)
3. Account: `http://192.168.1.162/dashboard` (top section)

**Strategy Research**:
1. View Strategies: `http://192.168.1.162/strategies.html`
2. Strategy Details: Click any strategy card

**Quick Checks**:
1. Account Balance: `curl http://192.168.1.162/api/account`
2. Current Positions: `curl http://192.168.1.162/api/positions`
3. AI Picks: `curl http://192.168.1.162/api/recommendations`

---

## 🔧 Troubleshooting

### Dashboard Not Loading?

1. **Check if server is running**:
   ```bash
   ps aux | grep dashboard_server.py
   ```

2. **Check if port 5000 is listening**:
   ```bash
   netstat -tlnp | grep 5000
   ```

3. **Restart dashboard**:
   ```bash
   pkill -f dashboard_server.py
   nohup ./backtest/bin/python3 dashboard_server.py > dashboard.log 2>&1 &
   ```

4. **Check logs**:
   ```bash
   tail -50 dashboard.log
   ```

### HTTPS Certificate Warnings?

Use HTTP instead:
```
http://192.168.1.162/dashboard
```

Or accept the self-signed certificate in your browser (one-time warning).

### API Returns Error?

Check if Flask is running:
```bash
curl -I http://localhost:5000/api/account
```

Should return `HTTP/1.1 200 OK`

---

## 📱 Mobile Access

The dashboard is responsive and works on mobile browsers:

**From your phone** (on same WiFi):
```
http://192.168.1.162/dashboard
```

---

## 🔄 Route Changes Made

### What Was Fixed (2026-01-12)

**Before**:
- `/` → orchestrator.html ❌
- `/dashboard` → 404 Not Found ❌
- `/orchestrator` → Not defined ❌

**After**:
- `/` → index.html (landing page) ✅
- `/dashboard` → orchestrator.html (trading dashboard) ✅
- `/orchestrator` → orchestrator.html (trading dashboard) ✅

### Files Modified

1. **dashboard_server.py**
   - Added `/dashboard` route
   - Changed `/` to serve index.html (landing page)
   - Made `/dashboard`, `/orchestrator`, `/orchestrator.html` serve orchestrator.html

2. **Dashboard Server**
   - Restarted with new routes
   - PID: 131786

---

## 📊 Dashboard Features

### Account Summary
- Total balance
- Available cash
- Total positions value
- Unrealized P&L

### Portfolio Performance
- Daily P&L
- Win rate
- Total trades
- Performance charts

### Active Strategies
- Currently running strategies
- Strategy status
- Recent signals

### Open Positions
- Symbol, quantity, entry price
- Current price, unrealized P&L
- P&L percentage
- One-click sell buttons
- Auto stop-loss status

### Recent Orders
- Order history
- Buy/sell tracking
- Execution timestamps
- Realized P&L

### AI Recommendations
- Latest stock picks
- Confidence levels
- Entry signals
- Risk assessment

---

## 🚀 Getting Started

### First Time Access

1. **Open browser** (Chromium on your subnet)
2. **Navigate to**: `http://192.168.1.162/dashboard`
3. **You'll see**:
   - Your account balance
   - Current positions (if any)
   - Recent trades
   - AI recommendations

### Bookmark These

Add to your bookmarks:
- Main Dashboard: `http://192.168.1.162/dashboard`
- Strategies: `http://192.168.1.162/strategies.html`
- Landing Page: `http://192.168.1.162/`

---

## 📝 Notes

- All URLs use IP address `192.168.1.162` (your Raspberry Pi)
- HTTP port 80 and 8080 both work
- HTTPS port 443 requires accepting self-signed certificate
- Dashboard auto-refreshes data periodically
- API endpoints return JSON (use `| python3 -m json.tool` for formatting)

---

**Document Created**: 2026-01-12
**Server Status**: ✅ Running
**All Routes**: ✅ Working
**Ready for Use**: ✅ Yes
