"""
Automated tests for Alembic migration chain verification.
Tests that the migration chain creates the complete schema from a completely empty database,
verifies foreign keys and constraints, checks boolean server defaults, and validates
offline SQL generation for PostgreSQL.
"""
import os
import sys
import tempfile
import subprocess
import urllib.parse
import pytest
from sqlalchemy import create_engine, inspect, text


EXPECTED_APPLICATION_TABLES = {
    "bookings",
    "cooking_history",
    "cylinders",
    "device_commands",
    "devices",
    "dish_library",
    "efficiency_scores",
    "gas_readings",
    "leak_events",
    "notifications",
    "recommendations",
    "refill_predictions",
    "system_logs",
    "usage_analytics",
    "users",
    "weight_readings",
}


@pytest.fixture
def empty_test_db():
    """Create an isolated, empty temporary database for migration testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "migration_test.db")
    db_url = f"sqlite:///{db_path}"

    yield {"path": db_path, "url": db_url}

    # Teardown
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


def run_alembic_command(db_url: str, args: list[str]) -> subprocess.CompletedProcess:
    """Run an alembic command pointing to the given test database using the active Python interpreter."""
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url
    env["JWT_SECRET"] = "x" * 32
    env["DEBUG"] = "False"

    # Backend root is current working directory or relative to tests
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return subprocess.run(
        [sys.executable, "-m", "alembic"] + args,
        cwd=backend_dir,
        env=env,
        capture_output=True,
        text=True,
    )


def test_migration_chain_creates_complete_schema_from_empty_db(empty_test_db):
    """Verify that alembic upgrade head creates all expected tables on an empty database."""
    proc = run_alembic_command(empty_test_db["url"], ["upgrade", "head"])
    assert proc.returncode == 0, f"Alembic upgrade failed:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"

    engine = create_engine(empty_test_db["url"])
    try:
        insp = inspect(engine)
        actual_tables = set(insp.get_table_names())

        assert "alembic_version" in actual_tables
        missing_tables = EXPECTED_APPLICATION_TABLES - actual_tables
        assert not missing_tables, f"Missing tables after migration: {missing_tables}"

        # Verify alembic_version is at the head revision
        with engine.connect() as conn:
            current_rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            assert current_rev == "20fc3eb6190a", f"Expected head revision 20fc3eb6190a, got {current_rev}"
    finally:
        engine.dispose()


def test_important_foreign_keys_exist_after_migration(empty_test_db):
    """Verify that key foreign-key relationships exist across tables after migration."""
    proc = run_alembic_command(empty_test_db["url"], ["upgrade", "head"])
    assert proc.returncode == 0, f"Alembic upgrade failed:\n{proc.stderr}"

    engine = create_engine(empty_test_db["url"])
    try:
        insp = inspect(engine)

        # Check devices -> users FK
        dev_fks = insp.get_foreign_keys("devices")
        dev_referred = {fk["referred_table"] for fk in dev_fks}
        assert "users" in dev_referred, f"devices missing FK to users: {dev_fks}"

        # Check recommendations -> devices and users FKs
        rec_fks = insp.get_foreign_keys("recommendations")
        rec_referred = {fk["referred_table"] for fk in rec_fks}
        assert "devices" in rec_referred, f"recommendations missing FK to devices: {rec_fks}"
        assert "users" in rec_referred, f"recommendations missing FK to users: {rec_fks}"

        # Check leak_events -> devices and notifications FKs
        leak_fks = insp.get_foreign_keys("leak_events")
        leak_referred = {fk["referred_table"] for fk in leak_fks}
        assert "devices" in leak_referred, f"leak_events missing FK to devices: {leak_fks}"
        assert "notifications" in leak_referred, f"leak_events missing FK to notifications: {leak_fks}"

        # Check device_commands -> devices FK
        cmd_fks = insp.get_foreign_keys("device_commands")
        cmd_referred = {fk["referred_table"] for fk in cmd_fks}
        assert "devices" in cmd_referred, f"device_commands missing FK to devices: {cmd_fks}"
    finally:
        engine.dispose()


def test_boolean_default_in_notifications_read(empty_test_db):
    """Verify that notifications.read default works correctly and evaluates to false."""
    proc = run_alembic_command(empty_test_db["url"], ["upgrade", "head"])
    assert proc.returncode == 0, f"Alembic upgrade failed:\n{proc.stderr}"

    engine = create_engine(empty_test_db["url"])
    try:
        insp = inspect(engine)
        cols = {c["name"]: c for c in insp.get_columns("notifications")}
        assert "read" in cols, "notifications table missing read column"

        # Insert a user and a notification without specifying read column
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO users (name, email, phone, language_pref) "
                    "VALUES ('Test User', 'test@example.com', '+919999999999', 'en')"
                )
            )
            user_id = conn.execute(text("SELECT id FROM users WHERE email = 'test@example.com'")).scalar()

            conn.execute(
                text(
                    "INSERT INTO notifications (user_id, channel, sent_at, delivery_status) "
                    "VALUES (:uid, 'app', '2026-10-18 12:00:00', 'delivered')"
                ),
                {"uid": user_id},
            )

            # Check that read defaulted to false (0 / False)
            read_val = conn.execute(text("SELECT read FROM notifications WHERE user_id = :uid"), {"uid": user_id}).scalar()
            assert read_val in (False, 0), f"Expected false default for read, got {read_val}"
    finally:
        engine.dispose()


def test_offline_sql_generation_for_postgresql():
    """Verify that alembic upgrade head --sql generates valid DDL for PostgreSQL without error."""
    pg_test_url = "postgresql://postgres:dummy@localhost:5432/testdb"
    proc = run_alembic_command(pg_test_url, ["upgrade", "head", "--sql"])
    assert proc.returncode == 0, f"Alembic offline PostgreSQL generation failed:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"

    sql_output = proc.stdout
    assert "CREATE TABLE users" in sql_output
    assert "CREATE TABLE devices" in sql_output
    assert "CREATE TABLE dish_library" in sql_output
    assert "CREATE TABLE recommendations" in sql_output
    assert "CREATE TABLE device_commands" in sql_output
    assert "ALTER TABLE notifications ADD COLUMN read BOOLEAN DEFAULT false NOT NULL" in sql_output
    assert "UPDATE alembic_version SET version_num='20fc3eb6190a'" in sql_output


def test_migration_downgrade_and_reupgrade(empty_test_db):
    """Verify that full downgrade to base and re-upgrade to head works cleanly."""
    proc = run_alembic_command(empty_test_db["url"], ["upgrade", "head"])
    assert proc.returncode == 0

    proc_down = run_alembic_command(empty_test_db["url"], ["downgrade", "base"])
    assert proc_down.returncode == 0, f"Downgrade to base failed:\n{proc_down.stderr}"

    engine = create_engine(empty_test_db["url"])
    try:
        insp = inspect(engine)
        remaining_tables = set(insp.get_table_names()) - {"alembic_version"}
        assert not remaining_tables, f"Tables remained after downgrade to base: {remaining_tables}"
    finally:
        engine.dispose()

    # Re-upgrade to head
    proc_reup = run_alembic_command(empty_test_db["url"], ["upgrade", "head"])
    assert proc_reup.returncode == 0, f"Re-upgrade failed:\n{proc_reup.stderr}"


def test_live_postgresql_migration_on_disposable_database():
    """Verify that alembic upgrade head executes on an actual PostgreSQL instance if locally available."""
    try:
        import psycopg
        pg_url = os.getenv("PG_DATABASE_URL")
        if not pg_url and os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("DATABASE_URL="):
                        pg_url = line.split("=", 1)[1].strip()
                        break
        if not pg_url or not pg_url.startswith("postgres"):
            pytest.skip("No PostgreSQL connection available in environment or .env")

        parsed = urllib.parse.urlparse(pg_url)

        user = parsed.username
        password = parsed.password
        host = (parsed.hostname or "").lower()
        port = parsed.port or 5432

        # Safety guard: Refuse to run disposable DB creation against remote/cloud hosts
        ALLOWED_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
        if host not in ALLOWED_LOCAL_HOSTS:
            pytest.skip(
                f"Refusing to run live PostgreSQL disposable database test against remote/cloud host '{host or 'unspecified'}'"
            )

        # Verify connectivity to admin database on local host
        admin_conn = psycopg.connect(
            f"host={host} port={port} user={user} password={password} dbname=postgres",
            autocommit=True,
            connect_timeout=3,
        )
    except Exception as exc:
        pytest.skip(f"Local PostgreSQL not reachable on {host}:{port} ({type(exc).__name__})")

    cur = admin_conn.cursor()
    disposable_db = "safegas_test_disposable_pg"
    try:
        cur.execute(f"DROP DATABASE IF EXISTS {disposable_db};")
        cur.execute(f"CREATE DATABASE {disposable_db};")

        test_pg_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{disposable_db}"
        proc = run_alembic_command(test_pg_url, ["upgrade", "head"])
        assert proc.returncode == 0, f"Alembic live PostgreSQL upgrade failed:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"

        pg_engine = create_engine(test_pg_url)
        try:
            insp = inspect(pg_engine)
            actual_tables = set(insp.get_table_names())
            assert "alembic_version" in actual_tables
            missing = EXPECTED_APPLICATION_TABLES - actual_tables
            assert not missing, f"Missing tables on live PostgreSQL: {missing}"

            notif_cols = {c["name"]: c for c in insp.get_columns("notifications")}
            read_col = notif_cols.get("read")
            assert read_col is not None, "notifications.read column missing on PostgreSQL"
            assert str(read_col["type"]).upper() == "BOOLEAN"
            assert read_col["default"] == "false"
        finally:
            pg_engine.dispose()
    finally:
        try:
            cur.execute(f"DROP DATABASE IF EXISTS {disposable_db};")
            cur.close()
            admin_conn.close()
        except Exception:
            pass

