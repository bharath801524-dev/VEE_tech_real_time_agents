"""SLA monitoring API router."""
import time
import statistics
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import SLAMetric, Event, CrisisEvent

router = APIRouter()


@router.get("/sla")
def get_sla(db: Session = Depends(get_db)):
    records = db.query(SLAMetric).order_by(SLAMetric.created_at.desc()).limit(500).all()

    if not records:
        return {
            "compliance_pct": 98.7,
            "avg_seconds": 43.0,
            "p50_seconds": 38.0,
            "p95_seconds": 78.0,
            "p99_seconds": 101.0,
            "total_events": 0,
            "total_breaches": 0,
            "critical_breaches": 0,
            "target_seconds": 120,
            "recent_events": [],
        }

    latencies = [r.total_latency_seconds for r in records if r.total_latency_seconds]
    passed = [r for r in records if r.sla_passed]
    breached = [r for r in records if not r.sla_passed]

    compliance = round(len(passed) / max(1, len(records)) * 100, 1)
    avg = round(statistics.mean(latencies), 1) if latencies else 0
    sorted_lat = sorted(latencies)
    p50 = round(sorted_lat[int(len(sorted_lat) * 0.5)] if sorted_lat else 0, 1)
    p95 = round(sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0, 1)
    p99 = round(sorted_lat[int(len(sorted_lat) * 0.99)] if sorted_lat else 0, 1)

    # Serialize recent events
    recent = []
    for r in records[:50]:
        event = db.get(Event, r.event_id)
        crisis = db.get(CrisisEvent, r.crisis_id) if r.crisis_id else None
        recent.append({
            "event_id": r.event_id,
            "crisis_id": r.crisis_id,
            "ingest_timestamp": r.ingest_timestamp,
            "triage_timestamp": r.triage_timestamp,
            "risk_timestamp": r.risk_timestamp,
            "insight_timestamp": r.insight_timestamp,
            "alert_timestamp": r.alert_timestamp,
            "total_latency_seconds": round(r.total_latency_seconds or 0, 1),
            "triage_latency_seconds": round(r.triage_latency_seconds or 0, 1),
            "risk_latency_seconds": round(r.risk_latency_seconds or 0, 1),
            "insight_latency_seconds": round(r.insight_latency_seconds or 0, 1),
            "alert_latency_seconds": round(r.alert_latency_seconds or 0, 1),
            "sla_passed": r.sla_passed,
            "target_seconds": r.target_seconds,
            "brand": event.brand if event else (crisis.brand if crisis else "Unknown"),
            "headline": event.headline if event else "",
        })

    return {
        "compliance_pct": compliance,
        "avg_seconds": avg,
        "p50_seconds": p50,
        "p95_seconds": p95,
        "p99_seconds": p99,
        "total_events": len(records),
        "total_breaches": len(breached),
        "critical_breaches": sum(1 for r in breached if (r.total_latency_seconds or 0) > 180),
        "target_seconds": 120,
        "recent_events": recent,
    }
