"""
Unit tests for Account Balance Updater

Tests ensure that balance calculations and updates work correctly
without breaking existing functionality.
"""
import pytest
import sqlite3
import tempfile
import os
from datetime import datetime
from unittest.mock import patch, MagicMock


# Import functions to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from account_balance_updater import (
    calculate_account_balance,
    update_account_balance,
    add_performance_record,
    check_balance_discrepancy
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_database():
    """Create a temporary test database"""
    # Create temp file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Initialize database
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Create account table
    cursor.execute("""
        CREATE TABLE account (
            id INTEGER PRIMARY KEY,
            cash REAL NOT NULL,
            last_updated TEXT NOT NULL,
            total_value REAL DEFAULT 0
        )
    """)

    # Create positions table
    cursor.execute("""
        CREATE TABLE positions (
            symbol TEXT PRIMARY KEY,
            quantity REAL NOT NULL,
            entry_price REAL NOT NULL,
            current_price REAL DEFAULT 0,
            entry_date TEXT NOT NULL,
            last_updated TEXT NOT NULL
        )
    """)

    # Create performance table
    cursor.execute("""
        CREATE TABLE performance (
            timestamp TEXT PRIMARY KEY,
            total_value REAL NOT NULL,
            cash REAL NOT NULL,
            positions_value REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    yield path

    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def populated_database(temp_database):
    """Database with sample data"""
    conn = sqlite3.connect(temp_database)
    cursor = conn.cursor()

    # Insert account
    cursor.execute("""
        INSERT INTO account (id, cash, last_updated, total_value)
        VALUES (1, 5000.0, '2024-01-01', 10000.0)
    """)

    # Insert positions
    positions = [
        ('AAPL', 100, 150.0, 160.0),  # Worth $16,000
        ('MSFT', 50, 300.0, 320.0),   # Worth $16,000
        ('GOOGL', 30, 100.0, 95.0)    # Worth $2,850
    ]

    for symbol, qty, entry, current in positions:
        cursor.execute("""
            INSERT INTO positions (symbol, quantity, entry_price, current_price, entry_date, last_updated)
            VALUES (?, ?, ?, ?, '2024-01-01', '2024-01-02')
        """, (symbol, qty, entry, current))

    conn.commit()
    conn.close()

    return temp_database


# ============================================================================
# Test Balance Calculation
# ============================================================================

class TestCalculateAccountBalance:
    """Test balance calculation logic"""

    def test_calculate_with_cash_only(self, temp_database):
        """Test calculation with cash, no positions"""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO account (id, cash, last_updated) VALUES (1, 10000.0, '2024-01-01')")
        conn.commit()
        conn.close()

        result = calculate_account_balance(temp_database)

        assert result is not None
        assert result['cash'] == 10000.0
        assert result['positions_value'] == 0.0
        assert result['total_value'] == 10000.0
        assert result['num_positions'] == 0

    def test_calculate_with_positions(self, populated_database):
        """Test calculation with cash and positions"""
        result = calculate_account_balance(populated_database)

        assert result is not None
        assert result['cash'] == 5000.0
        # AAPL: 100*160 = 16000, MSFT: 50*320 = 16000, GOOGL: 30*95 = 2850
        # Total positions: 34850
        assert result['positions_value'] == 34850.0
        assert result['total_value'] == 39850.0  # 5000 + 34850
        assert result['num_positions'] == 3

    def test_calculate_with_fractional_shares(self, temp_database):
        """Test with fractional share quantities"""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO account (id, cash, last_updated) VALUES (1, 1000.0, '2024-01-01')")
        cursor.execute("""
            INSERT INTO positions (symbol, quantity, entry_price, current_price, entry_date, last_updated)
            VALUES ('VTI', 123.456, 200.0, 215.75, '2024-01-01', '2024-01-02')
        """)

        conn.commit()
        conn.close()

        result = calculate_account_balance(temp_database)

        expected_position_value = 123.456 * 215.75
        assert result is not None
        assert pytest.approx(result['positions_value'], 0.01) == expected_position_value
        assert pytest.approx(result['total_value'], 0.01) == 1000.0 + expected_position_value

    def test_calculate_with_zero_price_position(self, temp_database):
        """Test handling of zero-priced position"""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO account (id, cash, last_updated) VALUES (1, 1000.0, '2024-01-01')")
        cursor.execute("""
            INSERT INTO positions (symbol, quantity, entry_price, current_price, entry_date, last_updated)
            VALUES ('TEST', 100, 10.0, 0.0, '2024-01-01', '2024-01-02')
        """)

        conn.commit()
        conn.close()

        result = calculate_account_balance(temp_database)

        assert result is not None
        assert result['positions_value'] == 0.0
        assert result['total_value'] == 1000.0

    def test_calculate_with_no_account(self, temp_database):
        """Test error handling when account doesn't exist"""
        result = calculate_account_balance(temp_database)

        assert result is None

    def test_calculate_with_empty_positions(self, temp_database):
        """Test with account but no positions"""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO account (id, cash, last_updated) VALUES (1, 5000.0, '2024-01-01')")
        conn.commit()
        conn.close()

        result = calculate_account_balance(temp_database)

        assert result is not None
        assert result['cash'] == 5000.0
        assert result['positions_value'] == 0.0
        assert result['total_value'] == 5000.0
        assert result['num_positions'] == 0


# ============================================================================
# Test Balance Update
# ============================================================================

class TestUpdateAccountBalance:
    """Test account balance update operations"""

    def test_update_sets_correct_balance(self, populated_database):
        """Test that update sets the correct total_value"""
        result = update_account_balance(populated_database)

        assert result is not None
        assert result['total_value'] == 39850.0

        # Verify database was updated
        conn = sqlite3.connect(populated_database)
        cursor = conn.cursor()
        cursor.execute("SELECT total_value FROM account WHERE id = 1")
        stored_value = cursor.fetchone()[0]
        conn.close()

        assert stored_value == 39850.0

    def test_update_sets_last_updated(self, populated_database):
        """Test that last_updated timestamp is set"""
        before_update = datetime.now()
        update_account_balance(populated_database)
        after_update = datetime.now()

        conn = sqlite3.connect(populated_database)
        cursor = conn.cursor()
        cursor.execute("SELECT last_updated FROM account WHERE id = 1")
        last_updated_str = cursor.fetchone()[0]
        conn.close()

        last_updated = datetime.fromisoformat(last_updated_str)

        # Timestamp should be between before and after
        assert before_update <= last_updated <= after_update

    def test_update_with_no_account(self, temp_database):
        """Test update fails gracefully with no account"""
        result = update_account_balance(temp_database)

        assert result is None

    def test_update_maintains_cash_value(self, populated_database):
        """Test that update doesn't modify cash"""
        original_cash = 5000.0

        update_account_balance(populated_database)

        conn = sqlite3.connect(populated_database)
        cursor = conn.cursor()
        cursor.execute("SELECT cash FROM account WHERE id = 1")
        cash = cursor.fetchone()[0]
        conn.close()

        assert cash == original_cash

    def test_update_is_idempotent(self, populated_database):
        """Test that multiple updates produce same result"""
        result1 = update_account_balance(populated_database)
        result2 = update_account_balance(populated_database)

        assert result1['total_value'] == result2['total_value']
        assert result1['cash'] == result2['cash']
        assert result1['positions_value'] == result2['positions_value']


# ============================================================================
# Test Performance Tracking
# ============================================================================

class TestAddPerformanceRecord:
    """Test performance record tracking"""

    def test_add_performance_record_success(self, populated_database):
        """Test adding a performance record"""
        result = add_performance_record(populated_database)

        assert result is True

        # Verify record was added
        conn = sqlite3.connect(populated_database)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM performance")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1

    def test_performance_record_has_correct_values(self, populated_database):
        """Test performance record contains correct values"""
        add_performance_record(populated_database)

        conn = sqlite3.connect(populated_database)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM performance ORDER BY timestamp DESC LIMIT 1")
        record = cursor.fetchone()
        conn.close()

        assert record is not None
        assert record['total_value'] == 39850.0
        assert record['cash'] == 5000.0
        assert record['positions_value'] == 34850.0

    def test_multiple_performance_records(self, populated_database):
        """Test adding multiple performance records"""
        add_performance_record(populated_database)
        add_performance_record(populated_database)
        add_performance_record(populated_database)

        conn = sqlite3.connect(populated_database)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM performance")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 3

    def test_performance_record_with_no_account(self, temp_database):
        """Test performance tracking fails gracefully with no account"""
        result = add_performance_record(temp_database)

        assert result is False


# ============================================================================
# Test Discrepancy Detection
# ============================================================================

class TestCheckBalanceDiscrepancy:
    """Test balance discrepancy detection"""

    def test_no_discrepancy_when_accurate(self, populated_database):
        """Test no discrepancy detected when balance is accurate"""
        # First update to set correct balance
        update_account_balance(populated_database)

        # Then check
        result = check_balance_discrepancy(populated_database)

        assert result is not None
        assert result['calculated_total'] == 39850.0
        assert result['stored_total'] == 39850.0
        assert result['discrepancy'] == 0.0
        assert result['has_issue'] is False

    def test_detects_positive_discrepancy(self, populated_database):
        """Test detection of positive discrepancy"""
        # Database has stored_total of 10000, but calculated is 39850
        result = check_balance_discrepancy(populated_database)

        assert result is not None
        assert result['calculated_total'] == 39850.0
        assert result['stored_total'] == 10000.0
        assert result['discrepancy'] == 29850.0
        assert result['discrepancy_pct'] > 0
        assert result['has_issue'] is True

    def test_detects_negative_discrepancy(self, temp_database):
        """Test detection of negative discrepancy"""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()

        # Set up account with stored_total > calculated_total
        cursor.execute("INSERT INTO account (id, cash, last_updated, total_value) VALUES (1, 1000.0, '2024-01-01', 15000.0)")
        cursor.execute("""
            INSERT INTO positions (symbol, quantity, entry_price, current_price, entry_date, last_updated)
            VALUES ('TEST', 100, 50.0, 50.0, '2024-01-01', '2024-01-02')
        """)

        conn.commit()
        conn.close()

        result = check_balance_discrepancy(temp_database)

        # Calculated: 1000 + (100 * 50) = 6000
        # Stored: 15000
        # Discrepancy: 6000 - 15000 = -9000
        assert result is not None
        assert result['calculated_total'] == 6000.0
        assert result['stored_total'] == 15000.0
        assert result['discrepancy'] == -9000.0
        assert result['has_issue'] is True

    def test_threshold_setting(self, populated_database):
        """Test custom threshold for discrepancy detection"""
        # Small discrepancy that should not trigger with high threshold
        conn = sqlite3.connect(populated_database)
        cursor = conn.cursor()
        cursor.execute("UPDATE account SET total_value = 39850.5 WHERE id = 1")
        conn.commit()
        conn.close()

        result = check_balance_discrepancy(populated_database, threshold=1.0)

        # Discrepancy is 0.5, threshold is 1.0 -> should not have issue
        assert result['discrepancy'] == pytest.approx(-0.5, 0.01)
        assert result['has_issue'] is False

    def test_percentage_calculation(self, populated_database):
        """Test discrepancy percentage calculation"""
        result = check_balance_discrepancy(populated_database)

        # Calculated: 39850, Stored: 10000
        # Discrepancy: 29850
        # Percentage: (29850 / 10000) * 100 = 298.5%
        assert result is not None
        assert pytest.approx(result['discrepancy_pct'], 0.1) == 298.5

    def test_check_with_no_account(self, temp_database):
        """Test check fails gracefully with no account"""
        result = check_balance_discrepancy(temp_database)

        assert result is None


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows"""

    def test_full_balance_update_workflow(self, populated_database):
        """Test complete workflow: detect -> update -> verify"""
        # 1. Check discrepancy
        check1 = check_balance_discrepancy(populated_database)
        assert check1['has_issue'] is True
        assert check1['discrepancy'] == 29850.0

        # 2. Update balance
        update_result = update_account_balance(populated_database)
        assert update_result is not None
        assert update_result['total_value'] == 39850.0

        # 3. Verify discrepancy is gone
        check2 = check_balance_discrepancy(populated_database)
        assert check2['has_issue'] is False
        assert check2['discrepancy'] == 0.0

    def test_position_price_change_workflow(self, populated_database):
        """Test balance update after position price changes"""
        # Initial state
        initial = calculate_account_balance(populated_database)
        assert initial['total_value'] == 39850.0

        # Simulate price change
        conn = sqlite3.connect(populated_database)
        cursor = conn.cursor()
        # AAPL goes from 160 to 200 (100 shares)
        cursor.execute("UPDATE positions SET current_price = 200.0 WHERE symbol = 'AAPL'")
        conn.commit()
        conn.close()

        # Calculate new balance
        updated = calculate_account_balance(populated_database)
        # New value: 5000 + (100*200 + 50*320 + 30*95) = 5000 + (20000 + 16000 + 2850) = 43850
        assert updated['total_value'] == 43850.0

        # Update database
        update_account_balance(populated_database)

        # Verify stored value matches
        check = check_balance_discrepancy(populated_database)
        assert check['discrepancy'] == 0.0

    def test_order_execution_workflow(self, populated_database):
        """Test balance update after simulated order"""
        # Execute a buy order (reduce cash, add position)
        conn = sqlite3.connect(populated_database)
        cursor = conn.cursor()

        # Buy 50 shares of TSLA at $250 (costs $12,500)
        cursor.execute("UPDATE account SET cash = cash - 12500 WHERE id = 1")
        cursor.execute("""
            INSERT INTO positions (symbol, quantity, entry_price, current_price, entry_date, last_updated)
            VALUES ('TSLA', 50, 250.0, 250.0, '2024-01-03', '2024-01-03')
        """)

        conn.commit()
        conn.close()

        # Update balance
        result = update_account_balance(populated_database)

        # Cash: 5000 - 12500 = -7500 (margin account)
        # Positions: 34850 + 12500 = 47350
        # Total: -7500 + 47350 = 39850 (same as before, net zero transaction)
        assert result is not None

        # Verify no discrepancy
        check = check_balance_discrepancy(populated_database)
        assert abs(check['discrepancy']) < 0.01


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_very_large_portfolio(self, temp_database):
        """Test with very large portfolio value"""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO account (id, cash, last_updated) VALUES (1, 1000000.0, '2024-01-01')")
        cursor.execute("""
            INSERT INTO positions (symbol, quantity, entry_price, current_price, entry_date, last_updated)
            VALUES ('BRK.A', 100, 500000.0, 550000.0, '2024-01-01', '2024-01-02')
        """)

        conn.commit()
        conn.close()

        result = calculate_account_balance(temp_database)

        # 100 shares * $550,000 = $55,000,000
        assert result is not None
        assert result['positions_value'] == 55000000.0
        assert result['total_value'] == 56000000.0

    def test_penny_stock_large_quantity(self, temp_database):
        """Test penny stock with large quantity"""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO account (id, cash, last_updated) VALUES (1, 100.0, '2024-01-01')")
        cursor.execute("""
            INSERT INTO positions (symbol, quantity, entry_price, current_price, entry_date, last_updated)
            VALUES ('PENNY', 1000000, 0.01, 0.02, '2024-01-01', '2024-01-02')
        """)

        conn.commit()
        conn.close()

        result = calculate_account_balance(temp_database)

        assert result is not None
        assert result['positions_value'] == 20000.0
        assert result['total_value'] == 20100.0

    def test_negative_cash_balance(self, temp_database):
        """Test with margin account (negative cash)"""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO account (id, cash, last_updated) VALUES (1, -5000.0, '2024-01-01')")
        cursor.execute("""
            INSERT INTO positions (symbol, quantity, entry_price, current_price, entry_date, last_updated)
            VALUES ('SPY', 100, 450.0, 460.0, '2024-01-01', '2024-01-02')
        """)

        conn.commit()
        conn.close()

        result = calculate_account_balance(temp_database)

        # -5000 + (100 * 460) = -5000 + 46000 = 41000
        assert result is not None
        assert result['cash'] == -5000.0
        assert result['positions_value'] == 46000.0
        assert result['total_value'] == 41000.0

    def test_rounding_precision(self, temp_database):
        """Test that precision is maintained in calculations"""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO account (id, cash, last_updated) VALUES (1, 1234.56, '2024-01-01')")
        cursor.execute("""
            INSERT INTO positions (symbol, quantity, entry_price, current_price, entry_date, last_updated)
            VALUES ('TEST', 123.456, 78.901, 89.123, '2024-01-01', '2024-01-02')
        """)

        conn.commit()
        conn.close()

        result = calculate_account_balance(temp_database)

        expected_position_value = 123.456 * 89.123
        expected_total = 1234.56 + expected_position_value

        assert result is not None
        assert pytest.approx(result['positions_value'], 0.01) == expected_position_value
        assert pytest.approx(result['total_value'], 0.01) == expected_total

    def test_database_connection_error(self):
        """Test handling of database connection error"""
        result = calculate_account_balance('nonexistent_database.db')

        assert result is None


if __name__ == '__main__':
    # Run with: pytest tests/unit/test_account_balance_updater.py -v
    pytest.main([__file__, '-v'])
