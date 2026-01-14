#!/usr/bin/env python3
"""
Quick script to download test data for backtesting using yfinance
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import gzip
import os

def download_data(tickers=['SPY', 'QQQ', 'AAPL'], days=180):
    """Download historical data and save in flat file format"""

    # Create directory if needed
    os.makedirs('market_data/daily_bars', exist_ok=True)

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    print(f"Downloading {days} days of data for {len(tickers)} tickers...")
    print(f"Date range: {start_date.date()} to {end_date.date()}")

    # Download data for each ticker
    all_data = []
    for ticker in tickers:
        print(f"  Downloading {ticker}...", end='')
        try:
            # Download single ticker at a time
            data = yf.Ticker(ticker)
            df = data.history(start=start_date, end=end_date)

            if not df.empty:
                # Reset index to make Date a column
                df = df.reset_index()

                # Ensure we have the columns we need
                if 'Date' in df.columns:
                    df['ticker'] = ticker
                    df['date'] = df['Date'].dt.strftime('%Y-%m-%d')
                    df['open'] = df['Open'].astype(float)
                    df['high'] = df['High'].astype(float)
                    df['low'] = df['Low'].astype(float)
                    df['close'] = df['Close'].astype(float)
                    df['volume'] = df['Volume'].astype(int)

                    # Select only the columns we need
                    result_df = df[['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']].copy()
                    all_data.append(result_df)
                    print(f" OK ({len(result_df)} bars)")
                else:
                    print(" FAIL (unexpected format)")
            else:
                print(" FAIL (no data)")
        except Exception as e:
            print(f" FAIL ({str(e)[:50]})")

    if not all_data:
        print("\nERROR: No data downloaded")
        return False

    # Combine all data
    combined = pd.concat(all_data, ignore_index=True)
    combined['date'] = pd.to_datetime(combined['date']).dt.strftime('%Y-%m-%d')

    # Group by date and save each day as a separate file
    dates = combined['date'].unique()
    print(f"\nSaving {len(dates)} daily files...")

    for date in sorted(dates):
        day_data = combined[combined['date'] == date]
        filename = f"market_data/daily_bars/daily_bars_{date}.csv.gz"

        # Save as compressed CSV
        with gzip.open(filename, 'wt') as f:
            day_data.to_csv(f, index=False)

    print(f"\nOK Downloaded {len(combined)} total bars")
    print(f"OK Saved {len(dates)} daily files")
    print(f"OK Data ready for backtesting")

    return True

if __name__ == '__main__':
    import sys

    # Default tickers - add more volatile ones for better testing
    tickers = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA']

    days = 180
    if len(sys.argv) > 1:
        days = int(sys.argv[1])

    success = download_data(tickers=tickers, days=days)
    sys.exit(0 if success else 1)
