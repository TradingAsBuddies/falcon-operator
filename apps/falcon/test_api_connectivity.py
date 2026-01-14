#!/usr/bin/env python3
"""
Test script to verify Polygon.io (Massive API) connectivity and data access
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_polygon_api():
    """Test Polygon.io API connectivity and data access"""
    api_key = os.getenv('MASSIVE_API_KEY')

    if not api_key:
        print("[X] ERROR: MASSIVE_API_KEY not found in environment")
        return False

    print(f"[OK] API Key found: {api_key[:10]}...")

    # Test 1: Check API key validity with a simple request
    print("\n=== Test 1: API Key Validation ===")
    test_symbol = "SPY"
    # Look back 7 days to account for weekends/holidays
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    url = f"https://api.polygon.io/v2/aggs/ticker/{test_symbol}/range/1/day/{start_date}/{end_date}"
    params = {'apiKey': api_key}

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK' and data.get('resultsCount', 0) > 0:
                print(f"[OK] API Key is VALID")
                print(f"[OK] Successfully fetched data for {test_symbol}")
                results = data.get('results', [])
                if results:
                    bar = results[-1]  # Get most recent bar
                    print(f"  Date: {datetime.fromtimestamp(bar['t']/1000).strftime('%Y-%m-%d')}")
                    print(f"  Open: ${bar['o']:.2f}")
                    print(f"  High: ${bar['h']:.2f}")
                    print(f"  Low: ${bar['l']:.2f}")
                    print(f"  Close: ${bar['c']:.2f}")
                    print(f"  Volume: {bar['v']:,}")
                    print(f"  Results count: {len(results)} days")
                return True
            else:
                print(f"[WARN] API responded but no data: {data}")
                return False
        elif response.status_code == 401:
            print(f"[X] API Key is INVALID (401 Unauthorized)")
            return False
        elif response.status_code == 403:
            print(f"[X] API Key lacks permissions (403 Forbidden)")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"[WARN] Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[X] Network error: {e}")
        return False
    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def test_real_time_quote():
    """Test real-time quote access"""
    api_key = os.getenv('MASSIVE_API_KEY')

    print("\n=== Test 2: Real-time Quote Access ===")
    test_symbol = "AAPL"

    url = f"https://api.polygon.io/v2/last/trade/{test_symbol}"
    params = {'apiKey': api_key}

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                print(f"[OK] Real-time quotes accessible")
                results = data.get('results', {})
                print(f"  Symbol: {test_symbol}")
                print(f"  Price: ${results.get('p', 0):.2f}")
                print(f"  Size: {results.get('s', 0)}")
                print(f"  Timestamp: {datetime.fromtimestamp(results.get('t', 0)/1000000000).strftime('%Y-%m-%d %H:%M:%S')}")
                return True
            else:
                print(f"[WARN] No real-time data available")
                return False
        elif response.status_code == 403:
            print(f"[WARN] Real-time quotes not available on your plan")
            print(f"  This is normal for free tier - historical data still works")
            return True  # Not a failure for free tier
        else:
            print(f"[WARN] Status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def test_multiple_tickers():
    """Test fetching data for multiple tickers"""
    api_key = os.getenv('MASSIVE_API_KEY')

    print("\n=== Test 3: Multiple Tickers ===")
    tickers = ["SPY", "QQQ", "AAPL", "MSFT", "TSLA"]
    # Look back 7 days to account for weekends/holidays
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    success_count = 0
    for ticker in tickers:
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {'apiKey': api_key}

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('resultsCount', 0) > 0:
                    results = data['results'][-1]  # Get most recent bar
                    print(f"  [OK] {ticker}: ${results['c']:.2f} (Vol: {results['v']:,})")
                    success_count += 1
                else:
                    print(f"  [WARN] {ticker}: No data")
            else:
                print(f"  [X] {ticker}: Error {response.status_code}")
        except Exception as e:
            print(f"  [X] {ticker}: {e}")

    print(f"\n[OK] Successfully fetched {success_count}/{len(tickers)} tickers")
    return success_count == len(tickers)

if __name__ == "__main__":
    print("=" * 60)
    print("Polygon.io (Massive API) Connectivity Test")
    print("=" * 60)

    # Run all tests
    test1 = test_polygon_api()
    test2 = test_real_time_quote()
    test3 = test_multiple_tickers()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"API Key Validation: {'[OK] PASS' if test1 else '[X] FAIL'}")
    print(f"Real-time Access: {'[OK] PASS' if test2 else '[X] FAIL'}")
    print(f"Multiple Tickers: {'[OK] PASS' if test3 else '[X] FAIL'}")

    if test1 and test3:
        print("\n[OK] Polygon.io API is fully accessible and working correctly")
        sys.exit(0)
    else:
        print("\n[X] Some tests failed - check API key or network connection")
        sys.exit(1)
