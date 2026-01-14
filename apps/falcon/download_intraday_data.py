#!/usr/bin/env python3
"""
Download intraday (1-minute) bars from Polygon.io for One Candle strategy backtesting

Usage:
    python3 download_intraday_data.py --ticker SPY --days 30
    python3 download_intraday_data.py --ticker TSLA --days 60 --interval 5min
"""
import os
import sys
import requests
import pandas as pd
import gzip
from datetime import datetime, timedelta
import time
import argparse


def load_api_key():
    """Load Polygon API key from .env file"""
    env_path = os.path.expanduser('~/.local/.env')

    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('MASSIVE_API_KEY='):
                    return line.strip().split('=', 1)[1]

    # Try environment variable
    api_key = os.getenv('MASSIVE_API_KEY')
    if api_key:
        return api_key

    print("ERROR: MASSIVE_API_KEY not found in ~/.local/.env or environment")
    return None


def download_intraday_bars(ticker, days=30, interval='1min'):
    """
    Download intraday bars from Polygon.io

    Args:
        ticker: Stock symbol (e.g., 'SPY')
        days: Number of days of history to download
        interval: Bar interval ('1min' or '5min')

    Returns:
        DataFrame with columns: ticker, datetime, open, high, low, close, volume
    """
    api_key = load_api_key()
    if not api_key:
        return None

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Polygon expects minute intervals as '1', '5', etc.
    interval_map = {
        '1min': 1,
        '5min': 5,
        '15min': 15,
        '30min': 30,
        '60min': 60
    }

    interval_num = interval_map.get(interval, 1)

    print(f"\nDownloading {interval} bars for {ticker}")
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print(f"This may take a minute...")

    # Polygon API endpoint for aggregates (bars)
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{interval_num}/minute/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

    params = {
        'adjusted': 'true',
        'sort': 'asc',
        'limit': 50000,  # Max per request
        'apiKey': api_key
    }

    all_bars = []

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data.get('status') == 'ERROR':
            print(f"ERROR: {data.get('error', 'Unknown error')}")
            return None

        if data.get('status') != 'OK':
            print(f"WARN: API returned status: {data.get('status')}")

        results = data.get('results', [])

        if not results:
            print(f"ERROR: No data returned for {ticker}")
            return None

        print(f"Downloaded {len(results)} bars")

        # Convert to DataFrame
        bars = []
        for bar in results:
            bars.append({
                'ticker': ticker,
                'datetime': datetime.fromtimestamp(bar['t'] / 1000),  # Polygon uses milliseconds
                'open': float(bar['o']),
                'high': float(bar['h']),
                'low': float(bar['l']),
                'close': float(bar['c']),
                'volume': int(bar['v'])
            })

        df = pd.DataFrame(bars)

        # Filter to only include market hours (9:30 AM - 4:00 PM ET)
        df['hour'] = df['datetime'].dt.hour
        df['minute'] = df['datetime'].dt.minute

        # Keep only regular trading hours
        df = df[
            ((df['hour'] == 9) & (df['minute'] >= 30)) |
            ((df['hour'] >= 10) & (df['hour'] < 16))
        ]

        df = df.drop(['hour', 'minute'], axis=1)

        print(f"Filtered to {len(df)} bars during market hours (9:30 AM - 4:00 PM)")

        return df

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to download data: {e}")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def save_intraday_data(df, output_dir='market_data/intraday_bars'):
    """
    Save intraday data grouped by date

    Args:
        df: DataFrame with intraday bars
        output_dir: Directory to save files
    """
    if df is None or df.empty:
        return False

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Group by date and save each day separately
    df['date'] = df['datetime'].dt.date
    dates = df['date'].unique()

    print(f"\nSaving data to {output_dir}/")

    for date in sorted(dates):
        day_data = df[df['date'] == date].copy()
        day_data = day_data.drop('date', axis=1)

        # Format datetime as string for CSV
        day_data['datetime'] = day_data['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')

        filename = f"{output_dir}/intraday_bars_{date}.csv.gz"

        # Check if file exists and append if needed
        if os.path.exists(filename):
            # Load existing data
            try:
                existing_df = pd.read_csv(filename, compression='gzip')
                # Append new data and remove duplicates
                combined = pd.concat([existing_df, day_data], ignore_index=True)
                combined = combined.drop_duplicates(subset=['ticker', 'datetime'], keep='last')
                # Save combined data
                with gzip.open(filename, 'wt') as f:
                    combined.to_csv(f, index=False)
            except:
                # If error reading, just overwrite
                with gzip.open(filename, 'wt') as f:
                    day_data.to_csv(f, index=False)
        else:
            # Save as compressed CSV
            with gzip.open(filename, 'wt') as f:
                day_data.to_csv(f, index=False)

    print(f"Saved {len(dates)} daily files")
    print(f"Total bars: {len(df)}")

    # Calculate statistics
    total_days = len(dates)
    avg_bars_per_day = len(df) / total_days if total_days > 0 else 0

    print(f"\nStatistics:")
    print(f"  Trading days: {total_days}")
    print(f"  Avg bars/day: {avg_bars_per_day:.0f}")
    print(f"  Total bars: {len(df)}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Download intraday bars from Polygon.io',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download 30 days of 1-minute SPY data
  python3 download_intraday_data.py --ticker SPY --days 30

  # Download 60 days of 5-minute TSLA data
  python3 download_intraday_data.py --ticker TSLA --days 60 --interval 5min

  # Download multiple tickers
  for ticker in SPY QQQ AAPL; do
      python3 download_intraday_data.py --ticker $ticker --days 30
  done
        """
    )

    parser.add_argument(
        '--ticker',
        type=str,
        required=True,
        help='Stock ticker symbol (e.g., SPY, TSLA, AAPL)'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days of history to download (default: 30)'
    )

    parser.add_argument(
        '--interval',
        type=str,
        default='1min',
        choices=['1min', '5min', '15min', '30min', '60min'],
        help='Bar interval (default: 1min)'
    )

    args = parser.parse_args()

    print("="*70)
    print("POLYGON.IO INTRADAY DATA DOWNLOADER")
    print("="*70)

    # Download data
    df = download_intraday_bars(args.ticker, args.days, args.interval)

    if df is None or df.empty:
        print("\nFAILED: No data downloaded")
        sys.exit(1)

    # Save data
    success = save_intraday_data(df)

    if success:
        print("\nSUCCESS: Intraday data ready for backtesting")
        print(f"\nTo backtest, run:")
        print(f"  ./backtest/bin/python3 backtest_one_candle_intraday.py --ticker {args.ticker} --days {args.days}")
        sys.exit(0)
    else:
        print("\nFAILED: Could not save data")
        sys.exit(1)


if __name__ == '__main__':
    main()
