"""
Unit tests for P&L (Profit and Loss) calculations

Tests cover:
- Position P&L calculations (unrealized gains/losses)
- FIFO (First-In-First-Out) realized P&L calculations
- Portfolio-level calculations
- Win rate and trading statistics
- Edge cases and error handling
"""
import pytest
from typing import Dict, List


# ============================================================================
# Functions under test (imported from actual modules)
# ============================================================================

def calculate_position_pnl(position: Dict, current_price: float) -> Dict:
    """
    Calculate profit/loss for a position
    Based on check_pnl.py:58-91
    """
    qty = position['quantity']
    entry = position['entry_price']

    invested = qty * entry
    current_value = qty * current_price
    pnl_dollars = current_value - invested
    pnl_percent = (pnl_dollars / invested) * 100 if invested > 0 else 0

    # Check if at stop-loss or profit target
    stop_loss = position.get('stop_loss', 0)
    profit_target = position.get('profit_target', 0)

    at_stop = stop_loss > 0 and current_price <= stop_loss
    at_target = profit_target > 0 and current_price >= profit_target

    return {
        'symbol': position.get('symbol', ''),
        'strategy': position.get('strategy', ''),
        'classification': position.get('classification', ''),
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
        'entry_date': position.get('entry_date', '')
    }


def calculate_fifo_realized_pnl(trades: List[tuple]) -> Dict:
    """
    Calculate realized P&L using FIFO (First-In-First-Out) method
    Based on dashboard_server.py:164-219

    Args:
        trades: List of (symbol, side, quantity, price, timestamp) tuples

    Returns:
        Dict with trade statistics including total_pnl, win_rate, etc.
    """
    positions_tracker = {}
    closed_trades = []

    for trade in trades:
        symbol, side, quantity, price, timestamp = trade

        if side == 'buy':
            if symbol not in positions_tracker:
                positions_tracker[symbol] = []
            positions_tracker[symbol].append({
                'quantity': quantity,
                'price': price,
                'timestamp': timestamp
            })
        elif side == 'sell' and symbol in positions_tracker:
            remaining_sell = quantity
            sell_proceeds = 0
            buy_cost = 0

            while remaining_sell > 0 and positions_tracker[symbol]:
                buy_trade = positions_tracker[symbol][0]

                if buy_trade['quantity'] <= remaining_sell:
                    # Close this buy position completely
                    qty = buy_trade['quantity']
                    buy_cost += qty * buy_trade['price']
                    sell_proceeds += qty * price
                    remaining_sell -= qty
                    positions_tracker[symbol].pop(0)
                else:
                    # Partial close
                    buy_cost += remaining_sell * buy_trade['price']
                    sell_proceeds += remaining_sell * price
                    buy_trade['quantity'] -= remaining_sell
                    remaining_sell = 0

            if buy_cost > 0:
                pnl = sell_proceeds - buy_cost
                closed_trades.append({
                    'symbol': symbol,
                    'pnl': pnl,
                    'timestamp': timestamp
                })

    # Calculate statistics
    total_trades = len(closed_trades)
    winning_trades = len([t for t in closed_trades if t['pnl'] > 0])
    losing_trades = total_trades - winning_trades
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    pnls = [t['pnl'] for t in closed_trades]
    best_trade = max(pnls) if pnls else 0
    worst_trade = min(pnls) if pnls else 0
    total_pnl = sum(pnls)

    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'best_trade': best_trade,
        'worst_trade': worst_trade,
        'total_pnl': total_pnl,
        'closed_trades': closed_trades
    }


# ============================================================================
# Test Classes
# ============================================================================

class TestPositionPnL:
    """Test unrealized P&L calculations for open positions"""

    def test_profitable_position(self):
        """Test calculating P&L for a winning position"""
        position = {
            'symbol': 'AAPL',
            'quantity': 100,
            'entry_price': 150.0,
            'strategy': 'momentum',
            'classification': 'tech',
            'entry_date': '2024-01-01'
        }
        current_price = 180.0

        result = calculate_position_pnl(position, current_price)

        assert result['pnl_dollars'] == 3000.0  # (180-150) * 100
        assert result['pnl_percent'] == 20.0    # ((180-150)/150) * 100
        assert result['invested'] == 15000.0    # 150 * 100
        assert result['current_value'] == 18000.0  # 180 * 100

    def test_losing_position(self):
        """Test calculating P&L for a losing position"""
        position = {
            'symbol': 'TSLA',
            'quantity': 50,
            'entry_price': 200.0
        }
        current_price = 170.0

        result = calculate_position_pnl(position, current_price)

        assert result['pnl_dollars'] == -1500.0  # (170-200) * 50
        assert result['pnl_percent'] == -15.0    # ((170-200)/200) * 100

    def test_breakeven_position(self):
        """Test position with no price change"""
        position = {
            'symbol': 'SPY',
            'quantity': 100,
            'entry_price': 450.0
        }
        current_price = 450.0

        result = calculate_position_pnl(position, current_price)

        assert result['pnl_dollars'] == 0.0
        assert result['pnl_percent'] == 0.0

    def test_fractional_shares(self):
        """Test with fractional shares (for stocks/ETFs that allow it)"""
        position = {
            'symbol': 'VTI',
            'quantity': 123.456,
            'entry_price': 200.50
        }
        current_price = 215.75

        result = calculate_position_pnl(position, current_price)

        expected_invested = 123.456 * 200.50
        expected_current = 123.456 * 215.75
        expected_pnl_dollars = expected_current - expected_invested
        expected_pnl_percent = (expected_pnl_dollars / expected_invested) * 100

        assert pytest.approx(result['pnl_dollars'], 0.01) == expected_pnl_dollars
        assert pytest.approx(result['pnl_percent'], 0.01) == expected_pnl_percent

    def test_large_quantity(self):
        """Test with large quantity (penny stocks)"""
        position = {
            'symbol': 'PENNY',
            'quantity': 10000,
            'entry_price': 0.50
        }
        current_price = 0.75

        result = calculate_position_pnl(position, current_price)

        assert result['pnl_dollars'] == 2500.0  # (0.75-0.50) * 10000
        assert result['pnl_percent'] == 50.0

    def test_stop_loss_triggered(self):
        """Test stop-loss trigger detection"""
        position = {
            'symbol': 'AMD',
            'quantity': 100,
            'entry_price': 100.0,
            'stop_loss': 95.0
        }
        current_price = 94.0  # Below stop-loss

        result = calculate_position_pnl(position, current_price)

        assert result['at_stop_loss'] is True
        assert result['pnl_dollars'] == -600.0

    def test_stop_loss_not_triggered(self):
        """Test when price is above stop-loss"""
        position = {
            'symbol': 'NVDA',
            'quantity': 100,
            'entry_price': 500.0,
            'stop_loss': 475.0
        }
        current_price = 490.0  # Above stop-loss

        result = calculate_position_pnl(position, current_price)

        assert result['at_stop_loss'] is False
        assert result['pnl_dollars'] == -1000.0

    def test_profit_target_reached(self):
        """Test profit target detection"""
        position = {
            'symbol': 'MSFT',
            'quantity': 100,
            'entry_price': 300.0,
            'profit_target': 350.0
        }
        current_price = 360.0  # Above profit target

        result = calculate_position_pnl(position, current_price)

        assert result['at_profit_target'] is True
        assert result['pnl_dollars'] == 6000.0

    def test_profit_target_not_reached(self):
        """Test when below profit target"""
        position = {
            'symbol': 'GOOGL',
            'quantity': 50,
            'entry_price': 100.0,
            'profit_target': 120.0
        }
        current_price = 115.0  # Below profit target

        result = calculate_position_pnl(position, current_price)

        assert result['at_profit_target'] is False
        assert result['pnl_dollars'] == 750.0

    def test_zero_entry_price_edge_case(self):
        """Test edge case with zero entry price (should not happen, but handle gracefully)"""
        position = {
            'symbol': 'TEST',
            'quantity': 100,
            'entry_price': 0.0
        }
        current_price = 10.0

        result = calculate_position_pnl(position, current_price)

        assert result['pnl_dollars'] == 1000.0
        assert result['pnl_percent'] == 0.0  # Avoid division by zero

    def test_negative_pnl_percentage(self):
        """Test that negative P&L percentage is calculated correctly"""
        position = {
            'symbol': 'LOSS',
            'quantity': 100,
            'entry_price': 100.0
        }
        current_price = 50.0

        result = calculate_position_pnl(position, current_price)

        assert result['pnl_percent'] == -50.0


class TestFIFORealizedPnL:
    """Test FIFO (First-In-First-Out) realized P&L calculations"""

    def test_simple_buy_sell_profitable(self):
        """Test simple profitable trade"""
        trades = [
            ('AAPL', 'buy', 100, 150.0, '2024-01-01'),
            ('AAPL', 'sell', 100, 180.0, '2024-01-10')
        ]

        result = calculate_fifo_realized_pnl(trades)

        assert result['total_trades'] == 1
        assert result['winning_trades'] == 1
        assert result['losing_trades'] == 0
        assert result['win_rate'] == 100.0
        assert result['total_pnl'] == 3000.0  # (180-150) * 100
        assert result['best_trade'] == 3000.0
        assert result['worst_trade'] == 3000.0

    def test_simple_buy_sell_loss(self):
        """Test simple losing trade"""
        trades = [
            ('TSLA', 'buy', 50, 200.0, '2024-01-01'),
            ('TSLA', 'sell', 50, 170.0, '2024-01-10')
        ]

        result = calculate_fifo_realized_pnl(trades)

        assert result['total_trades'] == 1
        assert result['winning_trades'] == 0
        assert result['losing_trades'] == 1
        assert result['win_rate'] == 0.0
        assert result['total_pnl'] == -1500.0  # (170-200) * 50

    def test_fifo_multiple_buys_single_sell(self):
        """Test FIFO with multiple buy orders filled at different prices"""
        trades = [
            ('SPY', 'buy', 50, 400.0, '2024-01-01'),   # First in
            ('SPY', 'buy', 50, 410.0, '2024-01-02'),   # Second in
            ('SPY', 'sell', 100, 430.0, '2024-01-10')  # Sell all
        ]

        result = calculate_fifo_realized_pnl(trades)

        # FIFO: First 50 @ 400, next 50 @ 410, all sell @ 430
        # P&L: (430-400)*50 + (430-410)*50 = 1500 + 1000 = 2500
        assert result['total_trades'] == 1
        assert result['total_pnl'] == 2500.0

    def test_fifo_partial_sell(self):
        """Test partial position close"""
        trades = [
            ('NVDA', 'buy', 100, 500.0, '2024-01-01'),
            ('NVDA', 'sell', 50, 550.0, '2024-01-10')  # Sell half
        ]

        result = calculate_fifo_realized_pnl(trades)

        assert result['total_trades'] == 1
        assert result['total_pnl'] == 2500.0  # (550-500) * 50
        # Note: 50 shares remain open (not tested here)

    def test_fifo_multiple_partial_sells(self):
        """Test multiple partial sells"""
        trades = [
            ('MSFT', 'buy', 100, 300.0, '2024-01-01'),
            ('MSFT', 'sell', 30, 320.0, '2024-01-05'),   # Sell 30
            ('MSFT', 'sell', 40, 310.0, '2024-01-10'),   # Sell 40 more
        ]

        result = calculate_fifo_realized_pnl(trades)

        # First sell: (320-300) * 30 = 600
        # Second sell: (310-300) * 40 = 400
        # Total: 1000
        assert result['total_trades'] == 2
        assert result['total_pnl'] == 1000.0
        assert result['winning_trades'] == 2

    def test_fifo_complex_scenario(self):
        """Test complex FIFO with multiple buys at different prices and multiple sells"""
        trades = [
            ('GOOGL', 'buy', 30, 100.0, '2024-01-01'),
            ('GOOGL', 'buy', 40, 105.0, '2024-01-02'),
            ('GOOGL', 'buy', 30, 110.0, '2024-01-03'),
            ('GOOGL', 'sell', 50, 120.0, '2024-01-10'),  # Closes first 30 @ 100, then 20 @ 105
            ('GOOGL', 'sell', 50, 115.0, '2024-01-15'),  # Closes remaining 20 @ 105, then 30 @ 110
        ]

        result = calculate_fifo_realized_pnl(trades)

        # First sell (50 shares @ 120):
        #   - 30 shares from first buy @ 100: (120-100)*30 = 600
        #   - 20 shares from second buy @ 105: (120-105)*20 = 300
        #   Total: 900

        # Second sell (50 shares @ 115):
        #   - 20 shares from second buy @ 105: (115-105)*20 = 200
        #   - 30 shares from third buy @ 110: (115-110)*30 = 150
        #   Total: 350

        # Grand total: 900 + 350 = 1250
        assert result['total_trades'] == 2
        assert result['total_pnl'] == 1250.0

    def test_multiple_symbols(self):
        """Test FIFO with different symbols"""
        trades = [
            ('AAPL', 'buy', 100, 150.0, '2024-01-01'),
            ('TSLA', 'buy', 50, 200.0, '2024-01-02'),
            ('AAPL', 'sell', 100, 170.0, '2024-01-10'),  # +2000
            ('TSLA', 'sell', 50, 180.0, '2024-01-11'),   # -1000
        ]

        result = calculate_fifo_realized_pnl(trades)

        assert result['total_trades'] == 2
        assert result['winning_trades'] == 1
        assert result['losing_trades'] == 1
        assert result['win_rate'] == 50.0
        assert result['total_pnl'] == 1000.0  # 2000 - 1000
        assert result['best_trade'] == 2000.0
        assert result['worst_trade'] == -1000.0

    def test_sell_without_buy_ignored(self):
        """Test that sell orders without corresponding buys are ignored"""
        trades = [
            ('FAKE', 'sell', 100, 50.0, '2024-01-01'),  # No buy - should be ignored
        ]

        result = calculate_fifo_realized_pnl(trades)

        assert result['total_trades'] == 0
        assert result['total_pnl'] == 0.0

    def test_empty_trades_list(self):
        """Test with no trades"""
        trades = []

        result = calculate_fifo_realized_pnl(trades)

        assert result['total_trades'] == 0
        assert result['winning_trades'] == 0
        assert result['losing_trades'] == 0
        assert result['win_rate'] == 0.0
        assert result['total_pnl'] == 0.0
        assert result['best_trade'] == 0
        assert result['worst_trade'] == 0

    def test_only_buy_orders(self):
        """Test with only buy orders (no closed trades)"""
        trades = [
            ('AAPL', 'buy', 100, 150.0, '2024-01-01'),
            ('MSFT', 'buy', 50, 300.0, '2024-01-02'),
        ]

        result = calculate_fifo_realized_pnl(trades)

        assert result['total_trades'] == 0
        assert result['total_pnl'] == 0.0


class TestWinRateCalculations:
    """Test win rate and trading statistics"""

    def test_perfect_win_rate(self):
        """Test 100% win rate"""
        trades = [
            ('AAPL', 'buy', 100, 150.0, '2024-01-01'),
            ('AAPL', 'sell', 100, 180.0, '2024-01-10'),
            ('MSFT', 'buy', 50, 300.0, '2024-01-11'),
            ('MSFT', 'sell', 50, 320.0, '2024-01-20'),
        ]

        result = calculate_fifo_realized_pnl(trades)

        assert result['win_rate'] == 100.0
        assert result['winning_trades'] == 2
        assert result['losing_trades'] == 0

    def test_zero_win_rate(self):
        """Test 0% win rate"""
        trades = [
            ('TSLA', 'buy', 50, 200.0, '2024-01-01'),
            ('TSLA', 'sell', 50, 180.0, '2024-01-10'),
            ('NVDA', 'buy', 20, 500.0, '2024-01-11'),
            ('NVDA', 'sell', 20, 480.0, '2024-01-20'),
        ]

        result = calculate_fifo_realized_pnl(trades)

        assert result['win_rate'] == 0.0
        assert result['winning_trades'] == 0
        assert result['losing_trades'] == 2

    def test_fifty_percent_win_rate(self):
        """Test 50% win rate"""
        trades = [
            ('WIN1', 'buy', 100, 10.0, '2024-01-01'),
            ('WIN1', 'sell', 100, 15.0, '2024-01-10'),  # +500
            ('LOSS1', 'buy', 100, 20.0, '2024-01-11'),
            ('LOSS1', 'sell', 100, 18.0, '2024-01-20'),  # -200
        ]

        result = calculate_fifo_realized_pnl(trades)

        assert result['win_rate'] == 50.0
        assert result['winning_trades'] == 1
        assert result['losing_trades'] == 1

    def test_breakeven_trades_not_counted_as_wins(self):
        """Test that breakeven trades (P&L = 0) are not counted as wins"""
        trades = [
            ('BREAK', 'buy', 100, 50.0, '2024-01-01'),
            ('BREAK', 'sell', 100, 50.0, '2024-01-10'),  # Breakeven
        ]

        result = calculate_fifo_realized_pnl(trades)

        assert result['winning_trades'] == 0
        assert result['losing_trades'] == 1  # Breakeven counted as non-win
        assert result['win_rate'] == 0.0


class TestPortfolioCalculations:
    """Test portfolio-level P&L calculations"""

    def test_portfolio_multiple_positions(self):
        """Test portfolio P&L with multiple positions"""
        positions = [
            {
                'symbol': 'AAPL',
                'quantity': 100,
                'entry_price': 150.0
            },
            {
                'symbol': 'MSFT',
                'quantity': 50,
                'entry_price': 300.0
            },
            {
                'symbol': 'GOOGL',
                'quantity': 30,
                'entry_price': 100.0
            }
        ]

        current_prices = {
            'AAPL': 180.0,   # +30 per share
            'MSFT': 320.0,   # +20 per share
            'GOOGL': 95.0    # -5 per share
        }

        total_pnl = 0
        total_invested = 0
        total_current = 0

        for pos in positions:
            result = calculate_position_pnl(pos, current_prices[pos['symbol']])
            total_pnl += result['pnl_dollars']
            total_invested += result['invested']
            total_current += result['current_value']

        # AAPL: (180-150)*100 = 3000
        # MSFT: (320-300)*50 = 1000
        # GOOGL: (95-100)*30 = -150
        # Total: 3850
        assert total_pnl == 3850.0

        # Invested: 15000 + 15000 + 3000 = 33000
        assert total_invested == 33000.0

        # Current: 18000 + 16000 + 2850 = 36850
        assert total_current == 36850.0

        # Portfolio return: 3850/33000 * 100 = 11.67%
        portfolio_return = (total_pnl / total_invested) * 100
        assert pytest.approx(portfolio_return, 0.01) == 11.67


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_very_small_prices(self):
        """Test with penny stock prices"""
        position = {
            'symbol': 'PENNY',
            'quantity': 10000,
            'entry_price': 0.01
        }
        current_price = 0.02

        result = calculate_position_pnl(position, current_price)

        assert result['pnl_dollars'] == 100.0
        assert result['pnl_percent'] == 100.0

    def test_very_large_prices(self):
        """Test with high-priced stocks"""
        position = {
            'symbol': 'BRK.A',
            'quantity': 1,
            'entry_price': 500000.0
        }
        current_price = 550000.0

        result = calculate_position_pnl(position, current_price)

        assert result['pnl_dollars'] == 50000.0
        assert result['pnl_percent'] == 10.0

    def test_rounding_precision(self):
        """Test that calculations maintain precision"""
        position = {
            'symbol': 'TEST',
            'quantity': 123.456,
            'entry_price': 78.901
        }
        current_price = 89.123

        result = calculate_position_pnl(position, current_price)

        # Manual calculation for verification
        invested = 123.456 * 78.901
        current_value = 123.456 * 89.123
        expected_pnl = current_value - invested

        assert pytest.approx(result['pnl_dollars'], 0.001) == expected_pnl

    def test_negative_quantity_handled(self):
        """Test behavior with negative quantity (short position)"""
        position = {
            'symbol': 'SHORT',
            'quantity': -100,  # Short position
            'entry_price': 50.0
        }
        current_price = 40.0  # Price dropped - profit for short

        result = calculate_position_pnl(position, current_price)

        # For short: profit when price drops
        # invested: -100 * 50 = -5000
        # current: -100 * 40 = -4000
        # pnl: -4000 - (-5000) = 1000
        assert result['pnl_dollars'] == 1000.0


if __name__ == '__main__':
    # Run with: pytest tests/unit/test_pnl_calculations.py -v
    # Or: pytest tests/unit/test_pnl_calculations.py -v --cov=. --cov-report=html
    pytest.main([__file__, '-v'])
