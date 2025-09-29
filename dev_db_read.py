from pickle import FALSE
import sqlite3
import csv

db_file = "db/log.db"
csv_file = "db/log_preview.csv"

with sqlite3.connect(db_file) as conn:
    cur = conn.cursor()

    # list all user tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print("Tables:", tables)

    # if you want to check columns of a specific table
    if tables:
        table_name = tables[0][0]
        cur.execute(f"PRAGMA table_info('{table_name}')")
        columns = cur.fetchall()
        print(f"Columns in {table_name}:")
        for cid, name, col_type, notnull, dflt, pk in columns:
            print(f"  {name} {col_type} (pk={pk})")

# test db api
from opcua_fmu_simulator.db.api import fetch, FetchRequest

# only tests that fail from runn
resp = fetch(FetchRequest(table="logs", run_id="2025_09_29_19_08_14", test_result=False))
for row in resp.rows:
    print(row)

# save as csv
SAVE_CSV = False

if SAVE_CSV:
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("SELECT * FROM logs").fetchall()

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

    print(f"Exported {len(rows)} rows to {csv_file}")
