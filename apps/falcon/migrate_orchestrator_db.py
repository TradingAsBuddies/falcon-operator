#!/usr/bin/env python3
"""
Database Migration for Orchestrator Schema
Adds columns needed by the multi-strategy orchestrator
"""
import sqlite3
import sys

def migrate_database(db_path='paper_trading.db'):
    """Add orchestrator columns to existing database"""

    print(f"Migrating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add strategy and reason columns to orders table
        print("\n[1] Adding 'strategy' column to orders table...")
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN strategy TEXT")
            print("  [OK] Added 'strategy' column")
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  [SKIP] 'strategy' column already exists")
            else:
                raise

        print("[2] Adding 'reason' column to orders table...")
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN reason TEXT")
            print("  [OK] Added 'reason' column")
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  [SKIP] 'reason' column already exists")
            else:
                raise

        # Add total_value column to account table (calculated)
        print("[3] Adding 'total_value' column to account table...")
        try:
            cursor.execute("ALTER TABLE account ADD COLUMN total_value REAL DEFAULT 0")
            print("  [OK] Added 'total_value' column")
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  [SKIP] 'total_value' column already exists")
            else:
                raise

        # Add current_price column to positions table
        print("[4] Adding 'current_price' column to positions table...")
        try:
            cursor.execute("ALTER TABLE positions ADD COLUMN current_price REAL DEFAULT 0")
            print("  [OK] Added 'current_price' column")
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  [SKIP] 'current_price' column already exists")
            else:
                raise

        # Initialize current_price to entry_price for existing positions
        print("[5] Initializing current_price for existing positions...")
        cursor.execute("""
            UPDATE positions
            SET current_price = entry_price
            WHERE current_price = 0 OR current_price IS NULL
        """)
        print(f"  [OK] Updated {cursor.rowcount} position records")

        # Update total_value for existing accounts
        print("[6] Updating total_value for existing accounts...")
        cursor.execute("""
            UPDATE account
            SET total_value = cash
        """)
        print(f"  [OK] Updated {cursor.rowcount} account records")

        # Add strategy column to positions table
        print("[7] Adding 'strategy' column to positions table...")
        try:
            cursor.execute("ALTER TABLE positions ADD COLUMN strategy TEXT")
            print("  [OK] Added 'strategy' column")
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  [SKIP] 'strategy' column already exists")
            else:
                raise

        # Add classification column to positions table
        print("[8] Adding 'classification' column to positions table...")
        try:
            cursor.execute("ALTER TABLE positions ADD COLUMN classification TEXT")
            print("  [OK] Added 'classification' column")
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  [SKIP] 'classification' column already exists")
            else:
                raise

        # Add profit_target column to positions table
        print("[9] Adding 'profit_target' column to positions table...")
        try:
            cursor.execute("ALTER TABLE positions ADD COLUMN profit_target REAL DEFAULT 0")
            print("  [OK] Added 'profit_target' column")
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  [SKIP] 'profit_target' column already exists")
            else:
                raise

        conn.commit()
        print("\n[SUCCESS] Database migration completed!")

        # Show updated schemas
        print("\n" + "="*60)
        print("UPDATED SCHEMAS")
        print("="*60)

        cursor.execute("PRAGMA table_info(orders)")
        print("\nOrders table columns:")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[2]})")

        cursor.execute("PRAGMA table_info(account)")
        print("\nAccount table columns:")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[2]})")

        cursor.execute("PRAGMA table_info(positions)")
        print("\nPositions table columns:")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[2]})")

        print()

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

    return True


if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'paper_trading.db'

    print("="*60)
    print("DATABASE MIGRATION - ORCHESTRATOR SCHEMA")
    print("="*60)

    success = migrate_database(db_path)
    sys.exit(0 if success else 1)
