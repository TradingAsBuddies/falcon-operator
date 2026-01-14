#!/usr/bin/env python3
"""
Real-time Profit/Loss Checker for Open Positions
Fetches current prices and calculates P&L for all open positions
"""

import sqlite3
import yfinance as yf
from datetime import datetime
from typing import List, Dict

def get_open_positions() -> List[Dict]:
    """Fetch all open positions from database"""
    conn = sqlite3.connect('paper_trading.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT symbol, quantity, entry_price, stop_loss, profit_target,
               strategy, classification, entry_date
        FROM positions
        ORDER BY entry_date DESC
    """)

    positions = []
    for row in cursor.fetchall():
        positions.append({
            'symbol': row['symbol'],
            'quantity': row['quantity'],
            'entry_price': row['entry_price'],
            'stop_loss': row['stop_loss'] if row['stop_loss'] else 0,
            'profit_target': row['profit_target'] if row['profit_target'] else 0,
            'strategy': row['strategy'] if row['strategy'] else 'unknown',
            'classification': row['classification'] if row['classification'] else 'N/A',
            'entry_date': row['entry_date']
        })

    conn.close()
    return positions

def fetch_current_price(symbol: str) -> float:
    """Fetch current price using yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        # Get most recent price
        hist = ticker.history(period='1d')
        if not hist.empty:
            return hist['Close'].iloc[-1]
        else:
            # Try 5 day history if today's data not available
            hist = ticker.history(period='5d')
            if not hist.empty:
                return hist['Close'].iloc[-1]
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
    return 0.0

def calculate_pnl(position: Dict, current_price: float) -> Dict:
    """Calculate profit/loss for a position"""
    qty = position['quantity']
    entry = position['entry_price']

    invested = qty * entry
    current_value = qty * current_price
    pnl_dollars = current_value - invested
    pnl_percent = (pnl_dollars / invested) * 100 if invested > 0 else 0

    # Check if at stop-loss or profit target
    stop_loss = position['stop_loss']
    profit_target = position['profit_target']

    at_stop = stop_loss > 0 and current_price <= stop_loss
    at_target = profit_target > 0 and current_price >= profit_target

    return {
        'symbol': position['symbol'],
        'strategy': position['strategy'],
        'classification': position['classification'],
        'quantity': qty,
        'entry_price': entry,
        'current_price': current_price,
        'invested': invested,
        'current_value': current_value,
        'pnl_dollars': pnl_dollars,
        'pnl_percent': pnl_percent,
        'stop_loss': stop_loss,
        'profit_target': profit_target,
        'at_stop_loss': at_stop,
        'at_profit_target': at_target,
        'entry_date': position['entry_date']
    }

def main():
    """Main P&L checker"""
    print("=" * 80)
    print("REAL-TIME PROFIT/LOSS CHECK")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    # Get open positions
    positions = get_open_positions()

    if not positions:
        print("No open positions found.")
        return

    print(f"Checking {len(positions)} open positions...\n")

    # Calculate P&L for each position
    pnl_data = []
    total_invested = 0
    total_current_value = 0

    for pos in positions:
        print(f"Fetching price for {pos['symbol']}...", end=' ')
        current_price = fetch_current_price(pos['symbol'])
        print(f"${current_price:.2f}")

        pnl = calculate_pnl(pos, current_price)
        pnl_data.append(pnl)

        total_invested += pnl['invested']
        total_current_value += pnl['current_value']

    print("\n" + "=" * 80)
    print("POSITION DETAILS")
    print("=" * 80)

    # Sort by P&L percentage
    pnl_data.sort(key=lambda x: x['pnl_percent'], reverse=True)

    for pnl in pnl_data:
        print(f"\n{pnl['symbol']} ({pnl['strategy']})")
        print(f"  Classification: {pnl['classification']}")
        print(f"  Quantity: {pnl['quantity']:,} shares")
        print(f"  Entry Price: ${pnl['entry_price']:.2f}")
        print(f"  Current Price: ${pnl['current_price']:.2f}")
        print(f"  Invested: ${pnl['invested']:,.2f}")
        print(f"  Current Value: ${pnl['current_value']:,.2f}")

        # Color-code P&L
        pnl_sign = '+' if pnl['pnl_dollars'] >= 0 else ''
        print(f"  P&L: {pnl_sign}${pnl['pnl_dollars']:.2f} ({pnl_sign}{pnl['pnl_percent']:.2f}%)")

        # Check triggers
        if pnl['at_stop_loss']:
            print(f"  [!] AT STOP-LOSS (${pnl['stop_loss']:.2f}) - Should exit!")
        if pnl['at_profit_target']:
            print(f"  [TARGET] AT PROFIT TARGET (${pnl['profit_target']:.2f}) - Consider exit!")

        if pnl['stop_loss'] > 0:
            print(f"  Stop-Loss: ${pnl['stop_loss']:.2f}")
        if pnl['profit_target'] > 0:
            print(f"  Profit Target: ${pnl['profit_target']:.2f}")

    # Portfolio summary
    print("\n" + "=" * 80)
    print("PORTFOLIO SUMMARY")
    print("=" * 80)

    total_pnl_dollars = total_current_value - total_invested
    total_pnl_percent = (total_pnl_dollars / total_invested) * 100 if total_invested > 0 else 0

    print(f"Total Invested: ${total_invested:,.2f}")
    print(f"Current Value: ${total_current_value:,.2f}")

    pnl_sign = '+' if total_pnl_dollars >= 0 else ''
    print(f"Total P&L: {pnl_sign}${total_pnl_dollars:.2f} ({pnl_sign}{total_pnl_percent:.2f}%)")

    # Best/worst performers
    if len(pnl_data) > 0:
        best = pnl_data[0]
        worst = pnl_data[-1]

        print(f"\nBest Performer: {best['symbol']} ({best['pnl_percent']:+.2f}%)")
        print(f"Worst Performer: {worst['symbol']} ({worst['pnl_percent']:+.2f}%)")

    # Positions needing attention
    attention_needed = [p for p in pnl_data if p['at_stop_loss'] or p['at_profit_target']]
    if attention_needed:
        print(f"\n[ATTENTION] {len(attention_needed)} position(s) need attention:")
        for p in attention_needed:
            if p['at_stop_loss']:
                print(f"  - {p['symbol']}: At stop-loss, should exit")
            if p['at_profit_target']:
                print(f"  - {p['symbol']}: At profit target, consider exit")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
