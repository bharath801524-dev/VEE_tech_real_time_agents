import sqlite3
import os

db_paths = [
    os.path.abspath("mindmesh.db"),
    os.path.abspath("../mindmesh.db"),
    os.path.abspath("backend/mindmesh.db")
]

for p in set(db_paths):
    if os.path.exists(p):
        print(f"Checking {p}...")
        con = sqlite3.connect(p)
        cur = con.cursor()
        tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if 'events' in tables:
            cols = [col[1] for col in cur.execute("PRAGMA table_info(events)").fetchall()]
            if 'publisher' not in cols:
                cur.execute("ALTER TABLE events ADD COLUMN publisher TEXT")
                print(f"Added column 'publisher' to {p}")
            if 'source_origin' not in cols:
                cur.execute("ALTER TABLE events ADD COLUMN source_origin TEXT")
                print(f"Added column 'source_origin' to {p}")
        con.commit()
        con.close()

print("Schema migration completed successfully!")
