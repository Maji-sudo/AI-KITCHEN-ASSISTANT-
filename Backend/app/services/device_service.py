from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.device_repository import device_repo, cylinder_repo
from app.schemas.device import DeviceCreate, DeviceUpdate, CylinderCreate, CylinderUpdate
from app.models.device import Device
from app.models.cylinder import Cylinder

class DeviceService:
    # --- Device Operations ---
    def get_device(self, db: Session, device_id: str) -> Optional[Device]:
        return device_repo.get(db, id=device_id)

    def get_user_devices(self, db: Session, user_id: int) -> List[Device]:
        return device_repo.get_by_user(db, user_id=user_id)

    def register_device(self, db: Session, device_in: DeviceCreate) -> Device:
        return device_repo.create(db, obj_in=device_in)

    def update_device(self, db: Session, db_device: Device, device_in: DeviceUpdate) -> Device:
        return device_repo.update(db, db_obj=db_device, obj_in=device_in)

    # --- Cylinder Operations ---
    def get_device_cylinders(self, db: Session, device_id: str) -> List[Cylinder]:
        return cylinder_repo.get_by_device(db, device_id=device_id)
        
    def add_cylinder(self, db: Session, cylinder_in: CylinderCreate) -> Cylinder:
        return cylinder_repo.create(db, obj_in=cylinder_in)

device_service = DeviceService()
