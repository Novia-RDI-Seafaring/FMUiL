import sqlite3
import csv

db_file = "db/logs.db"
csv_file = "db/logs_preview.csv"

conn = sqlite3.connect(db_file)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT * FROM logs").fetchall()

with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(row))

print(f"Exported {len(rows)} rows to {csv_file}")
