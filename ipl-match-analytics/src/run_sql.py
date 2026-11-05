"""Load the tidy tables into SQLite and run every query in sql/.

Usage:
    python src/run_sql.py

Each query's result is saved to outputs/<query name>.csv and printed.
"""

import csv
import glob
import os
import sqlite3

ROOT = os.path.join(os.path.dirname(__file__), "..")


def load(con, table, path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())
    con.execute(f"CREATE TABLE {table} ({', '.join(cols)})")
    con.executemany(
        f"INSERT INTO {table} VALUES ({', '.join('?' * len(cols))})",
        [[_num(r[c]) for c in cols] for r in rows],
    )


def _num(v):
    try:
        return int(v)
    except ValueError:
        return v


def main():
    con = sqlite3.connect(":memory:")
    load(con, "matches", os.path.join(ROOT, "data", "matches.csv"))
    load(con, "phases", os.path.join(ROOT, "data", "phases.csv"))
    out = os.path.join(ROOT, "outputs")
    os.makedirs(out, exist_ok=True)

    for path in sorted(glob.glob(os.path.join(ROOT, "sql", "*.sql"))):
        name = os.path.splitext(os.path.basename(path))[0]
        cur = con.execute(open(path, encoding="utf-8").read())
        header = [d[0] for d in cur.description]
        rows = cur.fetchall()
        with open(os.path.join(out, f"{name}.csv"), "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows([header, *rows])
        print(f"\n== {name} ({len(rows)} rows)")
        for r in [header, *rows[:12]]:
            print("  " + " | ".join(str(x) for x in r))


if __name__ == "__main__":
    main()
