"""System health & settings API router."""
import time
import random
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import SystemSetting

router = APIRouter()


class SettingsUpdate(BaseModel):
    mode: Optional[str] = None
    risk_threshold: Optional[int] = None
    critical_threshold: Optional[int] = None
    cooldown_seconds: Optional[int] = None
    alerts_in_app: Optional[bool] = None
    alerts_slack: Optional[bool] = None
    alerts_email: Optional[bool] = None
    alerts_sms: Optional[bool] = None
    sla_target_seconds: Optional[int] = None


def get_setting(db: Session, key: str, default: str = "") -> str:
    s = db.get(SystemSetting, key)
    return s.value if s else default


def set_setting(db: Session, key: str, value: str):
    s = db.get(SystemSetting, key)
    if s:
        s.value = value
    else:
        db.add(SystemSetting(key=key, value=value))
    db.commit()


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    return {
        "mode": get_setting(db, "mode", "DEMO"),
        "risk_threshold": int(get_setting(db, "risk_threshold", "60")),
        "critical_threshold": int(get_setting(db, "critical_threshold", "80")),
        "cooldown_seconds": int(get_setting(db, "cooldown_seconds", "300")),
        "alerts_in_app": get_setting(db, "alerts_in_app", "true") == "true",
        "alerts_slack": get_setting(db, "alerts_slack", "false") == "true",
        "alerts_email": get_setting(db, "alerts_email", "false") == "true",
        "alerts_sms": get_setting(db, "alerts_sms", "false") == "true",
        "sla_target_seconds": int(get_setting(db, "sla_target_seconds", "120")),
    }


@router.put("/settings")
def update_settings(body: SettingsUpdate, db: Session = Depends(get_db)):
    if body.mode is not None:
        set_setting(db, "mode", body.mode)
    if body.risk_threshold is not None:
        set_setting(db, "risk_threshold", str(body.risk_threshold))
    if body.critical_threshold is not None:
        set_setting(db, "critical_threshold", str(body.critical_threshold))
    if body.cooldown_seconds is not None:
        set_setting(db, "cooldown_seconds", str(body.cooldown_seconds))
    if body.alerts_in_app is not None:
        set_setting(db, "alerts_in_app", "true" if body.alerts_in_app else "false")
    if body.alerts_slack is not None:
        set_setting(db, "alerts_slack", "true" if body.alerts_slack else "false")
    if body.alerts_email is not None:
        set_setting(db, "alerts_email", "true" if body.alerts_email else "false")
    if body.alerts_sms is not None:
        set_setting(db, "alerts_sms", "true" if body.alerts_sms else "false")
    if body.sla_target_seconds is not None:
        set_setting(db, "sla_target_seconds", str(body.sla_target_seconds))

    return get_settings(db)


@router.get("/health")
def get_health():
    return {
        "ingestion": True,
        "queue": True,
        "ai_agent": True,
        "risk_engine": True,
        "alert_engine": True,
        "database": True,
        "websocket": True,
        "events_per_sec": round(random.uniform(0.2, 0.4), 2),
        "queue_depth": random.randint(0, 3),
        "ai_processing_ms": random.randint(350, 900),
        "uptime_seconds": int(time.time() % 86400),
    }


@router.get("/agents")
def get_agents():
    return [
        {"name": "Triage Agent", "active": True, "processed_today": random.randint(40, 120), "avg_processing_ms": random.randint(400, 800), "errors": 0},
        {"name": "Insight Agent", "active": True, "processed_today": random.randint(5, 20), "avg_processing_ms": random.randint(700, 1200), "errors": 0},
        {"name": "Risk Agent", "active": True, "processed_today": random.randint(40, 120), "avg_processing_ms": random.randint(20, 60), "errors": 0},
        {"name": "Response Agent", "active": True, "processed_today": random.randint(5, 20), "avg_processing_ms": random.randint(150, 350), "errors": 0},
    ]
