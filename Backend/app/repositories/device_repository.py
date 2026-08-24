from typing import List
from sqlalchemy.orm import Session
from app.repositories.base_repository import CRUDBase
from app.models.device import Device
from app.models.cylinder import Cylinder
from app.schemas.device import DeviceCreate, DeviceUpdate, CylinderCreate, CylinderUpdate

class DeviceRepository(CRUDBase[Device, DeviceCreate, DeviceUpdate]):
    def get_by_user(self, db: Session, *, user_id: int) -> List[Device]:
        return db.query(Device).filter(Device.user_id == user_id).all()

class CylinderRepository(CRUDBase[Cylinder, CylinderCreate, CylinderUpdate]):
    def get_by_device(self, db: Session, *, device_id: str) -> List[Cylinder]:
        return db.query(Cylinder).filter(Cylinder.device_id == device_id).all()

device_repo = DeviceRepository(Device)
cylinder_repo = CylinderRepository(Cylinder)
