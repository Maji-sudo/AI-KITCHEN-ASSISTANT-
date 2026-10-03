"""
READ-ONLY PostgreSQL Database Schema Inspection Script
=======================================================
This script ONLY reads from the database. It does NOT:
  - Create, modify, delete, truncate, or drop ANYTHING
  - Run any migrations
  - Insert or update any data

It uses only SELECT queries against information_schema and pg_catalog.
"""

import os
import json
import sys
import re

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("psycopg2 not installed.")
    sys.exit(1)

# Load DATABASE_URL from .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
db_url = None
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("DATABASE_URL="):
            db_url = line.split("=", 1)[1].strip()
            break

if not db_url:
    print("ERROR: DATABASE_URL not found in .env")
    sys.exit(1)

# Fix the database URL:
# The .env value may look like: postgresql://user:pass@host:port/"DB NAME"
# IMPORTANT: apply the quoted-dbname regex FIRST (before any strip) so pattern matches.
db_url = re.sub(r'/"([^"]+)"$', lambda m: '/' + m.group(1).replace(' ', '%20'), db_url)
db_url = re.sub(r"/'([^']+)'$", lambda m: '/' + m.group(1).replace(' ', '%20'), db_url)
# Encode any remaining literal spaces in the dbname segment
db_url = re.sub(r'(/[^/?#\s]* [^/?#]*)$', lambda m: m.group(0).replace(' ', '%20'), db_url)
# Strip accidental surrounding quotes on the whole URL string
if db_url.startswith('"') and db_url.endswith('"'):
    db_url = db_url[1:-1]
if db_url.startswith("'") and db_url.endswith("'"):
    db_url = db_url[1:-1]

# Mask password for display
masked_url = re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", db_url)
print(f"\n[INFO] Connecting to: {masked_url}\n")

try:
    conn = psycopg2.connect(db_url)
    conn.set_session(readonly=True, autocommit=True)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    print("[OK] Connected successfully.\n")
except Exception as e:
    print(f"[ERROR] Could not connect: {e}")
    sys.exit(1)

results = {}

# 1. Schemas
cur.execute("""
    SELECT schema_name
    FROM information_schema.schemata
    WHERE schema_name NOT IN ('pg_catalog','information_schema','pg_toast')
    ORDER BY schema_name;
""")
schemas = [r["schema_name"] for r in cur.fetchall()]
results["schemas"] = schemas
print(f"=== SCHEMAS ({len(schemas)}) ===")
for s in schemas:
    print(f"  - {s}")
print()

# 2. Tables with columns, PK, FK, indexes
cur.execute("""
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_schema NOT IN ('pg_catalog','information_schema','pg_toast')
      AND table_type = 'BASE TABLE'
    ORDER BY table_schema, table_name;
""")
all_tables = cur.fetchall()
results["tables"] = {}

print(f"=== TABLES ({len(all_tables)}) ===")
for row in all_tables:
    schema = row["table_schema"]
    table = row["table_name"]
    key = f"{schema}.{table}"
    print(f"\n  [{key}]")

    cur.execute("""
        SELECT column_name, data_type, udt_name, character_maximum_length,
               is_nullable, column_default, ordinal_position
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
    """, (schema, table))
    columns = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
          AND tc.table_schema = %s AND tc.table_name = %s;
    """, (schema, table))
    pk_cols = {r["column_name"] for r in cur.fetchall()}

    cur.execute("""
        SELECT kcu.column_name,
               ccu.table_schema AS ftable_schema,
               ccu.table_name AS ftable_name,
               ccu.column_name AS fcolumn_name,
               rc.delete_rule
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.referential_constraints rc
          ON tc.constraint_name = rc.constraint_name AND tc.table_schema = rc.constraint_schema
        JOIN information_schema.constraint_column_usage ccu
          ON rc.unique_constraint_name = ccu.constraint_name AND rc.unique_constraint_schema = ccu.constraint_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = %s AND tc.table_name = %s;
    """, (schema, table))
    fk_map = {}
    for fk in cur.fetchall():
        fk_map[fk["column_name"]] = f"{fk['ftable_schema']}.{fk['ftable_name']}.{fk['fcolumn_name']} (ON DELETE {fk['delete_rule']})"

    cur.execute("""
        SELECT tc.constraint_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'UNIQUE'
          AND tc.table_schema = %s AND tc.table_name = %s
        ORDER BY tc.constraint_name, kcu.ordinal_position;
    """, (schema, table))
    unique_constraints = {}
    for ur in cur.fetchall():
        cn = ur["constraint_name"]
        if cn not in unique_constraints:
            unique_constraints[cn] = []
        unique_constraints[cn].append(ur["column_name"])

    cur.execute("""
        SELECT cc.constraint_name, cc.check_clause
        FROM information_schema.check_constraints cc
        JOIN information_schema.table_constraints tc
          ON cc.constraint_name = tc.constraint_name AND cc.constraint_schema = tc.table_schema
        WHERE tc.table_schema = %s AND tc.table_name = %s;
    """, (schema, table))
    check_constraints = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT i.relname AS index_name, a.attname AS column_name,
               ix.indisunique AS is_unique, ix.indisprimary AS is_primary
        FROM pg_class t
        JOIN pg_index ix ON t.oid = ix.indrelid
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        JOIN pg_namespace ns ON ns.oid = t.relnamespace
        WHERE t.relname = %s AND ns.nspname = %s AND t.relkind = 'r'
        ORDER BY i.relname, a.attnum;
    """, (table, schema))
    indexes = [dict(r) for r in cur.fetchall()]

    col_info = []
    for col in columns:
        dtype = col["data_type"]
        if col["character_maximum_length"]:
            dtype = f"{dtype}({col['character_maximum_length']})"
        col_info.append({
            "column": col["column_name"],
            "type": dtype,
            "nullable": col["is_nullable"],
            "default": col["column_default"],
            "pk": col["column_name"] in pk_cols,
            "fk": fk_map.get(col["column_name"], None)
        })
        print(f"    {col['column_name']:<35} {dtype:<28} {'NOT NULL' if col['is_nullable']=='NO' else 'NULL':<10} "
              f"PK={'Y' if col['column_name'] in pk_cols else 'N'}  "
              f"{'FK->'+fk_map[col['column_name']] if col['column_name'] in fk_map else ''}")

    if unique_constraints:
        print(f"    UNIQUE: {unique_constraints}")
    if check_constraints:
        print(f"    CHECK: {[c['constraint_name'] for c in check_constraints]}")
    idx_names = list({ix["index_name"] for ix in indexes})
    if idx_names:
        print(f"    INDEXES: {idx_names}")

    results["tables"][key] = {
        "columns": col_info,
        "unique_constraints": unique_constraints,
        "check_constraints": check_constraints,
        "indexes": indexes
    }

print()

# 3. Views
cur.execute("""
    SELECT table_schema, table_name
    FROM information_schema.views
    WHERE table_schema NOT IN ('pg_catalog','information_schema')
    ORDER BY table_schema, table_name;
""")
views = [dict(r) for r in cur.fetchall()]
results["views"] = views
print(f"=== VIEWS ({len(views)}) ===")
for v in views:
    print(f"  {v['table_schema']}.{v['table_name']}")
if not views:
    print("  (none)")
print()

# 4. Sequences
cur.execute("""
    SELECT sequence_schema, sequence_name, data_type, start_value, minimum_value, maximum_value, increment
    FROM information_schema.sequences
    WHERE sequence_schema NOT IN ('pg_catalog','information_schema')
    ORDER BY sequence_schema, sequence_name;
""")
sequences = [dict(r) for r in cur.fetchall()]
results["sequences"] = sequences
print(f"=== SEQUENCES ({len(sequences)}) ===")
for seq in sequences:
    print(f"  {seq['sequence_schema']}.{seq['sequence_name']} (start={seq['start_value']}, inc={seq['increment']})")
if not sequences:
    print("  (none)")
print()

# 5. ENUM types
cur.execute("""
    SELECT n.nspname AS schema, t.typname AS enum_name,
           array_agg(e.enumlabel ORDER BY e.enumsortorder) AS labels
    FROM pg_type t
    JOIN pg_enum e ON t.oid = e.enumtypid
    JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname NOT IN ('pg_catalog','information_schema')
    GROUP BY n.nspname, t.typname
    ORDER BY n.nspname, t.typname;
""")
enums = [dict(r) for r in cur.fetchall()]
results["enums"] = enums
print(f"=== ENUM TYPES ({len(enums)}) ===")
for e in enums:
    print(f"  {e['schema']}.{e['enum_name']}: {e['labels']}")
if not enums:
    print("  (none)")
print()

# 6. Triggers
cur.execute("""
    SELECT trigger_schema, trigger_name, event_object_table, event_manipulation,
           action_timing, action_statement
    FROM information_schema.triggers
    WHERE trigger_schema NOT IN ('pg_catalog','information_schema')
    ORDER BY trigger_schema, event_object_table, trigger_name;
""")
triggers = [dict(r) for r in cur.fetchall()]
results["triggers"] = triggers
print(f"=== TRIGGERS ({len(triggers)}) ===")
for t in triggers:
    print(f"  {t['trigger_schema']}.{t['event_object_table']}: {t['trigger_name']} ({t['action_timing']} {t['event_manipulation']})")
if not triggers:
    print("  (none)")
print()

# 7. Functions/Procedures
cur.execute("""
    SELECT n.nspname AS schema, p.proname AS name,
           pg_get_function_arguments(p.oid) AS args,
           pg_get_function_result(p.oid) AS return_type,
           CASE p.prokind WHEN 'f' THEN 'function' WHEN 'p' THEN 'procedure'
                          WHEN 'a' THEN 'aggregate' WHEN 'w' THEN 'window' END AS kind
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname NOT IN ('pg_catalog','information_schema')
    ORDER BY n.nspname, p.proname;
""")
functions = [dict(r) for r in cur.fetchall()]
results["functions"] = functions
print(f"=== FUNCTIONS/PROCEDURES ({len(functions)}) ===")
for fn in functions:
    print(f"  {fn['schema']}.{fn['name']}({fn['args']}) -> {fn['return_type']} [{fn['kind']}]")
if not functions:
    print("  (none)")
print()

# 8. Alembic version
try:
    cur.execute("SELECT version_num FROM alembic_version;")
    alembic_versions = [r["version_num"] for r in cur.fetchall()]
except Exception:
    alembic_versions = ["(alembic_version table not found)"]
results["alembic_version"] = alembic_versions
print(f"=== ALEMBIC VERSION ===")
for av in alembic_versions:
    print(f"  {av}")
print()

# 9. Row counts
print("=== ROW COUNTS ===")
row_counts = {}
for full_name in results["tables"]:
    schema, table = full_name.split(".", 1)
    try:
        cur.execute(f'SELECT COUNT(*) AS cnt FROM "{schema}"."{table}";')
        cnt = cur.fetchone()["cnt"]
    except Exception as e:
        cnt = f"error: {e}"
    row_counts[full_name] = cnt
    print(f"  {full_name:<55} {cnt} rows")
results["row_counts"] = row_counts
print()

# Summary
total_cols = sum(len(v["columns"]) for v in results["tables"].values())
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  Schemas  : {len(results['schemas'])}")
print(f"  Tables   : {len(results['tables'])}")
print(f"  Columns  : {total_cols}")
print(f"  Views    : {len(results['views'])}")
print(f"  Sequences: {len(results['sequences'])}")
print(f"  ENUMs    : {len(results['enums'])}")
print(f"  Triggers : {len(results['triggers'])}")
print(f"  Functions: {len(results['functions'])}")
print()

# Save JSON results
out_path = os.path.join(os.path.dirname(__file__), "db_inspection_result.json")
def clean(obj):
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean(i) for i in obj]
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)

with open(out_path, "w") as jf:
    json.dump(clean(results), jf, indent=2)
print(f"[INFO] Full JSON saved to: {out_path}")

cur.close()
conn.close()
print("[INFO] Connection closed. No data was modified.")
