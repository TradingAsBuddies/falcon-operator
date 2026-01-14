#!/usr/bin/env python3
"""
Strategy Analytics - Performance Tracking and Metrics
Calculates and monitors per-strategy performance metrics
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from db_manager import DatabaseManager


class StrategyAnalytics:
    """Performance tracking and reporting for trading strategies"""

    def __init__(self, db_path: str = "/var/lib/falcon/paper_trading.db"):
        """
        Initialize strategy analytics

        Args:
            db_path: Database path
        """
        self.db = DatabaseManager({'db_path': db_path, 'db_type': 'sqlite'})
        print(f"[ANALYTICS] Initialized with database: {db_path}")

    def _get_strategy_trades(self, strategy_id: int) -> List[Dict]:
        """
        Get all trades for a strategy

        Args:
            strategy_id: Strategy ID

        Returns:
            List of trade dictionaries
        """
        trades = self.db.execute(
            """SELECT * FROM strategy_trades
               WHERE strategy_id = %s
               ORDER BY timestamp ASC""",
            (strategy_id,),
            fetch='all'
        )
        return [dict(trade) for trade in trades] if trades else []

    def _get_performance(self, strategy_id: int) -> Optional[Dict]:
        """
        Get current performance metrics for a strategy

        Args:
            strategy_id: Strategy ID

        Returns:
            Performance dict or None
        """
        perf = self.db.execute(
            "SELECT * FROM strategy_performance WHERE strategy_id = %s",
            (strategy_id,),
            fetch='one'
        )
        return dict(perf) if perf else None

    def _calculate_consecutive_losses(self, trades: List[Dict]) -> int:
        """
        Calculate current consecutive losses

        Args:
            trades: List of trades (sorted by timestamp)

        Returns:
            Number of consecutive losing trades
        """
        consecutive = 0
        for trade in reversed(trades):
            if trade['pnl'] < 0:
                consecutive += 1
            else:
                break
        return consecutive

    def _calculate_profit_factor(self, trades: List[Dict]) -> float:
        """
        Calculate profit factor (gross profit / gross loss)

        Args:
            trades: List of trades

        Returns:
            Profit factor
        """
        gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))

        if gross_loss == 0:
            return gross_profit if gross_profit > 0 else 0
        return gross_profit / gross_loss

    def _calculate_drawdown(self, trades: List[Dict]) -> Tuple[float, float]:
        """
        Calculate maximum drawdown and current drawdown

        Args:
            trades: List of trades (sorted by timestamp)

        Returns:
            Tuple of (max_drawdown, current_drawdown)
        """
        if not trades:
            return 0.0, 0.0

        # Calculate cumulative P&L
        cumulative_pnl = []
        running_total = 0
        for trade in trades:
            running_total += trade['pnl']
            cumulative_pnl.append(running_total)

        # Calculate drawdowns
        max_drawdown = 0.0
        peak = cumulative_pnl[0]

        for pnl in cumulative_pnl:
            if pnl > peak:
                peak = pnl
            drawdown = (peak - pnl) / abs(peak) if peak != 0 else 0
            max_drawdown = max(max_drawdown, drawdown)

        # Current drawdown
        current_peak = max(cumulative_pnl)
        current_pnl = cumulative_pnl[-1]
        current_drawdown = (current_peak - current_pnl) / abs(current_peak) if current_peak != 0 else 0

        return max_drawdown, current_drawdown

    def _calculate_roi(self, trades: List[Dict], initial_allocation: float = 10000.0) -> float:
        """
        Calculate return on investment percentage

        Args:
            trades: List of trades
            initial_allocation: Initial capital allocation

        Returns:
            ROI percentage
        """
        total_pnl = sum(t['pnl'] for t in trades)
        roi = (total_pnl / initial_allocation) * 100 if initial_allocation > 0 else 0
        return roi

    def update_strategy_performance(self, strategy_id: int):
        """
        Calculate and update all metrics for a strategy

        Updates strategy_performance table with:
        - Total trades, winning trades, losing trades
        - Consecutive losses (for optimization trigger)
        - Total P&L, win rate, profit factor
        - Max drawdown, current drawdown
        - ROI %

        Args:
            strategy_id: Strategy ID to update
        """
        try:
            # Get all trades for this strategy
            trades = self._get_strategy_trades(strategy_id)

            if not trades:
                print(f"[ANALYTICS] No trades for strategy {strategy_id}")
                return

            # Calculate metrics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['pnl'] > 0])
            losing_trades = len([t for t in trades if t['pnl'] < 0])
            consecutive_losses = self._calculate_consecutive_losses(trades)

            total_pnl = sum(t['pnl'] for t in trades)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            profit_factor = self._calculate_profit_factor(trades)

            max_drawdown, current_drawdown = self._calculate_drawdown(trades)
            roi_pct = self._calculate_roi(trades)

            # Update or insert performance record
            existing = self._get_performance(strategy_id)

            if existing:
                self.db.execute(
                    """UPDATE strategy_performance
                       SET total_trades = %s, winning_trades = %s, losing_trades = %s,
                           consecutive_losses = %s, total_pnl = %s, win_rate = %s,
                           profit_factor = %s, max_drawdown = %s, current_drawdown = %s,
                           roi_pct = %s, last_updated = %s
                       WHERE strategy_id = %s""",
                    (total_trades, winning_trades, losing_trades, consecutive_losses,
                     total_pnl, win_rate, profit_factor, max_drawdown, current_drawdown,
                     roi_pct, datetime.now().isoformat(), strategy_id)
                )
            else:
                self.db.execute(
                    """INSERT INTO strategy_performance
                       (strategy_id, total_trades, winning_trades, losing_trades,
                        consecutive_losses, total_pnl, win_rate, profit_factor,
                        max_drawdown, current_drawdown, roi_pct, last_updated)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (strategy_id, total_trades, winning_trades, losing_trades,
                     consecutive_losses, total_pnl, win_rate, profit_factor,
                     max_drawdown, current_drawdown, roi_pct, datetime.now().isoformat())
                )

            # Update performance weight for allocation
            self._update_performance_weight(strategy_id, win_rate)

            print(f"[ANALYTICS] Strategy {strategy_id}: {total_trades} trades, "
                  f"{win_rate:.1%} win rate, ${total_pnl:.2f} P&L")

        except Exception as e:
            print(f"[ANALYTICS] Error updating performance for strategy {strategy_id}: {e}")
            import traceback
            traceback.print_exc()

    def _update_performance_weight(self, strategy_id: int, win_rate: float):
        """
        Update performance weight for allocation algorithm

        Weight is used by StrategyExecutor for performance-weighted allocation

        Args:
            strategy_id: Strategy ID
            win_rate: Current win rate (0.0 to 1.0)
        """
        try:
            # Weight = win_rate (simple for now, can be enhanced later)
            weight = win_rate

            self.db.execute(
                "UPDATE active_strategies SET performance_weight = %s WHERE id = %s",
                (weight, strategy_id)
            )

        except Exception as e:
            print(f"[ANALYTICS] Error updating weight for strategy {strategy_id}: {e}")

    def check_optimization_triggers(self, strategy_id: int) -> Tuple[bool, str]:
        """
        Check if strategy needs optimization

        Triggers:
        - 5 consecutive losses
        - Win rate < 40% (with min 20 trades)
        - Drawdown > 15%
        - Total P&L negative over 20+ trades

        Args:
            strategy_id: Strategy ID to check

        Returns:
            Tuple of (should_optimize, reason)
        """
        perf = self._get_performance(strategy_id)

        if not perf:
            return False, ""

        # Trigger 1: Consecutive losses
        if perf['consecutive_losses'] >= 5:
            return True, f"5 consecutive losses"

        # Trigger 2: Low win rate (with minimum sample size)
        if perf['total_trades'] >= 20 and perf['win_rate'] < 0.40:
            return True, f"Win rate {perf['win_rate']:.1%} below 40%"

        # Trigger 3: High drawdown
        if perf['current_drawdown'] > 0.15:
            return True, f"Drawdown {perf['current_drawdown']:.1%} above 15%"

        # Trigger 4: Negative P&L with sufficient trades
        if perf['total_trades'] >= 20 and perf['total_pnl'] < 0:
            return True, f"Negative P&L: ${perf['total_pnl']:.2f}"

        return False, ""

    def get_strategy_summary(self, strategy_id: int) -> Dict:
        """
        Get comprehensive summary of strategy performance

        Args:
            strategy_id: Strategy ID

        Returns:
            Dict with all metrics and recent trades
        """
        perf = self._get_performance(strategy_id)
        trades = self._get_strategy_trades(strategy_id)

        # Get strategy info
        strategy = self.db.execute(
            "SELECT * FROM active_strategies WHERE id = %s",
            (strategy_id,),
            fetch='one'
        )

        if not strategy:
            return {}

        return {
            'strategy_id': strategy_id,
            'strategy_name': strategy['strategy_name'],
            'status': strategy['status'],
            'allocation_pct': strategy['allocation_pct'],
            'performance_weight': strategy['performance_weight'],
            'performance': perf if perf else {},
            'recent_trades': trades[-10:] if trades else [],
            'total_trades_count': len(trades),
            'should_optimize': self.check_optimization_triggers(strategy_id)
        }

    def get_all_strategies_leaderboard(self) -> List[Dict]:
        """
        Get leaderboard of all strategies ranked by performance

        Returns:
            List of strategy summaries sorted by win rate
        """
        strategies = self.db.execute(
            "SELECT id FROM active_strategies WHERE status = 'active'",
            fetch='all'
        )

        if not strategies:
            return []

        leaderboard = []
        for strat in strategies:
            summary = self.get_strategy_summary(strat['id'])
            if summary and summary.get('performance'):
                leaderboard.append(summary)

        # Sort by win rate descending
        leaderboard.sort(key=lambda x: x['performance'].get('win_rate', 0), reverse=True)

        return leaderboard

    def get_aggregate_statistics(self) -> Dict:
        """
        Get aggregate statistics across all active strategies

        Returns:
            Dict with system-wide metrics
        """
        strategies = self.db.execute(
            "SELECT id FROM active_strategies WHERE status = 'active'",
            fetch='all'
        )

        if not strategies:
            return {
                'total_strategies': 0,
                'total_trades': 0,
                'total_pnl': 0,
                'avg_win_rate': 0,
                'best_strategy': None,
                'worst_strategy': None
            }

        all_trades = []
        performances = []

        for strat in strategies:
            trades = self._get_strategy_trades(strat['id'])
            all_trades.extend(trades)

            perf = self._get_performance(strat['id'])
            if perf:
                performances.append({
                    'strategy_id': strat['id'],
                    'win_rate': perf['win_rate'],
                    'total_pnl': perf['total_pnl']
                })

        total_pnl = sum(t['pnl'] for t in all_trades)
        avg_win_rate = sum(p['win_rate'] for p in performances) / len(performances) if performances else 0

        # Find best and worst
        best = max(performances, key=lambda x: x['win_rate']) if performances else None
        worst = min(performances, key=lambda x: x['win_rate']) if performances else None

        return {
            'total_strategies': len(strategies),
            'total_trades': len(all_trades),
            'total_pnl': total_pnl,
            'avg_win_rate': avg_win_rate,
            'best_strategy': best,
            'worst_strategy': worst,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Test strategy analytics"""
    import sys

    analytics = StrategyAnalytics()

    print("\n" + "=" * 60)
    print("Strategy Analytics Test")
    print("=" * 60)

    # Get aggregate stats
    print("\nAggregate Statistics:")
    print("-" * 60)
    stats = analytics.get_aggregate_statistics()
    print(f"Total strategies: {stats['total_strategies']}")
    print(f"Total trades: {stats['total_trades']}")
    print(f"Total P&L: ${stats['total_pnl']:.2f}")
    print(f"Average win rate: {stats['avg_win_rate']:.1%}")

    if stats['best_strategy']:
        print(f"\nBest strategy: #{stats['best_strategy']['strategy_id']} "
              f"({stats['best_strategy']['win_rate']:.1%} win rate)")

    # Get leaderboard
    print("\n\nStrategy Leaderboard:")
    print("-" * 60)
    leaderboard = analytics.get_all_strategies_leaderboard()

    if not leaderboard:
        print("No active strategies with trades")
    else:
        for i, strat in enumerate(leaderboard, 1):
            perf = strat['performance']
            print(f"{i}. {strat['strategy_name']} (ID: {strat['strategy_id']})")
            print(f"   Win Rate: {perf['win_rate']:.1%} | "
                  f"Trades: {perf['total_trades']} | "
                  f"P&L: ${perf['total_pnl']:.2f} | "
                  f"Profit Factor: {perf['profit_factor']:.2f}")

            should_optimize, reason = strat['should_optimize']
            if should_optimize:
                print(f"   [OPTIMIZE] {reason}")
            print()

    print("=" * 60)


if __name__ == '__main__':
    main()
