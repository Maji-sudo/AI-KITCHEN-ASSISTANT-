import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def check_and_seed_safegas_iot():
    password = "postgre123"
    target_db = "SAFEGAS IoT"
    print(f"Connecting to PostgreSQL to check database '{target_db}'...")
    
    conn = psycopg2.connect(f"postgresql://postgres:{password}@127.0.0.1:5432/postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    cur.execute("SELECT datname FROM pg_database WHERE datname = %s;", (target_db,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{target_db}";')
        print(f"Created database: '{target_db}'")
    else:
        print(f"Database '{target_db}' already exists.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_and_seed_safegas_iot()
