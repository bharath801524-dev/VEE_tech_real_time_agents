"""Events API router."""
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import Event, AIAnalysis, RiskScore, CrisisInsight, SLAMetric, ProcessedEvent

router = APIRouter()


def serialize_event(e: Event, db: Session) -> dict:
    analysis = db.query(AIAnalysis).filter(AIAnalysis.event_id == e.id).first()
    risk = db.query(RiskScore).filter(RiskScore.event_id == e.id).first()
    insight = db.query(CrisisInsight).filter(CrisisInsight.event_id == e.id).first()
    sla = db.query(SLAMetric).filter(SLAMetric.event_id == e.id).first()
    proc = db.query(ProcessedEvent).filter(ProcessedEvent.event_id == e.id).first()

    result = {
        "id": e.id,
        "source": e.source,
        "source_origin": (
            getattr(e, "source_origin", None)
            or ("LIVE • Google News RSS" if e.source == "news" else e.source)
        ),
        "publisher": getattr(e, "publisher", None),
        "timestamp": e.timestamp,
        "brand": e.brand,
        "headline": e.headline,
        "content": e.content,
        "url": e.url,
        "location": e.location,
        "mention_count": proc.mention_count if proc else 1,
        "velocity_ratio": proc.velocity_ratio if proc else 1.0,
        "velocity_status": proc.velocity_status if proc else "NORMAL",
    }
    if analysis:
        result.update({
            "sentiment": analysis.sentiment,
            "risk_level": analysis.risk_level,
            "risk_score": analysis.risk_score,
            "topic": analysis.topic,
            "confidence": analysis.confidence,
            "urgency": analysis.urgency,
            "client_tier": analysis.client_tier,
            "competitor_impact": analysis.competitor_impact,
            "ai_provider": getattr(analysis, "ai_provider", "DemoAIProvider"),
        })
    if risk:
        result["risk_breakdown"] = json.loads(risk.breakdown_json or "[]")
    if insight:
        result["insight"] = {
            "what_happened": insight.what_happened,
            "why_it_matters": insight.why_it_matters,
            "recommended_action": insight.recommended_action,
            "priority": insight.priority,
            "recommended_team": insight.recommended_team,
            "action_checklist": json.loads(insight.action_checklist_json or "[]"),
            "competitor_reaction": insight.competitor_reaction,
        }
    if sla:
        result["sla_seconds"] = sla.total_latency_seconds
        result["sla_passed"] = sla.sla_passed
    return result


@router.get("/events")
def get_events(
    limit: int = Query(50, le=200),
    brand: Optional[str] = None,
    source: Optional[str] = None,
    risk: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Event).order_by(Event.created_at.desc())
    if brand:
        q = q.filter(Event.brand.ilike(brand))
    if source:
        q = q.filter(Event.source == source)
    events = q.limit(limit).all()

    result = [serialize_event(e, db) for e in events]

    if risk:
        result = [r for r in result if r.get("risk_level") == risk.upper()]

    return result


@router.get("/events/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    e = db.get(Event, event_id)
    if not e:
        from fastapi import HTTPException
        raise HTTPException(404, "Event not found")
    return serialize_event(e, db)
