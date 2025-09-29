import sqlite3
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel
from opcua_fmu_simulator.config import load_config
from opcua_fmu_simulator.db.connection import SQLDB

class FetchRequest(BaseModel):
    table: str
    run_id: Optional[str] = None
    test_name: Optional[str] = None
    test_result: Optional[bool] = None
    limit: Optional[int] = None
    order: Literal["ASC", "DESC"] = "ASC"

class Row(BaseModel):
    id: int
    run_id: str
    test_name: str
    evaluation_name: str
    evaluation_function: str
    measured_value: float
    test_result: bool
    system_timestamp: float
    created_unix: float

class FetchResponse(BaseModel):
    rows: list[Row]

# ---------------- Internals ----------------

def _connect() -> sqlite3.Connection:
    cfg = load_config()
    if not cfg.db.enabled:
        raise RuntimeError("Database disabled in config")
    return sqlite3.connect(cfg.db.file)

# ---------------- API ----------------

def list_tables() -> list[str]:
    """Return all table names."""
    with _connect() as conn:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [r[0] for r in cur.fetchall()]


def fetch(req: FetchRequest) -> FetchResponse:
    """Fetch rows with optional filters."""
    where = []
    params = []

    if req.run_id:
        where.append("run_id = ?")
        params.append(req.run_id)

    if req.test_name:
        where.append("test_name = ?")
        params.append(req.test_name)

    if req.test_result is not None:
        where.append("test_result = ?")
        params.append(1 if req.test_result else 0)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    limit_sql = "LIMIT ?" if req.limit else ""
    if req.limit:
        params.append(req.limit)

    sql = f"""
    SELECT id, run_id, test_name, evaluation_name, evaluation_function,
           measured_value, test_result, system_timestamp, created_unix
    FROM "{req.table}"
    {where_sql}
    ORDER BY system_timestamp {req.order}
    {limit_sql};
    """

    with _connect() as conn:
        cur = conn.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = []
        for tup in cur.fetchall():
            d = dict(zip(cols, tup))
            d["test_result"] = bool(d["test_result"])
            rows.append(Row(**d))
        return FetchResponse(rows=rows)