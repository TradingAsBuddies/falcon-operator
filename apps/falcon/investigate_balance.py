#!/usr/bin/env python3
"""
Investigate account balance discrepancy
Detailed analysis of cash, positions, and total_value
"""

import sqlite3
from datetime import datetime

def investigate_balance_discrepancy():
    """Detailed investigation of balance discrepancy"""
    print("=" * 80)
    print("ACCOUNT BALANCE DISCREPANCY INVESTIGATION")
    print("=" * 80)

    conn = sqlite3.connect('paper_trading.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Get current account state
    print("\n[1] CURRENT ACCOUNT STATE")
    print("-" * 80)
    cursor.execute("SELECT * FROM account")
    account = cursor.fetchone()

    if account:
        print(f"Account ID: {account['id']}")
        print(f"Cash: ${account['cash']:,.2f}")
        print(f"Stored Total Value: ${account['total_value']:,.2f}")
        print(f"Last Updated: {account['last_updated']}")

    # 2. Get all open positions with current prices
    print("\n[2] OPEN POSITIONS ANALYSIS")
    print("-" * 80)
    cursor.execute("""
        SELECT symbol, quantity, entry_price, current_price,
               last_updated, strategy, classification
        FROM positions
        ORDER BY symbol
    """)
    positions = cursor.fetchall()

    total_position_value = 0
    total_cost_basis = 0

    print(f"{'Symbol':<8} {'Qty':>8} {'Entry':>10} {'Current':>10} {'Value':>12} {'P&L':>12} {'Last Update':<20}")
    print("-" * 80)

    for pos in positions:
        cost_basis = pos['quantity'] * pos['entry_price']
        current_value = pos['quantity'] * pos['current_price']
        pnl = current_value - cost_basis

        total_cost_basis += cost_basis
        total_position_value += current_value

        print(f"{pos['symbol']:<8} {pos['quantity']:>8.0f} ${pos['entry_price']:>9.2f} "
              f"${pos['current_price']:>9.2f} ${current_value:>11.2f} "
              f"${pnl:>11.2f} {pos['last_updated']:<20}")

    print("-" * 80)
    print(f"{'TOTAL':<8} {'':<8} {'':>10} {'':>10} ${total_position_value:>11.2f} "
          f"${total_position_value - total_cost_basis:>11.2f}")

    # 3. Calculate what total_value SHOULD be
    print("\n[3] BALANCE CALCULATION")
    print("-" * 80)
    calculated_total = account['cash'] + total_position_value
    discrepancy = calculated_total - account['total_value']

    print(f"Cash:                    ${account['cash']:>12,.2f}")
    print(f"Position Value:          ${total_position_value:>12,.2f}")
    print(f"Cost Basis:              ${total_cost_basis:>12,.2f}")
    print(f"Unrealized P&L:          ${total_position_value - total_cost_basis:>12,.2f}")
    print(f"Calculated Total:        ${calculated_total:>12,.2f}")
    print(f"Stored Total:            ${account['total_value']:>12,.2f}")
    print(f"DISCREPANCY:             ${discrepancy:>12,.2f} ({(discrepancy/account['total_value'])*100:+.2f}%)")

    # 4. Check recent orders
    print("\n[4] RECENT ORDER ACTIVITY")
    print("-" * 80)
    cursor.execute("""
        SELECT symbol, side, quantity, price, timestamp, pnl
        FROM orders
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    orders = cursor.fetchall()

    print(f"{'Symbol':<8} {'Side':<6} {'Qty':>8} {'Price':>10} {'P&L':>10} {'Timestamp':<20}")
    print("-" * 80)

    total_realized_pnl = 0
    for order in orders:
        print(f"{order['symbol']:<8} {order['side']:<6} {order['quantity']:>8.0f} "
              f"${order['price']:>9.2f} ${order['pnl']:>9.2f} {order['timestamp']:<20}")
        if order['pnl']:
            total_realized_pnl += order['pnl']

    # 5. Check performance tracking
    print("\n[5] PERFORMANCE TRACKING")
    print("-" * 80)
    cursor.execute("""
        SELECT timestamp, total_value, cash, positions_value
        FROM performance
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    performance = cursor.fetchall()

    if performance:
        print(f"{'Timestamp':<20} {'Total Value':>12} {'Cash':>12} {'Positions':>12}")
        print("-" * 80)
        for perf in performance:
            print(f"{perf['timestamp']:<20} ${perf['total_value']:>11,.2f} "
                  f"${perf['cash']:>11,.2f} ${perf['positions_value']:>11,.2f}")

        # Check if most recent performance matches current account
        latest_perf = performance[0]
        print(f"\nLatest Performance Record: {latest_perf['timestamp']}")
        print(f"  Total Value: ${latest_perf['total_value']:,.2f}")
        print(f"  Account Total Value: ${account['total_value']:,.2f}")
        if abs(latest_perf['total_value'] - account['total_value']) < 0.01:
            print("  ✓ Performance table matches account table")
        else:
            print(f"  ✗ MISMATCH: ${latest_perf['total_value'] - account['total_value']:,.2f}")

    # 6. Identify root cause
    print("\n[6] ROOT CAUSE ANALYSIS")
    print("-" * 80)

    # Check when positions were last updated
    cursor.execute("SELECT symbol, last_updated FROM positions ORDER BY last_updated")
    oldest_update = cursor.fetchone()
    cursor.execute("SELECT symbol, last_updated FROM positions ORDER BY last_updated DESC")
    newest_update = cursor.fetchone()

    print(f"Oldest position update: {oldest_update['symbol']} at {oldest_update['last_updated']}")
    print(f"Newest position update: {newest_update['symbol']} at {newest_update['last_updated']}")
    print(f"Account last updated: {account['last_updated']}")

    # Check when last order was placed
    cursor.execute("SELECT symbol, side, timestamp FROM orders ORDER BY timestamp DESC LIMIT 1")
    last_order = cursor.fetchone()
    if last_order:
        print(f"Last order: {last_order['side']} {last_order['symbol']} at {last_order['timestamp']}")

    # 7. Recommendations
    print("\n[7] FINDINGS & RECOMMENDATIONS")
    print("=" * 80)

    if abs(discrepancy) < 0.01:
        print("✓ Balance is accurate (difference < $0.01)")
    elif abs(discrepancy) < 100:
        print(f"⚠ Minor discrepancy of ${abs(discrepancy):,.2f} detected")
        print("\nPossible causes:")
        print("  1. Position prices updated but account.total_value not refreshed")
        print("  2. Rounding differences in calculations")
    else:
        print(f"✗ SIGNIFICANT discrepancy of ${abs(discrepancy):,.2f} detected")
        print("\nPossible causes:")
        print("  1. account.total_value not being updated when positions change")
        print("  2. Position prices stale (not fetching current market prices)")
        print("  3. Missing logic to recalculate total_value")

    print("\nRecommended fixes:")
    print("  1. Add trigger to update account.total_value when positions.current_price changes")
    print("  2. Add scheduled job to refresh account.total_value periodically")
    print("  3. Update account.total_value in dashboard API endpoints")
    print("  4. Add validation to check for discrepancies > threshold")

    # 8. Generate SQL fix
    print("\n[8] SQL FIX TO UPDATE ACCOUNT BALANCE")
    print("=" * 80)
    print(f"""
UPDATE account SET
    total_value = {calculated_total:.2f},
    last_updated = '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'
WHERE id = {account['id']};

-- Verify the update
SELECT
    id,
    cash,
    total_value,
    last_updated
FROM account;
""")

    conn.close()

    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    investigate_balance_discrepancy()
