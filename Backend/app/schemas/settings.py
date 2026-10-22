from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class DeliveryAddressSchema(BaseModel):
    address_line: str = Field(..., min_length=2, max_length=255, description="House/Flat/Block, Street")
    area: str = Field(..., min_length=2, max_length=150, description="Area, Locality, or Landmark")
    city: str = Field(..., min_length=2, max_length=100, description="City")
    state: str = Field(..., min_length=2, max_length=100, description="State")
    pincode: str = Field(..., min_length=4, max_length=10, description="Postal PIN Code")

    @property
    def formatted(self) -> str:
        parts = [self.address_line, self.area, self.city, f"{self.state} - {self.pincode}"]
        return ", ".join([p.strip() for p in parts if p.strip()])


class NotificationPreferencesSchema(BaseModel):
    fcm_enabled: bool = True
    sms_enabled: bool = True
    whatsapp_enabled: bool = True
    gas_leak_alerts: bool = True
    cylinder_refill_reminders: bool = True
    weekly_efficiency_reports: bool = True
    device_offline_alerts: bool = True


class SafetyPreferencesSchema(BaseModel):
    emergency_buzzer: bool = True
    auto_shutoff_enabled: bool = True
    leak_sensitivity: str = Field(default="high", description="low | medium | high")
    warning_threshold_ppm: int = Field(default=500, ge=200, le=900)


class UpdateProfileSettingsRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    language_pref: Optional[str] = Field(None, max_length=10)


class DeviceSummary(BaseModel):
    id: str
    name: str
    status: str
    valve_status: Optional[str] = "OPEN"
    battery_level: Optional[int] = None
    signal_strength: Optional[int] = None

    class Config:
        from_attributes = True


class SettingsResponse(BaseModel):
    profile: Dict[str, Any]
    delivery_address: Optional[Dict[str, Any]] = None
    notification_preferences: Dict[str, Any]
    safety_preferences: Dict[str, Any]
    devices: List[DeviceSummary] = []
