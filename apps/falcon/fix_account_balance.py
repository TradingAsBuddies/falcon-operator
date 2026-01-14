#!/usr/bin/env python3
"""
Fix Account Balance Discrepancy

This script:
1. Calculates the correct account balance
2. Updates the database
3. Creates a function for ongoing balance updates
"""

import sqlite3
from datetime import datetime


def calculate_correct_balance():
    """Calculate what the account balance should be"""
    conn = sqlite3.connect('paper_trading.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get cash
    cursor.execute("SELECT cash FROM account WHERE id = 1")
    account = cursor.fetchone()
    cash = account['cash']

    # Get all positions with current prices
    cursor.execute("""
        SELECT symbol, quantity, current_price
        FROM positions
    """)
    positions = cursor.fetchall()

    # Calculate total position value
    total_position_value = 0
    for pos in positions:
        total_position_value += pos['quantity'] * pos['current_price']

    # Calculate total account value
    total_value = cash + total_position_value

    conn.close()

    return {
        'cash': cash,
        'positions_value': total_position_value,
        'total_value': total_value
    }


def update_account_balance():
    """Update account.total_value in database"""
    balance = calculate_correct_balance()

    conn = sqlite3.connect('paper_trading.db')
    cursor = conn.cursor()

    # Update account table
    cursor.execute("""
        UPDATE account
        SET total_value = ?,
            last_updated = ?
        WHERE id = 1
    """, (balance['total_value'], datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return balance


def add_performance_record():
    """Add current performance record"""
    balance = calculate_correct_balance()

    conn = sqlite3.connect('paper_trading.db')
    cursor = conn.cursor()

    # Insert performance record
    cursor.execute("""
        INSERT INTO performance (timestamp, total_value, cash, positions_value)
        VALUES (?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        balance['total_value'],
        balance['cash'],
        balance['positions_value']
    ))

    conn.commit()
    conn.close()

    return balance


def verify_fix():
    """Verify the balance is now correct"""
    conn = sqlite3.connect('paper_trading.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get account
    cursor.execute("SELECT * FROM account WHERE id = 1")
    account = cursor.fetchone()

    # Get positions
    cursor.execute("SELECT symbol, quantity, current_price FROM positions")
    positions = cursor.fetchall()

    # Calculate
    cash = account['cash']
    position_value = sum(p['quantity'] * p['current_price'] for p in positions)
    calculated_total = cash + position_value
    stored_total = account['total_value']

    conn.close()

    return {
        'cash': cash,
        'position_value': position_value,
        'calculated_total': calculated_total,
        'stored_total': stored_total,
        'discrepancy': calculated_total - stored_total,
        'is_correct': abs(calculated_total - stored_total) < 0.01
    }


def main():
    """Main fix function"""
    print("=" * 80)
    print("ACCOUNT BALANCE FIX")
    print("=" * 80)

    # 1. Show current state
    print("\n[1] BEFORE FIX")
    print("-" * 80)
    balance_before = calculate_correct_balance()
    verification_before = verify_fix()

    print(f"Cash: ${balance_before['cash']:,.2f}")
    print(f"Positions Value: ${balance_before['positions_value']:,.2f}")
    print(f"Calculated Total: ${balance_before['total_value']:,.2f}")
    print(f"Stored Total: ${verification_before['stored_total']:,.2f}")
    print(f"Discrepancy: ${verification_before['discrepancy']:,.2f}")

    # 2. Apply fix
    print("\n[2] APPLYING FIX")
    print("-" * 80)
    print("Updating account.total_value...")
    balance_after = update_account_balance()
    print(f"[OK] Updated to ${balance_after['total_value']:,.2f}")

    print("\nAdding performance record...")
    add_performance_record()
    print(f"[OK] Performance record added")

    # 3. Verify
    print("\n[3] AFTER FIX")
    print("-" * 80)
    verification_after = verify_fix()

    print(f"Cash: ${verification_after['cash']:,.2f}")
    print(f"Positions Value: ${verification_after['position_value']:,.2f}")
    print(f"Calculated Total: ${verification_after['calculated_total']:,.2f}")
    print(f"Stored Total: ${verification_after['stored_total']:,.2f}")
    print(f"Discrepancy: ${verification_after['discrepancy']:,.2f}")

    if verification_after['is_correct']:
        print("\n[OK] Balance is now CORRECT!")
    else:
        print(f"\n[WARNING] Discrepancy still exists: ${verification_after['discrepancy']:,.2f}")

    # 4. Show SQL for manual verification
    print("\n[4] VERIFICATION SQL")
    print("=" * 80)
    print("""
-- Verify account balance
SELECT
    id,
    cash,
    total_value,
    last_updated
FROM account;

-- Verify positions
SELECT
    symbol,
    quantity,
    entry_price,
    current_price,
    quantity * current_price AS position_value
FROM positions
ORDER BY symbol;

-- Verify performance records
SELECT
    timestamp,
    total_value,
    cash,
    positions_value
FROM performance
ORDER BY timestamp DESC
LIMIT 5;

-- Calculate balance manually
SELECT
    (SELECT cash FROM account WHERE id = 1) +
    (SELECT SUM(quantity * current_price) FROM positions) AS calculated_total,
    (SELECT total_value FROM account WHERE id = 1) AS stored_total;
""")

    print("\n" + "=" * 80)
    print("FIX COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
