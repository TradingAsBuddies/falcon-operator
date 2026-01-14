"""
Example unit tests for financial calculations

This file demonstrates proper unit testing structure for the Falcon trading system.
These tests should be expanded to cover all calculation logic.
"""
import pytest


class TestPositionPnL:
    """Test position P&L calculations"""

    @staticmethod
    def calculate_position_pnl(quantity, entry_price, current_price):
        """
        Calculate position P&L
        (This is a mock - actual implementation should be imported from your module)
        """
        invested = quantity * entry_price
        current_value = quantity * current_price
        pnl_dollars = current_value - invested
        pnl_percent = (pnl_dollars / invested) * 100 if invested > 0 else 0
        return pnl_dollars, pnl_percent

    def test_positive_pnl(self):
        """Test calculating positive P&L"""
        quantity = 100
        entry_price = 10.0
        current_price = 15.0

        pnl_dollars, pnl_percent = self.calculate_position_pnl(
            quantity, entry_price, current_price
        )

        assert pnl_dollars == 500.0  # (15-10) * 100
        assert pnl_percent == 50.0   # ((15-10)/10) * 100

    def test_negative_pnl(self):
        """Test calculating negative P&L"""
        quantity = 100
        entry_price = 10.0
        current_price = 8.0

        pnl_dollars, pnl_percent = self.calculate_position_pnl(
            quantity, entry_price, current_price
        )

        assert pnl_dollars == -200.0
        assert pnl_percent == -20.0

    def test_zero_pnl(self):
        """Test no change in price"""
        quantity = 100
        entry_price = 10.0
        current_price = 10.0

        pnl_dollars, pnl_percent = self.calculate_position_pnl(
            quantity, entry_price, current_price
        )

        assert pnl_dollars == 0.0
        assert pnl_percent == 0.0

    def test_fractional_shares(self):
        """Test with fractional shares"""
        quantity = 123.45
        entry_price = 12.34
        current_price = 15.67

        pnl_dollars, pnl_percent = self.calculate_position_pnl(
            quantity, entry_price, current_price
        )

        expected_dollars = (15.67 - 12.34) * 123.45
        expected_percent = ((15.67 - 12.34) / 12.34) * 100

        assert pytest.approx(pnl_dollars, 0.01) == expected_dollars
        assert pytest.approx(pnl_percent, 0.01) == expected_percent

    def test_zero_entry_price(self):
        """Test edge case with zero entry price"""
        quantity = 100
        entry_price = 0
        current_price = 10.0

        pnl_dollars, pnl_percent = self.calculate_position_pnl(
            quantity, entry_price, current_price
        )

        assert pnl_dollars == 1000.0
        assert pnl_percent == 0.0  # Should handle division by zero


class TestPortfolioPnL:
    """Test portfolio-level P&L calculations"""

    @staticmethod
    def calculate_portfolio_pnl(positions):
        """
        Calculate total portfolio P&L
        positions: list of dicts with 'quantity', 'entry_price', 'current_price'
        """
        total_invested = 0
        total_current = 0

        for pos in positions:
            invested = pos['quantity'] * pos['entry_price']
            current = pos['quantity'] * pos['current_price']
            total_invested += invested
            total_current += current

        pnl_dollars = total_current - total_invested
        pnl_percent = (pnl_dollars / total_invested) * 100 if total_invested > 0 else 0

        return pnl_dollars, pnl_percent

    def test_multiple_positions_mixed_pnl(self):
        """Test portfolio with winning and losing positions"""
        positions = [
            {'quantity': 100, 'entry_price': 10.0, 'current_price': 15.0},  # +$500
            {'quantity': 50, 'entry_price': 20.0, 'current_price': 18.0},   # -$100
            {'quantity': 200, 'entry_price': 5.0, 'current_price': 6.0},    # +$200
        ]

        pnl_dollars, pnl_percent = self.calculate_portfolio_pnl(positions)

        # Total invested: 100*10 + 50*20 + 200*5 = 1000 + 1000 + 1000 = 3000
        # Total current: 100*15 + 50*18 + 200*6 = 1500 + 900 + 1200 = 3600
        # P&L: 3600 - 3000 = 600
        # Percent: 600/3000 * 100 = 20%

        assert pnl_dollars == 600.0
        assert pnl_percent == 20.0

    def test_empty_portfolio(self):
        """Test empty portfolio"""
        positions = []

        pnl_dollars, pnl_percent = self.calculate_portfolio_pnl(positions)

        assert pnl_dollars == 0.0
        assert pnl_percent == 0.0

    def test_single_position(self):
        """Test portfolio with single position"""
        positions = [
            {'quantity': 100, 'entry_price': 10.0, 'current_price': 12.0}
        ]

        pnl_dollars, pnl_percent = self.calculate_portfolio_pnl(positions)

        assert pnl_dollars == 200.0
        assert pnl_percent == 20.0


class TestWinRate:
    """Test win rate calculations"""

    @staticmethod
    def calculate_win_rate(trades):
        """
        Calculate win rate from list of trades
        trades: list of dicts with 'pnl' field
        """
        if not trades:
            return 0.0

        winning_trades = sum(1 for t in trades if t['pnl'] > 0)
        total_trades = len(trades)

        return (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0

    def test_all_winning_trades(self):
        """Test 100% win rate"""
        trades = [
            {'pnl': 100},
            {'pnl': 200},
            {'pnl': 50}
        ]

        win_rate = self.calculate_win_rate(trades)
        assert win_rate == 100.0

    def test_all_losing_trades(self):
        """Test 0% win rate"""
        trades = [
            {'pnl': -100},
            {'pnl': -200},
            {'pnl': -50}
        ]

        win_rate = self.calculate_win_rate(trades)
        assert win_rate == 0.0

    def test_mixed_trades(self):
        """Test mixed win/loss"""
        trades = [
            {'pnl': 100},   # Win
            {'pnl': -50},   # Loss
            {'pnl': 200},   # Win
            {'pnl': -100},  # Loss
            {'pnl': 150}    # Win
        ]

        win_rate = self.calculate_win_rate(trades)
        assert win_rate == 60.0  # 3 wins out of 5 = 60%

    def test_empty_trades(self):
        """Test with no trades"""
        trades = []

        win_rate = self.calculate_win_rate(trades)
        assert win_rate == 0.0

    def test_breakeven_not_counted_as_win(self):
        """Test that breakeven trades are not counted as wins"""
        trades = [
            {'pnl': 100},   # Win
            {'pnl': 0},     # Breakeven - not a win
            {'pnl': -50}    # Loss
        ]

        win_rate = self.calculate_win_rate(trades)
        assert win_rate == pytest.approx(33.33, 0.01)  # 1 win out of 3


if __name__ == '__main__':
    # Run tests with: pytest tests/unit/test_calculations_example.py -v
    pytest.main([__file__, '-v'])
