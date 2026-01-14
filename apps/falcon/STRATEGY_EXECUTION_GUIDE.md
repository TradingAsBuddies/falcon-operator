# Falcon Automated Strategy Execution System

## Overview

The Falcon Strategy Execution System is a complete automated trading platform that:
- Converts YouTube strategy descriptions into executable code using Claude AI
- Executes multiple strategies in parallel with real-time market data
- Tracks performance per-strategy with detailed metrics
- Automatically optimizes underperforming strategies using AI
- Auto-deploys improved strategies when they backtest better

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Strategy Orchestrator                         │
│                  (Main Integration Layer)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                 ┌────────────┼────────────┐
                 │            │            │
        ┌────────▼────┐  ┌───▼─────┐  ┌──▼──────────┐
        │ Paper       │  │Strategy │  │  Strategy   │
        │ Trading Bot │  │Executor │  │  Optimizer  │
        └─────────────┘  └─────────┘  └─────────────┘
                │            │              │
                └────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │   Strategy      │
                    │   Analytics     │
                    └─────────────────┘
                             │
                    ┌────────▼────────┐
                    │    Database     │
                    │  (5 new tables) │
                    └─────────────────┘
```

## Components

### 1. Database Schema (`init_strategy_tables.py`)

Creates 5 tables:
- **active_strategies**: Strategies being executed
- **strategy_trades**: Links trades to strategies
- **strategy_performance**: Per-strategy metrics
- **strategy_signals**: Signal history for debugging
- **strategy_optimizations**: AI optimization history

**Usage:**
```bash
python3 init_strategy_tables.py
# Or specify database path:
python3 init_strategy_tables.py /var/lib/falcon/paper_trading.db
```

### 2. Strategy Parser (`strategy_parser.py`)

Converts YouTube strategy text into executable backtrader code using Claude AI.

**Features:**
- Extracts indicators, parameters, entry/exit conditions from text
- Generates complete backtrader Strategy class
- Validates code with StrategyManager
- Self-corrects errors using AI (up to 3 attempts)

**Usage:**
```python
from strategy_parser import StrategyCodeGenerator

generator = StrategyCodeGenerator(claude_api_key)

# Convert YouTube strategy to code
youtube_strategy = {
    'title': 'RSI Mean Reversion',
    'entry_rules': 'Buy when RSI < 30',
    'exit_rules': 'Sell when RSI > 70 or after 5 days',
    'risk_management': '10% position size, 2% stop loss'
}

success, code, error = generator.generate_from_youtube_strategy(youtube_strategy)
```

### 3. Enhanced Paper Trading Bot (`paper_trading_bot.py`)

Modified to support strategy attribution.

**New Methods:**
- `place_order_with_strategy()`: Links trades to strategies
- `_log_strategy_signal()`: Records signals in database

### 4. Strategy Executor (`strategy_executor.py`)

Multi-strategy execution engine that runs strategies in parallel.

**Features:**
- Loads active strategies from database
- Evaluates signals for all strategies
- Performance-weighted allocation: `weight = win_rate × signal_confidence`
- Background thread for continuous monitoring
- Position tracking per strategy

**Usage:**
```python
from strategy_executor import StrategyExecutor

executor = StrategyExecutor(paper_trading_bot, update_interval=60)
executor.start()
```

### 5. Strategy Analytics (`strategy_analytics.py`)

Comprehensive performance tracking.

**Metrics:**
- Win rate, profit factor, ROI
- Max drawdown, current drawdown
- Consecutive losses (for optimization trigger)

**Optimization Triggers:**
- 5 consecutive losses
- Win rate < 40% (with min 20 trades)
- Drawdown > 15%
- Negative P&L over 20+ trades

**Usage:**
```python
from strategy_analytics import StrategyAnalytics

analytics = StrategyAnalytics()
analytics.update_strategy_performance(strategy_id)

# Check if needs optimization
should_optimize, reason = analytics.check_optimization_triggers(strategy_id)

# Get leaderboard
leaderboard = analytics.get_all_strategies_leaderboard()
```

### 6. Strategy Optimizer (`strategy_optimizer.py`)

AI-driven strategy improvement with auto-deployment.

**Workflow:**
1. Monitor strategies for optimization triggers
2. Use Claude to analyze performance and suggest improvements
3. Generate improved code
4. Backtest old vs new versions
5. Auto-deploy if improvement >= threshold (default 5%)
6. Record in strategy_optimizations table

**Usage:**
```python
from strategy_optimizer import StrategyOptimizer

optimizer = StrategyOptimizer(claude_api_key, improvement_threshold=0.05)

# Optimize single strategy
success, message = optimizer.optimize_strategy(strategy_id)

# Monitor all strategies
optimizer.monitor_and_optimize()
```

### 7. Strategy Orchestrator (`strategy_orchestrator.py`)

Main entry point that integrates all components.

**Features:**
- Initializes all components with proper configuration
- Starts PaperTradingBot and StrategyExecutor
- Periodic status monitoring (every 5 minutes)
- Periodic optimization cycles (every hour)
- Graceful shutdown with signal handling

**Usage:**
```bash
# Set environment variables
export MASSIVE_API_KEY=your_polygon_api_key
export CLAUDE_API_KEY=your_claude_api_key

# Run orchestrator
python3 strategy_orchestrator.py
```

**Environment Variables:**
- `MASSIVE_API_KEY`: Polygon.io API key (required)
- `CLAUDE_API_KEY`: Claude API key (required)
- `TRADING_SYMBOLS`: Comma-separated symbols (default: SPY,QQQ,AAPL)
- `INITIAL_BALANCE`: Starting balance (default: 10000)
- `UPDATE_INTERVAL`: Seconds between evaluations (default: 60)

### 8. Dashboard API Endpoints (`dashboard_server.py`)

REST API for strategy management.

#### Activate YouTube Strategy
```bash
POST /api/strategies/youtube/<youtube_strategy_id>/activate
Content-Type: application/json

{
  "symbols": ["SPY", "QQQ"],
  "allocation_pct": 20.0
}

Response:
{
  "status": "success",
  "strategy_id": 1,
  "backtest_results": {...}
}
```

#### List Active Strategies
```bash
GET /api/strategies/active

Response:
{
  "status": "success",
  "strategies": [
    {
      "strategy_id": 1,
      "strategy_name": "RSI Mean Reversion",
      "status": "active",
      "allocation_pct": 20.0,
      "performance": {...}
    }
  ]
}
```

#### Get Strategy Performance
```bash
GET /api/strategies/<strategy_id>/performance

Response:
{
  "status": "success",
  "summary": {
    "performance": {
      "win_rate": 0.65,
      "total_pnl": 1250.50,
      "profit_factor": 1.8
    },
    "recent_trades": [...]
  }
}
```

#### Pause/Resume Strategy
```bash
POST /api/strategies/<strategy_id>/pause
POST /api/strategies/<strategy_id>/resume
```

#### Get Strategy Signals
```bash
GET /api/strategies/<strategy_id>/signals

Response:
{
  "status": "success",
  "signals": [
    {
      "symbol": "SPY",
      "signal_type": "buy",
      "confidence": 0.85,
      "market_price": 450.25,
      "timestamp": "2025-01-07T10:30:00"
    }
  ]
}
```

#### Strategy Leaderboard
```bash
GET /api/strategies/leaderboard

Response:
{
  "status": "success",
  "leaderboard": [
    {
      "strategy_id": 1,
      "strategy_name": "RSI Mean Reversion",
      "performance": {
        "win_rate": 0.72,
        "total_pnl": 2500.00
      }
    }
  ]
}
```

#### Aggregate Statistics
```bash
GET /api/strategies/aggregate

Response:
{
  "status": "success",
  "statistics": {
    "total_strategies": 3,
    "total_trades": 45,
    "total_pnl": 3250.50,
    "avg_win_rate": 0.68
  }
}
```

## Complete Workflow

### 1. Setup
```bash
# Initialize database tables
python3 init_strategy_tables.py /var/lib/falcon/paper_trading.db

# Verify tables created
sqlite3 /var/lib/falcon/paper_trading.db ".tables"
```

### 2. Add YouTube Strategy (via API)
```bash
# Extract strategy from YouTube video
curl -X POST http://localhost:5000/api/youtube-strategies/submit \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://youtube.com/watch?v=..."}'

# Response: {"strategy_id": 1}
```

### 3. Activate Strategy for Live Trading
```bash
# Activate with custom symbols and allocation
curl -X POST http://localhost:5000/api/strategies/youtube/1/activate \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["SPY", "QQQ", "AAPL"],
    "allocation_pct": 25.0
  }'

# Response includes backtest results and new strategy_id
```

### 4. Run the System
```bash
# Start orchestrator (runs all components)
python3 strategy_orchestrator.py
```

The system will now:
- Monitor market data for all tracked symbols
- Evaluate all active strategies every 60 seconds
- Generate signals when conditions are met
- Execute trades with performance-weighted allocation
- Track performance per strategy
- Check for optimization triggers every hour
- Auto-optimize and deploy improved strategies

### 5. Monitor via Dashboard
```bash
# View active strategies
curl http://localhost:5000/api/strategies/active

# View leaderboard
curl http://localhost:5000/api/strategies/leaderboard

# View specific strategy performance
curl http://localhost:5000/api/strategies/1/performance

# View recent signals
curl http://localhost:5000/api/strategies/1/signals
```

## Performance-Weighted Allocation

The system uses a sophisticated allocation algorithm:

```
For each signal:
  weight = strategy_win_rate × signal_confidence
  allocation = (weight / total_weight) × available_cash
  quantity = allocation / price
```

**Example:**
- Strategy A: 70% win rate, signal confidence 0.9 → weight = 0.63
- Strategy B: 50% win rate, signal confidence 0.8 → weight = 0.40
- Available cash: $10,000

Strategy A gets: (0.63 / 1.03) × $10,000 = $6,116
Strategy B gets: (0.40 / 1.03) × $10,000 = $3,883

## Optimization System

### Triggers
1. **5 consecutive losses** → Immediate optimization
2. **Win rate < 40%** (min 20 trades) → Needs improvement
3. **Drawdown > 15%** → Risk management issue
4. **Negative P&L** (min 20 trades) → Fundamental problem

### Process
1. **Analyze**: Claude examines code, performance, recent trades
2. **Suggest**: AI proposes specific improvements (parameters, conditions, filters)
3. **Generate**: Create improved code based on suggestions
4. **Validate**: Ensure code is syntactically valid and safe
5. **Backtest**: Compare old vs new on 365 days of data
6. **Deploy**: If improvement >= 5%, auto-deploy
7. **Record**: Save optimization history in database

### Optimization History
```python
from strategy_optimizer import StrategyOptimizer

optimizer = StrategyOptimizer(claude_api_key)
history = optimizer.get_optimization_history(strategy_id)

# View all optimizations for a strategy
for opt in history:
    print(f"Optimization #{opt['id']}")
    print(f"  Type: {opt['optimization_type']}")
    print(f"  Improvement: {opt['improvement_pct']:.1%}")
    print(f"  Deployed: {opt['deployed']}")
    print(f"  Date: {opt['created_at']}")
```

## Testing

### Test Individual Components
```bash
# Test analytics
python3 strategy_analytics.py

# Test optimizer (requires CLAUDE_API_KEY)
CLAUDE_API_KEY=your_key python3 strategy_optimizer.py

# Test executor (requires MASSIVE_API_KEY)
MASSIVE_API_KEY=your_key python3 strategy_executor.py
```

### Test Full System
```bash
# 1. Initialize database
python3 init_strategy_tables.py

# 2. Start dashboard (in separate terminal)
python3 dashboard_server.py

# 3. Add test strategy
curl -X POST http://localhost:5000/api/strategies/youtube/1/activate \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["SPY"], "allocation_pct": 100.0}'

# 4. Start orchestrator
python3 strategy_orchestrator.py

# System will now run the strategy and track performance
```

## Configuration

### Database Location
- Production: `/var/lib/falcon/paper_trading.db`
- Development: `./paper_trading.db`

### Update Intervals
- **Market data**: 60 seconds (configurable via `update_interval`)
- **Strategy evaluation**: 60 seconds (same as market data)
- **Status monitoring**: 5 minutes
- **Optimization cycles**: 1 hour

### Performance Thresholds
- **Auto-deploy threshold**: 5% improvement (configurable)
- **Backtest rejection**: < -5% return
- **Max drawdown limit**: 30% (in StrategyManager)

## File Locations

### Source Files
```
/home/ospartners/src/falcon/
├── init_strategy_tables.py      # Database schema
├── strategy_parser.py            # AI code generation
├── paper_trading_bot.py          # Enhanced bot
├── strategy_executor.py          # Multi-strategy engine
├── strategy_analytics.py         # Performance tracking
├── strategy_optimizer.py         # AI optimization
├── strategy_orchestrator.py      # Main integration
└── dashboard_server.py           # REST API
```

### Installation
```
/opt/falcon/
└── (all .py files copied here)
```

### Data
```
/var/lib/falcon/
└── paper_trading.db             # Main database
```

## Dependencies

All dependencies should already be installed from `requirements.txt`. New addition:
```bash
pip3 install anthropic --break-system-packages
```

## Troubleshooting

### Database Permission Error
```bash
# Fix: Run with sudo or change ownership
sudo chown $USER:$USER /var/lib/falcon/paper_trading.db
```

### Strategy Not Generating Signals
```bash
# Check strategy is active
sqlite3 /var/lib/falcon/paper_trading.db "SELECT * FROM active_strategies WHERE status='active'"

# Check recent signals
curl http://localhost:5000/api/strategies/1/signals
```

### Optimization Not Triggering
```bash
# Check performance metrics
curl http://localhost:5000/api/strategies/1/performance

# Manually trigger optimization
python3 -c "
from strategy_optimizer import StrategyOptimizer
import os
optimizer = StrategyOptimizer(os.getenv('CLAUDE_API_KEY'))
optimizer.monitor_and_optimize()
"
```

## Next Steps (Phase 2)

Future enhancements:
- Advanced multi-strategy coordination (conflict resolution)
- Portfolio optimization algorithms
- Machine learning for parameter tuning
- Strategy marketplace and community features
- Real-time visualization dashboard
- Backtesting on multiple timeframes
- Integration with additional data sources

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u falcon-trading -f`
2. Review database: `sqlite3 /var/lib/falcon/paper_trading.db`
3. Test components individually (see Testing section)

## License

Part of the Falcon Trading System
