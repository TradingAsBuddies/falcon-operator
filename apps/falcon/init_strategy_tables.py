#!/usr/bin/env python3
"""
Initialize Strategy Execution Tables
Creates all tables needed for automated strategy execution system
"""

import sqlite3
import sys
import os
from datetime import datetime


def init_strategy_tables(db_path: str = "paper_trading.db"):
    """
    Initialize all strategy execution tables

    Tables created:
    - active_strategies: Strategies being executed
    - strategy_trades: Links trades to strategies
    - strategy_performance: Per-strategy metrics
    - strategy_signals: Signal history for debugging
    - strategy_optimizations: AI optimization history
    """

    print(f"Initializing strategy tables in: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Active Strategies Table
    print("Creating active_strategies table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            youtube_strategy_id INTEGER,
            strategy_name TEXT NOT NULL,
            strategy_code TEXT NOT NULL,
            parameters TEXT NOT NULL,
            symbols TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            allocation_pct REAL DEFAULT 20.0,
            performance_weight REAL DEFAULT 1.0,
            created_at TEXT NOT NULL,
            activated_at TEXT,
            deactivated_at TEXT,
            parent_strategy_id INTEGER,
            evolution_note TEXT,
            FOREIGN KEY (youtube_strategy_id) REFERENCES youtube_strategies(id),
            FOREIGN KEY (parent_strategy_id) REFERENCES active_strategies(id)
        )
    ''')

    # 2. Strategy Trades Table
    print("Creating strategy_trades table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategy_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            signal_reason TEXT,
            signal_confidence REAL,
            timestamp TEXT NOT NULL,
            pnl REAL DEFAULT 0,
            FOREIGN KEY (strategy_id) REFERENCES active_strategies(id),
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')

    # 3. Strategy Performance Table
    print("Creating strategy_performance table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategy_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER NOT NULL UNIQUE,
            total_trades INTEGER DEFAULT 0,
            winning_trades INTEGER DEFAULT 0,
            losing_trades INTEGER DEFAULT 0,
            consecutive_losses INTEGER DEFAULT 0,
            total_pnl REAL DEFAULT 0,
            win_rate REAL DEFAULT 0,
            profit_factor REAL DEFAULT 0,
            max_drawdown REAL DEFAULT 0,
            current_drawdown REAL DEFAULT 0,
            roi_pct REAL DEFAULT 0,
            last_updated TEXT NOT NULL,
            FOREIGN KEY (strategy_id) REFERENCES active_strategies(id)
        )
    ''')

    # 4. Strategy Signals Table
    print("Creating strategy_signals table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategy_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            signal_reason TEXT,
            confidence REAL,
            market_price REAL,
            indicators TEXT,
            action_taken TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (strategy_id) REFERENCES active_strategies(id)
        )
    ''')

    # 5. Strategy Optimizations Table
    print("Creating strategy_optimizations table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategy_optimizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER NOT NULL,
            optimization_type TEXT NOT NULL,
            old_code TEXT,
            new_code TEXT,
            ai_reasoning TEXT,
            backtest_old_results TEXT,
            backtest_new_results TEXT,
            improvement_pct REAL,
            deployed BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            deployed_at TEXT,
            FOREIGN KEY (strategy_id) REFERENCES active_strategies(id)
        )
    ''')

    # Create indexes for performance
    print("Creating indexes...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_strategy_trades_strategy_id ON strategy_trades(strategy_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_strategy_trades_timestamp ON strategy_trades(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_strategy_signals_strategy_id ON strategy_signals(strategy_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_strategy_signals_timestamp ON strategy_signals(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_active_strategies_status ON active_strategies(status)')

    conn.commit()
    conn.close()

    print("[OK] All strategy tables created successfully")
    print(f"[OK] Database: {db_path}")


def verify_tables(db_path: str = "paper_trading.db"):
    """Verify all tables were created"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = [
        'active_strategies',
        'strategy_trades',
        'strategy_performance',
        'strategy_signals',
        'strategy_optimizations'
    ]

    print("\nVerifying tables...")
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cursor.fetchone():
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  [OK] {table}: {count} rows")
        else:
            print(f"  [X] {table}: MISSING")

    conn.close()


def main():
    """Main execution"""
    # Determine database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Try to use FHS-compliant path if running as service
        if os.path.exists('/var/lib/falcon'):
            db_path = '/var/lib/falcon/paper_trading.db'
        else:
            db_path = 'paper_trading.db'

    print("=" * 60)
    print("Falcon Strategy Execution System - Database Initialization")
    print("=" * 60)
    print()

    try:
        init_strategy_tables(db_path)
        verify_tables(db_path)
        print("\n" + "=" * 60)
        print("SUCCESS: Strategy tables initialized")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
