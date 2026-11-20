import os
import sys

from db import BASE_DIR, connect

# Children before parents, so foreign keys never block a DROP
TABLES_IN_DROP_ORDER = ["status_events", "crossing_goods", "crossings",
                        "goods_categories", "admin_windows", "lanes",
                        "trucks", "drivers", "users"]

def read_statements(filename):
    path = os.path.join(BASE_DIR, filename)
    with open(path, encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines()
                 if not ln.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]

def main(reset=False):
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            if reset:
                print("Dropping existing tables...")
                for table in TABLES_IN_DROP_ORDER:
                    cur.execute(f"DROP TABLE IF EXISTS {table}")   # fixed names, not user input

            print("Creating tables from schema.sql ...")
            for stmt in read_statements("schema.sql"):
                cur.execute(stmt)

            cur.execute("SELECT COUNT(*) AS n FROM lanes")
            if cur.fetchone()["n"] == 0:
                print("Loading sample data from seed.sql ...")
                for stmt in read_statements("seed.sql"):
                    cur.execute(stmt)
            else:
                print("Lanes already exist - sample data NOT loaded")

            for table in reversed(TABLES_IN_DROP_ORDER):
                cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
                print(f"  {table:<17}{cur.fetchone()['n']} rows")
        conn.commit()
    print("Done. Now run:  python app.py")

if __name__ == "__main__":
    main(reset="--reset" in sys.argv)
