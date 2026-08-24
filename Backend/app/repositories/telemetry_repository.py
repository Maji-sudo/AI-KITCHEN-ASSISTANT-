from typing import List
from datetime import datetime

from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.repositories.base_repository import CRUDBase

from app.models.gas_reading import GasReading
from app.models.weight_reading import WeightReading
from app.models.leak_event import LeakEvent

from app.schemas.telemetry import (
    GasReadingCreate,
    WeightReadingCreate,
    LeakEventCreate,
    LeakEventUpdate,
)


# ==========================================================
# GAS READING REPOSITORY
# ==========================================================

class GasReadingRepository(
    CRUDBase[GasReading, GasReadingCreate, BaseModel]
):

    def get_latest_for_device(
        self,
        db: Session,
        *,
        device_id: str,
        limit: int = 100
    ) -> List[GasReading]:

        return (
            db.query(GasReading)
            .filter(
                GasReading.device_id == device_id
            )
            .order_by(
                GasReading.timestamp.desc()
            )
            .limit(limit)
            .all()
        )


# ==========================================================
# WEIGHT READING REPOSITORY
# ==========================================================

class WeightReadingRepository(
    CRUDBase[WeightReading, WeightReadingCreate, BaseModel]
):

    # ------------------------------------------------------
    # Get latest weight readings
    # ------------------------------------------------------

    def get_latest_for_device(
        self,
        db: Session,
        *,
        device_id: str,
        limit: int = 100
    ) -> List[WeightReading]:

        return (
            db.query(WeightReading)
            .filter(
                WeightReading.device_id == device_id
            )
            .order_by(
                WeightReading.timestamp.desc()
            )
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------
    # Get weight readings within a time period
    # ------------------------------------------------------

    def get_for_period(
        self,
        db: Session,
        *,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[WeightReading]:

        return (
            db.query(WeightReading)
            .filter(
                WeightReading.device_id == device_id,
                WeightReading.timestamp >= start_time,
                WeightReading.timestamp <= end_time,
            )
            .order_by(
                WeightReading.timestamp.asc()
            )
            .all()
        )


# ==========================================================
# LEAK EVENT REPOSITORY
# ==========================================================

class LeakEventRepository(
    CRUDBase[
        LeakEvent,
        LeakEventCreate,
        LeakEventUpdate
    ]
):

    def get_unresolved_for_device(
        self,
        db: Session,
        *,
        device_id: str
    ) -> List[LeakEvent]:

        return (
            db.query(LeakEvent)
            .filter(
                LeakEvent.device_id == device_id,
                LeakEvent.end_time == None
            )
            .all()
        )


# ==========================================================
# REPOSITORY INSTANCES
# ==========================================================

gas_reading_repo = GasReadingRepository(
    GasReading
)

weight_reading_repo = WeightReadingRepository(
    WeightReading
)

leak_event_repo = LeakEventRepository(
    LeakEvent
)