import sqlite3
import sys

DB_PATH = "data/coverage.db"


def run_query(sql):
    """Run a read-only SQL query and return (column names, rows)."""
    if not sql.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = con.execute(sql)
    columns = [c[0] for c in cur.description]
    rows = cur.fetchall()
    con.close()
    return columns, rows


if __name__ == "__main__":
    columns, rows = run_query(sys.argv[1])
    print(columns)
    for row in rows[:20]:
        print(row)
