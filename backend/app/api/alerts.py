"""Alerts API router."""
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import Alert, CrisisEvent, Event

router = APIRouter()


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.sent_at.desc()).limit(100).all()
    result = []
    for a in alerts:
        event = db.get(Event, a.event_id)
        crisis = db.get(CrisisEvent, a.crisis_id) if a.crisis_id else None
        payload = json.loads(a.payload_json or "{}")
        result.append({
            "id": a.id,
            "crisis_id": a.crisis_id,
            "event_id": a.event_id,
            "channel": a.channel,
            "alert_level": a.alert_level,
            "sent_at": a.sent_at,
            "status": a.status,
            "brand": crisis.brand if crisis else (event.brand if event else "Unknown"),
            "headline": crisis.headline if crisis else (event.headline if event else ""),
            "risk_score": crisis.risk_score if crisis else payload.get("risk_score"),
        })
    return result
