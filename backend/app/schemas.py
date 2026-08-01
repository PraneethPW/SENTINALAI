from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)
class LoginIn(BaseModel): email: EmailStr; password: str
class TokenOut(BaseModel): access_token: str; token_type: str = "bearer"
class DeviceIn(BaseModel): name: str; platform: str
class DeviceUpdateIn(BaseModel): name: str = Field(min_length=2, max_length=120); platform: str = Field(min_length=2, max_length=40); status: str = Field(default="protected", max_length=30); risk_score: int = Field(default=18, ge=0, le=100)
class ContactIn(BaseModel): name: str; phone: str; relationship: str
class ProfileIn(BaseModel): full_name: str = Field(min_length=2, max_length=120); phone: str = Field(default="", max_length=40); location_label: str = Field(default="", max_length=120); emergency_mode: bool = False
class NotificationIn(BaseModel): push_enabled: bool = True; email_enabled: bool = True; sms_enabled: bool = False; weekly_summary: bool = True
class GeofenceIn(BaseModel): name: str = Field(min_length=2, max_length=120); latitude: float; longitude: float; radius_meters: int = Field(ge=50, le=10000); enabled: bool = True
class BrowserConnectIn(BaseModel): name: str = Field(min_length=2, max_length=120); platform: str = Field(min_length=2, max_length=40); user_agent: str = Field(max_length=1000)
class BrowserSyncIn(BaseModel): online: bool; battery_percent: int | None = Field(default=None, ge=0, le=100); network_type: str = Field(default="unknown", max_length=40); user_agent: str = Field(default="", max_length=1000)
class LocationUpdateIn(BaseModel): latitude: float = Field(ge=-90, le=90); longitude: float = Field(ge=-180, le=180); accuracy_meters: int = Field(default=0, ge=0, le=100000)
class AskIn(BaseModel): message: str = Field(min_length=2, max_length=2000)
class EventOut(BaseModel): id: int; title: str; severity: str; description: str; occurred_at: datetime
class DashboardOut(BaseModel): score: int; score_label: str; devices: list[dict]; events: list[EventOut]; recommendations: list[str]
