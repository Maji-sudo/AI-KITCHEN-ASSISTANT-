import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def init_postgres():
    password = "postgre123"
    print(f"Connecting to PostgreSQL with user 'postgres'...")
    try:
        conn = psycopg2.connect(f"postgresql://postgres:{password}@127.0.0.1:5432/postgres")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Get list of existing databases
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = [row[0] for row in cur.fetchall()]
        print(f"Existing PostgreSQL databases: {databases}")

        target_db = "safegas"
        if target_db not in databases:
            cur.execute(f'CREATE DATABASE "{target_db}";')
            print(f"CREATED database: {target_db}")
        else:
            print(f"Database '{target_db}' already exists.")

        cur.close()
        conn.close()
        return True, target_db
    except Exception as e:
        print(f"PostgreSQL connection error: {e}")
        return False, None

if __name__ == "__main__":
    init_postgres()
