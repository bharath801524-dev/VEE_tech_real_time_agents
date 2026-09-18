"""
MindMesh Demo Stream Adapter — Generates realistic, continuously streaming
news, Twitter, and Reddit events, including periodic crisis spikes.
"""
import asyncio
import random
import time
import uuid
from typing import Dict, Any, List

# ─── Realistic Content Templates ─────────────────────────────────────────────

BRANDS = ["PayU", "PhonePe", "Razorpay", "Flipkart", "Amazon", "Infosys", "TCS", "HDFC", "ICICI", "SBI"]

NORMAL_EVENTS = [
    {"brand": "PayU", "headline": "PayU launches new instant refund feature for merchants", "sentiment_hint": "positive"},
    {"brand": "PhonePe", "headline": "PhonePe crosses 500 million registered users milestone", "sentiment_hint": "positive"},
    {"brand": "Razorpay", "headline": "Razorpay expands international payment gateway to Southeast Asia", "sentiment_hint": "positive"},
    {"brand": "Flipkart", "headline": "Flipkart introduces AI-powered product recommendations", "sentiment_hint": "positive"},
    {"brand": "Amazon", "headline": "Amazon India announces two-hour delivery in 12 new cities", "sentiment_hint": "positive"},
    {"brand": "Infosys", "headline": "Infosys wins $500M digital transformation contract from US bank", "sentiment_hint": "positive"},
    {"brand": "TCS", "headline": "TCS recognized among top employers globally by Forbes", "sentiment_hint": "positive"},
    {"brand": "HDFC", "headline": "HDFC Bank reports 18% YoY growth in Q2 net profit", "sentiment_hint": "positive"},
    {"brand": "ICICI", "headline": "ICICI Bank launches zero-fee digital savings account", "sentiment_hint": "positive"},
    {"brand": "SBI", "headline": "SBI deploys AI chatbot for customer service across 22,000 branches", "sentiment_hint": "positive"},
]

CRISIS_EVENTS = [
    {
        "brand": "PayU", "source": "news",
        "headline": "RBI announces regulatory audit of PayU payment operations",
        "content": "The Reserve Bank of India has announced a comprehensive regulatory audit of PayU's payment gateway operations citing compliance concerns. The audit is expected to last 30 days and may impact PayU's merchant onboarding process.",
        "location": "Mumbai"
    },
    {
        "brand": "PayU", "source": "twitter",
        "headline": "Thousands of users report payment failures on PayU gateway",
        "content": "#PayUDown trending on X - Thousands of users are reporting failed payments on PayU's gateway. Merchants say transactions are timing out and refunds are delayed. PayU support is flooded with complaints.",
        "location": "Bengaluru"
    },
    {
        "brand": "PhonePe", "source": "news",
        "headline": "PhonePe facing SEBI scrutiny over cross-border fund transfers",
        "content": "SEBI has initiated a review of PhonePe's international money transfer operations following reports of regulatory non-compliance with FEMA guidelines.",
        "location": "Delhi"
    },
    {
        "brand": "Razorpay", "source": "reddit",
        "headline": "r/india: Razorpay data breach exposes 50,000 merchant accounts",
        "content": "Multiple merchants on Reddit report unauthorized access to their Razorpay accounts. Screenshots show unfamiliar transactions. Razorpay has not yet issued an official statement. Cybersecurity experts are calling this a major breach.",
        "location": "Hyderabad"
    },
    {
        "brand": "Flipkart", "source": "news",
        "headline": "Flipkart under CCI investigation for alleged predatory pricing",
        "content": "The Competition Commission of India has issued notices to Flipkart over allegations of predatory pricing and preferential treatment of select sellers, which may violate antitrust regulations.",
        "location": "Bengaluru"
    },
    {
        "brand": "HDFC", "source": "news",
        "headline": "HDFC Bank server outage disrupts mobile banking for 3 hours",
        "content": "HDFC Bank's mobile banking and internet banking services were down for over 3 hours on Tuesday due to a server infrastructure failure. The outage affected an estimated 2 million customers.",
        "location": "Mumbai"
    },
]

SOCIAL_NOISE = [
    {"brand": "PayU", "headline": "Anyone else's UPI not working? @PayU please fix!", "source": "twitter"},
    {"brand": "PhonePe", "headline": "PhonePe cashback offer ending soon — grab it!", "source": "twitter"},
    {"brand": "Razorpay", "headline": "Integrated Razorpay on my website — works flawlessly", "source": "reddit"},
    {"brand": "Flipkart", "headline": "Great deals on Flipkart Big Billion Days this weekend", "source": "twitter"},
    {"brand": "Amazon", "headline": "Amazon Prime Video adds 50 new titles this month", "source": "reddit"},
]

LOCATIONS = ["Mumbai", "Bengaluru", "Delhi", "Hyderabad", "Pune", "Chennai", "Kolkata", "Ahmedabad"]
SOURCES: List[str] = ["news", "twitter", "reddit"]

DEMO_SCENARIOS = {
    "regulatory_audit": {
        "id": "regulatory_audit",
        "name": "Scenario 1: Regulatory Crisis",
        "description": "RBI announces audit of PayU operations — triggers CRITICAL risk detection",
        "expected_risk": "CRITICAL",
        "expected_topic": "Regulatory",
        "client": "PayU",
        "events": [
            {"delay": 0, "type": "crisis", "index": 0, "velocity_boost": 1.0},
            {"delay": 5, "type": "social_spike", "brand": "PayU", "count": 3},
            {"delay": 10, "type": "velocity_spike", "brand": "PayU"},
            {"delay": 15, "type": "related", "brand": "PayU", "headline": "Merchants panic as RBI audit could freeze PayU operations"},
            {"delay": 20, "type": "related", "brand": "PayU", "headline": "PayU users rush to migrate to alternative payment gateways"},
        ],
    },
    "product_outage": {
        "id": "product_outage",
        "name": "Scenario 2: Product Failure",
        "description": "Mass payment failures reported on PhonePe — velocity CRITICAL spike",
        "expected_risk": "HIGH",
        "expected_topic": "Product",
        "client": "PhonePe",
        "events": [
            {"delay": 0, "type": "normal", "brand": "PhonePe", "headline": "PhonePe reports intermittent payment issues", "source": "twitter"},
            {"delay": 3, "type": "social_spike", "brand": "PhonePe", "count": 4},
            {"delay": 8, "type": "crisis", "index": 1, "velocity_boost": 4.8},
            {"delay": 12, "type": "related", "brand": "PhonePe", "headline": "PhonePe down detector shows 80,000 reports in last hour"},
        ],
    },
    "normal_news": {
        "id": "normal_news",
        "name": "Scenario 3: Normal News (No Alert)",
        "description": "PayU launches new feature — demonstrates intelligent non-alerting",
        "expected_risk": "LOW",
        "expected_topic": "Product",
        "client": "PayU",
        "events": [
            {"delay": 0, "type": "normal", "brand": "PayU", "headline": "PayU launches new instant refund feature for merchants", "source": "news"},
            {"delay": 5, "type": "normal", "brand": "PayU", "headline": "PayU partners with 10,000 new merchants this quarter", "source": "news"},
        ],
    },
}


def build_event(brand: str, headline: str, content: str = "", source: str = "news",
                location: str = None, velocity_ratio: float = 1.0, velocity_boost: float = 1.0) -> Dict[str, Any]:
    actual_velocity = round(velocity_ratio * velocity_boost, 2)
    return {
        "id": str(uuid.uuid4()),
        "source": source,
        "source_origin": "DEMO • Simulated",
        "publisher": "Simulated Feed",
        "external_id": str(uuid.uuid4())[:8],
        "timestamp": time.time(),
        "brand": brand,
        "headline": headline,
        "content": content or headline,
        "url": f"https://demo.mindmesh.ai/event/{uuid.uuid4().hex[:8]}",
        "language": "en",
        "location": location or random.choice(LOCATIONS),
        "velocity_ratio": actual_velocity,
    }


class DemoStreamAdapter:
    """Continuously generates a realistic stream of media events."""

    def __init__(self, queue: asyncio.Queue):
        self._queue = queue
        self._running = False
        self._total = 0

    async def start(self):
        self._running = True
        while self._running:
            await self._emit_random_event()
            # Interval: 3–8 seconds normally, occasionally burst
            await asyncio.sleep(random.uniform(3, 8))

    def stop(self):
        self._running = False

    async def _emit_random_event(self):
        roll = random.random()
        if roll < 0.05:
            # 5% chance: crisis event
            ev_data = random.choice(CRISIS_EVENTS)
            velocity = round(random.uniform(3.5, 5.5), 2)
            ev = build_event(
                brand=ev_data["brand"],
                headline=ev_data["headline"],
                content=ev_data.get("content", ev_data["headline"]),
                source=ev_data.get("source", "news"),
                location=ev_data.get("location"),
                velocity_ratio=velocity,
            )
        elif roll < 0.25:
            # 20% chance: social noise
            ev_data = random.choice(SOCIAL_NOISE)
            ev = build_event(
                brand=ev_data["brand"],
                headline=ev_data["headline"],
                source=ev_data["source"],
                velocity_ratio=round(random.uniform(0.8, 1.5), 2),
            )
        else:
            # 75% chance: normal positive news
            ev_data = random.choice(NORMAL_EVENTS)
            ev = build_event(
                brand=ev_data["brand"],
                headline=ev_data["headline"],
                source=random.choice(SOURCES),
                velocity_ratio=round(random.uniform(0.9, 1.3), 2),
            )

        self._total += 1
        await self._queue.put(ev)

    async def run_scenario(self, scenario_id: str) -> List[Dict[str, Any]]:
        """Queue scenario events with realistic delays."""
        scenario = DEMO_SCENARIOS.get(scenario_id)
        if not scenario:
            return []

        emitted = []
        for step in scenario["events"]:
            await asyncio.sleep(step["delay"] if emitted else 0)
            if step["type"] == "crisis":
                ev_data = CRISIS_EVENTS[step["index"]]
                ev = build_event(
                    brand=ev_data["brand"],
                    headline=ev_data["headline"],
                    content=ev_data.get("content", ev_data["headline"]),
                    source=ev_data.get("source", "news"),
                    location=ev_data.get("location"),
                    velocity_ratio=step.get("velocity_boost", 4.8),
                )
            elif step["type"] == "social_spike":
                for _ in range(step.get("count", 3)):
                    ev = build_event(
                        brand=step["brand"],
                        headline=f"Users report issues with {step['brand']} — frustrated with service disruption",
                        source="twitter",
                        velocity_ratio=round(random.uniform(3.0, 5.0), 2),
                    )
                    emitted.append(ev)
                    await self._queue.put(ev)
                continue
            elif step["type"] == "normal":
                ev = build_event(
                    brand=step["brand"],
                    headline=step["headline"],
                    source=step.get("source", "news"),
                    velocity_ratio=1.0,
                )
            elif step["type"] == "related":
                ev = build_event(
                    brand=step["brand"],
                    headline=step["headline"],
                    source=random.choice(["news", "twitter"]),
                    velocity_ratio=round(random.uniform(2.0, 4.0), 2),
                )
            else:
                continue

            emitted.append(ev)
            await self._queue.put(ev)

        return emitted
