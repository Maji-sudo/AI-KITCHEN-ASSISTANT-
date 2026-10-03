import sqlite3

def check_sqlite():
    try:
        conn = sqlite3.connect('sql_app.db')
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        print("SQLite Tables:", tables)
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t[0]};")
            print(f"  {t[0]}: {cur.fetchone()[0]} rows")
        conn.close()
    except Exception as e:
        print("SQLite error:", e)

if __name__ == '__main__':
    check_sqlite()
