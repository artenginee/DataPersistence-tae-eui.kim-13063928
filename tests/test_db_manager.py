import pytest
from database.db_manager import DatabaseManager


class TestDatabaseManagerInit:
    def test_creates_db_file(self, tmp_path):
        path = str(tmp_path / "test.db")
        DatabaseManager._instance = None
        DatabaseManager(path)
        assert (tmp_path / "test.db").exists()
        DatabaseManager._instance = None

    def test_creates_samples_table(self, db):
        conn = db.get_connection()
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='samples'"
        ).fetchone()
        assert row is not None

    def test_creates_orders_table(self, db):
        conn = db.get_connection()
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='orders'"
        ).fetchone()
        assert row is not None

    def test_creates_production_jobs_table(self, db):
        conn = db.get_connection()
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='production_jobs'"
        ).fetchone()
        assert row is not None


class TestDatabaseManagerGetInstance:
    def test_returns_same_instance(self, tmp_path):
        DatabaseManager._instance = None
        path = str(tmp_path / "singleton.db")
        inst1 = DatabaseManager.get_instance(path)
        inst2 = DatabaseManager.get_instance(path)
        assert inst1 is inst2
        DatabaseManager._instance = None

    def test_singleton_is_independent_of_direct_init(self, tmp_path):
        DatabaseManager._instance = None
        path = str(tmp_path / "s.db")
        inst = DatabaseManager.get_instance(path)
        assert DatabaseManager._instance is inst
        DatabaseManager._instance = None


class TestDatabaseManagerGetConnection:
    def test_row_factory_enables_column_name_access(self, db):
        with db.get_connection() as conn:
            conn.execute(
                "INSERT INTO samples (name, avg_production_time, yield_rate) VALUES ('T', 10.0, 0.9)"
            )
        row = db.get_connection().execute("SELECT name FROM samples").fetchone()
        assert row["name"] == "T"

    def test_foreign_keys_are_enabled(self, db):
        result = db.get_connection().execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1


class TestDatabaseManagerHelpers:
    def test_query_returns_list_of_rows(self, db):
        with db.get_connection() as conn:
            conn.execute(
                "INSERT INTO samples (name, avg_production_time, yield_rate) VALUES ('Q', 10.0, 0.9)"
            )
        rows = db.query("SELECT name FROM samples")
        assert len(rows) == 1
        assert rows[0]["name"] == "Q"

    def test_query_returns_empty_list_when_no_rows(self, db):
        assert db.query("SELECT * FROM samples") == []

    def test_query_one_returns_single_row(self, db):
        with db.get_connection() as conn:
            conn.execute(
                "INSERT INTO samples (name, avg_production_time, yield_rate) VALUES ('QO', 10.0, 0.9)"
            )
        row = db.query_one("SELECT name FROM samples WHERE name = 'QO'")
        assert row["name"] == "QO"

    def test_query_one_returns_none_when_no_row(self, db):
        assert db.query_one("SELECT * FROM samples WHERE sample_id = 9999") is None


class TestDatabaseManagerDropAll:
    def test_drop_all_clears_data(self, db):
        with db.get_connection() as conn:
            conn.execute(
                "INSERT INTO samples (name, avg_production_time, yield_rate) VALUES ('S', 10.0, 0.9)"
            )
        db.drop_all()
        count = db.get_connection().execute("SELECT COUNT(*) FROM samples").fetchone()[0]
        assert count == 0

    def test_drop_all_recreates_tables(self, db):
        db.drop_all()
        row = db.get_connection().execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='samples'"
        ).fetchone()
        assert row is not None
