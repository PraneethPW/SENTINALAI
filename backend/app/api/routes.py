import asyncio
from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from uuid import uuid4
import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import create_token, current_user, hash_password, verify_password
from app.core.config import get_settings
from app.database import get_db
from app.models import BrowserDeviceState, BrowserStateMetric, Device, EventAcknowledgement, Geofence, LiveLocationState, NotificationPreference, SecurityEvent, TrustedContact, User, UserProfile
from app.schemas import AskIn, BrowserConnectIn, BrowserSyncIn, ContactIn, DashboardOut, DeviceIn, DeviceUpdateIn, GeofenceIn, LocationUpdateIn, LoginIn, NotificationIn, ProfileIn, RegisterIn, TokenOut
from app.services.ai import AIService
from app.services.realtime import hub

router = APIRouter()
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
def seed_workspace(db: Session, user: User):
    db.add_all([UserProfile(user_id=user.id), NotificationPreference(user_id=user.id)]); db.commit()

def owned_or_404(db: Session, model, record_id: int, user_id: int):
    record = db.get(model, record_id)
    if not record or record.user_id != user_id: raise HTTPException(404, "Record not found")
    return record

@router.post("/auth/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)): raise HTTPException(409, "An account already exists for this email")
    user = User(email=str(body.email), full_name=body.full_name, password_hash=hash_password(body.password)); db.add(user); db.commit(); db.refresh(user); seed_workspace(db, user)
    return {"access_token": create_token(user.id)}
@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash): raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(user.id)}
@router.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id)) or UserProfile(user_id=user.id)
    if not profile.id: db.add(profile); db.commit(); db.refresh(profile)
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "is_admin": user.is_admin, "phone": profile.phone, "location_label": profile.location_label, "avatar_path": profile.avatar_path, "emergency_mode": profile.emergency_mode}
@router.put("/me")
def update_me(body: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id)) or UserProfile(user_id=user.id)
    user.full_name = body.full_name; profile.phone = body.phone; profile.location_label = body.location_label; profile.emergency_mode = body.emergency_mode
    db.add(profile); db.commit(); return {"ok": True}
@router.post("/me/avatar")
async def upload_avatar(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}: raise HTTPException(415, "Use a JPEG, PNG, or WebP image")
    content = await file.read()
    if len(content) > 5_000_000: raise HTTPException(413, "Image must be smaller than 5 MB")
    extension = {"image/jpeg":"jpg", "image/png":"png", "image/webp":"webp"}[file.content_type]
    filename = f"{user.id}-{uuid4().hex}.{extension}"; (UPLOAD_DIR / filename).write_bytes(content)
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id)) or UserProfile(user_id=user.id)
    profile.avatar_path = f"/uploads/{filename}"; db.add(profile); db.commit(); return {"avatar_path": profile.avatar_path}
@router.get("/dashboard", response_model=DashboardOut)
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    devices = list(db.scalars(select(Device).where(Device.user_id == user.id)).all()); events = list(db.scalars(select(SecurityEvent).where(SecurityEvent.user_id == user.id).order_by(SecurityEvent.occurred_at.desc()).limit(8)).all())
    if not devices:
        score, label, recommendations = 0, "Add a device to calculate your score", ["Add the device you want to track", "Add a trusted contact for recovery"]
    else:
        unresolved = len(events)
        score = max(0, 100 - unresolved * 12 - sum(d.risk_score for d in devices))
        label = "No unresolved activity" if unresolved == 0 else f"{unresolved} item{'s' if unresolved != 1 else ''} need review"
        recommendations = ["Review each item in Threat detection"] if unresolved else ["No action is currently required"]
    return {"score": score, "score_label": label, "devices": [{"id": d.id, "name": d.name, "platform": d.platform, "status": d.status, "risk_score": d.risk_score, "last_seen": d.last_seen} for d in devices], "events": events, "recommendations": recommendations}
@router.post("/devices")
def add_device(body: DeviceIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    device = Device(user_id=user.id, name=body.name, platform=body.platform); db.add(device); db.commit(); db.refresh(device); return {"id": device.id, "name": device.name}
@router.post("/devices/connect-browser")
async def connect_browser(body: BrowserConnectIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    device = Device(user_id=user.id, name=body.name, platform=body.platform, status="monitoring")
    db.add(device); db.commit(); db.refresh(device)
    db.add(BrowserDeviceState(device_id=device.id, user_id=user.id, user_agent=body.user_agent)); db.commit()
    event = SecurityEvent(user_id=user.id, title="Live browser protection connected", severity="low", description=f"{device.name} is now sending live browser-session status.")
    db.add(event); db.commit(); db.refresh(event)
    await hub.publish(user.id, {"type":"security_alert","id":event.id,"title":event.title,"severity":event.severity,"description":event.description,"occurred_at":event.occurred_at.isoformat()})
    return {"id":device.id,"name":device.name,"status":device.status}
@router.get("/devices")
def list_devices(user: User = Depends(current_user), db: Session = Depends(get_db)): return list(db.scalars(select(Device).where(Device.user_id == user.id)).all())
@router.put("/devices/{device_id}")
def update_device(device_id: int, body: DeviceUpdateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    device = owned_or_404(db, Device, device_id, user.id)
    for key, value in body.model_dump().items(): setattr(device, key, value)
    db.commit(); return {"ok": True}
@router.delete("/devices/{device_id}")
def delete_device(device_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(owned_or_404(db, Device, device_id, user.id)); db.commit(); return {"ok": True}
@router.post("/devices/{device_id}/check-in")
async def device_check_in(device_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    device = owned_or_404(db, Device, device_id, user.id); device.last_seen = datetime.now(timezone.utc); db.commit()
    await hub.publish(user.id, {"type":"device_check_in","device_id":device.id,"name":device.name,"at":device.last_seen.isoformat()})
    return {"ok": True, "last_seen": device.last_seen}
@router.post("/devices/{device_id}/browser-sync")
async def browser_sync(device_id: int, body: BrowserSyncIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    device = owned_or_404(db, Device, device_id, user.id)
    state = db.scalar(select(BrowserDeviceState).where(BrowserDeviceState.device_id == device.id))
    if not state: raise HTTPException(409, "This device is not connected as a browser session")
    changed = state.online != body.online
    state.online = body.online; state.battery_percent = body.battery_percent; state.network_type = body.network_type; state.user_agent = body.user_agent; state.updated_at = datetime.now(timezone.utc)
    device.last_seen = state.updated_at; device.status = "monitoring" if body.online else "offline"; db.commit()
    db.add(BrowserStateMetric(device_id=device.id, user_id=user.id, online=body.online, battery_percent=body.battery_percent, network_type=body.network_type, captured_at=state.updated_at)); db.commit()
    if changed:
        title = "Browser session went online" if body.online else "Browser session went offline"
        event = SecurityEvent(user_id=user.id, title=title, severity="low", description=f"{device.name} changed connection state.")
        db.add(event); db.commit(); db.refresh(event)
        await hub.publish(user.id, {"type":"security_alert","id":event.id,"title":event.title,"severity":event.severity,"description":event.description,"occurred_at":event.occurred_at.isoformat()})
    return {"ok":True,"updated_at":state.updated_at,"online":state.online,"battery_percent":state.battery_percent,"network_type":state.network_type}
@router.get("/devices/{device_id}/live")
def browser_status(device_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned_or_404(db, Device, device_id, user.id)
    state = db.scalar(select(BrowserDeviceState).where(BrowserDeviceState.device_id == device_id))
    if not state: raise HTTPException(404, "No live browser session for this device")
    return {"online":state.online,"battery_percent":state.battery_percent,"network_type":state.network_type,"updated_at":state.updated_at}
@router.get("/dashboard/metrics")
def dashboard_metrics(user: User = Depends(current_user), db: Session = Depends(get_db)):
    metrics = list(db.scalars(select(BrowserStateMetric).where(BrowserStateMetric.user_id == user.id).order_by(BrowserStateMetric.captured_at.desc()).limit(90)).all())
    return [{"captured_at":item.captured_at,"online":1 if item.online else 0,"battery_percent":item.battery_percent,"network_type":item.network_type} for item in reversed(metrics)]
@router.get("/contacts")
def contacts(user: User = Depends(current_user), db: Session = Depends(get_db)): return list(db.scalars(select(TrustedContact).where(TrustedContact.user_id == user.id)).all())
@router.post("/contacts")
def add_contact(body: ContactIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    contact = TrustedContact(user_id=user.id, **body.model_dump()); db.add(contact); db.commit(); db.refresh(contact); return contact
@router.put("/contacts/{contact_id}")
def update_contact(contact_id: int, body: ContactIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    contact = owned_or_404(db, TrustedContact, contact_id, user.id)
    for key, value in body.model_dump().items(): setattr(contact, key, value)
    db.commit(); return contact
@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(owned_or_404(db, TrustedContact, contact_id, user.id)); db.commit(); return {"ok": True}
@router.get("/activity")
def activity(user: User = Depends(current_user), db: Session = Depends(get_db)): return list(db.scalars(select(SecurityEvent).where(SecurityEvent.user_id == user.id).order_by(SecurityEvent.occurred_at.desc())).all())
@router.get("/alerts")
def alerts(user: User = Depends(current_user), db: Session = Depends(get_db)):
    acknowledged = set(db.scalars(select(EventAcknowledgement.event_id).where(EventAcknowledgement.user_id == user.id)).all())
    return [{"id": e.id, "title": e.title, "severity": e.severity, "description": e.description, "occurred_at": e.occurred_at, "acknowledged": e.id in acknowledged} for e in db.scalars(select(SecurityEvent).where(SecurityEvent.user_id == user.id).order_by(SecurityEvent.occurred_at.desc())).all()]
@router.post("/alerts/{event_id}/acknowledge")
def acknowledge(event_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned_or_404(db, SecurityEvent, event_id, user.id)
    exists = db.scalar(select(EventAcknowledgement).where(EventAcknowledgement.user_id == user.id, EventAcknowledgement.event_id == event_id))
    if not exists: db.add(EventAcknowledgement(user_id=user.id, event_id=event_id)); db.commit()
    return {"ok": True}
@router.post("/alerts/test")
async def create_test_alert(user: User = Depends(current_user), db: Session = Depends(get_db)):
    event = SecurityEvent(user_id=user.id, title="Security check requested", severity="medium", description="A live security check was requested from your SentinelAI workspace.")
    db.add(event); db.commit(); db.refresh(event)
    payload = {"type":"security_alert","id":event.id,"title":event.title,"severity":event.severity,"description":event.description,"occurred_at":event.occurred_at.isoformat()}
    await hub.publish(user.id, payload)
    return payload
@router.get("/preferences/notifications")
def get_preferences(user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(NotificationPreference).where(NotificationPreference.user_id == user.id)) or NotificationPreference(user_id=user.id)
    if not item.id: db.add(item); db.commit(); db.refresh(item)
    return {"push_enabled":item.push_enabled,"email_enabled":item.email_enabled,"sms_enabled":item.sms_enabled,"weekly_summary":item.weekly_summary}
@router.put("/preferences/notifications")
def update_preferences(body: NotificationIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(NotificationPreference).where(NotificationPreference.user_id == user.id)) or NotificationPreference(user_id=user.id)
    for key, value in body.model_dump().items(): setattr(item, key, value)
    db.add(item); db.commit(); return {"ok": True}
@router.get("/geofences")
def geofences(user: User = Depends(current_user), db: Session = Depends(get_db)): return list(db.scalars(select(Geofence).where(Geofence.user_id == user.id)).all())
@router.post("/geofences")
def add_geofence(body: GeofenceIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = Geofence(user_id=user.id, name=body.name, latitude=str(body.latitude), longitude=str(body.longitude), radius_meters=body.radius_meters, enabled=body.enabled); db.add(item); db.commit(); db.refresh(item); return item
@router.delete("/geofences/{geofence_id}")
def delete_geofence(geofence_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(owned_or_404(db, Geofence, geofence_id, user.id)); db.commit(); return {"ok": True}
@router.post("/location/check")
async def check_location(body: LocationUpdateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    zones = list(db.scalars(select(Geofence).where(Geofence.user_id == user.id, Geofence.enabled == True)).all())
    outside: list[str] = []
    for zone in zones:
        lat1, lon1, lat2, lon2 = map(radians, [body.latitude, body.longitude, float(zone.latitude), float(zone.longitude)])
        distance = 2 * 6_371_000 * asin(sqrt(sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2))
        if distance > zone.radius_meters: outside.append(zone.name)
    location = db.scalar(select(LiveLocationState).where(LiveLocationState.user_id == user.id)) or LiveLocationState(user_id=user.id, latitude="", longitude="")
    location.latitude = str(body.latitude); location.longitude = str(body.longitude); location.accuracy_meters = body.accuracy_meters; location.outside_zones = ",".join(outside); location.updated_at = datetime.now(timezone.utc)
    db.add(location); db.commit()
    if outside:
        event = SecurityEvent(user_id=user.id, title="Location boundary exited", severity="medium", description=f"Current location is outside: {', '.join(outside)}.")
        db.add(event); db.commit(); db.refresh(event)
        await hub.publish(user.id, {"type":"security_alert","id":event.id,"title":event.title,"severity":event.severity,"description":event.description,"occurred_at":event.occurred_at.isoformat()})
    return {"zones_checked":len(zones),"outside_zones":outside}
@router.get("/security/live-context")
def live_security_context(user: User = Depends(current_user), db: Session = Depends(get_db)):
    contacts = list(db.scalars(select(TrustedContact).where(TrustedContact.user_id == user.id)).all())
    browser = db.scalar(select(BrowserDeviceState).where(BrowserDeviceState.user_id == user.id).order_by(BrowserDeviceState.updated_at.desc()))
    location = db.scalar(select(LiveLocationState).where(LiveLocationState.user_id == user.id))
    now_time = datetime.now(timezone.utc)
    location_fresh = bool(location and (now_time - location.updated_at.replace(tzinfo=timezone.utc) if location.updated_at.tzinfo is None else now_time - location.updated_at).total_seconds() < 90)
    outside = location.outside_zones.split(",") if location and location.outside_zones else []
    points = 0
    if browser and browser.online: points += 25
    if location_fresh: points += 25
    if location_fresh and not outside: points += 25
    if contacts: points += 25
    status = "Ready" if points >= 75 else "Partial context" if points >= 40 else "Needs setup"
    return {"readiness_score":points,"status":status,"browser_online":bool(browser and browser.online),"location_active":location_fresh,"location_accuracy_meters":location.accuracy_meters if location_fresh and location else None,"outside_zones":outside,"contacts":[{"id":c.id,"name":c.name,"phone":c.phone,"relationship":c.relationship} for c in contacts],"explanation":"Readiness is based on live browser presence, a location update less than 90 seconds old, whether that update is inside enabled boundaries, and at least one trusted contact. It is not a threat probability."}
@router.post("/security/safety-check")
async def create_safety_check(user: User = Depends(current_user), db: Session = Depends(get_db)):
    contacts = list(db.scalars(select(TrustedContact).where(TrustedContact.user_id == user.id)).all())
    location = db.scalar(select(LiveLocationState).where(LiveLocationState.user_id == user.id))
    location_text = "No live location is active." if not location else (f"Outside boundaries: {location.outside_zones}." if location.outside_zones else "Current live location is inside enabled boundaries.")
    event = SecurityEvent(user_id=user.id, title="Safety check initiated", severity="low", description=f"Safety check recorded with {len(contacts)} trusted contact(s) available. {location_text}")
    db.add(event); db.commit(); db.refresh(event)
    await hub.publish(user.id, {"type":"security_alert","id":event.id,"title":event.title,"severity":event.severity,"description":event.description,"occurred_at":event.occurred_at.isoformat()})
    return {"event_id":event.id,"contacts_ready":len(contacts),"location_summary":location_text}
@router.post("/ai/ask")
async def ask_ai(body: AskIn, background_tasks: BackgroundTasks, user: User = Depends(current_user), db: Session = Depends(get_db)):
    devices = list(db.scalars(select(Device).where(Device.user_id == user.id)).all()); score = max(0, 100 - round(sum(d.risk_score for d in devices) / max(1, len(devices))))
    response = await AIService().ask(body.message, score)
    background_tasks.add_task(lambda: None)
    return {"answer": response, "score": score}
@router.post("/ai/live-briefing")
async def live_briefing(user: User = Depends(current_user), db: Session = Depends(get_db)):
    devices = list(db.scalars(select(Device).where(Device.user_id == user.id)).all())
    events = list(db.scalars(select(SecurityEvent).where(SecurityEvent.user_id == user.id).order_by(SecurityEvent.occurred_at.desc()).limit(5)).all())
    states = list(db.scalars(select(BrowserDeviceState).where(BrowserDeviceState.user_id == user.id).order_by(BrowserDeviceState.updated_at.desc()).limit(1)).all())
    score = 0 if not devices else max(0, 100 - len(events) * 12 - sum(device.risk_score for device in devices))
    browser_context = "No connected browser session." if not states else f"Browser is {'online' if states[0].online else 'offline'}, battery {states[0].battery_percent if states[0].battery_percent is not None else 'unavailable'}%, network {states[0].network_type}."
    event_context = "; ".join(f"{event.severity}: {event.title}" for event in events) or "No recorded security events."
    question = f"Give a concise live security briefing using only this account data. Devices: {len(devices)}. {browser_context} Recent events: {event_context}. State what is known, what is unknown, and the single best next action."
    return {"answer": await AIService().ask(question, score), "score": score, "generated_at": datetime.now(timezone.utc)}
@router.websocket("/ws")
async def websocket_feed(ws: WebSocket, token: str = Query(...)):
    try: user_id = int(jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])["sub"])
    except Exception:
        await ws.close(code=1008); return
    await hub.connect(ws, user_id)
    try:
        while True:
            await asyncio.sleep(20)
            await ws.send_json({"type": "heartbeat", "at": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect: hub.disconnect(ws)
