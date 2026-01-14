#!/usr/bin/env python3
"""
Account Balance Updater - Permanent Solution

This module provides functions to keep account.total_value synchronized
with actual cash + position values.

Usage:
    # After placing an order
    from account_balance_updater import update_account_balance
    update_account_balance()

    # Run as a scheduled job
    python3 account_balance_updater.py --schedule

    # One-time update
    python3 account_balance_updater.py --update
"""

import sqlite3
import time
from datetime import datetime
import argparse
import logging

# Optional import for scheduling
try:
    import schedule
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False
    schedule = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_account_balance(db_path='paper_trading.db'):
    """
    Calculate correct account balance from cash + positions

    Returns:
        dict: {
            'cash': float,
            'positions_value': float,
            'total_value': float,
            'num_positions': int
        }
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get cash
        cursor.execute("SELECT cash FROM account WHERE id = 1")
        account = cursor.fetchone()
        if not account:
            logger.error("No account found in database")
            return None

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
            'total_value': total_value,
            'num_positions': len(positions)
        }

    except Exception as e:
        logger.error(f"Error calculating balance: {e}")
        return None


def update_account_balance(db_path='paper_trading.db'):
    """
    Update account.total_value in database

    This should be called:
    - After every order (buy/sell)
    - After position price updates
    - Periodically (e.g., every 5 minutes)

    Returns:
        dict: Balance info or None on error
    """
    try:
        balance = calculate_account_balance(db_path)
        if not balance:
            return None

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Update account table
        cursor.execute("""
            UPDATE account
            SET total_value = ?,
                last_updated = ?
            WHERE id = 1
        """, (balance['total_value'], datetime.now().isoformat()))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        if rows_affected > 0:
            logger.info(f"Updated account balance to ${balance['total_value']:,.2f}")
        else:
            logger.warning("No rows updated in account table")

        return balance

    except Exception as e:
        logger.error(f"Error updating account balance: {e}")
        return None


def add_performance_record(db_path='paper_trading.db'):
    """
    Add a performance tracking record

    This should be called:
    - Periodically (e.g., every 5-15 minutes)
    - At end of trading day
    - After significant portfolio changes

    Returns:
        bool: Success status
    """
    try:
        balance = calculate_account_balance(db_path)
        if not balance:
            return False

        conn = sqlite3.connect(db_path)
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

        logger.info(f"Added performance record: ${balance['total_value']:,.2f}")
        return True

    except Exception as e:
        logger.error(f"Error adding performance record: {e}")
        return False


def check_balance_discrepancy(db_path='paper_trading.db', threshold=1.0):
    """
    Check if there's a discrepancy between calculated and stored balance

    Args:
        db_path: Path to database
        threshold: Threshold in dollars for warning

    Returns:
        dict: Discrepancy info or None
    """
    try:
        balance = calculate_account_balance(db_path)
        if not balance:
            return None

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get stored total_value
        cursor.execute("SELECT total_value FROM account WHERE id = 1")
        account = cursor.fetchone()
        stored_total = account[0]

        conn.close()

        discrepancy = balance['total_value'] - stored_total
        discrepancy_pct = (discrepancy / stored_total * 100) if stored_total > 0 else 0

        result = {
            'calculated_total': balance['total_value'],
            'stored_total': stored_total,
            'discrepancy': discrepancy,
            'discrepancy_pct': discrepancy_pct,
            'has_issue': abs(discrepancy) > threshold
        }

        if result['has_issue']:
            logger.warning(
                f"Balance discrepancy detected: ${discrepancy:,.2f} "
                f"({discrepancy_pct:+.2f}%)"
            )

        return result

    except Exception as e:
        logger.error(f"Error checking discrepancy: {e}")
        return None


def scheduled_update():
    """
    Function to run on schedule
    Updates balance and adds performance record
    """
    logger.info("Running scheduled balance update")

    # Check for discrepancy
    discrepancy = check_balance_discrepancy()
    if discrepancy and discrepancy['has_issue']:
        logger.warning(
            f"Fixing discrepancy: ${discrepancy['discrepancy']:,.2f}"
        )

    # Update balance
    balance = update_account_balance()

    # Add performance record every 15 minutes
    # (This will run more frequently than performance tracking)
    if balance:
        logger.info(f"Current balance: ${balance['total_value']:,.2f}")


def run_scheduler(update_interval_minutes=5, performance_interval_minutes=15):
    """
    Run scheduled balance updates

    Args:
        update_interval_minutes: How often to update account.total_value
        performance_interval_minutes: How often to log performance
    """
    if not HAS_SCHEDULE:
        logger.error("schedule module not installed. Install with: pip install schedule")
        return False

    logger.info(f"Starting balance updater scheduler")
    logger.info(f"Balance update: every {update_interval_minutes} minutes")
    logger.info(f"Performance log: every {performance_interval_minutes} minutes")

    # Schedule balance updates
    schedule.every(update_interval_minutes).minutes.do(update_account_balance)

    # Schedule performance tracking
    schedule.every(performance_interval_minutes).minutes.do(add_performance_record)

    # Run once immediately
    update_account_balance()
    add_performance_record()

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(30)  # Check every 30 seconds


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Account Balance Updater for Falcon Trading System'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Run one-time balance update'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check for balance discrepancy'
    )
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run as scheduled service'
    )
    parser.add_argument(
        '--performance',
        action='store_true',
        help='Add performance record'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Update interval in minutes (default: 5)'
    )

    args = parser.parse_args()

    if args.update:
        print("Updating account balance...")
        balance = update_account_balance()
        if balance:
            print(f"[OK] Balance updated to ${balance['total_value']:,.2f}")
            print(f"     Cash: ${balance['cash']:,.2f}")
            print(f"     Positions: ${balance['positions_value']:,.2f}")
        else:
            print("[ERROR] Failed to update balance")

    elif args.check:
        print("Checking for balance discrepancy...")
        disc = check_balance_discrepancy()
        if disc:
            print(f"Calculated Total: ${disc['calculated_total']:,.2f}")
            print(f"Stored Total:     ${disc['stored_total']:,.2f}")
            print(f"Discrepancy:      ${disc['discrepancy']:,.2f} ({disc['discrepancy_pct']:+.2f}%)")
            if disc['has_issue']:
                print("\n[WARNING] Discrepancy exceeds threshold!")
                print("Run with --update to fix")
            else:
                print("\n[OK] Balance is accurate")
        else:
            print("[ERROR] Failed to check balance")

    elif args.performance:
        print("Adding performance record...")
        if add_performance_record():
            print("[OK] Performance record added")
        else:
            print("[ERROR] Failed to add performance record")

    elif args.schedule:
        print("Starting scheduled balance updater...")
        print("Press Ctrl+C to stop")
        try:
            run_scheduler(update_interval_minutes=args.interval)
        except KeyboardInterrupt:
            print("\nScheduler stopped")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
