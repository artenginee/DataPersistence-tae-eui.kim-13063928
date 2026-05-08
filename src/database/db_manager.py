import sqlite3
from pathlib import Path
from typing import Optional


class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None

    def __init__(self, db_path: str = "data/semiconductor.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @classmethod
    def get_instance(cls, db_path: str = "data/semiconductor.db") -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def query(self, sql: str, params: tuple = ()) -> list:
        """다건 SELECT 헬퍼 — 연결을 자동으로 닫습니다."""
        conn = self.get_connection()
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def query_one(self, sql: str, params: tuple = ()):
        """단건 SELECT 헬퍼 — 연결을 자동으로 닫습니다."""
        conn = self.get_connection()
        try:
            return conn.execute(sql, params).fetchone()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.get_connection() as conn:
            conn.executescript(_DDL)

    def drop_all(self) -> None:
        with self.get_connection() as conn:
            conn.executescript("""
                DROP TABLE IF EXISTS production_jobs;
                DROP TABLE IF EXISTS orders;
                DROP TABLE IF EXISTS samples;
            """)
        self._init_schema()


_DDL = """
CREATE TABLE IF NOT EXISTS samples (
    sample_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT    NOT NULL UNIQUE,
    avg_production_time  REAL    NOT NULL CHECK (avg_production_time > 0),
    yield_rate           REAL    NOT NULL CHECK (yield_rate > 0 AND yield_rate <= 1),
    stock                INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    description          TEXT    NOT NULL DEFAULT '',
    created_at           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
    updated_at           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS orders (
    order_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT    NOT NULL,
    sample_id     INTEGER NOT NULL REFERENCES samples(sample_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    status        TEXT    NOT NULL DEFAULT 'RESERVED',
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
    updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS production_jobs (
    job_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id         INTEGER NOT NULL REFERENCES orders(order_id),
    sample_id        INTEGER NOT NULL REFERENCES samples(sample_id),
    planned_quantity INTEGER NOT NULL CHECK (planned_quantity > 0),
    actual_quantity  INTEGER NOT NULL DEFAULT 0 CHECK (actual_quantity >= 0),
    total_time_min   REAL    NOT NULL DEFAULT 0,
    status           TEXT    NOT NULL DEFAULT 'WAITING',
    queue_order      INTEGER NOT NULL DEFAULT 0,
    notes            TEXT    NOT NULL DEFAULT '',
    created_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
    updated_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_sample      ON orders(sample_id);
CREATE INDEX IF NOT EXISTS idx_jobs_order         ON production_jobs(order_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status        ON production_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_queue_order   ON production_jobs(queue_order);
"""
