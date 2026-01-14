#!/usr/bin/env python3
"""
Storage Cleanup Script for Falcon Trading System

Manages disk space by cleaning old market data, logs, and optimizing the database.

Usage:
    python3 storage_cleanup.py --dry-run              # Preview what would be cleaned
    python3 storage_cleanup.py --older-than 180       # Clean data older than 180 days
    python3 storage_cleanup.py --vacuum-db            # Optimize database
    python3 storage_cleanup.py --full-cleanup         # Clean data older than 365 days + vacuum
    python3 storage_cleanup.py --check                # Show current disk usage
"""

import os
import argparse
import sqlite3
import glob
from datetime import datetime, timedelta
from pathlib import Path


def get_disk_usage():
    """Get current disk usage statistics"""
    import subprocess
    result = subprocess.run(
        ['df', '-h', '/home/ospartners/src/falcon'],
        capture_output=True,
        text=True
    )
    lines = result.stdout.strip().split('\n')
    if len(lines) > 1:
        parts = lines[1].split()
        return {
            'total': parts[1],
            'used': parts[2],
            'available': parts[3],
            'use_percent': parts[4]
        }
    return None


def get_directory_size(path):
    """Calculate total size of directory in bytes"""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += get_directory_size(entry.path)
    except PermissionError:
        pass
    return total


def format_bytes(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def check_storage(verbose=True):
    """Check current storage usage"""
    disk_usage = get_disk_usage()

    if verbose:
        print("\n=== Disk Usage ===")
        print(f"Total: {disk_usage['total']}")
        print(f"Used: {disk_usage['used']}")
        print(f"Available: {disk_usage['available']}")
        print(f"Use%: {disk_usage['use_percent']}")
        print()

    # Check individual components
    components = {
        'market_data/intraday_bars': 'Intraday Data',
        'market_data/daily_bars': 'Daily Data',
        'paper_trading.db': 'Trading Database',
        'screened_stocks.json': 'Screened Stocks',
        'backtest': 'Backtest Venv'
    }

    if verbose:
        print("=== Component Sizes ===")

    sizes = {}
    for path, name in components.items():
        if os.path.exists(path):
            if os.path.isdir(path):
                size = get_directory_size(path)
            else:
                size = os.path.getsize(path)
            sizes[name] = size
            if verbose:
                print(f"{name:20s}: {format_bytes(size)}")

    if verbose:
        print()

    return disk_usage, sizes


def clean_old_data(days_threshold, dry_run=True):
    """Remove data older than specified days"""
    cutoff_date = datetime.now() - timedelta(days=days_threshold)
    print(f"\n=== Cleaning data older than {days_threshold} days (before {cutoff_date.date()}) ===")

    total_removed = 0
    files_removed = 0

    # Clean intraday bars
    intraday_pattern = 'market_data/intraday_bars/intraday_bars_*.csv.gz'
    for filepath in glob.glob(intraday_pattern):
        # Extract date from filename
        filename = os.path.basename(filepath)
        try:
            date_str = filename.replace('intraday_bars_', '').replace('.csv.gz', '')
            file_date = datetime.strptime(date_str, '%Y-%m-%d')

            if file_date < cutoff_date:
                file_size = os.path.getsize(filepath)
                total_removed += file_size
                files_removed += 1

                if dry_run:
                    print(f"[DRY RUN] Would remove: {filepath} ({format_bytes(file_size)})")
                else:
                    os.remove(filepath)
                    print(f"Removed: {filepath} ({format_bytes(file_size)})")
        except (ValueError, IndexError):
            continue

    # Clean daily bars
    daily_pattern = 'market_data/daily_bars/daily_bars_*.csv.gz'
    for filepath in glob.glob(daily_pattern):
        # Extract date from filename
        filename = os.path.basename(filepath)
        try:
            date_str = filename.replace('daily_bars_', '').replace('.csv.gz', '')
            file_date = datetime.strptime(date_str, '%Y-%m-%d')

            if file_date < cutoff_date:
                file_size = os.path.getsize(filepath)
                total_removed += file_size
                files_removed += 1

                if dry_run:
                    print(f"[DRY RUN] Would remove: {filepath} ({format_bytes(file_size)})")
                else:
                    os.remove(filepath)
                    print(f"Removed: {filepath} ({format_bytes(file_size)})")
        except (ValueError, IndexError):
            continue

    print(f"\nTotal: {files_removed} files, {format_bytes(total_removed)}")

    if dry_run:
        print("[DRY RUN] No files were actually deleted. Run without --dry-run to delete.")

    return files_removed, total_removed


def vacuum_database(dry_run=True):
    """Optimize database by reclaiming unused space"""
    db_path = 'paper_trading.db'

    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return

    print(f"\n=== Optimizing Database ===")

    # Get size before
    size_before = os.path.getsize(db_path)
    print(f"Database size before: {format_bytes(size_before)}")

    if dry_run:
        print("[DRY RUN] Would run VACUUM command on database")
        print("[DRY RUN] This reclaims deleted space and optimizes database")
    else:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get database stats
            cursor.execute("SELECT COUNT(*) FROM orders")
            order_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM positions")
            position_count = cursor.fetchone()[0]

            print(f"Orders: {order_count}, Positions: {position_count}")

            # Run VACUUM
            print("Running VACUUM...")
            cursor.execute("VACUUM")
            conn.commit()
            conn.close()

            # Get size after
            size_after = os.path.getsize(db_path)
            saved = size_before - size_after

            print(f"Database size after: {format_bytes(size_after)}")
            if saved > 0:
                print(f"Space reclaimed: {format_bytes(saved)} ({(saved/size_before*100):.1f}%)")
            else:
                print("No space reclaimed (database already optimal)")

        except Exception as e:
            print(f"Error optimizing database: {e}")


def clean_old_logs(days_threshold=30, dry_run=True):
    """Remove log entries older than specified days"""
    print(f"\n=== Cleaning logs older than {days_threshold} days ===")

    # Find log files
    log_files = glob.glob('*.log')

    total_size_before = 0
    total_size_after = 0

    for log_file in log_files:
        if not os.path.exists(log_file):
            continue

        size_before = os.path.getsize(log_file)
        total_size_before += size_before

        if size_before < 1024 * 10:  # Skip files smaller than 10KB
            print(f"Skipping {log_file} (too small: {format_bytes(size_before)})")
            continue

        print(f"Checking {log_file} ({format_bytes(size_before)})")

        if dry_run:
            print(f"[DRY RUN] Would trim log file to last {days_threshold} days")
            total_size_after += size_before
        else:
            # For now, just report - actual log rotation would need format-specific logic
            print(f"Note: Log rotation not implemented. Consider using logrotate or manually archiving.")
            total_size_after += size_before

    saved = total_size_before - total_size_after
    if saved > 0:
        print(f"Total space that would be saved: {format_bytes(saved)}")


def main():
    parser = argparse.ArgumentParser(
        description='Manage storage for Falcon Trading System'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Show current disk usage'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be cleaned without making changes'
    )
    parser.add_argument(
        '--older-than',
        type=int,
        metavar='DAYS',
        help='Remove data older than N days'
    )
    parser.add_argument(
        '--vacuum-db',
        action='store_true',
        help='Optimize database by reclaiming deleted space'
    )
    parser.add_argument(
        '--clean-logs',
        action='store_true',
        help='Clean old log files'
    )
    parser.add_argument(
        '--full-cleanup',
        action='store_true',
        help='Full cleanup (365 days + vacuum db)'
    )

    args = parser.parse_args()

    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # If no arguments, show check
    if not any([args.check, args.older_than, args.vacuum_db,
                args.clean_logs, args.full_cleanup]):
        args.check = True

    # Always show current status first
    if args.check or args.dry_run or args.older_than or args.vacuum_db or args.full_cleanup:
        check_storage(verbose=True)

    # Full cleanup mode
    if args.full_cleanup:
        print("\n=== FULL CLEANUP MODE ===")
        print("This will:")
        print("  1. Remove data older than 365 days")
        print("  2. Optimize database")
        print()

        if args.dry_run:
            print("[DRY RUN MODE - no changes will be made]")
        else:
            response = input("Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                return

        clean_old_data(365, dry_run=args.dry_run)
        vacuum_database(dry_run=args.dry_run)

        print("\n=== Updated Storage Status ===")
        check_storage(verbose=True)
        return

    # Individual operations
    if args.older_than:
        clean_old_data(args.older_than, dry_run=args.dry_run)

    if args.vacuum_db:
        vacuum_database(dry_run=args.dry_run)

    if args.clean_logs:
        clean_old_logs(dry_run=args.dry_run)

    # Show updated status if changes were made
    if not args.dry_run and (args.older_than or args.vacuum_db or args.clean_logs):
        print("\n=== Updated Storage Status ===")
        check_storage(verbose=True)


if __name__ == '__main__':
    main()
