from typing import List
from sqlalchemy.orm import Session
from app.repositories.system_log_repository import system_log_repo
from app.schemas.system_log import SystemLogCreate
from app.models.system_log import SystemLog

class SystemLogService:
    def log(self, db: Session, device_id: str, log_level: str, message: str) -> SystemLog:
        """Persist a device log entry."""
        log_in = SystemLogCreate(device_id=device_id, log_level=log_level, message=message)
        return system_log_repo.create(db, obj_in=log_in)

    def get_device_logs(self, db: Session, device_id: str, skip: int = 0, limit: int = 100) -> List[SystemLog]:
        return system_log_repo.get_by_device(db, device_id=device_id, skip=skip, limit=limit)

    def get_errors(self, db: Session, device_id: str, limit: int = 100) -> List[SystemLog]:
        return system_log_repo.get_by_level(db, device_id=device_id, log_level="ERROR", limit=limit)

system_log_service = SystemLogService()
