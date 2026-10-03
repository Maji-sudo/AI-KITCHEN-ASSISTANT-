import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.main import app
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.device import Device
from app.models.gas_reading import GasReading
from app.models.leak_event import LeakEvent
from app.models.notification import Notification
from app.models.device_command import DeviceCommand

# --- Fixtures ---

@pytest.fixture
def mock_user():
    return User(id=1, email="demo@safegas.com", name="Demo User", phone="+1234567890", language_pref="en")

@pytest.fixture
def test_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.database import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    yield db
    db.close()

@pytest.fixture
def client(test_db, mock_user):
    def override_get_db():
        yield test_db

    def override_get_current_user():
        return mock_user

    original_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)

@pytest.fixture
def setup_device(test_db, mock_user):
    test_db.add(mock_user)
    device = Device(
        id="SGD-DEMO-001",
        user_id=mock_user.id,
        name="Demo Sensor",
        firmware_version="1.0.0",
        status="active"
    )
    test_db.add(device)
    test_db.commit()
    return device


class TestPhase4EndToEndDemonstration:

    def _inject_manual_telemetry(self, client, device_id, ppm):
        return client.post(
            "/api/v1/telemetry/manual/gas",
            json={
                "device_id": device_id,
                "ppm_value": ppm,
                "source": "SIMULATOR"
            }
        )
        
    def _get_safety_status(self, client, device_id):
        return client.get(f"/api/v1/devices/{device_id}/safety")
        
    def _get_active_leak(self, client, device_id):
        return client.get(f"/api/v1/devices/{device_id}/leaks/active")
        
    def _get_leak_history(self, client, device_id):
        return client.get(f"/api/v1/devices/{device_id}/leaks")

    def test_full_demonstration_lifecycle(self, client, test_db, setup_device):
        device_id = setup_device.id
        
        # ==============================================================
        # TEST SCENARIO A — NORMAL
        # ==============================================================
        print("\\n[SCENARIO A] Injecting NORMAL telemetry (100 PPM)...")
        r_a = self._inject_manual_telemetry(client, device_id, 100)
        assert r_a.status_code == 201, f"Expected 201, got {r_a.status_code}: {r_a.text}"
        
        # Verify DB
        readings = test_db.query(GasReading).all()
        assert len(readings) == 1
        assert readings[0].ppm_value == 100
        assert readings[0].status == "normal"
        
        leaks = test_db.query(LeakEvent).all()
        assert len(leaks) == 0
        
        # Verify API
        safety_a = self._get_safety_status(client, device_id).json()
        assert safety_a["latest_gas_ppm"] == 100
        assert safety_a["status"] == "normal"
        assert safety_a["valve_status"] == "OPEN"
        
        active_a = self._get_active_leak(client, device_id).json()
        assert active_a is None
        
        print("OK: SCENARIO A VERIFIED")

        # ==============================================================
        # TEST SCENARIO B — WARNING
        # ==============================================================
        print("\\n[SCENARIO B] Injecting WARNING telemetry (700 PPM)...")
        r_b = self._inject_manual_telemetry(client, device_id, 700)
        assert r_b.status_code == 201
        
        # Verify DB
        readings = test_db.query(GasReading).order_by(GasReading.timestamp.desc()).all()
        assert readings[0].ppm_value == 700
        assert readings[0].status == "warning"
        
        notifications = test_db.query(Notification).all()
        warning_notifs = [n for n in notifications if n.payload and n.payload.get("type") == "GAS_LEVEL_WARNING"]
        assert len(warning_notifs) >= 1
        
        leaks = test_db.query(LeakEvent).all()
        assert len(leaks) == 0  # Still 0
        
        # Verify API
        safety_b = self._get_safety_status(client, device_id).json()
        assert safety_b["latest_gas_ppm"] == 700
        assert safety_b["status"] == "warning"
        assert safety_b["valve_status"] == "OPEN"
        
        print("OK: SCENARIO B VERIFIED")

        # ==============================================================
        # TEST SCENARIO C — CRITICAL
        # ==============================================================
        print("\\n[SCENARIO C] Injecting CRITICAL telemetry (1200 PPM)...")
        r_c = self._inject_manual_telemetry(client, device_id, 1200)
        assert r_c.status_code == 201
        
        # Verify DB
        leaks = test_db.query(LeakEvent).all()
        assert len(leaks) == 1
        assert leaks[0].peak_ppm == 1200
        assert leaks[0].end_time is None
        
        db_device = test_db.query(Device).filter_by(id=device_id).first()
        assert db_device.valve_status == "CLOSED"
        
        # Verify API
        safety_c = self._get_safety_status(client, device_id).json()
        assert safety_c["latest_gas_ppm"] == 1200
        assert safety_c["status"] == "critical"
        assert safety_c["valve_status"] == "CLOSED"
        
        active_c = self._get_active_leak(client, device_id).json()
        assert active_c is not None
        assert active_c["peak_ppm"] == 1200
        assert active_c["active"] is True
        
        print("OK: SCENARIO C VERIFIED")

        # ==============================================================
        # TEST SCENARIO D — PEAK UPDATE
        # ==============================================================
        print("\\n[SCENARIO D] Injecting CRITICAL PEAK telemetry (1800 PPM)...")
        r_d = self._inject_manual_telemetry(client, device_id, 1800)
        assert r_d.status_code == 201
        
        # Verify DB
        leaks = test_db.query(LeakEvent).all()
        assert len(leaks) == 1  # No duplicate
        assert leaks[0].peak_ppm == 1800
        
        # Verify API
        safety_d = self._get_safety_status(client, device_id).json()
        assert safety_d["latest_gas_ppm"] == 1800
        
        active_d = self._get_active_leak(client, device_id).json()
        assert active_d["peak_ppm"] == 1800
        assert active_d["active"] is True
        
        print("✓ SCENARIO D VERIFIED")

        # ==============================================================
        # TEST SCENARIO E — RECOVERY
        # ==============================================================
        print("\\n[SCENARIO E] Injecting RECOVERY telemetry (300 PPM)...")
        r_e = self._inject_manual_telemetry(client, device_id, 300)
        assert r_e.status_code == 201
        
        # Verify DB
        leaks = test_db.query(LeakEvent).all()
        assert len(leaks) == 1
        assert leaks[0].end_time is not None
        assert leaks[0].peak_ppm == 1800  # Peak is preserved
        
        db_device = test_db.query(Device).filter_by(id=device_id).first()
        assert db_device.valve_status == "CLOSED"  # Lockout remains
        
        # Verify API
        safety_e = self._get_safety_status(client, device_id).json()
        assert safety_e["latest_gas_ppm"] == 300
        assert safety_e["status"] == "normal"
        assert safety_e["valve_status"] == "CLOSED"
        
        active_e = self._get_active_leak(client, device_id).json()
        assert active_e is None
        
        history_e = self._get_leak_history(client, device_id).json()["leaks"]
        assert len(history_e) == 1
        assert history_e[0]["end_time"] is not None
        
        print("✓ SCENARIO E VERIFIED")

        # ==============================================================
        # TEST SCENARIO F — NEW CRITICAL EVENT
        # ==============================================================
        print("\\n[SCENARIO F] Injecting NEW CRITICAL telemetry (1500 PPM)...")
        r_f = self._inject_manual_telemetry(client, device_id, 1500)
        assert r_f.status_code == 201
        
        # Verify DB
        leaks = test_db.query(LeakEvent).all()
        assert len(leaks) == 2
        
        active_f = self._get_active_leak(client, device_id).json()
        assert active_f is not None
        assert active_f["peak_ppm"] == 1500
        assert active_f["active"] is True
        
        print("✓ SCENARIO F VERIFIED")


    def test_threshold_boundaries(self, client, test_db, setup_device):
        device_id = setup_device.id
        
        def check_status(ppm, expected):
            client.post("/api/v1/telemetry/manual/gas", json={"device_id": device_id, "ppm_value": ppm, "source": "SIMULATOR"})
            status = client.get(f"/api/v1/devices/{device_id}/safety").json()["status"]
            assert status == expected, f"Expected {expected} for {ppm} PPM, got {status}"

        # Test boundaries
        check_status(499, "normal")
        check_status(500, "warning")
        check_status(999, "warning")
        check_status(1000, "critical")

    def test_device_isolation(self, client, test_db, mock_user):
        test_db.add(mock_user)
        # Create two devices
        dev_a = Device(id="DEV-A", user_id=mock_user.id, name="Device A", status="active")
        dev_b = Device(id="DEV-B", user_id=mock_user.id, name="Device B", status="active")
        test_db.add(dev_a)
        test_db.add(dev_b)
        test_db.commit()

        # Inject CRITICAL into A
        self._inject_manual_telemetry(client, "DEV-A", 1500)
        
        # Inject NORMAL into B
        self._inject_manual_telemetry(client, "DEV-B", 200)

        safety_a = self._get_safety_status(client, "DEV-A").json()
        assert safety_a["status"] == "critical"
        
        safety_b = self._get_safety_status(client, "DEV-B").json()
        assert safety_b["status"] == "normal"
        
        active_a = self._get_active_leak(client, "DEV-A").json()
        assert active_a is not None
        
        active_b = self._get_active_leak(client, "DEV-B").json()
        assert active_b is None

