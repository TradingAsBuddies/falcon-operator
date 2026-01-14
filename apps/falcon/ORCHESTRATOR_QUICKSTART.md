# Multi-Strategy Orchestrator - Quick Start Guide
**Get started building in 30 minutes**

---

## Prerequisites

- Python 3.8+
- Existing Falcon system installed
- Access to paper_trading.db
- AI screener running (generates screened_stocks.json)

---

## Quick Setup (5 minutes)

```bash
# Navigate to Falcon directory
cd /home/ospartners/src/falcon

# Create orchestrator structure
mkdir -p orchestrator/{engines,validators,routers,monitors,utils}
touch orchestrator/__init__.py
touch orchestrator/{engines,validators,routers,monitors,utils}/__init__.py

# Install dependencies
./backtest/bin/pip3 install pyyaml dataclasses-json

# Copy configuration template
cat > orchestrator/orchestrator_config.yaml << 'EOF'
# Multi-Strategy Orchestrator Configuration

routing:
  penny_stock_threshold: 5.0
  high_volatility_threshold: 0.30
  large_cap_threshold: 100000000000
  min_stop_loss_buffer: 0.05

strategy_mapping:
  penny_stocks: "momentum_breakout"
  etfs: "rsi_mean_reversion"
  high_volatility: "momentum_breakout"
  large_cap_stable: "rsi_mean_reversion"
  default: "rsi_mean_reversion"

etf_symbols:
  - SPY
  - QQQ
  - IWM
  - DIA

risk_management:
  max_position_size: 0.95
  max_positions: 10
  max_daily_loss: 0.05
EOF

echo "Setup complete!"
```

---

## Step 1: Create Data Structures (10 minutes)

**File:** `orchestrator/utils/data_structures.py`

```python
"""Data structures for Multi-Strategy Orchestrator"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class StockProfile:
    """Stock classification profile"""
    symbol: str
    price: float
    volatility: float = 0.0
    market_cap: float = 0.0
    sector: str = "UNKNOWN"
    is_etf: bool = False
    classification: str = "unknown"

@dataclass
class RoutingDecision:
    """Strategy routing decision"""
    symbol: str
    selected_strategy: str
    classification: str
    reason: str
    confidence: float
    timestamp: datetime
    profile: StockProfile

@dataclass
class Position:
    """Active position tracking"""
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    stop_loss: float
    profit_target: float
    strategy: str
    entry_timestamp: datetime
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0

    def update_current_price(self, price: float):
        """Update current price and recalculate P&L"""
        self.current_price = price
        self.unrealized_pnl = (price - self.entry_price) * self.quantity
        self.unrealized_pnl_pct = (price - self.entry_price) / self.entry_price
```

---

## Step 2: Create Stock Classifier (10 minutes)

**File:** `orchestrator/routers/stock_classifier.py`

```python
"""Stock classification for strategy routing"""
import yfinance as yf
from orchestrator.utils.data_structures import StockProfile

class StockClassifier:
    """Classify stocks for strategy routing"""

    def __init__(self, config: dict):
        self.config = config
        self.etf_list = config.get('etf_symbols', [])
        self.penny_threshold = config['routing']['penny_stock_threshold']

    def get_stock_profile(self, symbol: str) -> StockProfile:
        """Get complete stock profile"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period='1mo')

            # Get current price
            price = hist['Close'].iloc[-1] if len(hist) > 0 else 0.0

            # Calculate 30-day volatility (annualized)
            if len(hist) > 1:
                returns = hist['Close'].pct_change().dropna()
                volatility = returns.std() * (252 ** 0.5)  # Annualized
            else:
                volatility = 0.0

            # Get market cap
            market_cap = info.get('marketCap', 0)

            # Check if ETF
            is_etf = symbol in self.etf_list or info.get('quoteType') == 'ETF'

            # Classify
            classification = self._classify(price, volatility, market_cap, is_etf)

            return StockProfile(
                symbol=symbol,
                price=price,
                volatility=volatility,
                market_cap=market_cap,
                sector=info.get('sector', 'UNKNOWN'),
                is_etf=is_etf,
                classification=classification
            )

        except Exception as e:
            print(f"[ERROR] Failed to classify {symbol}: {e}")
            return StockProfile(symbol=symbol, price=0.0)

    def _classify(self, price: float, volatility: float, market_cap: float, is_etf: bool) -> str:
        """Classify stock type"""
        if is_etf:
            return "etf"
        elif price < self.penny_threshold:
            return "penny_stock"
        elif market_cap > 100e9:
            return "large_cap"
        elif market_cap > 10e9:
            return "mid_cap"
        else:
            return "small_cap"
```

---

## Step 3: Create Strategy Router (10 minutes)

**File:** `orchestrator/routers/strategy_router.py`

```python
"""Strategy routing logic"""
from datetime import datetime
from orchestrator.routers.stock_classifier import StockClassifier
from orchestrator.utils.data_structures import RoutingDecision

class StrategyRouter:
    """Route stocks to optimal strategies"""

    def __init__(self, config: dict):
        self.config = config
        self.classifier = StockClassifier(config)
        self.strategy_mapping = config['strategy_mapping']

    def route(self, symbol: str) -> RoutingDecision:
        """Route stock to optimal strategy"""
        # Get stock profile
        profile = self.classifier.get_stock_profile(symbol)

        # Select strategy based on classification
        strategy = self._select_strategy(profile)

        # Determine reason and confidence
        reason = self._get_routing_reason(profile, strategy)
        confidence = self._calculate_confidence(profile)

        return RoutingDecision(
            symbol=symbol,
            selected_strategy=strategy,
            classification=profile.classification,
            reason=reason,
            confidence=confidence,
            timestamp=datetime.now(),
            profile=profile
        )

    def _select_strategy(self, profile) -> str:
        """Select strategy based on profile"""
        # ETFs -> RSI Mean Reversion
        if profile.is_etf:
            return self.strategy_mapping.get('etfs', 'rsi_mean_reversion')

        # Penny stocks -> Momentum Breakout
        if profile.classification == "penny_stock":
            return self.strategy_mapping.get('penny_stocks', 'momentum_breakout')

        # High volatility -> Momentum Breakout
        threshold = self.config['routing']['high_volatility_threshold']
        if profile.volatility > threshold:
            return self.strategy_mapping.get('high_volatility', 'momentum_breakout')

        # Large cap stable -> RSI Mean Reversion
        if profile.classification == "large_cap" and profile.volatility < 0.25:
            return self.strategy_mapping.get('large_cap_stable', 'rsi_mean_reversion')

        # Default
        return self.strategy_mapping.get('default', 'rsi_mean_reversion')

    def _get_routing_reason(self, profile, strategy: str) -> str:
        """Generate human-readable routing reason"""
        if profile.is_etf:
            return f"ETF classification - using mean reversion"
        elif profile.classification == "penny_stock":
            return f"Penny stock (${profile.price:.2f}) - using momentum breakout"
        elif profile.volatility > 0.30:
            return f"High volatility ({profile.volatility:.1%}) - using momentum breakout"
        else:
            return f"Stable large-cap - using mean reversion"

    def _calculate_confidence(self, profile) -> float:
        """Calculate routing confidence (0.0 to 1.0)"""
        # High confidence for clear cases
        if profile.is_etf:
            return 0.95
        elif profile.classification == "penny_stock":
            return 0.90
        elif profile.volatility > 0.40:
            return 0.85
        else:
            return 0.75
```

---

## Step 4: Test Your Implementation (5 minutes)

**File:** `test_orchestrator.py`

```python
"""Quick test of orchestrator components"""
import yaml
from orchestrator.routers.strategy_router import StrategyRouter

# Load config
with open('orchestrator/orchestrator_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create router
router = StrategyRouter(config)

# Test routing
test_symbols = ['SPY', 'MU', 'ABTC', 'AAPL']

print("=" * 80)
print("MULTI-STRATEGY ORCHESTRATOR - ROUTING TEST")
print("=" * 80)

for symbol in test_symbols:
    print(f"\n{symbol}:")
    try:
        decision = router.route(symbol)
        print(f"  Strategy: {decision.selected_strategy}")
        print(f"  Classification: {decision.classification}")
        print(f"  Reason: {decision.reason}")
        print(f"  Confidence: {decision.confidence:.1%}")
        print(f"  Price: ${decision.profile.price:.2f}")
        print(f"  Volatility: {decision.profile.volatility:.1%}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
```

**Run the test:**
```bash
cd /home/ospartners/src/falcon
./backtest/bin/python3 test_orchestrator.py
```

**Expected Output:**
```
================================================================================
MULTI-STRATEGY ORCHESTRATOR - ROUTING TEST
================================================================================

SPY:
  Strategy: rsi_mean_reversion
  Classification: etf
  Reason: ETF classification - using mean reversion
  Confidence: 95.0%
  Price: $475.50
  Volatility: 12.5%

MU:
  Strategy: momentum_breakout
  Classification: large_cap
  Reason: High volatility (35.2%) - using momentum breakout
  Confidence: 85.0%
  Price: $95.50
  Volatility: 35.2%

ABTC:
  Strategy: momentum_breakout
  Classification: penny_stock
  Reason: Penny stock ($1.91) - using momentum breakout
  Confidence: 90.0%
  Price: $1.91
  Volatility: 45.8%

AAPL:
  Strategy: rsi_mean_reversion
  Classification: large_cap
  Reason: Stable large-cap - using mean reversion
  Confidence: 75.0%
  Price: $185.50
  Volatility: 22.3%

================================================================================
TEST COMPLETE
```

---

## Next Steps

Now that you have the core routing working, continue with:

### Phase 2: Entry Validation
**File:** `orchestrator/validators/entry_validator.py`
- Validate entries against AI screener recommendations
- Check stop-loss buffers
- Verify price ranges

### Phase 3: Strategy Engines
**File:** `orchestrator/engines/rsi_engine.py`
- Implement RSI mean reversion execution
- Connect to existing active_strategy.py logic
- Handle order placement

**File:** `orchestrator/engines/momentum_engine.py`
- Implement momentum breakout execution
- Use strategies/momentum_breakout_strategy.py
- Track positions

### Phase 4: Execution Manager
**File:** `orchestrator/execution_manager.py`
- Integrate with paper_trading.db
- Place orders via API
- Monitor positions

### Phase 5: Main Orchestrator
**File:** `orchestrator/main.py`
- Tie all components together
- Monitor AI screener for new stocks
- Execute trades via router
- Track performance

---

## Helpful Commands

```bash
# Run orchestrator
./backtest/bin/python3 orchestrator/main.py

# Run tests
./backtest/bin/python3 test_orchestrator.py

# Check logs
tail -f /var/log/falcon/orchestrator.log

# View configuration
cat orchestrator/orchestrator_config.yaml

# Check active positions
sqlite3 paper_trading.db "SELECT * FROM positions"

# View routing decisions
grep "ROUTING" /var/log/falcon/orchestrator.log | tail -20
```

---

## Troubleshooting

**Issue:** `ImportError: No module named 'yfinance'`
```bash
./backtest/bin/pip3 install yfinance
```

**Issue:** `FileNotFoundError: orchestrator_config.yaml`
```bash
# Create config from template (see Step 1)
```

**Issue:** `PermissionError` accessing database
```bash
# Check database permissions
ls -la paper_trading.db
chmod 664 paper_trading.db  # If needed
```

**Issue:** Router always selects default strategy
```bash
# Check that yfinance can fetch data
./backtest/bin/python3 -c "import yfinance as yf; print(yf.Ticker('SPY').info)"

# Check your internet connection
# Verify API limits not exceeded
```

---

## Architecture Overview

```
Your Build Path:

Week 1: Core (You are here!)
├── ✓ Data Structures
├── ✓ Stock Classifier
├── ✓ Strategy Router
└── ✓ Basic Testing

Week 2: Validation & Engines
├── Entry Validator
├── Safety Validator
├── RSI Engine
└── Momentum Engine

Week 3: Execution & Integration
├── Execution Manager
├── Database Integration
├── AI Screener Integration
└── Position Monitoring

Week 4: Deployment
├── Full System Testing
├── Performance Tracking
├── Monitoring Dashboard
└── Production Deployment
```

---

## Resources

- **Full Specification:** `MULTI_STRATEGY_ORCHESTRATOR_SPEC.md`
- **Exit Analysis:** `ACTIVE_STRATEGY_EXIT_ANALYSIS.md`
- **Strategy Comparison:** `EXIT_STRATEGY_COMPARISON.md`
- **Backtest Results:** `BACKTEST_RESULTS_SUMMARY.md`
- **Existing Strategies:** `strategies/` directory
- **Database Schema:** `init_database.py`

---

## Success Criteria

After completing this quick start, you should have:

- [x] Created orchestrator directory structure
- [x] Implemented data structures
- [x] Built stock classifier
- [x] Built strategy router
- [x] Tested routing on 4+ stocks
- [x] Verified routing decisions make sense

**Next:** Move to Phase 2 (Entry Validation) in the full specification.

---

*Quick Start Guide Version: 1.0*
*Estimated Time: 30 minutes*
*Difficulty: Intermediate*
*Prerequisites: Python, basic trading knowledge*
