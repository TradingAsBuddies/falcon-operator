#!/usr/bin/env python3
"""
Unit Tests for Database Manager (db_manager.py)

Tests the database abstraction layer that supports SQLite and PostgreSQL.
"""

import pytest
import sqlite3
import tempfile
import os
from unittest.mock import patch, MagicMock
import datetime

# Import the module to test
from db_manager import DatabaseManager, get_db_manager


@pytest.fixture
def temp_db_path():
    """Create a temporary database path"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    os.unlink(path)  # Remove the file so DatabaseManager can create it fresh
    yield path
    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def sqlite_config(temp_db_path):
    """SQLite configuration for testing"""
    return {
        'db_type': 'sqlite',
        'db_path': temp_db_path
    }


@pytest.fixture
def db_manager(sqlite_config):
    """Create a DatabaseManager instance for testing"""
    db = DatabaseManager(config=sqlite_config)
    db.init_schema()
    db.init_account(initial_balance=10000.0)
    yield db
    db.close()


# ============================================================================
# Initialization Tests
# ============================================================================

class TestDatabaseManagerInit:
    """Test DatabaseManager initialization"""

    def test_init_with_sqlite_config(self, sqlite_config):
        """Test initialization with SQLite config"""
        db = DatabaseManager(config=sqlite_config)

        assert db.db_type == 'sqlite'
        assert db.db_path == sqlite_config['db_path']
        assert db.psycopg2 is None
        assert db.pool is None

    def test_init_without_config_uses_defaults(self):
        """Test initialization without config uses environment/defaults"""
        with patch.dict(os.environ, {'DB_TYPE': 'sqlite', 'DB_PATH': '/tmp/test.db'}, clear=False):
            db = DatabaseManager()

            assert db.db_type == 'sqlite'
            assert db.db_path == '/tmp/test.db'

    def test_init_creates_directory_if_not_exists(self, temp_db_path):
        """Test that initialization creates database directory"""
        # Use a path in a non-existent directory
        nested_path = os.path.join(os.path.dirname(temp_db_path), 'nested', 'db.sqlite')

        config = {
            'db_type': 'sqlite',
            'db_path': nested_path
        }

        db = DatabaseManager(config=config)

        # Directory should be created
        assert os.path.exists(os.path.dirname(nested_path))

        # Cleanup
        try:
            os.rmdir(os.path.dirname(nested_path))
        except:
            pass

    def test_init_with_invalid_db_type_raises_error(self):
        """Test that invalid database type raises ValueError"""
        config = {'db_type': 'mongodb'}

        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseManager(config=config)

    def test_load_config_from_env(self):
        """Test loading configuration from environment variables"""
        db = DatabaseManager()
        config = db._load_config_from_env()

        assert 'db_type' in config
        assert 'db_path' in config
        assert 'db_host' in config
        assert 'db_port' in config
        assert 'db_name' in config
        assert 'db_user' in config
        assert 'db_password' in config


# ============================================================================
# Connection Management Tests
# ============================================================================

class TestConnectionManagement:
    """Test connection management"""

    def test_get_connection_returns_valid_connection(self, db_manager):
        """Test that get_connection returns a valid SQLite connection"""
        with db_manager.get_connection() as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)

    def test_get_connection_enables_row_factory(self, db_manager):
        """Test that connections have dict-like row access enabled"""
        with db_manager.get_connection() as conn:
            assert conn.row_factory == sqlite3.Row

    def test_connection_is_closed_after_context(self, db_manager):
        """Test that connection is closed after context manager exits"""
        with db_manager.get_connection() as conn:
            pass

        # Attempting to use closed connection should raise error
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_multiple_connections_work_independently(self, db_manager):
        """Test that multiple connections can be opened independently"""
        with db_manager.get_connection() as conn1:
            cursor1 = conn1.cursor()
            cursor1.execute("SELECT cash FROM account WHERE id = 1")
            result1 = cursor1.fetchone()

            with db_manager.get_connection() as conn2:
                cursor2 = conn2.cursor()
                cursor2.execute("SELECT cash FROM account WHERE id = 1")
                result2 = cursor2.fetchone()

                assert result1[0] == result2[0]


# ============================================================================
# Execute Tests
# ============================================================================

class TestExecute:
    """Test query execution"""

    def test_execute_select_fetch_one(self, db_manager):
        """Test executing SELECT with fetch='one'"""
        result = db_manager.execute(
            'SELECT cash FROM account WHERE id = %s',
            (1,),
            fetch='one'
        )

        assert result is not None
        assert result[0] == 10000.0

    def test_execute_select_fetch_all(self, db_manager):
        """Test executing SELECT with fetch='all'"""
        # Insert some test data
        db_manager.execute(
            'INSERT INTO positions (symbol, quantity, entry_price, entry_date, last_updated) VALUES (%s, %s, %s, %s, %s)',
            ('AAPL', 100, 150.0, '2024-01-01', '2024-01-01')
        )
        db_manager.execute(
            'INSERT INTO positions (symbol, quantity, entry_price, entry_date, last_updated) VALUES (%s, %s, %s, %s, %s)',
            ('GOOGL', 50, 2800.0, '2024-01-01', '2024-01-01')
        )

        result = db_manager.execute('SELECT * FROM positions', fetch='all')

        assert len(result) == 2

    def test_execute_insert_returns_lastrowid(self, db_manager):
        """Test that INSERT returns last inserted row ID"""
        result = db_manager.execute(
            'INSERT INTO orders (symbol, side, quantity, price, timestamp) VALUES (%s, %s, %s, %s, %s)',
            ('AAPL', 'buy', 100, 150.0, '2024-01-01 10:00:00')
        )

        # For SQLite, lastrowid should be returned
        assert result is not None
        assert isinstance(result, int)
        assert result > 0

    def test_execute_update_commits_changes(self, db_manager):
        """Test that UPDATE commits changes"""
        # Update cash
        db_manager.execute(
            'UPDATE account SET cash = %s WHERE id = %s',
            (5000.0, 1)
        )

        # Verify change persisted
        result = db_manager.execute(
            'SELECT cash FROM account WHERE id = %s',
            (1,),
            fetch='one'
        )

        assert result[0] == 5000.0

    def test_execute_delete_removes_rows(self, db_manager):
        """Test that DELETE removes rows"""
        # Insert a position
        db_manager.execute(
            'INSERT INTO positions (symbol, quantity, entry_price, entry_date, last_updated) VALUES (%s, %s, %s, %s, %s)',
            ('AAPL', 100, 150.0, '2024-01-01', '2024-01-01')
        )

        # Delete it
        db_manager.execute('DELETE FROM positions WHERE symbol = %s', ('AAPL',))

        # Verify it's gone
        result = db_manager.execute(
            'SELECT * FROM positions WHERE symbol = %s',
            ('AAPL',),
            fetch='one'
        )

        assert result is None

    def test_execute_converts_placeholders_for_sqlite(self, db_manager):
        """Test that %s placeholders are converted to ? for SQLite"""
        # This should work even though we use %s (PostgreSQL style)
        result = db_manager.execute(
            'SELECT cash FROM account WHERE id = %s',
            (1,),
            fetch='one'
        )

        assert result is not None

    def test_execute_without_params(self, db_manager):
        """Test executing query without parameters"""
        result = db_manager.execute('SELECT COUNT(*) FROM account', fetch='one')

        assert result[0] >= 1


# ============================================================================
# Execute Many Tests
# ============================================================================

class TestExecuteMany:
    """Test batch query execution"""

    def test_executemany_inserts_multiple_rows(self, db_manager):
        """Test inserting multiple rows with executemany"""
        params_list = [
            ('AAPL', 'buy', 100, 150.0, '2024-01-01 10:00:00', 0),
            ('GOOGL', 'buy', 50, 2800.0, '2024-01-01 11:00:00', 0),
            ('MSFT', 'buy', 75, 300.0, '2024-01-01 12:00:00', 0),
        ]

        rowcount = db_manager.executemany(
            'INSERT INTO orders (symbol, side, quantity, price, timestamp, pnl) VALUES (%s, %s, %s, %s, %s, %s)',
            params_list
        )

        assert rowcount == 3

        # Verify all rows inserted
        result = db_manager.execute('SELECT COUNT(*) FROM orders', fetch='one')
        assert result[0] == 3

    def test_executemany_returns_rowcount(self, db_manager):
        """Test that executemany returns number of affected rows"""
        params_list = [
            ('AAPL', 100, 150.0, '2024-01-01', '2024-01-01'),
            ('GOOGL', 50, 2800.0, '2024-01-01', '2024-01-01'),
        ]

        rowcount = db_manager.executemany(
            'INSERT INTO positions (symbol, quantity, entry_price, entry_date, last_updated) VALUES (%s, %s, %s, %s, %s)',
            params_list
        )

        assert rowcount == 2


# ============================================================================
# Schema Initialization Tests
# ============================================================================

class TestSchemaInitialization:
    """Test database schema initialization"""

    def test_init_schema_creates_all_tables(self, sqlite_config):
        """Test that init_schema creates all required tables"""
        db = DatabaseManager(config=sqlite_config)
        db.init_schema()

        # Check that all tables exist
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]

        assert 'account' in tables
        assert 'positions' in tables
        assert 'orders' in tables
        assert 'performance' in tables
        assert 'youtube_strategies' in tables
        assert 'strategy_backtests' in tables

    def test_init_schema_is_idempotent(self, db_manager):
        """Test that calling init_schema multiple times is safe"""
        # Schema already initialized by fixture
        # Call again
        db_manager.init_schema()

        # Should still work
        result = db_manager.execute('SELECT COUNT(*) FROM account', fetch='one')
        assert result[0] >= 0

    def test_account_table_has_correct_columns(self, db_manager):
        """Test that account table has correct schema"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(account)")
            columns = {row[1] for row in cursor.fetchall()}

        assert 'id' in columns
        assert 'cash' in columns
        assert 'last_updated' in columns

    def test_positions_table_has_correct_columns(self, db_manager):
        """Test that positions table has correct schema"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(positions)")
            columns = {row[1] for row in cursor.fetchall()}

        assert 'symbol' in columns
        assert 'quantity' in columns
        assert 'entry_price' in columns
        assert 'entry_date' in columns
        assert 'last_updated' in columns


# ============================================================================
# Account Initialization Tests
# ============================================================================

class TestAccountInitialization:
    """Test account initialization"""

    def test_init_account_creates_account_with_balance(self, sqlite_config):
        """Test that init_account creates account with correct balance"""
        db = DatabaseManager(config=sqlite_config)
        db.init_schema()
        db.init_account(initial_balance=25000.0)

        result = db.execute('SELECT cash FROM account WHERE id = %s', (1,), fetch='one')

        assert result is not None
        assert result[0] == 25000.0

    def test_init_account_uses_default_balance(self, sqlite_config):
        """Test that init_account uses default $10,000 if not specified"""
        db = DatabaseManager(config=sqlite_config)
        db.init_schema()
        db.init_account()

        result = db.execute('SELECT cash FROM account WHERE id = %s', (1,), fetch='one')

        assert result[0] == 10000.0

    def test_init_account_is_idempotent(self, db_manager):
        """Test that calling init_account multiple times doesn't create duplicates"""
        # Account already initialized by fixture with 10000

        # Try to init again with different balance
        db_manager.init_account(initial_balance=50000.0)

        # Should still have original balance
        result = db_manager.execute('SELECT cash FROM account WHERE id = %s', (1,), fetch='one')
        assert result[0] == 10000.0

        # Should still have only one account
        count = db_manager.execute('SELECT COUNT(*) FROM account', fetch='one')
        assert count[0] == 1

    def test_init_account_sets_timestamp(self, sqlite_config):
        """Test that init_account sets last_updated timestamp"""
        db = DatabaseManager(config=sqlite_config)
        db.init_schema()
        db.init_account()

        result = db.execute(
            'SELECT last_updated FROM account WHERE id = %s',
            (1,),
            fetch='one'
        )

        assert result is not None
        assert result[0] is not None


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test complete workflows"""

    def test_full_trading_workflow(self, db_manager):
        """Test a complete trading workflow"""
        # 1. Check initial balance
        result = db_manager.execute('SELECT cash FROM account WHERE id = %s', (1,), fetch='one')
        initial_cash = result[0]
        assert initial_cash == 10000.0

        # 2. Place a buy order
        db_manager.execute(
            'INSERT INTO orders (symbol, side, quantity, price, timestamp, pnl) VALUES (%s, %s, %s, %s, %s, %s)',
            ('AAPL', 'buy', 100, 150.0, '2024-01-01 10:00:00', 0)
        )

        # 3. Add position
        db_manager.execute(
            'INSERT INTO positions (symbol, quantity, entry_price, entry_date, last_updated) VALUES (%s, %s, %s, %s, %s)',
            ('AAPL', 100, 150.0, '2024-01-01', '2024-01-01')
        )

        # 4. Update cash (deduct purchase)
        new_cash = initial_cash - (100 * 150.0)
        db_manager.execute('UPDATE account SET cash = %s WHERE id = %s', (new_cash, 1))

        # 5. Verify final state
        cash_result = db_manager.execute('SELECT cash FROM account WHERE id = %s', (1,), fetch='one')
        assert cash_result[0] == -5000.0  # 10000 - 15000

        positions = db_manager.execute('SELECT * FROM positions', fetch='all')
        assert len(positions) == 1

        orders = db_manager.execute('SELECT * FROM orders', fetch='all')
        assert len(orders) == 1

    def test_performance_tracking_workflow(self, db_manager):
        """Test performance tracking workflow"""
        # Add multiple performance records
        timestamps = [
            '2024-01-01 09:00:00',
            '2024-01-01 10:00:00',
            '2024-01-01 11:00:00',
        ]

        for i, ts in enumerate(timestamps):
            db_manager.execute(
                'INSERT INTO performance (timestamp, total_value, cash, positions_value) VALUES (%s, %s, %s, %s)',
                (ts, 10000.0 + (i * 100), 5000.0, 5000.0 + (i * 100))
            )

        # Query performance history
        results = db_manager.execute(
            'SELECT * FROM performance ORDER BY timestamp',
            fetch='all'
        )

        assert len(results) == 3
        assert results[0][1] == 10000.0  # total_value of first record
        assert results[2][1] == 10200.0  # total_value of last record


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_execute_with_sql_injection_attempt(self, db_manager):
        """Test that parameterized queries prevent SQL injection"""
        # This should be safely handled by parameterization
        malicious_symbol = "AAPL'; DROP TABLE positions; --"

        db_manager.execute(
            'INSERT INTO positions (symbol, quantity, entry_price, entry_date, last_updated) VALUES (%s, %s, %s, %s, %s)',
            (malicious_symbol, 100, 150.0, '2024-01-01', '2024-01-01')
        )

        # Table should still exist
        result = db_manager.execute('SELECT COUNT(*) FROM positions', fetch='one')
        assert result[0] == 1

    def test_execute_with_empty_result_set(self, db_manager):
        """Test querying for non-existent data"""
        result = db_manager.execute(
            'SELECT * FROM positions WHERE symbol = %s',
            ('NONEXISTENT',),
            fetch='one'
        )

        assert result is None

    def test_execute_with_large_batch(self, db_manager):
        """Test inserting a large batch of records"""
        # Insert 1000 orders
        params_list = [
            (f'TICK{i}', 'buy', 100, 50.0 + i, f'2024-01-01 {i%24:02d}:00:00', 0)
            for i in range(1000)
        ]

        rowcount = db_manager.executemany(
            'INSERT INTO orders (symbol, side, quantity, price, timestamp, pnl) VALUES (%s, %s, %s, %s, %s, %s)',
            params_list
        )

        assert rowcount == 1000

        # Verify count
        result = db_manager.execute('SELECT COUNT(*) FROM orders', fetch='one')
        assert result[0] == 1000

    def test_decimal_precision_in_calculations(self, db_manager):
        """Test that decimal precision is maintained"""
        # Insert position with precise price
        price = 123.456789
        db_manager.execute(
            'INSERT INTO positions (symbol, quantity, entry_price, entry_date, last_updated) VALUES (%s, %s, %s, %s, %s)',
            ('AAPL', 100, price, '2024-01-01', '2024-01-01')
        )

        result = db_manager.execute(
            'SELECT entry_price FROM positions WHERE symbol = %s',
            ('AAPL',),
            fetch='one'
        )

        # SQLite stores as REAL, so some precision loss is expected
        assert abs(result[0] - price) < 0.000001

    def test_unicode_handling(self, db_manager):
        """Test that unicode characters are handled correctly"""
        # Insert with unicode characters
        db_manager.execute(
            'INSERT INTO youtube_strategies (title, creator, youtube_url, video_id, description, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            ('Strategy 策略', 'Creator 创建者', 'https://youtube.com/watch?v=test123', 'test123', 'Description 描述', '2024-01-01', '2024-01-01')
        )

        result = db_manager.execute(
            'SELECT title, creator FROM youtube_strategies WHERE video_id = %s',
            ('test123',),
            fetch='one'
        )

        assert result[0] == 'Strategy 策略'
        assert result[1] == 'Creator 创建者'


# ============================================================================
# Factory Function Tests
# ============================================================================

class TestFactoryFunction:
    """Test get_db_manager factory function"""

    def test_get_db_manager_returns_instance(self, sqlite_config):
        """Test that factory function returns DatabaseManager instance"""
        db = get_db_manager(config=sqlite_config)

        assert isinstance(db, DatabaseManager)
        assert db.db_type == 'sqlite'

    def test_get_db_manager_without_config(self):
        """Test factory function without config"""
        db = get_db_manager()

        assert isinstance(db, DatabaseManager)
        assert db.db_type in ['sqlite', 'postgresql']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
