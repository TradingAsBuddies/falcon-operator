# Adaptive Feedback System - Learning from Strategy Performance
**Continuous improvement through performance tracking and adaptive routing**

---

## Table of Contents
1. [Overview](#overview)
2. [Feedback Loop Architecture](#feedback-loop-architecture)
3. [Performance Tracking](#performance-tracking)
4. [Routing Decision Analysis](#routing-decision-analysis)
5. [Adaptive Routing Rules](#adaptive-routing-rules)
6. [Strategy Performance Scoring](#strategy-performance-scoring)
7. [A/B Testing Framework](#ab-testing-framework)
8. [Machine Learning Integration](#machine-learning-integration-optional)
9. [Implementation](#implementation)

---

## Overview

The feedback loop continuously monitors strategy performance and adapts routing decisions to maximize returns. It learns which strategies work best for different stock characteristics and adjusts routing rules accordingly.

### Key Principles

1. **Track Everything** - Record every routing decision and outcome
2. **Measure Performance** - Quantify strategy success by stock type
3. **Learn Patterns** - Identify which strategies work for which stocks
4. **Adapt Rules** - Adjust routing logic based on evidence
5. **Validate Changes** - A/B test rule modifications before full deployment

### Feedback Loop Cycle

```
┌─────────────────────────────────────────────────────────────┐
│                    FEEDBACK LOOP CYCLE                       │
│                                                              │
│  1. ROUTING DECISION                                         │
│     ├── Classify stock (penny, large cap, etc.)            │
│     ├── Select strategy (RSI, Momentum, etc.)              │
│     └── Log decision with confidence score                  │
│                          │                                   │
│                          ▼                                   │
│  2. TRADE EXECUTION                                          │
│     ├── Place order via selected strategy                   │
│     ├── Track entry price, stop-loss, target               │
│     └── Monitor position lifecycle                          │
│                          │                                   │
│                          ▼                                   │
│  3. OUTCOME TRACKING                                         │
│     ├── Record exit price and P&L                           │
│     ├── Calculate hold time and exit reason                 │
│     └── Store complete trade record                         │
│                          │                                   │
│                          ▼                                   │
│  4. PERFORMANCE ANALYSIS                                     │
│     ├── Aggregate results by strategy + stock type          │
│     ├── Calculate win rate, avg return, Sharpe             │
│     └── Compare actual vs expected performance              │
│                          │                                   │
│                          ▼                                   │
│  5. PATTERN RECOGNITION                                      │
│     ├── Identify successful routing patterns                │
│     ├── Detect failing strategy-stock combinations          │
│     └── Discover edge cases and outliers                    │
│                          │                                   │
│                          ▼                                   │
│  6. RULE ADAPTATION                                          │
│     ├── Adjust routing thresholds                           │
│     ├── Modify strategy selection logic                     │
│     └── Update confidence scoring                           │
│                          │                                   │
│                          ▼                                   │
│  7. VALIDATION                                               │
│     ├── A/B test new rules vs current                       │
│     ├── Backtest proposed changes                           │
│     └── Monitor for improvement                             │
│                          │                                   │
│                          └──────────► Back to Step 1        │
└─────────────────────────────────────────────────────────────┘
```

---

## Feedback Loop Architecture

### Component Overview

```
┌──────────────────────────────────────────────────────────────┐
│                  FEEDBACK SYSTEM COMPONENTS                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        1. DECISION TRACKER                           │   │
│  │  - Records every routing decision                    │   │
│  │  - Logs stock characteristics at decision time       │   │
│  │  - Stores confidence scores and reasoning            │   │
│  └────────────────┬────────────────────────────────────┘   │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────┐   │
│  │        2. OUTCOME RECORDER                          │   │
│  │  - Tracks trade execution and lifecycle             │   │
│  │  - Records final P&L and exit reason                │   │
│  │  - Links outcome back to original decision          │   │
│  └────────────────┬────────────────────────────────────┘   │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────┐   │
│  │        3. PERFORMANCE ANALYZER                      │   │
│  │  - Aggregates results by strategy + stock type      │   │
│  │  - Calculates performance metrics                   │   │
│  │  - Identifies patterns and anomalies                │   │
│  └────────────────┬────────────────────────────────────┘   │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────┐   │
│  │        4. RULE OPTIMIZER                            │   │
│  │  - Proposes routing rule adjustments                │   │
│  │  - Tests changes via backtesting                    │   │
│  │  - Deploys validated improvements                   │   │
│  └────────────────┬────────────────────────────────────┘   │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────┐   │
│  │        5. STRATEGY SCORER                           │   │
│  │  - Maintains live strategy performance scores       │   │
│  │  - Adjusts confidence by stock type                 │   │
│  │  - Disables consistently failing strategies         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Performance Tracking

### Database Schema Extensions

**New Table: `routing_decisions`**
```sql
CREATE TABLE routing_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT UNIQUE NOT NULL,
    timestamp DATETIME NOT NULL,

    -- Stock Information
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    volatility REAL,
    market_cap REAL,
    sector TEXT,
    is_etf BOOLEAN,
    classification TEXT,  -- "penny_stock", "large_cap", etc.

    -- Routing Decision
    selected_strategy TEXT NOT NULL,
    confidence REAL NOT NULL,  -- 0.0 to 1.0
    reason TEXT,

    -- Alternative Strategies Considered
    alternatives TEXT,  -- JSON: [{"strategy": "momentum", "score": 0.75}, ...]

    -- AI Screener Context
    ai_entry_range TEXT,
    ai_target REAL,
    ai_stop_loss REAL,
    ai_confidence TEXT,

    -- Trade Link (populated after execution)
    trade_id INTEGER,

    FOREIGN KEY (trade_id) REFERENCES trades(id)
);
```

**New Table: `trades`**
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Basic Info
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,

    -- Entry
    entry_timestamp DATETIME NOT NULL,
    entry_price REAL NOT NULL,
    quantity INTEGER NOT NULL,

    -- Exit
    exit_timestamp DATETIME,
    exit_price REAL,
    exit_reason TEXT,  -- "profit_target", "stop_loss", "rsi_exit", "time_limit"

    -- Performance
    hold_duration_seconds INTEGER,
    pnl REAL,
    pnl_pct REAL,

    -- Context
    entry_rsi REAL,
    exit_rsi REAL,
    max_favorable_excursion REAL,  -- Best price reached
    max_adverse_excursion REAL,    -- Worst price reached

    -- Links
    decision_id TEXT,
    order_entry_id INTEGER,
    order_exit_id INTEGER,

    FOREIGN KEY (decision_id) REFERENCES routing_decisions(decision_id),
    FOREIGN KEY (order_entry_id) REFERENCES orders(id),
    FOREIGN KEY (order_exit_id) REFERENCES orders(id)
);
```

**New Table: `strategy_performance`**
```sql
CREATE TABLE strategy_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Grouping
    strategy TEXT NOT NULL,
    stock_classification TEXT NOT NULL,  -- "penny_stock", "large_cap", etc.
    time_period TEXT NOT NULL,  -- "daily", "weekly", "monthly", "all_time"
    period_start DATETIME NOT NULL,
    period_end DATETIME NOT NULL,

    -- Performance Metrics
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    win_rate REAL NOT NULL,

    avg_return REAL NOT NULL,
    total_return REAL NOT NULL,
    sharpe_ratio REAL,
    max_drawdown REAL,

    avg_hold_duration_seconds INTEGER,

    -- Comparison
    expected_performance REAL,  -- From backtests
    actual_vs_expected REAL,    -- Actual / Expected

    -- Confidence Adjustment
    routing_confidence REAL,  -- Adjusted confidence for this combo

    updated_at DATETIME NOT NULL
);
```

### Performance Recorder Implementation

```python
class PerformanceRecorder:
    """Records and tracks all routing decisions and outcomes"""

    def record_decision(self, decision: RoutingDecision) -> str:
        """Record a routing decision"""
        decision_id = f"DEC-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{decision.symbol}"

        self.db.execute("""
            INSERT INTO routing_decisions (
                decision_id, timestamp, symbol, price, volatility, market_cap,
                sector, is_etf, classification, selected_strategy, confidence,
                reason, ai_entry_range, ai_target, ai_stop_loss
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision_id,
            decision.timestamp,
            decision.symbol,
            decision.profile.price,
            decision.profile.volatility,
            decision.profile.market_cap,
            decision.profile.sector,
            decision.profile.is_etf,
            decision.classification,
            decision.selected_strategy,
            decision.confidence,
            decision.reason,
            # ... AI screener data
        ))

        return decision_id

    def record_trade_entry(self, decision_id: str, order: Order) -> int:
        """Record trade entry"""
        trade_id = self.db.execute("""
            INSERT INTO trades (
                symbol, strategy, entry_timestamp, entry_price,
                quantity, decision_id, order_entry_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            order.symbol,
            order.strategy,
            order.timestamp,
            order.executed_price,
            order.quantity,
            decision_id,
            order.order_id
        ))

        # Link decision to trade
        self.db.execute("""
            UPDATE routing_decisions
            SET trade_id = ?
            WHERE decision_id = ?
        """, (trade_id, decision_id))

        return trade_id

    def record_trade_exit(self, trade_id: int, exit_order: Order, exit_reason: str):
        """Record trade exit and calculate final metrics"""
        # Get trade entry info
        trade = self.db.execute("""
            SELECT * FROM trades WHERE id = ?
        """, (trade_id,), fetch='one')

        # Calculate metrics
        hold_duration = (exit_order.timestamp - trade['entry_timestamp']).total_seconds()
        pnl = (exit_order.executed_price - trade['entry_price']) * trade['quantity']
        pnl_pct = (exit_order.executed_price - trade['entry_price']) / trade['entry_price']

        # Update trade record
        self.db.execute("""
            UPDATE trades
            SET exit_timestamp = ?,
                exit_price = ?,
                exit_reason = ?,
                hold_duration_seconds = ?,
                pnl = ?,
                pnl_pct = ?,
                order_exit_id = ?
            WHERE id = ?
        """, (
            exit_order.timestamp,
            exit_order.executed_price,
            exit_reason,
            hold_duration,
            pnl,
            pnl_pct,
            exit_order.order_id,
            trade_id
        ))

        # Trigger performance analysis
        self.trigger_performance_update(trade)
```

---

## Routing Decision Analysis

### Performance Analyzer

```python
class PerformanceAnalyzer:
    """Analyzes strategy performance by stock type"""

    def analyze_strategy_performance(self, strategy: str, classification: str,
                                    time_period: str = "all_time") -> dict:
        """
        Analyze how a strategy performs on a stock classification

        Returns metrics like win rate, avg return, Sharpe ratio
        """

        # Get all completed trades for this strategy + classification
        trades = self.db.execute("""
            SELECT t.*, rd.classification
            FROM trades t
            JOIN routing_decisions rd ON t.decision_id = rd.decision_id
            WHERE t.strategy = ?
              AND rd.classification = ?
              AND t.exit_timestamp IS NOT NULL
              AND t.exit_timestamp >= ?
        """, (strategy, classification, self._get_period_start(time_period)))

        if not trades:
            return {"error": "No trades found"}

        # Calculate metrics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['pnl'] > 0)
        win_rate = winning_trades / total_trades

        returns = [t['pnl_pct'] for t in trades]
        avg_return = sum(returns) / len(returns)
        total_return = sum(returns)

        sharpe_ratio = self._calculate_sharpe(returns)
        max_drawdown = self._calculate_max_drawdown(trades)

        avg_hold = sum(t['hold_duration_seconds'] for t in trades) / total_trades

        return {
            'strategy': strategy,
            'classification': classification,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_hold_seconds': avg_hold
        }

    def compare_to_baseline(self, strategy: str, classification: str) -> dict:
        """
        Compare strategy performance to expected baseline (from backtests)
        """
        actual = self.analyze_strategy_performance(strategy, classification)
        expected = self.get_backtest_baseline(strategy, classification)

        return {
            'actual_return': actual['avg_return'],
            'expected_return': expected['avg_return'],
            'delta': actual['avg_return'] - expected['avg_return'],
            'performance_ratio': actual['avg_return'] / expected['avg_return'] if expected['avg_return'] != 0 else 0,
            'verdict': 'OUTPERFORMING' if actual['avg_return'] > expected['avg_return'] else 'UNDERPERFORMING'
        }

    def identify_misrouted_trades(self) -> list:
        """
        Identify trades where a different strategy would have performed better

        This is done by comparing actual outcome to what other strategies
        achieved on similar stocks in the same time period
        """

        misrouted = []

        # Get all completed trades
        trades = self.db.execute("""
            SELECT t.*, rd.*
            FROM trades t
            JOIN routing_decisions rd ON t.decision_id = rd.decision_id
            WHERE t.exit_timestamp IS NOT NULL
        """)

        for trade in trades:
            # Find similar stocks traded with different strategies
            alternatives = self._find_alternative_outcomes(
                symbol=trade['symbol'],
                classification=trade['classification'],
                time_period=(trade['entry_timestamp'], trade['exit_timestamp'])
            )

            # Did an alternative strategy perform better?
            for alt in alternatives:
                if alt['avg_return'] > trade['pnl_pct'] * 1.5:  # 50% better
                    misrouted.append({
                        'trade_id': trade['id'],
                        'symbol': trade['symbol'],
                        'actual_strategy': trade['strategy'],
                        'actual_return': trade['pnl_pct'],
                        'better_strategy': alt['strategy'],
                        'better_return': alt['avg_return'],
                        'opportunity_cost': alt['avg_return'] - trade['pnl_pct']
                    })

        return misrouted
```

---

## Adaptive Routing Rules

### Rule Optimizer

```python
class RuleOptimizer:
    """
    Optimizes routing rules based on performance feedback
    """

    def __init__(self, analyzer: PerformanceAnalyzer):
        self.analyzer = analyzer
        self.current_rules = self.load_current_rules()

    def propose_rule_adjustments(self) -> list:
        """
        Analyze performance and propose routing rule adjustments

        Returns list of proposed changes with supporting evidence
        """
        proposals = []

        # 1. Check if any strategy is underperforming on a classification
        for strategy in ['rsi_mean_reversion', 'momentum_breakout', 'bollinger']:
            for classification in ['penny_stock', 'large_cap', 'mid_cap', 'etf']:
                perf = self.analyzer.analyze_strategy_performance(strategy, classification)

                if perf.get('total_trades', 0) < 5:
                    continue  # Need more data

                # If win rate < 50%, consider disabling this routing
                if perf.get('win_rate', 0) < 0.50:
                    proposals.append({
                        'type': 'DISABLE_ROUTING',
                        'strategy': strategy,
                        'classification': classification,
                        'reason': f"Win rate only {perf['win_rate']:.1%} (< 50%)",
                        'evidence': perf,
                        'priority': 'HIGH'
                    })

                # If significantly outperforming, increase confidence
                baseline = self.analyzer.compare_to_baseline(strategy, classification)
                if baseline.get('performance_ratio', 0) > 1.5:  # 50% better than expected
                    proposals.append({
                        'type': 'INCREASE_CONFIDENCE',
                        'strategy': strategy,
                        'classification': classification,
                        'reason': f"Outperforming by {(baseline['performance_ratio'] - 1) * 100:.0f}%",
                        'evidence': baseline,
                        'priority': 'MEDIUM'
                    })

        # 2. Check for misrouted trades
        misrouted = self.analyzer.identify_misrouted_trades()
        if len(misrouted) > 10:  # Pattern of misrouting
            # Group by classification
            by_classification = {}
            for mr in misrouted:
                classification = mr['classification']
                better_strategy = mr['better_strategy']
                key = (classification, better_strategy)
                by_classification[key] = by_classification.get(key, 0) + 1

            # If consistently misrouting a classification
            for (classification, better_strategy), count in by_classification.items():
                if count >= 5:
                    proposals.append({
                        'type': 'CHANGE_DEFAULT_STRATEGY',
                        'classification': classification,
                        'new_strategy': better_strategy,
                        'reason': f"{count} trades would have performed better with {better_strategy}",
                        'evidence': misrouted,
                        'priority': 'HIGH'
                    })

        # 3. Adjust thresholds based on actual stock characteristics
        threshold_adjustments = self._analyze_threshold_effectiveness()
        proposals.extend(threshold_adjustments)

        return sorted(proposals, key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}[x['priority']])

    def apply_rule_adjustment(self, proposal: dict, validate: bool = True):
        """
        Apply a proposed rule adjustment

        If validate=True, will A/B test before full deployment
        """
        if validate:
            # Test the change via backtesting first
            test_result = self.backtest_rule_change(proposal)

            if test_result['improvement'] < 0.05:  # Less than 5% improvement
                print(f"Rejecting proposal: Only {test_result['improvement']:.1%} improvement")
                return False

        # Apply the change
        if proposal['type'] == 'DISABLE_ROUTING':
            self._disable_routing(proposal['strategy'], proposal['classification'])

        elif proposal['type'] == 'INCREASE_CONFIDENCE':
            self._adjust_confidence(proposal['strategy'], proposal['classification'], +0.10)

        elif proposal['type'] == 'CHANGE_DEFAULT_STRATEGY':
            self._change_default_strategy(proposal['classification'], proposal['new_strategy'])

        # Log the change
        self._log_rule_change(proposal)

        return True

    def backtest_rule_change(self, proposal: dict) -> dict:
        """
        Backtest a proposed rule change on historical data

        Returns expected improvement metrics
        """
        # Get historical routing decisions
        historical = self.db.execute("""
            SELECT * FROM routing_decisions
            WHERE timestamp >= date('now', '-90 days')
        """)

        current_performance = 0
        proposed_performance = 0

        for decision in historical:
            # What was the actual outcome?
            actual_trade = self._get_trade_outcome(decision['decision_id'])
            if actual_trade:
                current_performance += actual_trade['pnl_pct']

            # What would the outcome be with proposed rule?
            proposed_strategy = self._apply_proposed_rule(decision, proposal)
            if proposed_strategy != decision['selected_strategy']:
                # Find similar trades with proposed strategy
                similar_outcome = self._estimate_outcome(
                    decision['symbol'],
                    decision['classification'],
                    proposed_strategy
                )
                proposed_performance += similar_outcome
            else:
                proposed_performance += actual_trade['pnl_pct']

        improvement = (proposed_performance - current_performance) / len(historical)

        return {
            'current_performance': current_performance / len(historical),
            'proposed_performance': proposed_performance / len(historical),
            'improvement': improvement,
            'verdict': 'APPROVE' if improvement > 0.05 else 'REJECT'
        }
```

---

## Strategy Performance Scoring

### Dynamic Confidence Adjustment

```python
class StrategyScorer:
    """
    Maintains live strategy performance scores
    Adjusts routing confidence based on recent performance
    """

    def __init__(self):
        self.base_confidence = {
            ('rsi_mean_reversion', 'etf'): 0.95,
            ('rsi_mean_reversion', 'large_cap'): 0.75,
            ('momentum_breakout', 'penny_stock'): 0.90,
            ('momentum_breakout', 'high_volatility'): 0.85,
            # ... etc
        }

        self.performance_multipliers = {}

    def get_adjusted_confidence(self, strategy: str, classification: str) -> float:
        """
        Get confidence score adjusted by recent performance
        """
        base = self.base_confidence.get((strategy, classification), 0.50)

        # Get recent performance (last 30 days)
        recent_perf = self.analyzer.analyze_strategy_performance(
            strategy, classification, time_period='30_days'
        )

        if recent_perf.get('total_trades', 0) < 3:
            return base  # Not enough data, use base

        # Adjust based on win rate
        win_rate = recent_perf.get('win_rate', 0.50)

        if win_rate > 0.80:
            multiplier = 1.10  # +10% confidence
        elif win_rate > 0.70:
            multiplier = 1.05  # +5% confidence
        elif win_rate < 0.40:
            multiplier = 0.70  # -30% confidence (warning)
        elif win_rate < 0.50:
            multiplier = 0.85  # -15% confidence
        else:
            multiplier = 1.00  # No adjustment

        # Adjust based on return vs expected
        baseline = self.analyzer.compare_to_baseline(strategy, classification)
        if baseline.get('performance_ratio', 1.0) > 1.20:
            multiplier *= 1.05  # Additional +5% for outperformance
        elif baseline.get('performance_ratio', 1.0) < 0.80:
            multiplier *= 0.90  # Additional -10% for underperformance

        adjusted = base * multiplier

        # Cache the multiplier
        self.performance_multipliers[(strategy, classification)] = multiplier

        return min(max(adjusted, 0.10), 0.99)  # Clamp between 10% and 99%

    def should_disable_strategy(self, strategy: str, classification: str) -> bool:
        """
        Determine if a strategy should be disabled for a classification
        """
        confidence = self.get_adjusted_confidence(strategy, classification)

        if confidence < 0.30:  # Very low confidence
            recent = self.analyzer.analyze_strategy_performance(
                strategy, classification, time_period='30_days'
            )

            # Disable if:
            # - Low confidence AND
            # - At least 5 recent trades AND
            # - Win rate < 40%
            if recent.get('total_trades', 0) >= 5 and recent.get('win_rate', 1.0) < 0.40:
                return True

        return False
```

---

## A/B Testing Framework

### Controlled Experimentation

```python
class ABTestingFramework:
    """
    A/B test routing rule changes before full deployment
    """

    def create_ab_test(self, test_name: str, control_rule: dict,
                       variant_rule: dict, duration_days: int = 30) -> str:
        """
        Create an A/B test to compare routing rules

        Example:
        - Control: penny_stock → momentum_breakout
        - Variant: penny_stock → rsi_mean_reversion (proposed change)
        """
        test_id = f"TEST-{datetime.now().strftime('%Y%m%d')}-{test_name}"

        self.db.execute("""
            INSERT INTO ab_tests (
                test_id, test_name, control_rule, variant_rule,
                start_date, end_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            test_id,
            test_name,
            json.dumps(control_rule),
            json.dumps(variant_rule),
            datetime.now(),
            datetime.now() + timedelta(days=duration_days),
            'ACTIVE'
        ))

        return test_id

    def route_with_ab_test(self, decision: RoutingDecision, test_id: str) -> str:
        """
        Route using A/B test (50/50 split)
        """
        test = self._get_ab_test(test_id)

        # Random 50/50 assignment
        import random
        variant = 'A' if random.random() < 0.5 else 'B'

        if variant == 'A':
            strategy = test['control_rule']['strategy']
        else:
            strategy = test['variant_rule']['strategy']

        # Record assignment
        self.db.execute("""
            INSERT INTO ab_test_assignments (
                test_id, decision_id, variant, assigned_strategy
            ) VALUES (?, ?, ?, ?)
        """, (test_id, decision.decision_id, variant, strategy))

        return strategy

    def analyze_ab_test(self, test_id: str) -> dict:
        """
        Analyze A/B test results
        """
        # Get all trades from this test
        results = self.db.execute("""
            SELECT ata.variant, t.*
            FROM ab_test_assignments ata
            JOIN routing_decisions rd ON ata.decision_id = rd.decision_id
            JOIN trades t ON rd.trade_id = t.id
            WHERE ata.test_id = ?
              AND t.exit_timestamp IS NOT NULL
        """, (test_id,))

        # Split by variant
        variant_a = [r for r in results if r['variant'] == 'A']
        variant_b = [r for r in results if r['variant'] == 'B']

        # Calculate metrics
        a_return = sum(t['pnl_pct'] for t in variant_a) / len(variant_a) if variant_a else 0
        b_return = sum(t['pnl_pct'] for t in variant_b) / len(variant_b) if variant_b else 0

        a_win_rate = sum(1 for t in variant_a if t['pnl'] > 0) / len(variant_a) if variant_a else 0
        b_win_rate = sum(1 for t in variant_b if t['pnl'] > 0) / len(variant_b) if variant_b else 0

        # Statistical significance
        p_value = self._calculate_p_value(
            [t['pnl_pct'] for t in variant_a],
            [t['pnl_pct'] for t in variant_b]
        )

        return {
            'test_id': test_id,
            'variant_a': {
                'trades': len(variant_a),
                'avg_return': a_return,
                'win_rate': a_win_rate
            },
            'variant_b': {
                'trades': len(variant_b),
                'avg_return': b_return,
                'win_rate': b_win_rate
            },
            'winner': 'B' if b_return > a_return else 'A',
            'improvement': abs(b_return - a_return),
            'p_value': p_value,
            'is_significant': p_value < 0.05,
            'recommendation': 'DEPLOY_VARIANT_B' if (b_return > a_return and p_value < 0.05) else 'KEEP_CONTROL'
        }
```

---

## Machine Learning Integration (Optional)

### ML-Based Strategy Selection

```python
class MLStrategySelector:
    """
    Optional: Use machine learning to predict optimal strategy

    This is an advanced feature that learns from historical data
    to predict which strategy will perform best for a given stock
    """

    def __init__(self):
        self.model = None
        self.feature_columns = [
            'price', 'volatility', 'market_cap', 'avg_volume',
            'rsi_14', 'rsi_30', 'bb_position', 'trend_strength'
        ]

    def train_model(self):
        """
        Train ML model on historical routing decisions and outcomes
        """
        from sklearn.ensemble import RandomForestClassifier

        # Get training data
        training_data = self.db.execute("""
            SELECT rd.*, t.pnl_pct, t.pnl
            FROM routing_decisions rd
            JOIN trades t ON rd.trade_id = t.id
            WHERE t.exit_timestamp IS NOT NULL
        """)

        # Prepare features and labels
        X = []
        y = []

        for row in training_data:
            features = [
                row['price'],
                row['volatility'],
                row['market_cap'],
                # ... calculate other features
            ]

            # Label: 1 if this strategy was profitable, 0 otherwise
            label = 1 if row['pnl'] > 0 else 0

            X.append(features)
            y.append(label)

        # Train model
        self.model = RandomForestClassifier(n_estimators=100)
        self.model.fit(X, y)

        # Evaluate
        accuracy = self.model.score(X, y)
        print(f"Model accuracy: {accuracy:.2%}")

    def predict_best_strategy(self, profile: StockProfile) -> tuple:
        """
        Use ML model to predict which strategy will perform best

        Returns: (strategy_name, confidence_score)
        """
        if not self.model:
            raise ValueError("Model not trained")

        # Calculate features
        features = [
            profile.price,
            profile.volatility,
            profile.market_cap,
            # ... other features
        ]

        # Get predictions for each strategy
        strategies = ['rsi_mean_reversion', 'momentum_breakout', 'bollinger']
        predictions = {}

        for strategy in strategies:
            # Predict probability of success
            prob = self.model.predict_proba([features])[0][1]
            predictions[strategy] = prob

        # Select best strategy
        best_strategy = max(predictions, key=predictions.get)
        confidence = predictions[best_strategy]

        return (best_strategy, confidence)
```

---

## Implementation Example

### Complete Feedback Loop

```python
from orchestrator.routers.strategy_router import StrategyRouter
from orchestrator.performance_recorder import PerformanceRecorder
from orchestrator.performance_analyzer import PerformanceAnalyzer
from orchestrator.rule_optimizer import RuleOptimizer
from orchestrator.strategy_scorer import StrategyScorer

class AdaptiveOrchestrator:
    """
    Orchestrator with adaptive feedback loop
    """

    def __init__(self, config):
        self.router = StrategyRouter(config)
        self.recorder = PerformanceRecorder()
        self.analyzer = PerformanceAnalyzer()
        self.optimizer = RuleOptimizer(self.analyzer)
        self.scorer = StrategyScorer()

        # Start background tasks
        self.start_feedback_loop()

    def start_feedback_loop(self):
        """Start continuous feedback loop"""
        import schedule

        # Hourly: Update performance metrics
        schedule.every().hour.do(self.update_performance_metrics)

        # Daily: Analyze and propose adjustments
        schedule.every().day.at("22:00").do(self.daily_optimization)

        # Weekly: Review and apply approved changes
        schedule.every().sunday.at("23:00").do(self.weekly_review)

    def process_stock_with_feedback(self, symbol: str):
        """
        Process a stock with full feedback loop integration
        """
        # 1. Get routing decision with dynamic confidence
        decision = self.router.route(symbol)

        # 2. Adjust confidence based on recent performance
        adjusted_confidence = self.scorer.get_adjusted_confidence(
            decision.selected_strategy,
            decision.classification
        )
        decision.confidence = adjusted_confidence

        # 3. Check if strategy should be disabled
        if self.scorer.should_disable_strategy(decision.selected_strategy, decision.classification):
            print(f"[WARNING] {decision.selected_strategy} disabled for {decision.classification}")
            # Fall back to alternative strategy
            decision.selected_strategy = self._get_fallback_strategy(decision.classification)
            decision.reason += " (Primary strategy disabled due to poor performance)"

        # 4. Record decision
        decision_id = self.recorder.record_decision(decision)

        # 5. Execute trade (if valid)
        if self.validate_entry(symbol, decision):
            trade_id = self.execute_trade(decision, decision_id)

            # 6. Monitor position and record outcome when closed
            self.monitor_position(trade_id, decision_id)

        return decision

    def update_performance_metrics(self):
        """Hourly update of performance metrics"""
        print("[FEEDBACK] Updating performance metrics...")

        # Update strategy performance tables
        strategies = ['rsi_mean_reversion', 'momentum_breakout', 'bollinger']
        classifications = ['penny_stock', 'large_cap', 'mid_cap', 'etf']

        for strategy in strategies:
            for classification in classifications:
                perf = self.analyzer.analyze_strategy_performance(
                    strategy, classification, time_period='30_days'
                )

                if perf.get('total_trades', 0) > 0:
                    self._update_performance_table(strategy, classification, perf)

    def daily_optimization(self):
        """Daily analysis and optimization"""
        print("[FEEDBACK] Running daily optimization...")

        # Get proposed rule adjustments
        proposals = self.optimizer.propose_rule_adjustments()

        if proposals:
            print(f"[FEEDBACK] Found {len(proposals)} proposed adjustments:")
            for p in proposals:
                print(f"  - {p['type']}: {p['reason']} (Priority: {p['priority']})")

            # Auto-apply high-priority proposals
            for proposal in proposals:
                if proposal['priority'] == 'HIGH':
                    success = self.optimizer.apply_rule_adjustment(proposal, validate=True)
                    if success:
                        print(f"[FEEDBACK] Applied: {proposal['type']}")

    def weekly_review(self):
        """Weekly comprehensive review"""
        print("[FEEDBACK] Running weekly review...")

        # Generate performance report
        report = self.generate_weekly_report()

        # Check for misrouted trades
        misrouted = self.analyzer.identify_misrouted_trades()
        if len(misrouted) > 10:
            print(f"[FEEDBACK] WARNING: {len(misrouted)} potentially misrouted trades")

        # Review A/B tests
        active_tests = self._get_active_ab_tests()
        for test in active_tests:
            results = self.ab_tester.analyze_ab_test(test['test_id'])
            if results['is_significant']:
                print(f"[FEEDBACK] A/B Test {test['test_id']}: {results['recommendation']}")
```

---

## Summary

### Feedback Loop Components

1. **Decision Tracking** - Record every routing decision with context
2. **Outcome Recording** - Link decisions to actual trade outcomes
3. **Performance Analysis** - Aggregate and analyze by strategy + stock type
4. **Pattern Recognition** - Identify what works and what doesn't
5. **Rule Optimization** - Propose and validate improvements
6. **Adaptive Confidence** - Adjust routing confidence based on performance
7. **A/B Testing** - Test changes before full deployment
8. **Continuous Learning** - Improve over time automatically

### Key Metrics Tracked

- **Per Strategy-Classification:** Win rate, avg return, Sharpe ratio
- **Routing Accuracy:** % of optimal decisions
- **Misrouting Cost:** Opportunity cost of wrong strategy
- **Performance vs Baseline:** Actual vs expected performance
- **Confidence Calibration:** Are high-confidence decisions actually better?

### Adaptation Mechanisms

1. **Disable Poor Performers** - Auto-disable strategy+classification combos with <40% win rate
2. **Boost High Performers** - Increase confidence for outperformers
3. **Adjust Thresholds** - Modify volatility/price thresholds based on evidence
4. **Change Defaults** - Update default strategy for classifications
5. **Learn New Patterns** - Discover edge cases and special scenarios

### Expected Timeline

- **Week 1-2:** Basic tracking (decisions + outcomes)
- **Week 3-4:** Performance analysis and reporting
- **Month 2:** Adaptive confidence adjustments
- **Month 3:** Automated rule optimization
- **Month 4+:** ML integration (optional)

---

*Adaptive Feedback System Specification*
*Version: 1.0*
*Date: January 8, 2026*
*Status: Ready for Implementation*
