"""Crises API router."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import CrisisEvent, CrisisInsight, AIAnalysis, RiskScore, SLAMetric, Event

router = APIRouter()


def serialize_crisis(c: CrisisEvent, db: Session) -> dict:
    insight = db.query(CrisisInsight).filter(CrisisInsight.event_id == c.event_id).first()
    analysis = db.query(AIAnalysis).filter(AIAnalysis.event_id == c.event_id).first()
    risk = db.query(RiskScore).filter(RiskScore.event_id == c.event_id).first()
    sla = db.query(SLAMetric).filter(SLAMetric.event_id == c.event_id).first()
    event = db.get(Event, c.event_id)

    result = {
        "id": c.id,
        "event_id": c.event_id,
        "brand": c.brand,
        "headline": c.headline,
        "topic": c.topic,
        "risk_score": c.risk_score,
        "risk_level": c.risk_level,
        "mentions": c.mentions,
        "velocity_ratio": c.velocity_ratio,
        "sentiment": c.sentiment,
        "status": c.status,
        "detected_at": c.detected_at,
    }

    if sla:
        result["sla_passed"] = sla.sla_passed
        result["sla_seconds"] = sla.total_latency_seconds
        result["sla_stages"] = [
            {"label": "Ingest", "timestamp": sla.ingest_timestamp, "latency_seconds": 0, "icon": "📥"},
            {"label": "AI Triage", "timestamp": sla.triage_timestamp, "latency_seconds": round(sla.triage_latency_seconds, 1), "icon": "🤖"},
            {"label": "Risk Score", "timestamp": sla.risk_timestamp, "latency_seconds": round(sla.risk_latency_seconds, 1), "icon": "⚡"},
            {"label": "Insight", "timestamp": sla.insight_timestamp, "latency_seconds": round(sla.insight_latency_seconds, 1), "icon": "💡"},
            {"label": "Alert", "timestamp": sla.alert_timestamp, "latency_seconds": round(sla.alert_latency_seconds, 1), "icon": "🚨"},
        ]

    if analysis:
        result["confidence"] = analysis.confidence
        result["urgency"] = analysis.urgency
        result["client_tier"] = analysis.client_tier
        result["competitor_impact"] = analysis.competitor_impact

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

    if event:
        result["source"] = event.source
        result["url"] = event.url
        result["location"] = event.location
        result["content"] = event.content

    return result


@router.get("/crises")
def get_crises(db: Session = Depends(get_db)):
    crises = db.query(CrisisEvent).order_by(CrisisEvent.detected_at.desc()).limit(100).all()
    return [serialize_crisis(c, db) for c in crises]


@router.get("/crises/{crisis_id}")
def get_crisis(crisis_id: str, db: Session = Depends(get_db)):
    c = db.get(CrisisEvent, crisis_id)
    if not c:
        raise HTTPException(404, "Crisis not found")
    return serialize_crisis(c, db)
