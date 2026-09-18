"""
MindMesh Core Processing Pipeline — orchestrates the full event lifecycle:
Ingest → Filter → Dedup → Velocity → Triage → Risk → Insight → Alert → SLA
"""
import asyncio
import json
import time
import uuid
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session

from app.agents.ai_provider import get_ai_provider
from app.processing.risk_engine import calculate_risk
from app.processing.dedup_velocity import DeduplicationEngine, VelocityDetector
from app.alerts.alert_engine import AlertEngine
from app.database.models import (
    Client, Event, ProcessedEvent, AIAnalysis, RiskScore, CrisisInsight, CrisisEvent, Alert, SLAMetric
)
from app.config import settings

# ─── Monitored Brands & Keywords ─────────────────────────────────────────────
DEFAULT_MONITORED_BRANDS = {
    "PayU", "PhonePe", "Razorpay", "Flipkart", "Amazon",
    "Infosys", "TCS", "HDFC", "ICICI", "SBI",
}


def is_relevant(event: Dict[str, Any], monitored_brands: set, brand_keywords: Optional[Dict[str, List[str]]] = None) -> bool:
    """Pre-filter: check if event brand or content matches any monitored client or keywords.
    Social events (Reddit/HN) are always let through if they passed keyword filtering.
    """
    source_type = event.get("source_type", "")
    # Social ingester already applies keyword filtering — trust it
    if source_type in ("social", "tech_social"):
        return True

    brand = (event.get("brand") or "").strip()
    brand_lower = brand.lower()

    # 1. Direct case-insensitive brand match
    for b in monitored_brands:
        if brand_lower == b.lower():
            return True

    # 2. Check headline & content
    headline = str(event.get("headline") or "")
    content_raw = str(event.get("content") or "")
    content = f"{headline} {content_raw}".lower()

    for b in monitored_brands:
        if b.lower() in content:
            return True

    # 3. Check client keywords (e.g. ChatGPT, Sora, UPI, etc.)
    if brand_keywords:
        for b_name, kws in brand_keywords.items():
            for kw in kws:
                if kw and kw in content:
                    return True

    return False


class EventPipeline:
    """Full processing pipeline for a single event."""

    def __init__(self, db_session_factory, ws_broadcast_fn=None):
        self._db_factory = db_session_factory
        self._ai = get_ai_provider()
        self._dedup = DeduplicationEngine()
        self._velocity = VelocityDetector()
        self._alert_engine = AlertEngine(ws_broadcast_fn)
        self._ws_broadcast = ws_broadcast_fn
        self._monitored_brands = set(DEFAULT_MONITORED_BRANDS)
        self._brand_keywords: Dict[str, List[str]] = {}
        self._last_brands_refresh = 0.0
        self.refresh_monitored_brands()
        self._stats = {
            "processed": 0,
            "duplicates": 0,
            "crises": 0,
            "alerts_sent": 0,
        }
        # In-memory SLA accumulator for aggregates
        self._sla_records: List[float] = []

    def refresh_monitored_brands(self):
        """Dynamically fetch all active clients and their keywords from database."""
        db: Session = self._db_factory()
        try:
            clients = db.query(Client).filter(Client.is_active == True).all()
            brands = set(DEFAULT_MONITORED_BRANDS)
            keywords_map: Dict[str, List[str]] = {}
            for c in clients:
                brands.add(c.name)
                try:
                    kws = json.loads(c.keywords or "[]")
                    keywords_map[c.name] = [str(k).lower().strip() for k in kws if k]
                except Exception:
                    keywords_map[c.name] = []
            self._monitored_brands = brands
            self._brand_keywords = keywords_map
            self._last_brands_refresh = time.time()
        except Exception as err:
            pass
        finally:
            db.close()

    def update_brands(self, brands: set):
        self._monitored_brands = brands

    async def process(self, raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single raw event through the full pipeline. Returns enriched event dict."""
        t_ingest = time.time()

        # Refresh monitored brands from DB periodically (every 30 seconds)
        if time.time() - self._last_brands_refresh > 30:
            self.refresh_monitored_brands()

        # ── 1. Pre-filter ─────────────────────────────────────────────────
        if not is_relevant(raw_event, self._monitored_brands, self._brand_keywords):
            return None

        # Canonicalize brand casing matching monitored client
        raw_brand = (raw_event.get("brand") or "").strip()
        for mb in self._monitored_brands:
            if raw_brand.lower() == mb.lower():
                raw_event["brand"] = mb
                break

        # ── 2. Deduplication ──────────────────────────────────────────────
        is_dup, norm_hash, mention_count = self._dedup.check(raw_event)
        if is_dup:
            self._stats["duplicates"] += 1
            # Broadcast dedup update to live feed
            if self._ws_broadcast:
                await self._ws_broadcast({
                    "type": "NEW_EVENT",
                    "data": {**raw_event, "mention_count": mention_count, "is_duplicate": True},
                    "timestamp": time.time(),
                })
            return None

        # ── 3. Velocity detection ─────────────────────────────────────────
        velocity_ratio, velocity_status = self._velocity.record(raw_event.get("brand", ""))
        raw_event["velocity_ratio"] = velocity_ratio
        raw_event["velocity_status"] = velocity_status
        raw_event["mention_count"] = mention_count

        # ── 4. Persist event ──────────────────────────────────────────────
        db: Session = self._db_factory()
        try:
            event_id = raw_event.get("id", str(uuid.uuid4()))
            # Upsert event
            existing = db.get(Event, event_id)
            if not existing:
                db_event = Event(
                    id=event_id,
                    source=raw_event.get("source", "news"),
                    source_origin=raw_event.get(
                    "source_origin",
                    "LIVE • Google News RSS" if raw_event.get("source") == "news"
                    else f"LIVE • {raw_event.get('source', 'Unknown').title()}"
                ),
                    publisher=raw_event.get("publisher"),
                    external_id=raw_event.get("external_id"),
                    timestamp=raw_event.get("timestamp", t_ingest),
                    brand=raw_event.get("brand", "Unknown"),
                    headline=raw_event.get("headline", ""),
                    content=raw_event.get("content", ""),
                    url=raw_event.get("url"),
                    language=raw_event.get("language", "en"),
                    location=raw_event.get("location", "Global"),
                    created_at=t_ingest,
                )
                db.add(db_event)
                db.commit()

            db_proc = ProcessedEvent(
                event_id=event_id,
                normalized_hash=norm_hash,
                mention_count=mention_count,
                velocity_ratio=velocity_ratio,
                velocity_status=velocity_status,
                is_duplicate=False,
                created_at=t_ingest,
            )
            db.add(db_proc)
            db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()

        # ── 5. Broadcast ingestion to live feed ───────────────────────────
        if self._ws_broadcast:
            await self._ws_broadcast({
                "type": "NEW_EVENT",
                "data": {**raw_event, "is_duplicate": False},
                "timestamp": time.time(),
            })

        # ── 6. AI Triage ──────────────────────────────────────────────────
        t_triage = time.time()
        triage = await self._ai.triage(raw_event)
        triage["ai_provider"] = type(self._ai).__name__  # GeminiProvider or DemoAIProvider
        t_triage_done = time.time()

        # Persist triage
        db = self._db_factory()
        try:
            db_analysis = AIAnalysis(
                event_id=event_id,
                client=triage["client"],
                client_tier=triage["client_tier"],
                topic=triage["topic"],
                sentiment=triage["sentiment"],
                sentiment_score=triage["sentiment_score"],
                risk_level=triage["risk_level"],
                risk_score=triage["risk_score"],
                competitor_impact=triage["competitor_impact"],
                urgency=triage["urgency"],
                confidence=triage["confidence"],
            )
            db.add(db_analysis)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        # Broadcast triage update
        if self._ws_broadcast:
            await self._ws_broadcast({
                "type": "TRIAGE_UPDATE",
                "data": {"event_id": event_id, **triage},
                "timestamp": time.time(),
            })

        # ── 7. Risk scoring ───────────────────────────────────────────────
        t_risk = time.time()
        risk_score, risk_level, risk_breakdown = calculate_risk(
            topic=triage["topic"],
            sentiment=triage["sentiment"],
            velocity_ratio=velocity_ratio,
            client_tier=triage["client_tier"],
            source=raw_event.get("source", "news"),
            competitor_impact=triage["competitor_impact"],
            confidence=triage["confidence"],
        )
        triage["risk_score"] = risk_score
        triage["risk_level"] = risk_level
        t_risk_done = time.time()

        # Persist risk score
        db = self._db_factory()
        try:
            db_risk = RiskScore(
                event_id=event_id,
                total_score=risk_score,
                risk_level=risk_level,
                breakdown_json=json.dumps(risk_breakdown),
            )
            db.add(db_risk)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        if self._ws_broadcast:
            await self._ws_broadcast({
                "type": "RISK_UPDATE",
                "data": {"event_id": event_id, "risk_score": risk_score, "risk_level": risk_level, "breakdown": risk_breakdown},
                "timestamp": time.time(),
            })

        # ── 8. Insight generation (for HIGH or CRITICAL) ──────────────────
        insight = {}
        t_insight = t_risk_done
        if risk_level in ("HIGH", "CRITICAL"):
            insight_raw = await self._ai.generate_insight(raw_event, triage)
            response_rec = await self._ai.recommend_response(raw_event, triage, risk_score)
            insight = {**insight_raw, **response_rec}
            t_insight = time.time()

            # Persist insight
            db = self._db_factory()
            try:
                db_insight = CrisisInsight(
                    event_id=event_id,
                    what_happened=insight.get("what_happened", ""),
                    why_it_matters=insight.get("why_it_matters", ""),
                    recommended_action=insight.get("recommended_action", ""),
                    priority=insight.get("priority", ""),
                    recommended_team=insight.get("recommended_team", ""),
                    action_checklist_json=json.dumps(insight.get("actions", [])),
                    competitor_reaction=insight.get("competitor_reaction"),
                )
                db.add(db_insight)

                # Create crisis event record
                crisis_id = str(uuid.uuid4())
                db_crisis = CrisisEvent(
                    id=crisis_id,
                    event_id=event_id,
                    brand=triage["client"],
                    headline=raw_event.get("headline", ""),
                    topic=triage["topic"],
                    risk_score=risk_score,
                    risk_level=risk_level,
                    mentions=mention_count,
                    velocity_ratio=velocity_ratio,
                    sentiment=triage["sentiment"],
                    status="ACTIVE",
                    detected_at=t_ingest,
                )
                db.add(db_crisis)
                db.commit()
                raw_event["crisis_id"] = crisis_id
            except Exception:
                db.rollback()
                crisis_id = str(uuid.uuid4())
            finally:
                db.close()

            # Broadcast crisis detection
            if self._ws_broadcast:
                await self._ws_broadcast({
                    "type": "CRISIS_DETECTED",
                    "data": {
                        "event_id": event_id,
                        "crisis_id": raw_event.get("crisis_id"),
                        "brand": triage["client"],
                        "headline": raw_event.get("headline", ""),
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "topic": triage["topic"],
                        "insight": insight,
                        "breakdown": risk_breakdown,
                    },
                    "timestamp": time.time(),
                })

            self._stats["crises"] += 1

        # ── 9. Alert engine ───────────────────────────────────────────────
        raw_event["insight"] = insight
        alert = await self._alert_engine.process(raw_event, triage, risk_score, raw_event.get("crisis_id"))
        t_alert = time.time()

        if alert:
            # Persist alert
            db = self._db_factory()
            try:
                db_alert = Alert(
                    id=alert["id"],
                    crisis_id=raw_event.get("crisis_id"),
                    event_id=event_id,
                    channel=alert["channel"],
                    alert_level=alert["alert_level"],
                    payload_json=json.dumps(alert),
                    sent_at=alert["sent_at"],
                    status=alert["status"],
                )
                db.add(db_alert)
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()
            self._stats["alerts_sent"] += 1

        # ── 10. SLA recording ─────────────────────────────────────────────
        total_latency = t_alert - t_ingest
        sla_passed = total_latency <= settings.SLA_TARGET_SECONDS
        self._sla_records.append(total_latency)

        db = self._db_factory()
        try:
            db_sla = SLAMetric(
                event_id=event_id,
                crisis_id=raw_event.get("crisis_id"),
                ingest_timestamp=t_ingest,
                triage_timestamp=t_triage_done,
                risk_timestamp=t_risk_done,
                insight_timestamp=t_insight,
                alert_timestamp=t_alert,
                total_latency_seconds=total_latency,
                triage_latency_seconds=t_triage_done - t_ingest,
                risk_latency_seconds=t_risk_done - t_triage_done,
                insight_latency_seconds=t_insight - t_risk_done,
                alert_latency_seconds=t_alert - t_insight,
                sla_passed=sla_passed,
                target_seconds=settings.SLA_TARGET_SECONDS,
            )
            db.add(db_sla)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        if self._ws_broadcast:
            await self._ws_broadcast({
                "type": "SLA_UPDATE",
                "data": {
                    "event_id": event_id,
                    "total_latency": total_latency,
                    "sla_passed": sla_passed,
                    "stages": {
                        "ingest": 0,
                        "triage": round(t_triage_done - t_ingest, 2),
                        "risk": round(t_risk_done - t_ingest, 2),
                        "insight": round(t_insight - t_ingest, 2),
                        "alert": round(t_alert - t_ingest, 2),
                    },
                },
                "timestamp": time.time(),
            })

        self._stats["processed"] += 1
        return {
            **raw_event,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "sla_seconds": total_latency,
            "triage": triage,
            "insight": insight,
            "risk_breakdown": risk_breakdown,
            "sla_passed": sla_passed,
            "total_latency": total_latency,
        }

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)
