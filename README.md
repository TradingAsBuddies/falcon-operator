# Falcon Operator

Trading platform orchestration and control center for a distributed Raspberry Pi cluster.

## Core Tenets

1. **Research Strategies** - Find and analyze trading strategies
2. **Backtest Strategies** - Validate against historical data
3. **Paper Trade Intraday** - Test with simulated trades
4. **Improve Incrementally** - Continuously refine the process

See [docs/WORKFLOW.md](docs/WORKFLOW.md) for detailed workflow documentation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FALCON TRADING PLATFORM                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │  falcon-control  │  │    falcon-db     │  │  falcon-compute  │      │
│  │    (this Pi)     │  │  192.168.1.194   │  │  192.168.1.162   │      │
│  │                  │  │                  │  │                  │      │
│  │  • Orchestration │  │  • PostgreSQL    │  │  • Dashboard     │      │
│  │  • Code storage  │  │  • trading db    │  │  • Screener      │      │
│  │  • Backups       │  │  • finviz db     │  │  • Orchestrator  │      │
│  │  • 235GB NVMe    │  │  • 28GB SD       │  │  • Stop-loss     │      │
│  │                  │  │                  │  │  • nginx proxy   │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Hosts

| Alias | Hostname | IP | User | Role | Storage |
|-------|----------|-----|------|------|---------|
| falcon-control | raspberrypi | localhost | davdunc | Orchestration | 235GB NVMe (208GB free) |
| falcon-db | lake-raspbian | 192.168.1.194 | ospartners | Database | 28GB SD (20GB free) |
| falcon-compute | raspberrypi | 192.168.1.162 | ospartners | Compute/Web | 28GB SD (9.5GB free) |

## Running Services

### falcon-compute (192.168.1.162)

| Service | Script | Port | Description |
|---------|--------|------|-------------|
| Dashboard | `dashboard_server.py` | 5000 | Flask web UI |
| Orchestrator | `run_orchestrator.py` | - | Trade orchestration |
| Strategy Orchestrator | `strategy_orchestrator.py` | - | Strategy management (runs as `falcon` user) |
| AI Screener | `ai_stock_screener.py` | - | Stock screening |
| Stop-Loss Monitor | `stop_loss_monitor.py` | - | Position monitoring |
| nginx | - | 80/443 | Reverse proxy to Flask |

### falcon-db (192.168.1.194)

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Database server |

## Databases

### trading (PostgreSQL)
Main trading database. Owner: `davdunc`, access granted to `falcon` user.

### finviz (PostgreSQL)
Stock screening data with tables:
- `filings` - SEC filings
- `news` - News articles
- `outcomes` - Trade outcomes
- `picks` - Stock picks
- `scans` - Screening results

## Directory Structure

```
falcon-operator/
├── README.md
├── inventory/
│   └── hosts.yaml           # Host definitions
├── apps/
│   └── falcon/              # Main trading application (synced)
│       ├── dashboard_server.py
│       ├── ai_stock_screener.py
│       ├── run_orchestrator.py
│       ├── stop_loss_monitor.py
│       ├── strategies/      # Trading strategies
│       ├── orchestrator/    # Orchestration modules
│       └── ...
├── deploy/
│   └── sync.sh              # Deploy changes to compute node
├── backups/                 # Database backups
├── logs/                    # Aggregated logs
├── docs/                    # Documentation
└── scripts/
    └── discover.sh          # Discovery script
```

## Quick Start

### Sync code to compute node
```bash
./deploy/sync.sh
```

### View running services
```bash
ssh ospartners@192.168.1.162 "ps aux | grep python"
```

### Check dashboard
```bash
curl http://192.168.1.162/health
```

### Access web UI
Open: http://192.168.1.162 or https://192.168.1.162

## GitHub Repository

- **URL**: https://github.com/davdunc/falcon
- **Branch**: development
- **Status**: Has uncommitted changes

## Trading Strategies

Located in `apps/falcon/strategies/`:
- `one_candle_strategy.py` - One candle momentum
- `momentum_breakout_strategy.py` - Breakout detection
- `bollinger_mean_reversion_strategy.py` - Mean reversion
- `rsi_strategy.py` - RSI-based
- `macd_momentum_strategy.py` - MACD crossover
- `moving_average_crossover_strategy.py` - MA crossover
- `hybrid_multi_indicator_strategy.py` - Multi-indicator
