"""
Integration test for EventPipeline end-to-end processing
"""
import pytest
import pytest_asyncio
from app.services.pipeline import EventPipeline, is_relevant
from app.database.session import SessionLocal


def test_is_relevant():
    monitored = {"PayU", "CRED", "Zepto"}
    event_relevant = {"brand": "PayU", "headline": "News on PayU"}
    event_irrelevant = {"brand": "Tesla", "headline": "Electric cars in US"}

    assert is_relevant(event_relevant, monitored) is True
    assert is_relevant(event_irrelevant, monitored) is False


@pytest.mark.asyncio
async def test_pipeline_end_to_end():
    pipeline = EventPipeline(db_session_factory=SessionLocal)

    event_payload = {
        "id": "test-event-001",
        "brand": "PayU",
        "headline": "RBI initiates special regulatory compliance audit on PayU India payments aggregator",
        "content": "Reserve Bank of India has initiated a comprehensive audit of payment aggregator PayU. Increased merchant scrutiny expected.",
        "source": "news",
        "timestamp": 1720000000.0,
        "url": "https://economictimes.example.com/payu-rbi",
    }

    result = await pipeline.process(event_payload)
    assert result is not None
    assert result["brand"] == "PayU"
    assert "risk_score" in result
    assert result["risk_score"] > 0
    assert "risk_level" in result
    assert "insight" in result
    assert "sla_seconds" in result
