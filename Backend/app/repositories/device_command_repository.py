from app.repositories.base_repository import CRUDBase
from app.models.device_command import DeviceCommand
from app.schemas.device_command import DeviceCommandCreate, DeviceCommandUpdate

class DeviceCommandRepository(CRUDBase[DeviceCommand, DeviceCommandCreate, DeviceCommandUpdate]):
    pass

device_command_repo = DeviceCommandRepository(DeviceCommand)
