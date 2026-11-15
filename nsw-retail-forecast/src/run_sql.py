"""Load data/retail.csv into SQLite and run every query in sql/.

Usage:
    python src/run_sql.py

Each query's result is saved to outputs/<query name>.csv and printed.
"""

import glob
import os
import sqlite3

import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")


def main() -> None:
    con = sqlite3.connect(":memory:")
    pd.read_csv(os.path.join(ROOT, "data", "retail.csv")).to_sql("retail", con, index=False)
    out = os.path.join(ROOT, "outputs")
    os.makedirs(out, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(ROOT, "sql", "*.sql"))):
        name = os.path.splitext(os.path.basename(path))[0]
        with open(path) as f:
            result = pd.read_sql_query(f.read(), con)
        result.to_csv(os.path.join(out, f"{name}.csv"), index=False)
        print(f"\n== {name} ==\n{result.to_string(index=False)}")


if __name__ == "__main__":
    main()
