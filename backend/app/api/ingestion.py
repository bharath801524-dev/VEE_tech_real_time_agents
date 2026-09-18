"""
MindMesh Ingestion & Source Health API Router
Provides endpoints to monitor Google News RSS status, trigger manual refresh, and switch modes.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models import SystemSetting

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

# Global reference set by lifespan in main.py
rss_ingester_instance = None
stream_adapter_instance = None
mode_switcher_callback = None
social_ingester_instance = None  # Reddit + HackerNews


def set_ingester_instances(rss_ingester, stream_adapter, mode_switcher, social_ingester=None):
    global rss_ingester_instance, stream_adapter_instance, mode_switcher_callback, social_ingester_instance
    rss_ingester_instance = rss_ingester
    stream_adapter_instance = stream_adapter
    mode_switcher_callback = mode_switcher
    social_ingester_instance = social_ingester


class ModeToggleRequest(BaseModel):
    mode: str  # "LIVE" or "DEMO"


@router.get("/status")
def get_source_status(db: Session = Depends(get_db)):
    """Return real-time Google News RSS health, article count, and last fetch timestamp."""
    setting = db.get(SystemSetting, "mode")
    current_mode = setting.value if setting else "LIVE"

    if rss_ingester_instance:
        status_data = rss_ingester_instance.get_status_dict()
    else:
        status_data = {
            "source_name": "Google News RSS",
            "status": "IDLE",
            "is_running": False,
            "last_successful_fetch": None,
            "last_fetch_attempt": None,
            "articles_fetched_total": 0,
            "articles_ingested_total": 0,
            "last_article_published": None,
            "last_error": None,
            "poll_interval_seconds": 45,
            "monitored_queries": [],
        }

    status_data["current_mode"] = current_mode
    # Include social ingester summary
    if social_ingester_instance:
        social_status = social_ingester_instance.get_status()
        status_data["reddit"] = social_status.get("reddit", {})
        status_data["hackernews"] = social_status.get("hackernews", {})
    return status_data


@router.get("/social-status")
def get_social_status():
    """Return Reddit and HackerNews ingester health and stats."""
    if not social_ingester_instance:
        return {"reddit": {"is_running": False}, "hackernews": {"is_running": False}}
    return social_ingester_instance.get_status()


@router.post("/refresh")
async def trigger_refresh(db: Session = Depends(get_db)):
    """Trigger an immediate, on-demand Google News RSS fetch cycle."""
    if not rss_ingester_instance:
        raise HTTPException(status_code=503, detail="RSS Ingester is not initialized")
    
    try:
        if hasattr(rss_ingester_instance, "reset_seen_cache"):
            rss_ingester_instance.reset_seen_cache()
        result = await rss_ingester_instance.poll_once()
        return {
            "ok": True,
            "message": f"Fetched {result.get('articles_fetched', 0)} articles, {result.get('articles_new_ingested', 0)} new.",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@router.post("/mode")
async def toggle_mode(body: ModeToggleRequest, db: Session = Depends(get_db)):
    """Switch active operational mode between LIVE and DEMO."""
    target_mode = body.mode.upper()
    if target_mode not in ("LIVE", "DEMO"):
        raise HTTPException(status_code=400, detail="Mode must be LIVE or DEMO")

    # Update system setting
    s = db.get(SystemSetting, "mode")
    if s:
        s.value = target_mode
    else:
        db.add(SystemSetting(key="mode", value=target_mode))
    db.commit()

    if mode_switcher_callback:
        await mode_switcher_callback(target_mode)

    return {"ok": True, "mode": target_mode}
