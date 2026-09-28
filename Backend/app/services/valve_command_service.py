import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.device import Device
from app.schemas.device_command import DeviceCommandCreate
from app.repositories.device_command_repository import device_command_repo

logger = logging.getLogger(__name__)

class ValveCommandService:

    def _verify_device_ownership(self, db: Session, device_id: str, user_id: int) -> Device:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        if device.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this device"
            )
        return device

    def emergency_close(self, db: Session, device_id: str, user_id: int) -> Device:
        """
        Manually requested emergency close.
        Validates ownership and issues a close command.
        """
        device = self._verify_device_ownership(db, device_id, user_id)
        return self.issue_emergency_close(db, device)

    def reset_valve(self, db: Session, device_id: str, user_id: int) -> Device:
        """
        Manually requested reset.
        Validates ownership and issues an open/reset command.
        """
        device = self._verify_device_ownership(db, device_id, user_id)
        
        # Idempotency check
        if device.valve_status == "OPEN":
            logger.info("Valve already OPEN for device %s. Skipping reset.", device_id)
            return device
            
        device.valve_status = "OPEN"
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Record command
        cmd_in = DeviceCommandCreate(
            device_id=device_id,
            command="RESET"
        )
        device_command_repo.create(db, obj_in=cmd_in)
        logger.info("Recorded RESET command for device %s", device_id)
        return device

    def issue_emergency_close(self, db: Session, device: Device) -> Device:
        """
        Internal method to issue emergency close (e.g. from telemetry).
        Does NOT check ownership since telemetry service might not have user_id handy
        in the immediate state machine context, or it's handled automatically.
        """
        if device.valve_status == "CLOSED":
            logger.info("Valve already CLOSED for device %s. Skipping emergency close.", device.id)
            return device

        device.valve_status = "CLOSED"
        db.add(device)
        db.commit()
        db.refresh(device)

        # Record command
        cmd_in = DeviceCommandCreate(
            device_id=device.id,
            command="EMERGENCY_CLOSE"
        )
        device_command_repo.create(db, obj_in=cmd_in)
        logger.info("Recorded EMERGENCY_CLOSE command for device %s", device.id)
        return device

valve_command_service = ValveCommandService()
