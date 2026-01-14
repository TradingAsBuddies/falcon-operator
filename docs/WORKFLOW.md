# Falcon Trading Platform - Workflow

## Core Tenets

1. **Research Strategies** - Find and analyze trading strategies
2. **Backtest Strategies** - Validate against historical data
3. **Paper Trade Intraday** - Test with simulated trades
4. **Improve Incrementally** - Continuously refine

---

## 1. Research Strategies

### Sources
- YouTube trading channels (parsed via `youtube_strategies.py`)
- Finviz screener patterns
- AI agent analysis (Claude, ChatGPT, Perplexity)
- Technical analysis patterns

### Current Strategies (in `apps/falcon/strategies/`)
| Strategy | Type | Description |
|----------|------|-------------|
| `one_candle_strategy.py` | Momentum | Single candle breakout patterns |
| `momentum_breakout_strategy.py` | Momentum | Breakout detection |
| `bollinger_mean_reversion_strategy.py` | Mean Reversion | Bollinger band bounces |
| `macd_momentum_strategy.py` | Trend | MACD crossover signals |
| `moving_average_crossover_strategy.py` | Trend | MA crossover |
| `balanced_rsi_strategy.py` | Oscillator | RSI with position sizing |
| `improved_rsi_strategy.py` | Oscillator | Enhanced RSI |
| `hybrid_multi_indicator_strategy.py` | Multi | Combined indicators |

### How to Add New Strategies
1. Research strategy logic
2. Create strategy file in `strategies/` following the template
3. Run validation: `python3 strategy_manager.py validate -f strategies/new_strategy.py`

---

## 2. Backtest Strategies

### Quick Backtest
```bash
# From falcon-compute
cd ~/src/falcon

# Backtest specific strategy
python3 backtest_one_candle.py

# Backtest all strategies
python3 backtest_all_strategies.py

# Backtest with specific ticker
python3 strategy_manager.py backtest -f strategies/momentum_breakout_strategy.py --ticker SPY --days 180
```

### Backtest Results
Results are stored in:
- `backtest_results.json` - Latest results
- Various `*_BACKTEST_RESULTS.md` files - Detailed analysis

### Data Available
- Daily bars: July 2025 - January 2026 (6+ months)
- Intraday bars: November 2025 - January 2026

---

## 3. Paper Trade Intraday

### Services Running
| Service | Purpose |
|---------|---------|
| `dashboard_server.py` | Web UI and API |
| `run_orchestrator.py` | Trade execution |
| `ai_stock_screener.py` | Stock screening |
| `stop_loss_monitor.py` | Risk management |
| `strategy_orchestrator.py` | Strategy management |

### Access Dashboard
- HTTP: http://192.168.1.162
- HTTPS: https://192.168.1.162

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/positions` | GET | Current positions |
| `/api/orders` | GET | Order history |
| `/api/account` | GET | Account balance |
| `/api/screener/results` | GET | Screened stocks |
| `/api/strategy` | GET | Current strategy |

### Start Paper Trading
```bash
# One candle strategy
python3 paper_trade_one_candle.py

# General paper trading
python3 paper_trading_bot.py
```

---

## 4. Improve Incrementally

### Strategy Improvement Cycle
```
Research → Backtest → Deploy → Monitor → Analyze → Improve
    ↑                                                  │
    └──────────────────────────────────────────────────┘
```

### Validation Gates
Before deploying any strategy change:
1. **Syntax validation** - Valid Python
2. **Structure validation** - Has required Strategy class
3. **Security validation** - No dangerous imports
4. **Backtest validation** - Return > -10%, Drawdown < 30%
5. **Git commit** - Version controlled

### Deploy Improved Strategy
```bash
# Validate first
python3 strategy_manager.py validate -f strategies/improved_strategy.py

# Run backtest
python3 strategy_manager.py backtest -f strategies/improved_strategy.py

# Deploy (only if backtest passes)
python3 strategy_manager.py deploy -f strategies/improved_strategy.py

# Rollback if needed
python3 strategy_manager.py rollback
```

### Metrics to Track
- Win rate
- Profit factor
- Max drawdown
- Sharpe ratio
- Average trade duration

---

## Control Node Commands

From `falcon-operator/`:

```bash
# Check status
./deploy/status.sh

# Sync code changes
./deploy/sync.sh

# Restart services
./deploy/restart-services.sh

# View logs
./deploy/logs.sh all --follow
./deploy/logs.sh dashboard --follow

# Backup database
./deploy/backup-db.sh
```

---

## Database

### PostgreSQL (falcon-db: 192.168.1.194)
- `trading` - Main trading data
- `finviz` - Screening data (filings, news, outcomes, picks, scans)

### SQLite (falcon-compute: paper_trading.db)
- `account` - Cash and balance
- `positions` - Current holdings
- `orders` - Order history
