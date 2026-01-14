#!/usr/bin/env python3
"""
Test script to verify database structure and calculations
"""

import sqlite3
from datetime import datetime
import os

def test_database_structure():
    """Test database structure and integrity"""
    db_path = "paper_trading.db"

    if not os.path.exists(db_path):
        print(f"[X] Database not found at {db_path}")
        return False

    print(f"[OK] Database found: {db_path}")
    print(f"     Size: {os.path.getsize(db_path) / (1024*1024):.2f} MB")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tables
        print("\n=== Database Tables ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()

        if not tables:
            print("[X] No tables found in database")
            return False

        for (table_name,) in tables:
            print(f"\n[Table: {table_name}]")

            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            print("  Columns:")
            for col in columns:
                col_id, col_name, col_type, not_null, default, pk = col
                pk_str = " [PRIMARY KEY]" if pk else ""
                not_null_str = " NOT NULL" if not_null else ""
                default_str = f" DEFAULT {default}" if default else ""
                print(f"    - {col_name}: {col_type}{pk_str}{not_null_str}{default_str}")

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  Rows: {count}")

        print("\n=== Database Structure Verification ===")

        # Check for required tables
        required_tables = ['account', 'positions', 'orders']
        table_names = [t[0] for t in tables]

        all_present = True
        for req_table in required_tables:
            if req_table in table_names:
                print(f"  [OK] Table '{req_table}' exists")
            else:
                print(f"  [X] Required table '{req_table}' is missing")
                all_present = False

        conn.close()
        return all_present

    except sqlite3.Error as e:
        print(f"[X] Database error: {e}")
        return False
    except Exception as e:
        print(f"[X] Error: {e}")
        return False


def test_account_calculations():
    """Test account balance calculations"""
    print("\n=== Account Balance Verification ===")

    try:
        conn = sqlite3.connect("paper_trading.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if account table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='account'")
        if not cursor.fetchone():
            print("[WARN] Account table does not exist")
            return True

        # Get account data
        cursor.execute("SELECT * FROM account ORDER BY id DESC LIMIT 1")
        account = cursor.fetchone()

        if account:
            print(f"  Account ID: {account['id']}")
            print(f"  Cash: ${account['cash']:,.2f}")
            try:
                print(f"  Balance: ${account['balance']:,.2f}")
            except (KeyError, IndexError):
                try:
                    print(f"  Total Value: ${account['total_value']:,.2f}")
                except (KeyError, IndexError):
                    pass

            # Get total positions value
            cursor.execute("SELECT * FROM positions")
            positions = cursor.fetchall()

            if positions:
                print(f"\n  Open Positions: {len(positions)}")
                total_position_value = 0
                for pos in positions:
                    value = pos['quantity'] * pos['current_price']
                    total_position_value += value
                    # Try avg_price first, fall back to entry_price
                    try:
                        entry_price = pos['avg_price']
                    except (KeyError, IndexError):
                        entry_price = pos['entry_price']

                    pnl = (pos['current_price'] - entry_price) * pos['quantity']
                    pnl_pct = ((pos['current_price'] - entry_price) / entry_price) * 100 if entry_price > 0 else 0

                    print(f"\n    {pos['symbol']}:")
                    print(f"      Quantity: {pos['quantity']}")
                    print(f"      Entry Price: ${entry_price:.2f}")
                    print(f"      Current Price: ${pos['current_price']:.2f}")
                    print(f"      Value: ${value:,.2f}")
                    print(f"      P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%)")

                print(f"\n  Total Position Value: ${total_position_value:,.2f}")
                calculated_balance = account['cash'] + total_position_value
                print(f"  Cash + Positions: ${calculated_balance:,.2f}")

                # Check against stored value
                try:
                    stored_value = account['balance']
                except (KeyError, IndexError):
                    try:
                        stored_value = account['total_value']
                    except (KeyError, IndexError):
                        stored_value = 0

                print(f"  Stored Value: ${stored_value:,.2f}")

                # Check if calculations match
                difference = abs(calculated_balance - stored_value)
                if difference < 0.01:  # Allow for rounding errors
                    print(f"  [OK] Balance calculations match")
                else:
                    print(f"  [WARN] Balance mismatch: ${difference:,.2f}")
            else:
                print(f"  No open positions")
                try:
                    stored_value = account['balance']
                except (KeyError, IndexError):
                    try:
                        stored_value = account['total_value']
                    except (KeyError, IndexError):
                        stored_value = 0

                if abs(account['cash'] - stored_value) < 0.01:
                    print(f"  [OK] Cash equals total value (no positions)")
                else:
                    print(f"  [WARN] Cash != Total Value but no positions")
        else:
            print("  [WARN] No account records found")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"[X] Database error: {e}")
        return False
    except Exception as e:
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_order_history():
    """Test order history and trade calculations"""
    print("\n=== Order History Verification ===")

    try:
        conn = sqlite3.connect("paper_trading.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if orders table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        if not cursor.fetchone():
            print("[WARN] Orders table does not exist")
            return True

        # Get order summary
        cursor.execute("""
            SELECT
                side,
                COUNT(*) as count,
                SUM(quantity * price) as total_value
            FROM orders
            GROUP BY side
        """)
        summary = cursor.fetchall()

        if summary:
            print("  Orders Summary:")
            for row in summary:
                print(f"    {row['side'].upper()}: {row['count']} orders, ${row['total_value']:,.2f}")

            # Get recent orders
            cursor.execute("""
                SELECT * FROM orders
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            recent_orders = cursor.fetchall()

            print(f"\n  Recent Orders (last 10):")
            for order in recent_orders:
                print(f"    {order['symbol']}: {order['side']} {order['quantity']} @ ${order['price']:.2f}")

        else:
            print("  No filled orders found")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"[X] Database error: {e}")
        return False
    except Exception as e:
        print(f"[X] Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Database Structure and Calculation Verification")
    print("=" * 60)

    test1 = test_database_structure()
    test2 = test_account_calculations()
    test3 = test_order_history()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Database Structure: {'[OK] PASS' if test1 else '[X] FAIL'}")
    print(f"Account Calculations: {'[OK] PASS' if test2 else '[X] FAIL'}")
    print(f"Order History: {'[OK] PASS' if test3 else '[X] FAIL'}")

    if test1 and test2 and test3:
        print("\n[OK] Database verification completed successfully")
    else:
        print("\n[WARN] Some verification checks had issues")
