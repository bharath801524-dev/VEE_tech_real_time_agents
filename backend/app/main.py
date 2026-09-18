"""
MindMesh FastAPI Application — main entry point.
"""
import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.session import engine, SessionLocal
from app.database.models import Base, SystemSetting, Client
from app.services.ws_manager import ws_manager
from app.services.pipeline import EventPipeline
from app.ingestion.demo_adapter import DemoStreamAdapter
from app.ingestion.rss_ingester import GoogleNewsRSSIngester
from app.ingestion.social_ingester import SocialIngester  # Reddit + Hacker News


# ─── API Routers ──────────────────────────────────────────────────────────────
from app.api import events, crises, alerts, analytics, sla, clients as clients_router, demo, system, news, ingestion

# ─── Global State ─────────────────────────────────────────────────────────────
event_queue: asyncio.Queue = asyncio.Queue()
pipeline: Optional[EventPipeline] = None
stream_adapter: Optional[DemoStreamAdapter] = None
rss_ingester: Optional[GoogleNewsRSSIngester] = None
social_ingester: Optional[SocialIngester] = None  # Reddit + HackerNews
stream_task: Optional[asyncio.Task] = None
consumer_task: Optional[asyncio.Task] = None
current_mode: str = "LIVE"


async def queue_consumer():
    """Continuously drain the event queue through the pipeline."""
    global pipeline
    while True:
        try:
            raw_event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
            if pipeline:
                await pipeline.process(raw_event)
            event_queue.task_done()
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print(f"[Pipeline] Error: {e}")


async def switch_mode(target_mode: str):
    """Dynamically switch between LIVE Google News RSS + Social and DEMO simulation."""
    global current_mode, stream_adapter, stream_task, rss_ingester, social_ingester
    target_mode = target_mode.upper()
    if target_mode == current_mode:
        return

    current_mode = target_mode
    print(f"[MindMesh] Switching Operational Mode to: {current_mode}")

    if current_mode == "LIVE":
        # Stop DEMO generator
        if stream_adapter:
            stream_adapter.stop()
        if stream_task:
            stream_task.cancel()
            stream_task = None
        # Start Live Google News RSS ingester
        if rss_ingester:
            rss_ingester.start()
        # Start Social ingester (Reddit + HackerNews)
        if social_ingester:
            social_ingester.start()
    else:
        # Stop LIVE ingesters
        if rss_ingester:
            rss_ingester.stop()
        if social_ingester:
            social_ingester.stop()
        # Start DEMO generator
        if not stream_adapter:
            stream_adapter = DemoStreamAdapter(event_queue)
        stream_adapter.is_running = True
        stream_task = asyncio.create_task(stream_adapter.start())

    # Broadcast mode change to all connected UI clients
    await ws_manager.broadcast({
        "type": "MODE_CHANGE",
        "data": {"mode": current_mode},
        "timestamp": time.time(),
    })


def seed_defaults(db):
    """Seed default clients and settings if the database is empty."""
    if db.query(Client).count() == 0:
        defaults = [
            Client(name="PayU", tier="Tier-1", keywords='["payment","rbi","audit","fintech"]', competitors='["PhonePe","Razorpay"]'),
            Client(name="PhonePe", tier="Tier-1", keywords='["upi","payment","digital"]', competitors='["PayU","Google Pay"]'),
            Client(name="Razorpay", tier="Tier-1", keywords='["payment gateway","merchant"]', competitors='["PayU","Cashfree"]'),
            Client(name="Flipkart", tier="Tier-1", keywords='["ecommerce","delivery","cci"]', competitors='["Amazon"]'),
            Client(name="Amazon", tier="Tier-1", keywords='["ecommerce","aws","india"]', competitors='["Flipkart"]'),
            Client(name="Infosys", tier="Tier-1", keywords='["it services","infosys"]', competitors='["TCS","Wipro"]'),
            Client(name="TCS", tier="Tier-1", keywords='["it","tata consultancy"]', competitors='["Infosys"]'),
            Client(name="HDFC", tier="Tier-1", keywords='["bank","hdfc","loan"]', competitors='["ICICI","SBI"]'),
            Client(name="ICICI", tier="Tier-1", keywords='["bank","icici","credit card"]', competitors='["HDFC","SBI"]'),
            Client(name="SBI", tier="Tier-1", keywords='["bank","sbi","government"]', competitors='["HDFC","ICICI"]'),
        ]
        db.add_all(defaults)

    mode_setting = db.get(SystemSetting, "mode")
    if not mode_setting:
        db.add(SystemSetting(key="mode", value="LIVE"))
    if not db.get(SystemSetting, "risk_threshold"):
        db.add(SystemSetting(key="risk_threshold", value="60"))
    if not db.get(SystemSetting, "critical_threshold"):
        db.add(SystemSetting(key="critical_threshold", value="80"))
    if not db.get(SystemSetting, "cooldown_seconds"):
        db.add(SystemSetting(key="cooldown_seconds", value="300"))
    if not db.get(SystemSetting, "sla_target_seconds"):
        db.add(SystemSetting(key="sla_target_seconds", value="120"))
    if not db.get(SystemSetting, "alerts_in_app"):
        db.add(SystemSetting(key="alerts_in_app", value="true"))

    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline, stream_adapter, rss_ingester, stream_task, consumer_task, current_mode

    # Initialize database
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_defaults(db)
        mode_setting = db.get(SystemSetting, "mode")
        current_mode = mode_setting.value if mode_setting else "LIVE"
    finally:
        db.close()

    # Initialize pipeline
    pipeline = EventPipeline(SessionLocal, ws_broadcast_fn=ws_manager.broadcast)

    # Start the event consumer
    consumer_task = asyncio.create_task(queue_consumer())

    # Initialize Ingesters
    stream_adapter = DemoStreamAdapter(event_queue)
    rss_ingester = GoogleNewsRSSIngester(event_queue, SessionLocal)  # Google News RSS (kept)
    social_ingester = SocialIngester(event_queue)                    # Reddit + HackerNews (new)

    # Wire ingester instances to ingestion API router
    ingestion.set_ingester_instances(rss_ingester, stream_adapter, switch_mode, social_ingester)

    # Start appropriate ingester based on configured mode
    if current_mode == "LIVE":
        rss_ingester.start()
        social_ingester.start()  # Start social feeds alongside Google RSS
        print("[MindMesh] System Online - Mode: LIVE (Google News RSS + Reddit + HackerNews Active)")
    else:
        stream_task = asyncio.create_task(stream_adapter.start())
        print("[MindMesh] System Online - Mode: DEMO (Simulation Active)")

    print("[MindMesh] API: http://localhost:8000")
    print("[MindMesh] WS:  ws://localhost:8000/ws/live")

    yield

    # Shutdown
    if rss_ingester:
        rss_ingester.stop()
    if social_ingester:
        social_ingester.stop()  # Stop Reddit + HackerNews
    if stream_adapter:
        stream_adapter.stop()
    if stream_task:
        stream_task.cancel()
    if consumer_task:
        consumer_task.cancel()


# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MindMesh API",
    description="AI Agents & Real-Time Intelligence — 2-Minute Crisis Response Platform",
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Include Routers ──────────────────────────────────────────────────────────
app.include_router(events.router, prefix="/api")
app.include_router(crises.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(sla.router, prefix="/api")
app.include_router(clients_router.router, prefix="/api")
app.include_router(demo.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(ingestion.router, prefix="/api")


# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    # Send welcome message with exact current mode
    await websocket.send_text(json.dumps({
        "type": "CONNECTED",
        "data": {
            "message": "Connected to MindMesh real-time feed",
            "mode": current_mode,
            "system": "ONLINE",
            "source": "Google News RSS" if current_mode == "LIVE" else "Simulated",
        },
        "timestamp": time.time(),
    }))
    try:
        while True:
            await asyncio.sleep(25)
            await websocket.send_text(json.dumps({"type": "PING", "timestamp": time.time()}))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "subtitle": settings.SUBTITLE,
        "version": settings.VERSION,
        "status": "online",
        "mode": current_mode,
        "source": "Google News RSS" if current_mode == "LIVE" else "Simulated",
    }
