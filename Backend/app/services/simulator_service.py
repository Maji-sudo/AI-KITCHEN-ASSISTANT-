import threading
import time
import logging
import random
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.telemetry import GasReadingCreate
from app.services.telemetry_service import telemetry_service
from app.db.database import get_db

logger = logging.getLogger(__name__)


def _get_db_session() -> Session:
    """Helper to acquire a DB session, respecting FastAPI dependency overrides (e.g. in tests)."""
    from app.main import app
    db_func = app.dependency_overrides.get(get_db, get_db)
    gen = db_func()
    return next(gen)


class SimulatorState:
    """Track the runtime state of an active background simulator thread."""

    def __init__(
        self,
        device_id: str,
        baseline_ppm: float,
        interval_seconds: float,
        count: Optional[int],
        mode: str,
    ):
        self.device_id = device_id
        self.baseline_ppm = baseline_ppm
        self.interval_seconds = interval_seconds
        self.count = count
        self.mode = mode
        self.generated_count = 0
        self.stop_requested = False
        self.thread: Optional[threading.Thread] = None
        self.last_ppm: Optional[float] = None

    def is_running(self) -> bool:
        return (
            self.thread is not None
            and self.thread.is_alive()
            and not self.stop_requested
        )

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "running": self.is_running(),
            "generated_count": self.generated_count,
            "baseline_ppm": self.baseline_ppm,
            "last_ppm": self.last_ppm,
            "interval_seconds": self.interval_seconds,
            "mode": self.mode,
        }


class SimulatorService:
    """
    Development-only Realtime Telemetry Simulator Service.

    Generates simulated gas readings for a device and routes every single reading
    through the canonical telemetry_service.record_gas_reading(...) pipeline.

    CRITICAL SAFETY REQUIREMENT:
    This service MUST NOT contain any gas classification, leak detection, notification,
    or valve auto-shutoff logic. All safety evaluations are handled strictly downstream
    by the canonical TelemetryService.
    """

    def __init__(self):
        self._simulators: Dict[str, SimulatorState] = {}
        self._lock = threading.Lock()

    def _is_running_locked(self, device_id: str) -> bool:
        """Check running state WITHOUT acquiring the lock. Caller must hold self._lock."""
        sim = self._simulators.get(device_id)
        return sim.is_running() if sim else False

    def is_running(self, device_id: str) -> bool:
        """Thread-safe public check. Acquires the lock internally."""
        with self._lock:
            return self._is_running_locked(device_id)

    def start_simulation(
        self,
        device_id: str,
        baseline_ppm: float = 300.0,
        interval_seconds: float = 1.0,
        count: Optional[int] = None,
        mode: str = "fluctuate",
    ) -> SimulatorState:
        """
        Start simulating gas telemetry for device_id.
        Raises HTTP 409 Conflict if a simulator is already running for device_id.
        """
        with self._lock:
            if self._is_running_locked(device_id):  # uses lock-free helper — lock already held
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Simulator is already running for device '{device_id}'"
                )

            sim = SimulatorState(
                device_id=device_id,
                baseline_ppm=baseline_ppm,
                interval_seconds=interval_seconds,
                count=count,
                mode=mode or "fluctuate",
            )
            self._simulators[device_id] = sim

            t = threading.Thread(
                target=self._run_loop,
                args=(sim,),
                name=f"SimulatorThread-{device_id}",
                daemon=True,
            )
            sim.thread = t
            t.start()
            return sim

    def _run_loop(self, sim: SimulatorState):
        logger.info(f"[SIMULATOR] Thread started for device {sim.device_id}")
        step = 0
        while not sim.stop_requested:
            if sim.count is not None and sim.generated_count >= sim.count:
                logger.info(f"[SIMULATOR] Reached count limit ({sim.count}) for device {sim.device_id}")
                break

            # Generate realistic changing PPM value based on mode
            if sim.mode == "spike":
                ppm = sim.baseline_ppm + (step * 250.0)
            elif sim.mode == "increase":
                ppm = sim.baseline_ppm + (step * 50.0)
            elif sim.mode == "decrease":
                ppm = max(0.0, sim.baseline_ppm - (step * 20.0))
            else:  # fluctuate
                noise = random.uniform(-15.0, 15.0)
                drift = (step % 4) * 3.0
                ppm = max(0.0, sim.baseline_ppm + noise + drift)

            ppm = round(ppm, 1)
            sim.last_ppm = ppm

            # Send via canonical telemetry service
            db = _get_db_session()
            try:
                reading_in = GasReadingCreate(
                    device_id=sim.device_id,
                    ppm_value=ppm,
                    status="normal",  # Re-classified by canonical service
                    timestamp=datetime.now(timezone.utc),
                    source="SIMULATOR",
                )
                telemetry_service.record_gas_reading(db, reading_in)
                sim.generated_count += 1
            except Exception as exc:
                logger.error(f"[SIMULATOR] Ingestion error on device {sim.device_id}: {exc}")
            finally:
                db.close()

            step += 1

            if sim.count is not None and sim.generated_count >= sim.count:
                break

            time.sleep(sim.interval_seconds)

        sim.stop_requested = True
        logger.info(f"[SIMULATOR] Thread finished for device {sim.device_id}")

    def stop_simulation(self, device_id: str) -> bool:
        """Stop simulator background thread for device_id cleanly."""
        with self._lock:
            sim = self._simulators.get(device_id)
            if not sim:
                return False

            sim.stop_requested = True
            return True

    def stop_all(self, timeout: float = 2.0) -> None:
        """Stop all running simulator background threads and wait for them to finish."""
        with self._lock:
            threads = []
            for sim in list(self._simulators.values()):
                sim.stop_requested = True
                if sim.thread and sim.thread.is_alive():
                    threads.append(sim.thread)
            self._simulators.clear()

        for t in threads:
            if t != threading.current_thread():
                t.join(timeout=timeout)

    def get_status(self, device_id: str) -> dict:
        """Return simulator status for device_id."""
        with self._lock:
            sim = self._simulators.get(device_id)
            if not sim:
                return {
                    "device_id": device_id,
                    "running": False,
                    "generated_count": 0,
                    "baseline_ppm": None,
                    "last_ppm": None,
                    "interval_seconds": None,
                    "mode": None,
                }
            return sim.to_dict()

    def generate_single_reading(self, db: Session, device_id: str, ppm_value: float) -> Any:
        """Direct helper to ingest one SIMULATOR reading via canonical service."""
        reading_in = GasReadingCreate(
            device_id=device_id,
            ppm_value=ppm_value,
            status="normal",
            timestamp=datetime.now(timezone.utc),
            source="SIMULATOR",
        )
        return telemetry_service.record_gas_reading(db, reading_in)


simulator_service = SimulatorService()
