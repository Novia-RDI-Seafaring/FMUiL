# src/mypackage/db/connection.py
from __future__ import annotations
import sqlite3
from pathlib import Path
from opcua_fmu_simulator.utils import load_config, db_enabled, PROJECT_ROOT


# --- Fixed schema definition ---
DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS {table} (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  test_name           TEXT   NOT NULL,
  evaluation_name     TEXT   NOT NULL,
  evaluation_function TEXT   NOT NULL,
  measured_value      REAL   NOT NULL,
  test_result         INTEGER NOT NULL,  -- 0/1
  system_timestamp    REAL   NOT NULL,
  created_unix        REAL   NOT NULL DEFAULT (unixepoch())
);
CREATE INDEX IF NOT EXISTS idx_{table}_names_time
  ON {table}(test_name, evaluation_name, system_timestamp);
"""

class SQLDB:
    """Tiny SQLite wrapper with a fixed schema but configurable table name."""

    def __init__(self, table: str = "eval_logs") -> None:
        self.table = table
        cfg = load_config()

        if not db_enabled(cfg):
            self.enabled = False
            self.db_file: Path | None = None
            self.conn: sqlite3.Connection | None = None
            return

        db_cfg = cfg["database"]
        db_dir = PROJECT_ROOT / db_cfg.get("dir", "db/")
        db_name = db_cfg.get("name", "logs")
        db_dir.mkdir(parents=True, exist_ok=True)

        self.enabled = True
        self.db_file = db_dir / f"{db_name}.db"
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self.conn.execute("PRAGMA busy_timeout=3000;")

    def ensure_schema(self) -> None:
        """Create the table and index if missing."""
        if not self.enabled or self.conn is None:
            return
        self.conn.executescript(DB_SCHEMA.format(table=self.table))
        self.conn.commit()

    def insert_eval(
        self,
        *,
        test_name: str,
        evaluation_name: str,
        evaluation_function: str,
        measured_value: float,
        test_result: int | bool,
        system_timestamp: float,
    ) -> None:
        """Insert one row. No-op if DB disabled."""
        if not self.enabled or self.conn is None:
            return
        self.conn.execute(
            f"""INSERT INTO {self.table}
                (test_name, evaluation_name, evaluation_function, measured_value, test_result, system_timestamp)
                VALUES (?, ?, ?, ?, ?, ?)""",
            (
                test_name,
                evaluation_name,
                evaluation_function,
                float(measured_value),
                int(test_result),
                float(system_timestamp),
            ),
        )

    def commit(self) -> None:
        if self.enabled and self.conn:
            self.conn.commit()

    def close(self) -> None:
        if self.enabled and self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "SQLDB":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                self.commit()
        finally:
            self.close()
