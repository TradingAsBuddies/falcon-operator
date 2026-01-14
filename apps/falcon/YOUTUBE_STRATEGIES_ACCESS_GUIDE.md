# YouTube Strategies - Access Guide

**Date**: 2026-01-12
**Status**: 2 Strategies Captured, 0 Backtests Run

---

## Overview

The Falcon system captures trading strategies from YouTube videos using AI extraction. Currently, 2 strategies are stored in the database and accessible via web interface and API.

---

## Accessing Strategies via Web Interface

### Main Strategies Page

**URL**: `http://192.168.1.162/strategies.html`

**Features**:
- View all captured YouTube strategies in a grid layout
- Submit new YouTube URLs for AI extraction
- Click on any strategy card to view detailed information
- See strategy metadata: creator, tags, trading style

### Individual Strategy View

**URL**: `http://192.168.1.162/strategies/{strategy_id}.html`

**Examples**:
- Strategy #1: `http://192.168.1.162/strategies/1.html`
- Strategy #2: `http://192.168.1.162/strategies/2.html`

---

## Current Strategies in Database

### Strategy #1: Universal Liquidity Playbook
- **ID**: 1
- **Creator**: Zee (The Travelling Trader) - Chart Fanatics
- **YouTube URL**: https://youtu.be/nMhywubR2xc
- **Trading Style**: Universal (day trading, swing trading, options, long-term)
- **Instruments**: All asset classes
- **Win Rate**: Not specified
- **Performance**: 15+ years experience, Wall Street background

**Strategy Overview**:
Narrative-based framework requiring: (1) liquidity catalyst, (2) retracement, (3) technical/fundamental confluence

**Key Tags**: liquidity, retracement, market-structure, multi-timeframe, narrative-trading

### Strategy #2: One Candle Rule (Support/Resistance Retest)
- **ID**: 2
- **Creator**: Scarface Trades (Chart Fanatics)
- **YouTube URL**: https://www.youtube.com/watch?v=ZwV-xkXoeuA
- **Trading Style**: Scalping/Day Trading (9:30-11 AM ET)
- **Instruments**: Stocks (works on any instrument)
- **Win Rate**: 60-80%
- **Performance**: $3 million profit to date, 1:2 risk-reward

**Strategy Overview**:
Price action strategy focused on breakouts and retests using single candle confirmation

**Key Tags**: breakout, retest, price-action, support-resistance, scalping

---

## Accessing Strategies via API

### 1. List All Strategies

```bash
curl http://192.168.1.162/api/youtube-strategies | python3 -m json.tool
```

**Response**:
```json
{
  "status": "success",
  "strategies": [
    {
      "id": 1,
      "title": "...",
      "creator": "...",
      "youtube_url": "...",
      "strategy_overview": "...",
      "entry_rules": "...",
      "exit_rules": "...",
      "risk_management": "...",
      "trading_style": "...",
      "instruments": "...",
      "tags": [...],
      "pros": "...",
      "cons": "...",
      "performance_metrics": {...}
    }
  ]
}
```

### 2. Get Specific Strategy

```bash
curl http://192.168.1.162/api/youtube-strategies/1 | python3 -m json.tool
```

### 3. Submit New YouTube URL

```bash
curl -X POST http://192.168.1.162/api/youtube-strategies/submit \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

**Note**: Requires Claude API key to be configured in `.env` file.

---

## Accessing Strategy Data Programmatically (Python)

### Example 1: Fetch All Strategies

```python
import sqlite3
import json

conn = sqlite3.connect('paper_trading.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all strategies
cursor.execute('SELECT * FROM youtube_strategies')
strategies = cursor.fetchall()

for strat in strategies:
    print(f"ID: {strat['id']}")
    print(f"Title: {strat['title']}")
    print(f"Creator: {strat['creator']}")
    print(f"Win Rate: {json.loads(strat['performance_metrics'])['win_rate']}")
    print(f"Entry Rules: {strat['entry_rules']}")
    print()

conn.close()
```

### Example 2: Filter Strategies by Criteria

```python
import sqlite3
import json

conn = sqlite3.connect('paper_trading.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Find scalping strategies
cursor.execute("""
    SELECT * FROM youtube_strategies
    WHERE trading_style LIKE '%scalping%'
       OR trading_style LIKE '%day trading%'
""")

scalping_strategies = cursor.fetchall()

for strat in scalping_strategies:
    print(f"Found: {strat['title']}")
    print(f"Style: {strat['trading_style']}")

conn.close()
```

### Example 3: Export Strategy to JSON

```python
import sqlite3
import json

def export_strategy_to_json(strategy_id, output_file):
    conn = sqlite3.connect('paper_trading.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM youtube_strategies WHERE id = ?', (strategy_id,))
    strategy = cursor.fetchone()

    if strategy:
        strategy_dict = dict(strategy)

        # Parse JSON fields
        if strategy_dict['tags']:
            strategy_dict['tags'] = json.loads(strategy_dict['tags'])
        if strategy_dict['performance_metrics']:
            strategy_dict['performance_metrics'] = json.loads(strategy_dict['performance_metrics'])

        with open(output_file, 'w') as f:
            json.dump(strategy_dict, f, indent=2)

        print(f"Strategy exported to {output_file}")
    else:
        print(f"Strategy {strategy_id} not found")

    conn.close()

# Usage
export_strategy_to_json(1, 'strategy_1.json')
```

### Example 4: Use Strategy Data in External Application

```python
import sqlite3
import json

class StrategyReader:
    def __init__(self, db_path='paper_trading.db'):
        self.db_path = db_path

    def get_strategy(self, strategy_id):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM youtube_strategies WHERE id = ?', (strategy_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return dict(result)
        return None

    def get_entry_rules(self, strategy_id):
        strategy = self.get_strategy(strategy_id)
        return strategy['entry_rules'] if strategy else None

    def get_exit_rules(self, strategy_id):
        strategy = self.get_strategy(strategy_id)
        return strategy['exit_rules'] if strategy else None

    def get_risk_management(self, strategy_id):
        strategy = self.get_strategy(strategy_id)
        return strategy['risk_management'] if strategy else None

# Usage in your application
reader = StrategyReader()

# Get specific rules for implementation
entry_rules = reader.get_entry_rules(2)  # One Candle Rule strategy
print("Entry Rules:")
print(entry_rules)
```

---

## Backtesting Status

### Current State
- **Total Strategies**: 2
- **Strategies with Backtests**: 0
- **Backtest Records in Database**: 0

### Why No Backtests?

The captured strategies are **conceptual/narrative-based** and do not have executable code:
1. Strategy #1 has `strategy_code: "None provided"` (manual interpretation required)
2. Strategy #2 has `strategy_code: ""` (no automated code generated)

These strategies describe **discretionary trading methods** that require:
- Human interpretation of market context
- Subjective judgment calls
- Visual pattern recognition
- Multiple timeframe analysis

---

## Running Backtests

### Option 1: Manual Backtest (Current Approach)

You would need to:
1. Read the strategy rules from the database
2. Manually interpret and implement the logic
3. Write a backtrader strategy class
4. Run backtests using `massive_flat_files.py`

**Example**:
```bash
# After implementing the strategy in Python
python3 massive_flat_files.py --backtest SPY --strategy one_candle_rule
```

### Option 2: Use Strategy Manager (For Automated Strategies)

If you have executable strategy code:

```bash
# Validate strategy
python3 strategy_manager.py validate -f my_strategy.py

# Run backtest
python3 strategy_manager.py backtest -f my_strategy.py

# Deploy if successful
python3 strategy_manager.py deploy -f my_strategy.py
```

### Option 3: API-Based Backtesting

```bash
# Send strategy code for backtesting
curl -X POST http://192.168.1.162/api/strategy/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "code": "class MyStrategy(bt.Strategy): ...",
    "ticker": "SPY",
    "days": 365
  }'
```

---

## Database Schema

### youtube_strategies Table

```sql
CREATE TABLE youtube_strategies (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    creator TEXT NOT NULL,
    youtube_url TEXT UNIQUE NOT NULL,
    video_id TEXT NOT NULL,
    description TEXT,
    strategy_overview TEXT,
    trading_style TEXT,
    instruments TEXT,
    entry_rules TEXT,
    exit_rules TEXT,
    risk_management TEXT,
    strategy_code TEXT,
    tags TEXT,  -- JSON array
    performance_metrics TEXT,  -- JSON object
    pros TEXT,
    cons TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### strategy_backtests Table

```sql
CREATE TABLE strategy_backtests (
    id INTEGER PRIMARY KEY,
    strategy_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    total_return REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    win_rate REAL,
    total_trades INTEGER,
    backtest_data TEXT,  -- JSON with full results
    created_at TEXT NOT NULL,
    FOREIGN KEY (strategy_id) REFERENCES youtube_strategies(id)
);
```

---

## Exporting Strategy Data

### Export All Strategies to CSV

```python
import sqlite3
import csv

conn = sqlite3.connect('paper_trading.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, title, creator, youtube_url, trading_style,
           instruments, entry_rules, exit_rules
    FROM youtube_strategies
""")

with open('youtube_strategies.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'Title', 'Creator', 'URL', 'Trading Style',
                     'Instruments', 'Entry Rules', 'Exit Rules'])
    writer.writerows(cursor.fetchall())

conn.close()
print("Exported to youtube_strategies.csv")
```

### Export to Excel

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('paper_trading.db')

# Read strategies into DataFrame
df = pd.read_sql_query("SELECT * FROM youtube_strategies", conn)

# Export to Excel
df.to_excel('youtube_strategies.xlsx', index=False)

conn.close()
print("Exported to youtube_strategies.xlsx")
```

---

## Using Strategies in Third-Party Applications

### REST API Integration

Any application can access the strategies via HTTP:

```javascript
// JavaScript/Node.js example
const fetch = require('node-fetch');

async function getStrategies() {
    const response = await fetch('http://192.168.1.162/api/youtube-strategies');
    const data = await response.json();
    return data.strategies;
}

async function getStrategy(id) {
    const response = await fetch(`http://192.168.1.162/api/youtube-strategies/${id}`);
    const data = await response.json();
    return data.strategy;
}

// Use in your trading bot
const strategies = await getStrategies();
console.log(`Found ${strategies.length} strategies`);
```

### Database Connection

Direct database access from any language:

**Python**:
```python
import sqlite3
conn = sqlite3.connect('/home/ospartners/src/falcon/paper_trading.db')
```

**R**:
```r
library(DBI)
conn <- dbConnect(RSQLite::SQLite(),
                  "/home/ospartners/src/falcon/paper_trading.db")
strategies <- dbGetQuery(conn, "SELECT * FROM youtube_strategies")
```

**Java**:
```java
Connection conn = DriverManager.getConnection(
    "jdbc:sqlite:/home/ospartners/src/falcon/paper_trading.db"
);
```

---

## Adding New Strategies

### Via Web Interface

1. Navigate to `http://192.168.1.162/strategies.html`
2. Paste YouTube URL in the submission form
3. Click "Extract Strategy"
4. Wait for AI extraction (requires Claude API key)
5. Strategy will appear in the grid once processed

### Via API

```bash
curl -X POST http://192.168.1.162/api/youtube-strategies/submit \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=NEW_VIDEO_ID"
  }'
```

### Via Python Script

```python
import requests

def submit_youtube_strategy(url):
    response = requests.post(
        'http://192.168.1.162/api/youtube-strategies/submit',
        json={'youtube_url': url}
    )
    return response.json()

# Submit new strategy
result = submit_youtube_strategy('https://www.youtube.com/watch?v=abc123')
print(result)
```

---

## Limitations and Considerations

### Current Limitations

1. **No Executable Code**: Strategies are conceptual descriptions, not executable code
2. **No Automated Backtests**: Requires manual implementation before backtesting
3. **Discretionary Nature**: Most YouTube strategies require human judgment
4. **Pattern Recognition**: Visual patterns can't be easily automated

### What You CAN Do

1. ✅ **Access strategy descriptions** via web interface or API
2. ✅ **Export strategy data** to JSON, CSV, Excel
3. ✅ **Use in external applications** via REST API or database connection
4. ✅ **Reference rules for manual trading**
5. ✅ **Build custom implementations** based on the extracted rules

### What You CAN'T Do (Yet)

1. ❌ **Automated backtesting** (no executable code)
2. ❌ **One-click deployment** (requires manual implementation)
3. ❌ **Live signal generation** (discretionary strategies)

---

## Recommended Workflow

### For Using These Strategies

1. **Access via Web Interface**:
   - Go to `http://192.168.1.162/strategies.html`
   - Review strategy details
   - Understand entry/exit rules

2. **Export for Reference**:
   - Use API to fetch full strategy details
   - Export to JSON or PDF for offline reference
   - Print rules for manual trading

3. **Implement in Code** (if possible):
   - Translate discretionary rules to quantitative logic
   - Write backtrader strategy class
   - Test with historical data

4. **Track Performance**:
   - Use paper trading account to test implementation
   - Track trades manually against strategy rules
   - Record results in strategy_backtests table

---

## Quick Reference Commands

```bash
# View all strategies via API
curl http://192.168.1.162/api/youtube-strategies | python3 -m json.tool

# Get specific strategy
curl http://192.168.1.162/api/youtube-strategies/1 | python3 -m json.tool

# Export to JSON file
curl http://192.168.1.162/api/youtube-strategies/1 > strategy_1.json

# Check database directly
python3 -c "import sqlite3; conn=sqlite3.connect('paper_trading.db'); \
print(conn.execute('SELECT id, title FROM youtube_strategies').fetchall())"

# Access web interface
# Open browser: http://192.168.1.162/strategies.html
```

---

## Summary

✅ **2 YouTube strategies captured** in database
✅ **Accessible via web interface** at `/strategies.html`
✅ **Full API access** with GET/POST endpoints
✅ **Exportable to any format** (JSON, CSV, Excel)
✅ **Usable from external applications** (REST API or direct DB)
❌ **No automated backtests** (strategies are conceptual/discretionary)
❌ **No executable code** (requires manual implementation)

**The strategies are captured and accessible, but they represent discretionary trading methods that require human interpretation and cannot be directly backtested without manual implementation into executable code.**

---

**Document Generated**: 2026-01-12
**Status**: Strategies Accessible
**Next Steps**: Implement strategy logic in code for automated backtesting
