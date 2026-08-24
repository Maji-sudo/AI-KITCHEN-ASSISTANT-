from typing import List
from sqlalchemy.orm import Session
from app.repositories.base_repository import CRUDBase
from app.models.system_log import SystemLog
from app.schemas.system_log import SystemLogCreate
from pydantic import BaseModel

class SystemLogRepository(CRUDBase[SystemLog, SystemLogCreate, BaseModel]):
    def get_by_device(self, db: Session, *, device_id: str, skip: int = 0, limit: int = 100) -> List[SystemLog]:
        return (
            db.query(SystemLog)
            .filter(SystemLog.device_id == device_id)
            .order_by(SystemLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_level(self, db: Session, *, device_id: str, log_level: str, limit: int = 100) -> List[SystemLog]:
        return (
            db.query(SystemLog)
            .filter(SystemLog.device_id == device_id, SystemLog.log_level == log_level)
            .order_by(SystemLog.created_at.desc())
            .limit(limit)
            .all()
        )

system_log_repo = SystemLogRepository(SystemLog)
