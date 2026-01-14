#!/usr/bin/env python3
"""
Backfill P&L for historical orders

This script calculates P&L for SELL orders that have pnl=0 or NULL,
using FIFO matching against BUY orders.
"""

import sqlite3
import sys
from collections import defaultdict
from datetime import datetime


def backfill_pnl(db_path: str, dry_run: bool = True):
    """
    Backfill P&L for historical orders

    Args:
        db_path: Path to the SQLite database
        dry_run: If True, just print what would be done without making changes
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"Database: {db_path}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 60)

    # Get all orders sorted by timestamp
    cursor.execute("""
        SELECT id, symbol, side, quantity, price, timestamp, pnl
        FROM orders
        ORDER BY timestamp ASC
    """)
    orders = cursor.fetchall()

    print(f"Total orders: {len(orders)}")

    # Track positions using FIFO for each symbol
    # positions[symbol] = [(entry_price, quantity, timestamp), ...]
    positions = defaultdict(list)

    # Track updates to make
    updates = []
    total_pnl = 0.0

    for order in orders:
        order_id = order['id']
        symbol = order['symbol']
        side = order['side'].upper()
        quantity = float(order['quantity'])
        price = float(order['price'])
        timestamp = order['timestamp']
        current_pnl = order['pnl'] or 0.0

        if side == 'BUY':
            # Add to position queue
            positions[symbol].append({
                'price': price,
                'quantity': quantity,
                'timestamp': timestamp
            })

        elif side == 'SELL':
            # Calculate P&L using FIFO
            remaining_qty = quantity
            calculated_pnl = 0.0

            while remaining_qty > 0 and positions[symbol]:
                oldest = positions[symbol][0]
                entry_price = oldest['price']

                if oldest['quantity'] <= remaining_qty:
                    # Use entire lot
                    lot_qty = oldest['quantity']
                    lot_pnl = (price - entry_price) * lot_qty
                    calculated_pnl += lot_pnl
                    remaining_qty -= lot_qty
                    positions[symbol].pop(0)
                else:
                    # Partial lot
                    lot_pnl = (price - entry_price) * remaining_qty
                    calculated_pnl += lot_pnl
                    oldest['quantity'] -= remaining_qty
                    remaining_qty = 0

            # If we couldn't match (no position), use 0
            if remaining_qty > 0:
                print(f"  WARNING: {symbol} SELL {quantity} @ {price:.4f} - no matching BUY (unmatched: {remaining_qty})")

            # Update if different from current
            if abs(calculated_pnl - current_pnl) > 0.001:
                updates.append({
                    'id': order_id,
                    'symbol': symbol,
                    'old_pnl': current_pnl,
                    'new_pnl': calculated_pnl,
                    'timestamp': timestamp
                })
                total_pnl += calculated_pnl

    print()
    print(f"Orders to update: {len(updates)}")
    print(f"Total calculated P&L: ${total_pnl:.2f}")
    print()

    if updates:
        print("Updates:")
        for u in updates[:20]:  # Show first 20
            diff = u['new_pnl'] - u['old_pnl']
            print(f"  {u['symbol']:6} | old: ${u['old_pnl']:8.2f} -> new: ${u['new_pnl']:8.2f} | diff: ${diff:+8.2f}")

        if len(updates) > 20:
            print(f"  ... and {len(updates) - 20} more")

        if not dry_run:
            print()
            print("Applying updates...")
            for u in updates:
                cursor.execute(
                    "UPDATE orders SET pnl = ? WHERE id = ?",
                    (u['new_pnl'], u['id'])
                )
            conn.commit()
            print(f"Updated {len(updates)} orders")
        else:
            print()
            print("To apply these changes, run with --apply flag")

    conn.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Backfill P&L for historical orders')
    parser.add_argument('--db', default='paper_trading.db', help='Path to database')
    parser.add_argument('--apply', action='store_true', help='Actually apply changes (default is dry run)')

    args = parser.parse_args()

    backfill_pnl(args.db, dry_run=not args.apply)
