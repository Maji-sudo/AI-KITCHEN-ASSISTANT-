import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.device import Device
from app.schemas.settings import (
    DeliveryAddressSchema,
    NotificationPreferencesSchema,
    SafetyPreferencesSchema,
    UpdateProfileSettingsRequest,
    SettingsResponse,
    DeviceSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULT_NOTIFICATION_PREFS = {
    "fcm_enabled": True,
    "sms_enabled": True,
    "whatsapp_enabled": True,
    "gas_leak_alerts": True,
    "cylinder_refill_reminders": True,
    "weekly_efficiency_reports": True,
    "device_offline_alerts": True,
}

DEFAULT_SAFETY_PREFS = {
    "emergency_buzzer": True,
    "auto_shutoff_enabled": True,
    "leak_sensitivity": "high",
    "warning_threshold_ppm": 500,
}


@router.get("/", response_model=SettingsResponse)
def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve all settings for the authenticated user, including:
    - User profile details
    - Saved Target Delivery Address for cylinder refill booking
    - Notification preferences
    - Safety preferences
    - Connected devices
    """
    user_devices = db.query(Device).filter(Device.user_id == current_user.id).all()

    notif_prefs = {**DEFAULT_NOTIFICATION_PREFS, **(current_user.notification_preferences or {})}
    safety_prefs = {**DEFAULT_SAFETY_PREFS, **(current_user.safety_preferences or {})}

    return SettingsResponse(
        profile={
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "language_pref": current_user.language_pref,
        },
        delivery_address=current_user.delivery_address,
        notification_preferences=notif_prefs,
        safety_preferences=safety_prefs,
        devices=[
            DeviceSummary(
                id=d.id,
                name=d.name,
                status=d.status,
                valve_status=d.valve_status,
                battery_level=d.battery_level,
                signal_strength=d.signal_strength,
            )
            for d in user_devices
        ],
    )


@router.put("/profile")
def update_profile(
    body: UpdateProfileSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile details (name, phone, language preference)."""
    if body.name is not None:
        trimmed = body.name.strip()
        if not trimmed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Name cannot be blank.",
            )
        current_user.name = trimmed

    if body.phone is not None:
        current_user.phone = body.phone.strip() or None

    if body.language_pref is not None:
        current_user.language_pref = body.language_pref.strip()

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile updated successfully",
        "profile": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "language_pref": current_user.language_pref,
        },
    }


@router.put("/address")
def save_delivery_address(
    body: DeliveryAddressSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save the target delivery address used for cylinder refill booking.
    Persisted to PostgreSQL and isolated to the authenticated user.
    """
    address_dict = {
        "address_line": body.address_line.strip(),
        "area": body.area.strip(),
        "city": body.city.strip(),
        "state": body.state.strip(),
        "pincode": body.pincode.strip(),
        "formatted": body.formatted,
    }

    current_user.delivery_address = address_dict
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Target delivery address saved successfully",
        "delivery_address": current_user.delivery_address,
    }


@router.delete("/address")
def clear_delivery_address(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Clear the target delivery address.
    Removes it from persistent storage so subsequent cylinder bookings open with no address.
    """
    current_user.delivery_address = None
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Target delivery address cleared successfully",
        "delivery_address": None,
    }


@router.put("/notifications")
def update_notification_preferences(
    body: NotificationPreferencesSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update notification preferences for FCM, SMS, WhatsApp, and alert categories."""
    prefs = body.model_dump()
    current_user.notification_preferences = prefs
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Notification preferences updated successfully",
        "notification_preferences": current_user.notification_preferences,
    }


@router.put("/safety")
def update_safety_preferences(
    body: SafetyPreferencesSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Configure supported safety preferences without compromising emergency protections."""
    prefs = body.model_dump()
    current_user.safety_preferences = prefs
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Safety preferences updated successfully",
        "safety_preferences": current_user.safety_preferences,
    }
