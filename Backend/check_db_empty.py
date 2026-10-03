"""Check if the database has any tables."""
import re, urllib.parse, psycopg2

with open('.env') as f:
    content = f.read()

m = re.search(r'DATABASE_URL\s*=\s*(.*)', content)
raw = m.group(1).strip().strip('"').strip("'")
p = re.match(r'(postgresql://[^:]+:[^@]+@[^/]+/)"?(.+?)"?$', raw)
url = p.group(1) + urllib.parse.quote(p.group(2), safe='')

conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
rows = cur.fetchall()
if rows:
    print(f"Tables in DB ({len(rows)}):")
    for r in rows:
        print(f"  - {r[0]}")
else:
    print("Database is EMPTY (no tables in public schema)")

cur.execute("SELECT * FROM pg_tables WHERE tablename='alembic_version'")
if cur.fetchone():
    cur.execute("SELECT version_num FROM alembic_version")
    versions = cur.fetchall()
    print(f"Alembic version: {versions}")
else:
    print("No alembic_version table")
conn.close()
