#!/usr/bin/env python3
"""Test script to see what Finviz is actually returning"""
import os
import sys
import requests
import csv
from io import StringIO

# Get config from env
screener_url = os.getenv('FINVIZ_SCREENER_URL', '')
if not screener_url:
    # Try loading from .env file
    env_path = os.path.expanduser('~/.local/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith('FINVIZ_SCREENER_URL='):
                    screener_url = line.strip().split('=', 1)[1]
                    break

if not screener_url:
    print("ERROR: FINVIZ_SCREENER_URL not found")
    sys.exit(1)

# Parse URL
import urllib.parse
parsed = urllib.parse.urlparse(screener_url)
params = urllib.parse.parse_qs(parsed.query)
auth_key = params.get('auth', [''])[0]
filters = params.get('f', [''])[0]

print(f"Auth key: {auth_key[:20]}..." if auth_key else "No auth key")
print(f"Filters: {filters}\n")

# Try to fetch CSV
columns = "1,2,3,4,6,7,8,9,10,65,66,93"
csv_params = {
    'v': 152,
    'c': columns,
    'auth': auth_key
}
if filters:
    csv_params['f'] = filters

print("Fetching from elite.finviz.com CSV export...")
try:
    response = requests.get('https://elite.finviz.com/export.ashx',
                           params=csv_params, timeout=30)

    print(f"Status: {response.status_code}")
    print(f"Content length: {len(response.text)} bytes\n")

    if response.status_code == 200:
        # Parse CSV
        reader = csv.DictReader(StringIO(response.text))
        stocks = list(reader)

        print(f"Total stocks returned: {len(stocks)}\n")

        if stocks:
            print("First 20 tickers (as returned by Finviz):")
            for i, stock in enumerate(stocks[:20]):
                ticker = stock.get('Ticker', 'N/A')
                perf_5min = stock.get('Performance (5 Minutes)', 'N/A')
                price = stock.get('Price', 'N/A')
                print(f"  {i+1:2}. {ticker:6} - 5min: {perf_5min:>8} - Price: ${price}")

            # Check first letters
            from collections import Counter
            first_letters = Counter([s.get('Ticker', 'X')[0] for s in stocks if s.get('Ticker')])
            print(f"\nFirst letter distribution:")
            for letter in sorted(first_letters.keys())[:10]:
                count = first_letters[letter]
                pct = (count / len(stocks) * 100)
                print(f"  {letter}: {count:3} ({pct:.1f}%)")

            # Check if 5-minute performance data exists
            has_5min = sum(1 for s in stocks if s.get('Performance (5 Minutes)', '').strip() not in ['', '-', 'N/A'])
            print(f"\nStocks with 5-minute performance data: {has_5min}/{len(stocks)}")

    else:
        print(f"ERROR: HTTP {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"ERROR: {e}")
