# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git Workflow

- **main**: Protected branch. Requires PR with passing tests and 1 approval to merge.
- **development**: Active development branch. All work happens here.

Workflow:
1. Work on `development` branch
2. Push changes and create PR to `main`
3. Wait for GitHub workflow tests to pass
4. Get approval and merge to `main`

## Project Overview

Falcon is an AI-powered algorithmic trading system that combines:
- Automated stock screening using AI agents (Claude, ChatGPT, Perplexity)
- Live paper trading with real-time market data from Polygon.io
- Backtesting framework using backtrader
- Local flat file data management for efficient historical data storage

Designed to run on Raspberry Pi and Linux systems with automated daily market data updates.

## Commands

### Setup
```bash
./setup_env_script.sh              # Initial setup (creates .env, installs deps, inits DB)
pip3 install -r requirements.txt   # Install dependencies only
python3 init_database.py           # Initialize/reset database
python3 init_database.py --reset   # Reset existing database
```

### Running Applications
```bash
python3 integrated_trading_bot.py                  # Main bot (AI screener + live trading)
python3 ai_stock_screener.py                       # Start AI screener scheduler
python3 ai_stock_screener.py --test                # Run single screen (test mode)
python3 live_paper_trading.py YOUR_MASSIVE_API_KEY # Paper trading with real-time data
python3 paper_trading_bot.py                       # Paper trading with backtesting
python3 dashboard_server.py                        # Flask web dashboard
python3 daily_report.py                            # Generate end-of-day report
python3 daily_report.py --live                     # Generate live intraday report
python3 daily_report.py --date 2026-01-14          # Report for specific date
```

### Manual Watchlist
Add tickers to your `.env` file to always include them in scans (bypasses Finviz filters):
```bash
MANUAL_WATCHLIST=FEED,BAC,EVTV,BEEM
```

### Flat Files Data Management
```bash
python3 massive_flat_files.py --download           # Download 365 days of data
python3 massive_flat_files.py --download --days 730 # Download 2 years
python3 massive_flat_files.py --update             # Update with latest day
python3 massive_flat_files.py --backtest SPY       # Backtest single ticker
python3 massive_flat_files.py --batch-backtest SPY,QQQ,AAPL  # Batch backtest
```

## Architecture

### Data Flow
```
Finviz Screener (web scraping)
        │
        ▼
ai_stock_screener.py ──► AI Agents (Claude/ChatGPT/Perplexity)
        │                         │
        │                         ▼
        │              screened_stocks.json
        ▼
integrated_trading_bot.py
        │
        ├───► Polygon.io API (real-time)
        │
        └───► market_data/daily_bars/*.csv.gz (historical flat files)
                       │
                       ▼
              live_paper_trading.py
                       │
                       ▼
              paper_trading.db (SQLite)
                       │
                       ▼
              dashboard_server.py (Flask REST API)
```

### Key Files

| File | Purpose |
|------|---------|
| `ai_stock_screener.py` | Multi-agent AI stock analysis with Finviz scraping |
| `integrated_trading_bot.py` | Main entry point combining screener + trading |
| `live_paper_trading.py` | Paper trading engine with Polygon.io real-time data |
| `massive_flat_files.py` | Local historical data management (download/update/backtest) |
| `paper_trading_bot.py` | Backtrader-based paper trading bot |
| `dashboard_server.py` | Flask web server with REST API |
| `strategy_manager.py` | AI-driven strategy modification with validation |
| `active_strategy.py` | Current deployed trading strategy (AI-modifiable) |
| `init_database.py` | SQLite database initialization |

## Strategy Management (AI-Modifiable)

The `strategy_manager.py` module allows AI agents to safely modify trading strategies.

### CLI Usage
```bash
python3 strategy_manager.py show                    # View current strategy
python3 strategy_manager.py validate -f strategy.py # Validate a strategy file
python3 strategy_manager.py backtest -f strategy.py # Run backtest
python3 strategy_manager.py deploy -f strategy.py   # Deploy after validation
python3 strategy_manager.py rollback                # Rollback to previous
python3 strategy_manager.py list                    # List version history
```

### API Endpoints (via dashboard_server.py)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/strategy` | GET | Get current strategy code |
| `/api/strategy/validate` | POST | Validate strategy (body: `{code: "..."}`) |
| `/api/strategy/backtest` | POST | Run backtest (body: `{code: "...", ticker: "SPY", days: 365}`) |
| `/api/strategy/deploy` | POST | Deploy strategy (body: `{code: "...", force: false}`) |
| `/api/strategy/rollback` | POST | Rollback (body: `{version: "filename"}` or `{}` for last) |
| `/api/strategy/versions` | GET | List all versions |

### Safety Controls
- **Syntax validation**: Python AST parsing
- **Structure validation**: Must have Strategy class with `__init__` and `next` methods
- **Security validation**: Blocks dangerous imports (subprocess, os.system, eval, exec)
- **Backtesting**: Runs backtest before deployment; rejects if return < -10% or drawdown > 30%
- **Git versioning**: All changes are committed with backtest results
- **Rollback**: Easy revert to any previous version

### AI Agent System

The screener uses a priority-based multi-agent system with automatic fallback:
1. Claude (Priority 1) - Best for structured financial analysis
2. ChatGPT (Priority 2) - Good alternative
3. Perplexity (Priority 3) - Good for real-time news data

### Multi-Screener Profiles

The system supports multiple screener profiles with different themes:

**Built-in Profiles:**
- **Momentum Breakouts** - High-volume breakout candidates (morning + midday)
- **Earnings Plays** - Stocks with upcoming earnings (morning + evening)
- **Seasonal Sector Rotation** - Sector-based seasonal patterns (morning + evening)

**CLI Usage:**
```bash
python3 -m screener.multi_screener --init        # Initialize default profiles
python3 -m screener.multi_screener --run-type morning  # Run morning screen
python3 -m screener.multi_screener --profile "Momentum Breakouts"  # Run specific profile
```

**API Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/screener/profiles` | GET | List all profiles |
| `/api/screener/profiles` | POST | Create new profile |
| `/api/screener/profiles/<id>` | GET/PUT/DELETE | CRUD for profile |
| `/api/screener/profiles/<id>/run` | POST | Manually run profile |
| `/api/screener/profiles/<id>/performance` | GET | Get performance metrics |
| `/api/screener/profiles/export` | GET | Export profiles as YAML |
| `/api/screener/profiles/import` | POST | Import profiles from YAML |
| `/api/screener/profiles/<id>/weights/adjust` | POST | Adjust profile weights |
| `/api/screener/profiles/init` | POST | Initialize default profiles |

**YAML Export/Import:**
```bash
# Export via API
curl http://localhost:5000/api/screener/profiles/export > screener_profiles.yaml

# Import via API
curl -X POST http://localhost:5000/api/screener/profiles/import \
  -H "Content-Type: text/yaml" \
  --data-binary @screener_profiles.yaml
```

### Feedback Loop

The system auto-adjusts profile weights based on daily report performance:
- Matches recommendations to actual gainers/losers
- Tracks win rate by attribution category
- Suggests weight adjustments weekly
- Can auto-apply within safety bounds (max 10% change per factor)

```bash
python3 -m screener.feedback_loop --daily        # Process today's report
python3 -m screener.feedback_loop --weekly --auto  # Run weekly optimization
```

### Scheduled Tasks

AI screener schedule (US/Eastern timezone):
- 4:00 AM - Morning screen
- 9:00 AM - 12:00 PM - Hourly midday updates
- 7:00 PM - Evening review

Data updater runs at 5:00 AM EST daily.

## Configuration

Environment variables (in `.env`):
```bash
MASSIVE_API_KEY=        # Polygon.io API key (required)
CLAUDE_API_KEY=         # Claude API key
OPENAI_API_KEY=         # ChatGPT API key
PERPLEXITY_API_KEY=     # Perplexity API key
FINVIZ_AUTH_KEY=        # Finviz Elite auth key (for CSV export API)
FINVIZ_SCREENER_URL=    # Custom Finviz screener URL (for filter extraction)
```

### Finviz Elite API

The system uses [Finviz Elite](https://finviz.com/elite) CSV export API for stock screening with rate limiting:

**Features:**
- Centralized client (`finviz_client.py`) handles all Finviz requests
- Exponential backoff with jitter on rate limiting (429 errors)
- Request caching (60s TTL) to avoid duplicate requests
- Thread-safe for concurrent operations
- Automatic retry on server errors (5xx)

**Rate Limit Configuration:**
- Minimum 1 second between requests
- Maximum backoff: 60 seconds
- Backoff multiplier: 2x (exponential)
- Maximum retries: 5

**Usage:**
```python
from finviz_client import get_finviz_client

client = get_finviz_client()
stocks = client.get_stocks(filters="sh_avgvol_o750,sh_price_u20", limit=30)
top_movers = client.get_top_movers(direction='up', top_n=10)
```

### Database

SQLite database `paper_trading.db` with tables:
- `account` - Cash and balance tracking
- `positions` - Current holdings
- `orders` - Order history
- `screener_profiles` - Multi-screener profile configurations
- `profile_runs` - Screening execution history
- `profile_performance` - Daily performance tracking per profile

### Flat Files Storage

```
market_data/
├── daily_bars/          # Compressed daily OHLCV files (.csv.gz)
│   └── daily_bars_YYYY-MM-DD.csv.gz
└── cache/               # Cached data for performance
```

Storage: ~500MB/year compressed. Each file contains all tickers for that trading day.

## Technology Stack

- **Trading**: backtrader 1.9.78
- **Data**: pandas 2.0.3, numpy 1.24.3
- **Market Data**: Polygon.io API (via requests)
- **Web Scraping**: BeautifulSoup4, lxml
- **Web Framework**: Flask 3.0.0, Flask-CORS
- **Scheduling**: schedule, pytz
- **Database**: SQLite3 (built-in), PostgreSQL (optional)

## Deployment

### Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CANARY                                  │
│                    (falcon-canary.service)                      │
│              Health monitoring & auto-recovery                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ monitors & restarts
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  falcon-trader  │    │falcon-feedback  │    │ falcon-screener │
│    .service     │    │  -loop.service  │    │   @*.service    │
│                 │    │                 │    │ (morning/midday │
│ Multi-strategy  │    │ Daily backtest  │    │   /evening)     │
│  orchestrator   │    │   analysis      │    │                 │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Database (SQLite/   │
                    │     PostgreSQL)       │
                    │  /var/lib/falcon/     │
                    └───────────────────────┘
```

### Systemd Services

| Service | Description | Resource Limits |
|---------|-------------|-----------------|
| `falcon-trader` | Main trading orchestrator | 2GB RAM, 75% CPU |
| `falcon-feedback-loop` | Daily performance analysis | 1GB RAM, 50% CPU |
| `falcon-screener@morning` | 4:00 AM ET screen | 1GB RAM, 50% CPU |
| `falcon-screener@midday` | 10:00 AM ET screen | 1GB RAM, 50% CPU |
| `falcon-screener@evening` | 7:00 PM ET screen | 1GB RAM, 50% CPU |
| `falcon-canary` | Health monitoring daemon | 256MB RAM, 10% CPU |

### Installation Paths (FHS-compliant)

```
/opt/falcon/              # Application code
/etc/falcon/              # Configuration
  └── falcon.env          # Environment variables
/var/lib/falcon/          # Data (database, state)
/var/log/falcon/          # Logs
/var/cache/falcon/        # Cache
```

### Service Management

```bash
# View all falcon services
systemctl list-units 'falcon-*' --all

# Start/stop/restart a service
sudo systemctl start falcon-trader
sudo systemctl stop falcon-trader
sudo systemctl restart falcon-trader

# View logs
sudo journalctl -u falcon-trader -f
sudo journalctl -u falcon-canary -n 50

# Enable/disable at boot
sudo systemctl enable falcon-canary
sudo systemctl disable falcon-canary
```

## Canary Health Monitoring

The canary system (`canary.py`) provides automated health monitoring and recovery.

### Features

- **Network monitoring**: Connectivity checks, IP validation
- **Service monitoring**: Systemd service status, HTTP health endpoints
- **Auto-recovery**: Service restarts, network repair (DHCP, interface reset)
- **Alerting**: Configurable alert command for notifications
- **State persistence**: Tracks failures and restart counts across runs

### Usage

```bash
# Check current status
python3 canary.py --status

# Run single check with repairs
python3 canary.py

# Run check without repairs
python3 canary.py --check-only

# Run as daemon (every 60 seconds)
python3 canary.py --daemon --interval 60

# JSON output
python3 canary.py --status --json
```

### Configuration

Environment variables in `/etc/falcon/falcon.env`:

```bash
# Network interface (leave empty for auto-detection)
FALCON_NETWORK_INTERFACE=

# Expected IP prefix for validation
FALCON_EXPECTED_IP_PREFIX=192.168.

# Optional alert command (receives: severity, message)
FALCON_ALERT_COMMAND=/opt/falcon/scripts/send_alert.sh
```

### Recovery Actions

| Issue | Action | Limits |
|-------|--------|--------|
| Service down | Restart via systemctl | Max 3 attempts, 5min cooldown |
| Network down | Interface restart → DHCP renewal | Max 3 attempts, 5min cooldown |
| Persistent failure | Send alert | After 3 consecutive failures |

## Database Schema

### SQLite/PostgreSQL Tables

#### `account`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| cash | DECIMAL(15,2) | Available cash |
| initial_balance | DECIMAL(15,2) | Starting balance |
| last_updated | TIMESTAMP | Last update time |

#### `positions`
| Column | Type | Description |
|--------|------|-------------|
| symbol | VARCHAR(20) | Ticker symbol (PK) |
| quantity | DECIMAL(15,4) | Shares held |
| entry_price | DECIMAL(15,2) | Average entry price |
| entry_date | TIMESTAMP | Position open date |
| stop_loss | DECIMAL(15,2) | Stop-loss price |
| last_updated | TIMESTAMP | Last update time |

#### `orders`
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| symbol | VARCHAR(20) | Ticker symbol |
| side | VARCHAR(10) | BUY or SELL |
| quantity | DECIMAL(15,4) | Order quantity |
| price | DECIMAL(15,2) | Execution price |
| timestamp | TIMESTAMP | Order time |
| pnl | DECIMAL(15,2) | Profit/loss (sells only) |
| strategy | VARCHAR(50) | Strategy name |

#### `performance`
| Column | Type | Description |
|--------|------|-------------|
| timestamp | TIMESTAMP | Record time (PK) |
| total_value | DECIMAL(15,2) | Total portfolio value |
| cash | DECIMAL(15,2) | Cash balance |
| positions_value | DECIMAL(15,2) | Value of holdings |

#### `screener_profiles`
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| name | VARCHAR(100) | Profile name (unique) |
| theme | VARCHAR(50) | momentum/earnings/seasonal |
| finviz_filters | JSONB | Finviz filter parameters |
| weights | JSONB | Scoring weights |
| enabled | BOOLEAN | Is profile active |
| performance_score | DECIMAL(5,4) | Historical accuracy |

### PostgreSQL Support

The system supports both SQLite (default) and PostgreSQL:

```bash
# Environment variables for PostgreSQL
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=falcon
DB_USER=falcon
DB_PASSWORD=your_password
```

PostgreSQL features:
- Connection pooling (1-10 connections)
- Automatic retry with exponential backoff (5 attempts, 1-30s delay)
- Health check and reconnection methods

## API Response Examples

### GET /api/account
```json
{
  "totalValue": 10523.45,
  "cash": 5234.12,
  "positionsValue": 5289.33,
  "initialBalance": 10000.0
}
```

### GET /api/positions
```json
[
  {
    "symbol": "AAPL",
    "quantity": 10,
    "avgPrice": 185.50,
    "currentPrice": 187.25,
    "stopLoss": 180.00
  }
]
```

### GET /api/trades/summary
```json
{
  "totalTrades": 45,
  "winningTrades": 28,
  "losingTrades": 17,
  "winRate": 62.2,
  "bestTrade": 523.40,
  "worstTrade": -187.20,
  "totalPnL": 1847.33
}
```

### GET /api/recommendations
```json
{
  "status": "success",
  "timestamp": "2026-02-05T09:15:00",
  "screen_type": "morning",
  "total_stocks_screened": 127,
  "recommendations": [
    {
      "symbol": "XYZ",
      "score": 0.85,
      "reasons": ["high relative volume", "breaking resistance"],
      "entry_price": 45.20,
      "target_price": 48.50
    }
  ]
}
```

### POST /api/order
Request:
```json
{
  "symbol": "AAPL",
  "side": "buy",
  "quantity": 10,
  "order_type": "market"
}
```
Response:
```json
{
  "status": "success",
  "order_id": 123,
  "symbol": "AAPL",
  "side": "buy",
  "quantity": 10,
  "filled_price": 185.50
}
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status and logs
sudo systemctl status falcon-trader
sudo journalctl -u falcon-trader -n 50 --no-pager

# Common issues:
# 1. Missing environment file
ls -la /etc/falcon/falcon.env

# 2. Wrong permissions
sudo chown -R falcon:falcon /opt/falcon /var/lib/falcon

# 3. Missing Python venv
ls -la /opt/falcon/venv/bin/python3
```

### Database Connection Errors

```bash
# SQLite: Check file permissions
ls -la /var/lib/falcon/paper_trading.db

# PostgreSQL: Test connection
psql -h localhost -U falcon -d falcon -c "SELECT 1"

# Check database type in config
grep DB_TYPE /etc/falcon/falcon.env
```

### Network Issues

```bash
# Check canary status
python3 /opt/falcon/canary.py --status

# Manual network check
ping -c 3 8.8.8.8
ip addr show

# Force network repair
python3 /opt/falcon/canary.py  # runs repair automatically
```

### API Not Responding

```bash
# Check if dashboard is running
curl http://localhost:5000/health

# Check port binding
ss -tlnp | grep 5000

# Restart dashboard
sudo systemctl restart falcon-dashboard
```

### Screener Not Finding Stocks

```bash
# Check API keys are set
grep -E '(CLAUDE|OPENAI|PERPLEXITY|FINVIZ)' /etc/falcon/falcon.env

# Run test screen
python3 ai_stock_screener.py --test

# Check screened_stocks.json
cat screened_stocks.json | python3 -m json.tool | head -50
```

### High Memory Usage

```bash
# Check service memory
systemctl status falcon-trader | grep Memory

# View resource limits
systemctl show falcon-trader | grep -E '(Memory|CPU)'

# Restart to clear memory
sudo systemctl restart falcon-trader
```

### Logs Location

| Log | Location |
|-----|----------|
| Service logs | `journalctl -u falcon-*` |
| Canary logs | `/var/log/falcon/canary.log` |
| Application logs | stdout → journald |

### Recovery Commands

```bash
# Full service restart
sudo systemctl restart falcon-trader falcon-feedback-loop

# Reinitialize database (CAUTION: loses data)
python3 db_manager.py --reset

# Force canary repair cycle
python3 /opt/falcon/canary.py

# Check all services health
systemctl list-units 'falcon-*' --state=failed
```
