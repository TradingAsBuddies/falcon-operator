#!/usr/bin/env python3
"""
Strategy Optimizer - AI-Driven Strategy Improvement
Monitors strategy performance and uses Claude to optimize underperformers
"""

import json
import anthropic
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from db_manager import DatabaseManager
from strategy_manager import StrategyManager
from strategy_analytics import StrategyAnalytics


class StrategyOptimizer:
    """AI-driven strategy optimization with auto-deployment"""

    def __init__(self, claude_api_key: str,
                 db_path: str = "/var/lib/falcon/paper_trading.db",
                 improvement_threshold: float = 0.05):
        """
        Initialize strategy optimizer

        Args:
            claude_api_key: Claude API key for AI optimization
            db_path: Database path
            improvement_threshold: Minimum improvement % to auto-deploy (default 5%)
        """
        self.client = anthropic.Anthropic(api_key=claude_api_key)
        self.db = DatabaseManager({'db_path': db_path, 'db_type': 'sqlite'})
        self.strategy_manager = StrategyManager()
        self.analytics = StrategyAnalytics(db_path)
        self.improvement_threshold = improvement_threshold

        print(f"[OPTIMIZER] Initialized (threshold: {improvement_threshold:.1%})")

    def _get_strategy(self, strategy_id: int) -> Optional[Dict]:
        """Get strategy from database"""
        strategy = self.db.execute(
            "SELECT * FROM active_strategies WHERE id = %s",
            (strategy_id,),
            fetch='one'
        )
        return dict(strategy) if strategy else None

    def _format_trades_for_ai(self, trades: List[Dict], limit: int = 20) -> str:
        """
        Format recent trades for Claude analysis

        Args:
            trades: List of trades
            limit: Max trades to include

        Returns:
            Formatted string
        """
        if not trades:
            return "No trades yet"

        recent = trades[-limit:]
        output = []

        for i, trade in enumerate(recent, 1):
            output.append(
                f"{i}. {trade['side'].upper()} {trade['quantity']} {trade['symbol']} "
                f"@ ${trade['price']:.2f} - "
                f"P&L: ${trade['pnl']:.2f} - "
                f"Reason: {trade['signal_reason']}"
            )

        return "\n".join(output)

    def _get_ai_suggestions(self, strategy: Dict, performance: Dict,
                           trades: List[Dict]) -> Dict:
        """
        Use Claude to analyze and suggest improvements

        Args:
            strategy: Strategy dict from database
            performance: Performance metrics
            trades: List of trades

        Returns:
            Dict with analysis and suggestions
        """
        prompt = f"""You are an expert trading strategy optimizer. Analyze this underperforming strategy and suggest specific improvements.

STRATEGY NAME: {strategy['strategy_name']}

CURRENT CODE:
```python
{strategy['strategy_code']}
```

PERFORMANCE METRICS:
- Total trades: {performance.get('total_trades', 0)}
- Win rate: {performance.get('win_rate', 0):.1%}
- Total P&L: ${performance.get('total_pnl', 0):.2f}
- Profit factor: {performance.get('profit_factor', 0):.2f}
- Consecutive losses: {performance.get('consecutive_losses', 0)}
- Max drawdown: {performance.get('max_drawdown', 0):.1%}
- ROI: {performance.get('roi_pct', 0):.1%}

RECENT TRADES (last 20):
{self._format_trades_for_ai(trades)}

ANALYSIS REQUIRED:
1. Identify the core issues causing poor performance
2. Suggest 2-3 specific code improvements:
   - Parameter adjustments (e.g., RSI thresholds)
   - Additional filters or conditions
   - Risk management improvements
   - Entry/exit logic refinements

3. Provide the reasoning for each change

Return your analysis in JSON format:
{{
    "analysis": "Brief analysis of why strategy is underperforming (2-3 sentences)",
    "issues": ["Issue 1", "Issue 2", "Issue 3"],
    "improvements": [
        {{
            "type": "parameter_change",
            "description": "Adjust RSI buy threshold from 30 to 25",
            "reasoning": "Strategy missing good entry points",
            "code_change": "specific parameter or condition to modify"
        }},
        {{
            "type": "add_condition",
            "description": "Add volume filter",
            "reasoning": "Many false signals on low volume",
            "code_change": "specific condition to add"
        }}
    ],
    "expected_improvement": "Estimated improvement (e.g., '10-15% better win rate')"
}}

Return ONLY the JSON object, no other text."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response.content[0].text

            # Extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                suggestions = json.loads(json_match.group())
                print(f"[OPTIMIZER] AI analysis complete")
                return suggestions
            else:
                raise ValueError("Could not extract JSON from Claude response")

        except Exception as e:
            print(f"[OPTIMIZER] Error getting AI suggestions: {e}")
            return {
                'analysis': 'Error analyzing strategy',
                'issues': [],
                'improvements': [],
                'expected_improvement': 'Unknown'
            }

    def _apply_suggestions(self, original_code: str, suggestions: Dict) -> str:
        """
        Apply AI suggestions to generate improved code

        Args:
            original_code: Current strategy code
            suggestions: Suggestions from _get_ai_suggestions()

        Returns:
            Improved code
        """
        # Build prompt with suggestions
        improvements_text = "\n".join([
            f"- {imp['description']}: {imp['reasoning']}"
            for imp in suggestions.get('improvements', [])
        ])

        prompt = f"""Apply these improvements to the trading strategy code.

ORIGINAL CODE:
```python
{original_code}
```

IMPROVEMENTS TO APPLY:
{improvements_text}

DETAILED CHANGES:
{json.dumps(suggestions.get('improvements', []), indent=2)}

Generate the improved strategy code. Make sure:
1. All improvements are applied correctly
2. Code is syntactically valid Python
3. Maintains backtrader Strategy structure
4. Includes all necessary imports
5. Preserves any good aspects of the original

Return ONLY the complete improved Python code, no explanations."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response.content[0].text

            # Extract code
            import re
            code_match = re.search(r'```python\n([\s\S]*?)\n```', content)
            if code_match:
                improved_code = code_match.group(1)
                print(f"[OPTIMIZER] Applied improvements to code")
                return improved_code
            else:
                # If no code block, assume entire response is code
                print(f"[OPTIMIZER] Using full response as code")
                return content.strip()

        except Exception as e:
            print(f"[OPTIMIZER] Error applying suggestions: {e}")
            return original_code

    def _record_optimization(self, strategy_id: int, old_code: str, new_code: str,
                            ai_reasoning: str, old_results: Dict, new_results: Dict,
                            improvement: float) -> int:
        """
        Record optimization in database

        Args:
            strategy_id: Strategy ID
            old_code: Original code
            new_code: Improved code
            ai_reasoning: AI analysis
            old_results: Old backtest results
            new_results: New backtest results
            improvement: Improvement percentage

        Returns:
            Optimization ID
        """
        try:
            self.db.execute(
                """INSERT INTO strategy_optimizations
                   (strategy_id, optimization_type, old_code, new_code,
                    ai_reasoning, backtest_old_results, backtest_new_results,
                    improvement_pct, deployed, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (strategy_id, 'performance_trigger', old_code, new_code,
                 ai_reasoning, json.dumps(old_results), json.dumps(new_results),
                 improvement, False, datetime.now().isoformat())
            )

            # Get ID
            result = self.db.execute(
                "SELECT id FROM strategy_optimizations ORDER BY id DESC LIMIT 1",
                fetch='one'
            )

            return result['id'] if result else None

        except Exception as e:
            print(f"[OPTIMIZER] Error recording optimization: {e}")
            return None

    def _deploy_optimization(self, strategy_id: int, new_code: str, opt_id: int):
        """
        Deploy optimized strategy

        Args:
            strategy_id: Strategy ID
            new_code: Improved code
            opt_id: Optimization ID
        """
        try:
            # Update strategy code
            self.db.execute(
                """UPDATE active_strategies
                   SET strategy_code = %s,
                       evolution_note = %s,
                       parent_strategy_id = %s
                   WHERE id = %s""",
                (new_code,
                 f"AI optimization #{opt_id} deployed at {datetime.now().isoformat()}",
                 strategy_id,  # Self-reference for tracking
                 strategy_id)
            )

            # Mark optimization as deployed
            self.db.execute(
                "UPDATE strategy_optimizations SET deployed = 1, deployed_at = %s WHERE id = %s",
                (datetime.now().isoformat(), opt_id)
            )

            print(f"[OPTIMIZER] Deployed optimization #{opt_id} for strategy {strategy_id}")

        except Exception as e:
            print(f"[OPTIMIZER] Error deploying optimization: {e}")

    def optimize_strategy(self, strategy_id: int) -> Tuple[bool, str]:
        """
        Full optimization workflow for a single strategy

        Process:
        1. Analyze current performance
        2. Use Claude to suggest improvements
        3. Generate new strategy code
        4. Backtest old vs new
        5. If >threshold improvement, auto-deploy
        6. Record in strategy_optimizations table

        Args:
            strategy_id: Strategy ID to optimize

        Returns:
            Tuple of (success, message)
        """
        try:
            print(f"\n[OPTIMIZER] Starting optimization for strategy {strategy_id}")

            # Get strategy and performance data
            strategy = self._get_strategy(strategy_id)
            if not strategy:
                return False, "Strategy not found"

            perf = self.analytics._get_performance(strategy_id)
            if not perf:
                return False, "No performance data available"

            trades = self.analytics._get_strategy_trades(strategy_id)

            print(f"[OPTIMIZER] Strategy: {strategy['strategy_name']}")
            print(f"[OPTIMIZER] Performance: {perf['win_rate']:.1%} win rate, "
                  f"${perf['total_pnl']:.2f} P&L")

            # Ask Claude for optimization suggestions
            print(f"[OPTIMIZER] Requesting AI analysis...")
            suggestions = self._get_ai_suggestions(strategy, perf, trades)

            print(f"[OPTIMIZER] AI Analysis: {suggestions.get('analysis', 'N/A')}")
            print(f"[OPTIMIZER] Issues found: {len(suggestions.get('issues', []))}")
            print(f"[OPTIMIZER] Improvements proposed: {len(suggestions.get('improvements', []))}")

            # Generate improved strategy
            print(f"[OPTIMIZER] Generating improved code...")
            improved_code = self._apply_suggestions(strategy['strategy_code'], suggestions)

            # Validate
            print(f"[OPTIMIZER] Validating improved code...")
            valid, validation_results = self.strategy_manager.validate_strategy(improved_code)
            if not valid:
                error_msg = validation_results.get('error', 'Unknown validation error')
                print(f"[OPTIMIZER] Generated invalid code: {error_msg}")
                return False, f"Generated invalid code: {error_msg}"

            print(f"[OPTIMIZER] Code validation passed")

            # Backtest both versions
            symbols = json.loads(strategy['symbols'])
            ticker = symbols[0] if symbols else 'SPY'

            print(f"[OPTIMIZER] Backtesting original code on {ticker}...")
            old_plot, old_results = self.strategy_manager.run_backtest(
                strategy['strategy_code'], ticker=ticker, days=365
            )

            print(f"[OPTIMIZER] Backtesting improved code on {ticker}...")
            new_plot, new_results = self.strategy_manager.run_backtest(
                improved_code, ticker=ticker, days=365
            )

            # Calculate improvement
            old_return = old_results.get('return_pct', 0)
            new_return = new_results.get('return_pct', 0)

            if old_return == 0:
                improvement = 1.0 if new_return > 0 else 0.0
            else:
                improvement = (new_return - old_return) / abs(old_return)

            print(f"[OPTIMIZER] Old return: {old_return:.2f}%")
            print(f"[OPTIMIZER] New return: {new_return:.2f}%")
            print(f"[OPTIMIZER] Improvement: {improvement:.1%}")

            # Record optimization
            opt_id = self._record_optimization(
                strategy_id, strategy['strategy_code'], improved_code,
                json.dumps(suggestions), old_results, new_results, improvement
            )

            # Auto-deploy if meets threshold
            if improvement >= self.improvement_threshold:
                print(f"[OPTIMIZER] Improvement {improvement:.1%} >= threshold {self.improvement_threshold:.1%}")
                self._deploy_optimization(strategy_id, improved_code, opt_id)
                return True, f"Optimized and deployed (improvement: {improvement:.1%})"
            else:
                print(f"[OPTIMIZER] Improvement {improvement:.1%} < threshold {self.improvement_threshold:.1%}")
                return True, f"Optimized but not deployed (improvement: {improvement:.1%} < {self.improvement_threshold:.1%})"

        except Exception as e:
            print(f"[OPTIMIZER] Error in optimization pipeline: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)

    def monitor_and_optimize(self):
        """
        Check all active strategies for optimization triggers

        Called by StrategyExecutor or can be run independently
        """
        print(f"\n[OPTIMIZER] Checking all strategies for optimization triggers...")

        active_strategies = self.db.execute(
            "SELECT id FROM active_strategies WHERE status = 'active'",
            fetch='all'
        )

        if not active_strategies:
            print(f"[OPTIMIZER] No active strategies")
            return

        optimized_count = 0
        for strat in active_strategies:
            strategy_id = strat['id']

            # Check if needs optimization
            should_optimize, reason = self.analytics.check_optimization_triggers(strategy_id)

            if should_optimize:
                print(f"\n[OPTIMIZER] Strategy {strategy_id} triggered: {reason}")

                # Optimize
                success, message = self.optimize_strategy(strategy_id)

                if success:
                    optimized_count += 1
                    print(f"[OPTIMIZER] {message}")
                else:
                    print(f"[OPTIMIZER] Optimization failed: {message}")

        print(f"\n[OPTIMIZER] Monitoring complete. Optimized {optimized_count} strategies.")

    def get_optimization_history(self, strategy_id: int) -> List[Dict]:
        """
        Get optimization history for a strategy

        Args:
            strategy_id: Strategy ID

        Returns:
            List of optimization records
        """
        optimizations = self.db.execute(
            """SELECT * FROM strategy_optimizations
               WHERE strategy_id = %s
               ORDER BY created_at DESC""",
            (strategy_id,),
            fetch='all'
        )

        return [dict(opt) for opt in optimizations] if optimizations else []


def main():
    """Test the strategy optimizer"""
    import os
    import sys

    claude_key = os.getenv('CLAUDE_API_KEY')
    if not claude_key:
        print("ERROR: CLAUDE_API_KEY not set")
        sys.exit(1)

    optimizer = StrategyOptimizer(claude_key)

    print("\n" + "=" * 60)
    print("Strategy Optimizer Test")
    print("=" * 60)

    # Monitor all strategies
    optimizer.monitor_and_optimize()

    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
