#!/usr/bin/env python3
"""
5-Minute Performance Scanner using Polygon.io
Fetches real-time minute bars and calculates recent momentum
"""

import os
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class FiveMinutePerformance:
    """5-minute performance data for a stock"""
    ticker: str
    start_price: float
    current_price: float
    performance_pct: float
    volume_5min: int
    timestamp: str

    def __repr__(self):
        return f"{self.ticker}: {self.performance_pct:+.2f}% (${self.start_price:.2f} -> ${self.current_price:.2f})"


class FiveMinuteScanner:
    """Real-time 5-minute momentum scanner using Polygon.io"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"

    def get_minute_bars(self, ticker: str, minutes: int = 5) -> Optional[List[Dict]]:
        """
        Fetch minute bars for the last N minutes

        Args:
            ticker: Stock symbol
            minutes: Number of minutes to look back (default 5)

        Returns:
            List of minute bar data, or None if error
        """
        try:
            # Calculate time range (using today's date for intraday data)
            now = datetime.now()
            from_date = now.strftime('%Y-%m-%d')
            to_date = now.strftime('%Y-%m-%d')

            # Polygon v2 aggregates endpoint for minute bars (date format)
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/minute/{from_date}/{to_date}"

            params = {
                'adjusted': 'true',
                'sort': 'desc',  # Get most recent first
                'limit': minutes + 2,  # Get enough bars
                'apiKey': self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Accept both 'OK' (real-time) and 'DELAYED' (15-min delay) status
            if data.get('status') in ['OK', 'DELAYED'] and data.get('resultsCount', 0) > 0:
                results = data['results']

                # Convert Polygon format to our format
                bars = []
                for bar in results:
                    bars.append({
                        'timestamp': datetime.fromtimestamp(bar['t'] / 1000).isoformat(),
                        'open': bar['o'],
                        'high': bar['h'],
                        'low': bar['l'],
                        'close': bar['c'],
                        'volume': bar['v']
                    })

                return bars

            return None

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"[POLYGON] Rate limit hit for {ticker}")
            else:
                print(f"[POLYGON] HTTP error for {ticker}: {e.response.status_code}")
            return None

        except requests.exceptions.Timeout:
            print(f"[POLYGON] Timeout for {ticker}")
            return None

        except Exception as e:
            print(f"[POLYGON] Error fetching {ticker}: {type(e).__name__}")
            return None

    def calculate_5min_performance(self, ticker: str) -> Optional[FiveMinutePerformance]:
        """
        Calculate 5-minute performance for a stock

        Args:
            ticker: Stock symbol

        Returns:
            FiveMinutePerformance object, or None if insufficient data
        """
        bars = self.get_minute_bars(ticker, minutes=5)

        if not bars or len(bars) < 2:
            return None

        # Bars are sorted desc (most recent first), so reverse for chronological order
        bars = list(reversed(bars))

        # Get the price from 5 minutes ago (or earliest available)
        start_bar = bars[0]
        start_price = start_bar['close']

        # Get the most recent price
        current_bar = bars[-1]
        current_price = current_bar['close']

        # Calculate performance
        performance_pct = ((current_price - start_price) / start_price) * 100

        # Sum volume over the period
        volume_5min = sum(bar['volume'] for bar in bars)

        return FiveMinutePerformance(
            ticker=ticker,
            start_price=start_price,
            current_price=current_price,
            performance_pct=performance_pct,
            volume_5min=volume_5min,
            timestamp=current_bar['timestamp']
        )

    def scan_tickers(self, tickers: List[str],
                     min_performance: float = None,
                     max_performance: float = None,
                     rate_limit_delay: float = 0.15) -> List[FiveMinutePerformance]:
        """
        Scan multiple tickers and calculate 5-minute performance

        Args:
            tickers: List of stock symbols
            min_performance: Optional minimum performance filter (e.g., -5.0 for stocks down >5%)
            max_performance: Optional maximum performance filter (e.g., 5.0 for stocks up <5%)
            rate_limit_delay: Delay between API calls (default 0.15s = ~6 calls/sec)

        Returns:
            List of FiveMinutePerformance objects, sorted by performance (highest first)
        """
        results = []
        total = len(tickers)

        print(f"[5MIN SCANNER] Scanning {total} tickers for 5-minute performance...")

        for i, ticker in enumerate(tickers, 1):
            # Progress indicator every 10 stocks
            if i % 10 == 0 or i == 1:
                print(f"[5MIN SCANNER] Progress: {i}/{total} ({i/total*100:.0f}%)")

            perf = self.calculate_5min_performance(ticker)

            if perf:
                # Apply filters if specified
                if min_performance is not None and perf.performance_pct < min_performance:
                    continue
                if max_performance is not None and perf.performance_pct > max_performance:
                    continue

                results.append(perf)

            # Rate limiting to avoid hitting Polygon API limits
            # Free tier: 5 calls/minute, Basic: unlimited but throttled
            if i < total:  # Don't sleep after last call
                time.sleep(rate_limit_delay)

        # Sort by performance (highest first)
        results.sort(key=lambda x: x.performance_pct, reverse=True)

        print(f"[5MIN SCANNER] Found performance data for {len(results)}/{total} stocks")

        if results:
            print(f"[5MIN SCANNER] Top mover: {results[0]}")
            print(f"[5MIN SCANNER] Bottom mover: {results[-1]}")

        return results

    def get_top_movers(self, tickers: List[str],
                       top_n: int = 20,
                       direction: str = 'both') -> List[FiveMinutePerformance]:
        """
        Get top N movers from a list of tickers

        Args:
            tickers: List of stock symbols
            top_n: Number of top movers to return
            direction: 'up' (gainers only), 'down' (losers only), 'both' (both)

        Returns:
            List of top N FiveMinutePerformance objects
        """
        all_results = self.scan_tickers(tickers)

        if direction == 'up':
            # Only gainers
            results = [r for r in all_results if r.performance_pct > 0]
        elif direction == 'down':
            # Only losers (but sorted by most negative)
            results = [r for r in all_results if r.performance_pct < 0]
        else:
            # Both directions - take top absolute movers
            results = sorted(all_results, key=lambda x: abs(x.performance_pct), reverse=True)

        return results[:top_n]


def main():
    """Test the 5-minute scanner"""
    import sys
    from dotenv import load_dotenv

    load_dotenv('/home/ospartners/.local/.env')
    api_key = os.getenv('MASSIVE_API_KEY')
    if not api_key:
        print("ERROR: MASSIVE_API_KEY environment variable not set")
        sys.exit(1)

    scanner = FiveMinuteScanner(api_key)

    # Test with a few common tickers
    test_tickers = ['AAPL', 'MSFT', 'TSLA', 'SPY', 'QQQ', 'NVDA', 'AMD', 'AMZN']

    print("=" * 80)
    print("5-MINUTE PERFORMANCE SCANNER - TEST")
    print("=" * 80)
    print()

    results = scanner.scan_tickers(test_tickers)

    print("\n" + "=" * 80)
    print("RESULTS (sorted by 5-minute performance)")
    print("=" * 80)

    for i, perf in enumerate(results, 1):
        print(f"{i}. {perf}")

    print("\n" + "=" * 80)
    print("TOP 3 GAINERS")
    print("=" * 80)

    top_gainers = scanner.get_top_movers(test_tickers, top_n=3, direction='up')
    for perf in top_gainers:
        print(f"  {perf}")


if __name__ == '__main__':
    main()
