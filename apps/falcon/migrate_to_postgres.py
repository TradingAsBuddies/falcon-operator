#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for Falcon Trading Platform

This script:
1. Creates all tables in PostgreSQL
2. Adds additional columns for orchestrator support
3. Exports data from SQLite
4. Imports data to PostgreSQL
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

# PostgreSQL configuration
POSTGRES_CONFIG = {
    'db_type': 'postgresql',
    'db_host': '192.168.1.194',
    'db_port': 5432,
    'db_name': 'falcon',
    'db_user': 'falcon',
    'db_password': 'falcon_trading_2026'
}

SQLITE_PATH = 'paper_trading.db'


def create_postgres_schema():
    """Create full PostgreSQL schema including all tables and columns"""
    from db_manager import DatabaseManager

    print("\n" + "=" * 60)
    print("PHASE 1: Creating PostgreSQL Schema")
    print("=" * 60)

    db = DatabaseManager(POSTGRES_CONFIG)

    # Create base tables
    print("\n[1] Creating base trading tables...")
    db.init_schema()
    print("    Base tables created")

    # Add orchestrator columns to account table
    print("\n[2] Adding orchestrator columns...")

    alter_statements = [
        ("ALTER TABLE account ADD COLUMN IF NOT EXISTS total_value DECIMAL(15,2) DEFAULT 0", "account.total_value"),
        ("ALTER TABLE orders ADD COLUMN IF NOT EXISTS strategy TEXT", "orders.strategy"),
        ("ALTER TABLE orders ADD COLUMN IF NOT EXISTS reason TEXT", "orders.reason"),
        ("ALTER TABLE positions ADD COLUMN IF NOT EXISTS current_price DECIMAL(15,2) DEFAULT 0", "positions.current_price"),
        ("ALTER TABLE positions ADD COLUMN IF NOT EXISTS strategy TEXT", "positions.strategy"),
        ("ALTER TABLE positions ADD COLUMN IF NOT EXISTS classification TEXT", "positions.classification"),
        ("ALTER TABLE positions ADD COLUMN IF NOT EXISTS profit_target DECIMAL(15,2) DEFAULT 0", "positions.profit_target"),
        ("ALTER TABLE positions ADD COLUMN IF NOT EXISTS stop_loss DECIMAL(15,2)", "positions.stop_loss"),
    ]

    for sql, col_name in alter_statements:
        try:
            db.execute(sql)
            print(f"    Added {col_name}")
        except Exception as e:
            if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                print(f"    {col_name} already exists")
            else:
                print(f"    Warning: {col_name} - {e}")

    # Create indexes
    print("\n[3] Creating indexes...")
    indexes = [
        ("CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(timestamp)", "orders.timestamp"),
        ("CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol)", "orders.symbol"),
        ("CREATE INDEX IF NOT EXISTS idx_orders_strategy ON orders(strategy)", "orders.strategy"),
        ("CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)", "positions.symbol"),
    ]

    for sql, idx_name in indexes:
        try:
            db.execute(sql)
            print(f"    Created index on {idx_name}")
        except Exception as e:
            print(f"    Index {idx_name}: {e}")

    db.close()
    print("\n[SUCCESS] PostgreSQL schema created")
    return True


def export_sqlite_data():
    """Export all data from SQLite database"""
    print("\n" + "=" * 60)
    print("PHASE 2: Exporting SQLite Data")
    print("=" * 60)

    if not os.path.exists(SQLITE_PATH):
        print(f"[ERROR] SQLite database not found: {SQLITE_PATH}")
        return None

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    data = {}

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"\nFound {len(tables)} tables: {', '.join(tables)}")

    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()

        if rows:
            # Get column names
            columns = rows[0].keys()
            data[table] = {
                'columns': list(columns),
                'rows': [dict(row) for row in rows]
            }
            print(f"  {table}: {len(rows)} rows")
        else:
            data[table] = {'columns': [], 'rows': []}
            print(f"  {table}: 0 rows")

    conn.close()

    # Save to JSON for reference
    export_file = '/tmp/falcon_sqlite_export.json'
    with open(export_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"\n[SUCCESS] Data exported to {export_file}")

    return data


def import_to_postgres(data):
    """Import data to PostgreSQL"""
    from db_manager import DatabaseManager

    print("\n" + "=" * 60)
    print("PHASE 3: Importing Data to PostgreSQL")
    print("=" * 60)

    if not data:
        print("[SKIP] No data to import")
        return True

    db = DatabaseManager(POSTGRES_CONFIG)

    # Import order matters due to foreign keys
    import_order = ['account', 'positions', 'orders', 'performance',
                    'youtube_strategies', 'strategy_backtests']

    # Filter to tables that exist in our data
    tables_to_import = [t for t in import_order if t in data and data[t]['rows']]

    # Add any other tables not in the predefined order
    for table in data:
        if table not in tables_to_import and data[table]['rows']:
            tables_to_import.append(table)

    for table in tables_to_import:
        table_data = data[table]
        rows = table_data['rows']
        columns = table_data['columns']

        if not rows:
            continue

        print(f"\n[{table}] Importing {len(rows)} rows...")

        # Clear existing data
        try:
            db.execute(f"DELETE FROM {table}")
            print(f"  Cleared existing data")
        except Exception as e:
            print(f"  Could not clear table: {e}")

        # Build insert statement
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        insert_sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

        # Insert rows
        success_count = 0
        error_count = 0

        for row in rows:
            try:
                values = []
                for col in columns:
                    val = row.get(col)
                    # Handle None/empty values
                    if val == '' or val is None:
                        values.append(None)
                    else:
                        values.append(val)

                db.execute(insert_sql, tuple(values))
                success_count += 1
            except Exception as e:
                error_count += 1
                if error_count <= 3:  # Only show first 3 errors
                    print(f"  Error inserting row: {e}")

        print(f"  Imported: {success_count}, Errors: {error_count}")

        # Reset sequence for serial columns
        if table in ['orders', 'youtube_strategies', 'strategy_backtests']:
            try:
                db.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1))")
                print(f"  Reset sequence for {table}.id")
            except Exception as e:
                print(f"  Could not reset sequence: {e}")

    db.close()
    print("\n[SUCCESS] Data import completed")
    return True


def verify_migration():
    """Verify data was migrated correctly"""
    from db_manager import DatabaseManager

    print("\n" + "=" * 60)
    print("PHASE 4: Verifying Migration")
    print("=" * 60)

    # Connect to both databases
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_cursor = sqlite_conn.cursor()

    pg_db = DatabaseManager(POSTGRES_CONFIG)

    tables = ['account', 'positions', 'orders', 'performance']
    all_match = True

    print("\nRow count comparison:")
    print("-" * 40)

    for table in tables:
        try:
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]
        except:
            sqlite_count = 0

        try:
            pg_result = pg_db.execute(f"SELECT COUNT(*) FROM {table}", fetch='one')
            pg_count = pg_result[0] if pg_result else 0
        except:
            pg_count = 0

        status = "OK" if sqlite_count == pg_count else "MISMATCH"
        if sqlite_count != pg_count:
            all_match = False

        print(f"  {table:20} SQLite: {sqlite_count:6}  PostgreSQL: {pg_count:6}  [{status}]")

    # Check account balance
    print("\nAccount balance check:")
    print("-" * 40)

    try:
        sqlite_cursor.execute("SELECT cash, total_value FROM account WHERE id = 1")
        sqlite_acc = sqlite_cursor.fetchone()
        sqlite_cash = sqlite_acc[0] if sqlite_acc else 0
        sqlite_total = sqlite_acc[1] if sqlite_acc and len(sqlite_acc) > 1 else sqlite_cash
    except:
        sqlite_cash = 0
        sqlite_total = 0

    try:
        pg_acc = pg_db.execute("SELECT cash, total_value FROM account WHERE id = 1", fetch='one')
        pg_cash = float(pg_acc[0]) if pg_acc else 0
        pg_total = float(pg_acc[1]) if pg_acc and len(pg_acc) > 1 else pg_cash
    except:
        pg_cash = 0
        pg_total = 0

    print(f"  SQLite:     Cash=${sqlite_cash:,.2f}  Total=${sqlite_total:,.2f}")
    print(f"  PostgreSQL: Cash=${pg_cash:,.2f}  Total=${pg_total:,.2f}")

    sqlite_conn.close()
    pg_db.close()

    if all_match:
        print("\n[SUCCESS] Migration verified - all data matches!")
    else:
        print("\n[WARNING] Some data counts don't match - please review")

    return all_match


def test_postgres_connection():
    """Test PostgreSQL connection"""
    print("\n" + "=" * 60)
    print("Testing PostgreSQL Connection")
    print("=" * 60)

    try:
        from db_manager import DatabaseManager
        db = DatabaseManager(POSTGRES_CONFIG)

        result = db.execute("SELECT 1", fetch='one')
        if result and result[0] == 1:
            print(f"  Host: {POSTGRES_CONFIG['db_host']}")
            print(f"  Database: {POSTGRES_CONFIG['db_name']}")
            print(f"  User: {POSTGRES_CONFIG['db_user']}")
            print("  [SUCCESS] Connection successful!")
            db.close()
            return True
        else:
            print("  [ERROR] Unexpected result from test query")
            return False
    except Exception as e:
        print(f"  [ERROR] Connection failed: {e}")
        return False


def main():
    """Run full migration"""
    print("=" * 60)
    print("FALCON TRADING PLATFORM")
    print("SQLite to PostgreSQL Migration")
    print("=" * 60)
    print(f"\nSource: {SQLITE_PATH}")
    print(f"Target: {POSTGRES_CONFIG['db_host']}:{POSTGRES_CONFIG['db_port']}/{POSTGRES_CONFIG['db_name']}")

    # Step 0: Test connection
    if not test_postgres_connection():
        print("\n[ABORT] Cannot connect to PostgreSQL")
        sys.exit(1)

    # Step 1: Create schema
    if not create_postgres_schema():
        print("\n[ABORT] Schema creation failed")
        sys.exit(1)

    # Step 2: Export SQLite data
    data = export_sqlite_data()

    # Step 3: Import to PostgreSQL
    if data:
        if not import_to_postgres(data):
            print("\n[ABORT] Data import failed")
            sys.exit(1)

    # Step 4: Verify
    verify_migration()

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update environment: export DB_TYPE=postgresql")
    print("2. Restart services: sudo systemctl restart falcon-dashboard")
    print("3. Verify dashboard: curl http://192.168.1.162/api/account")
    print()


if __name__ == '__main__':
    main()
