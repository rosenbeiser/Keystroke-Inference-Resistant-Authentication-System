import sqlite3, os

db_path = "gridauth.db"
if os.path.exists(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cols = [row[1] for row in cur.execute("PRAGMA table_info(users)").fetchall()]
    if "security_level" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN security_level TEXT NOT NULL DEFAULT 'normal'")
        con.commit()
        print("Migration applied: added security_level column with default 'normal'")
    else:
        print("Column already exists — no migration needed")
    con.close()
else:
    print("No DB file found — will be created fresh on server start (schema includes security_level)")
