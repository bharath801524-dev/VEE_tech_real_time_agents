"""Demo simulation API router."""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.ingestion.demo_adapter import DEMO_SCENARIOS

router = APIRouter()


class SimulateRequest(BaseModel):
    scenario_id: str


class ToggleRequest(BaseModel):
    active: bool


@router.get("/demo/scenarios")
def get_scenarios():
    return [
        {
            "id": v["id"],
            "name": v["name"],
            "description": v["description"],
            "expected_risk": v["expected_risk"],
            "expected_topic": v["expected_topic"],
            "client": v["client"],
        }
        for v in DEMO_SCENARIOS.values()
    ]


@router.post("/demo/simulate")
async def start_simulation(body: SimulateRequest):
    from app.main import stream_adapter
    if stream_adapter is None:
        raise HTTPException(500, "Stream adapter not initialized")
    if body.scenario_id not in DEMO_SCENARIOS:
        raise HTTPException(400, f"Unknown scenario: {body.scenario_id}")

    # Run simulation in background
    asyncio.create_task(stream_adapter.run_scenario(body.scenario_id))
    scenario = DEMO_SCENARIOS[body.scenario_id]

    return {
        "ok": True,
        "message": f"Crisis simulation '{scenario['name']}' started. Watch the live feed!",
        "scenario": body.scenario_id,
        "expected_risk": scenario["expected_risk"],
    }


@router.post("/demo/toggle-stream")
async def toggle_stream(body: ToggleRequest):
    from app.main import stream_adapter, stream_task
    import asyncio
    if stream_adapter is None:
        raise HTTPException(500, "Stream adapter not initialized")

    if body.active:
        if not stream_adapter._running:
            stream_adapter._running = True
    else:
        stream_adapter.stop()

    return {"ok": True, "active": body.active}
