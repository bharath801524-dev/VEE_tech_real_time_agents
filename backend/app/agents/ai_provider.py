"""
MindMesh AI Providers — Abstraction layer for AI triage, insight, and response agents.
Automatically uses DemoAIProvider when no AI_API_KEY / GEMINI_API_KEY is set.
If GEMINI_API_KEY is set, uses Google Gemini Flash (free tier) for real AI analysis.
"""
import asyncio
import json
import logging
import random
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import aiohttp

from app.config import settings

logger = logging.getLogger("mindmesh.ai")


# ─── Base ────────────────────────────────────────────────────────────────────

class AIProvider(ABC):
    @abstractmethod
    async def triage(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Classify an event: brand, topic, sentiment, risk, urgency, confidence."""

    @abstractmethod
    async def generate_insight(self, event: Dict[str, Any], triage: Dict[str, Any]) -> Dict[str, Any]:
        """Generate what_happened, why_it_matters, recommended_action."""

    @abstractmethod
    async def recommend_response(self, event: Dict[str, Any], triage: Dict[str, Any], risk: int) -> Dict[str, Any]:
        """Return priority, recommended_team, and action checklist."""


# ─── Demo Provider ────────────────────────────────────────────────────────────

class DemoAIProvider(AIProvider):
    """
    High-fidelity rule-based AI simulation. Produces realistic outputs
    based on keyword analysis and weighted random distributions.
    """

    TOPIC_KEYWORDS = {
        "Regulatory": ["rbi", "sebi", "audit", "regulation", "compliance", "fine", "penalty", "ban", "license"],
        "Financial": ["loss", "revenue", "profit", "decline", "quarter", "earnings", "write-off", "debt"],
        "Cybersecurity": ["hack", "breach", "data leak", "cyberattack", "vulnerability", "ransomware", "phishing"],
        "Product": ["failure", "outage", "down", "bug", "crash", "not working", "error", "glitch", "slow"],
        "Customer Complaints": ["complaint", "refund", "fraud", "scam", "failed payment", "stuck", "angry", "furious"],
        "Reputation": ["controversy", "scandal", "backlash", "boycott", "viral", "trending", "criticism", "ceo"],
    }

    SENTIMENT_KEYWORDS = {
        "Positive": ["launch", "new feature", "partnership", "award", "milestone", "growth", "success", "record"],
        "Negative": ["audit", "rbi", "failure", "outage", "complaint", "refund", "fine", "penalty", "hack", "loss",
                     "backlash", "angry", "fraud", "decline", "crash", "breach", "stuck"],
    }

    CRISIS_BRANDS = {"PayU", "PhonePe", "Razorpay"}
    TIER1_CLIENTS = {"PayU", "PhonePe", "Razorpay", "Flipkart", "Amazon", "HDFC", "ICICI", "SBI", "Infosys", "TCS"}

    def _classify_topic(self, text: str) -> str:
        text_lower = text.lower()
        scores = {topic: sum(1 for kw in kws if kw in text_lower) for topic, kws in self.TOPIC_KEYWORDS.items()}
        best = max(scores, key=lambda t: scores[t])
        return best if scores[best] > 0 else "General"

    def _classify_sentiment(self, text: str) -> tuple[str, float]:
        text_lower = text.lower()
        pos = sum(1 for kw in self.SENTIMENT_KEYWORDS["Positive"] if kw in text_lower)
        neg = sum(1 for kw in self.SENTIMENT_KEYWORDS["Negative"] if kw in text_lower)
        if neg > pos:
            score = round(-0.4 - min(neg * 0.15, 0.6), 2)
            return "Negative", score
        elif pos > neg:
            score = round(0.3 + min(pos * 0.15, 0.6), 2)
            return "Positive", score
        return "Neutral", round(random.uniform(-0.1, 0.1), 2)

    def _get_client_tier(self, brand: str) -> str:
        return "Tier-1" if brand in self.TIER1_CLIENTS else "Tier-2"

    def _get_urgency(self, risk_score: int) -> str:
        if risk_score >= 80: return "CRITICAL"
        if risk_score >= 60: return "HIGH"
        if risk_score >= 40: return "MEDIUM"
        return "LOW"

    def _get_risk_level(self, risk_score: int) -> str:
        if risk_score >= 81: return "CRITICAL"
        if risk_score >= 61: return "HIGH"
        if risk_score >= 31: return "MEDIUM"
        return "LOW"

    async def triage(self, event: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(random.uniform(0.3, 0.8))  # Simulate AI processing time
        content = f"{event.get('headline', '')} {event.get('content', '')}".lower()
        brand = event.get("brand", "Unknown")

        topic = self._classify_topic(content)
        sentiment, sentiment_score = self._classify_sentiment(content)
        client_tier = self._get_client_tier(brand)

        # Base risk
        base_risk = 30 if sentiment == "Negative" else (15 if sentiment == "Neutral" else 5)

        # Topic severity bonus
        topic_bonus = {
            "Regulatory": 25, "Cybersecurity": 22, "Financial": 18,
            "Product": 15, "Customer Complaints": 12, "Reputation": 18,
        }.get(topic, 5)

        # Tier bonus
        tier_bonus = 15 if client_tier == "Tier-1" else 5
        # Velocity bonus (from event)
        velocity_ratio = event.get("velocity_ratio", 1.0)
        velocity_bonus = min(int((velocity_ratio - 1) * 5), 20)

        raw_score = base_risk + topic_bonus + tier_bonus + velocity_bonus + random.randint(-5, 5)
        risk_score = max(0, min(100, raw_score))
        risk_level = self._get_risk_level(risk_score)
        urgency = self._get_urgency(risk_score)

        competitor_impact = "HIGH" if risk_score >= 70 else ("MEDIUM" if risk_score >= 40 else "LOW")
        confidence = round(random.uniform(0.85, 0.97), 2)

        return {
            "client": brand,
            "client_tier": client_tier,
            "topic": topic,
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "competitor_impact": competitor_impact,
            "urgency": urgency,
            "confidence": confidence,
        }

    async def generate_insight(self, event: Dict[str, Any], triage: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(random.uniform(0.5, 1.2))  # Simulate insight generation
        brand = triage.get("client", "the company")
        topic = triage.get("topic", "General")
        risk_score = triage.get("risk_score", 50)
        risk_level = triage.get("risk_level", "MEDIUM")
        sentiment = triage.get("sentiment", "Neutral")
        headline = event.get("headline", "A significant event was detected")

        what_happened_templates = {
            "Regulatory": f"{headline}. This regulatory development directly involves {brand} and may require immediate legal and compliance review.",
            "Financial": f"{headline}. This financial development for {brand} could impact investor confidence and market sentiment.",
            "Cybersecurity": f"{headline}. A potential security incident has been identified involving {brand}'s systems or data.",
            "Product": f"{headline}. {brand} is experiencing significant service disruption affecting customer transactions.",
            "Customer Complaints": f"{headline}. A large volume of customer complaints is trending across social platforms about {brand}.",
            "Reputation": f"{headline}. A reputational event is gaining traction online and in media about {brand}.",
        }
        why_matters_templates = {
            "Regulatory": f"Regulatory scrutiny from authorities like RBI/SEBI can lead to operational restrictions, public loss of confidence, and potential financial penalties. For a {triage.get('client_tier', 'Tier-1')} client like {brand}, swift communication and legal response is essential to control the narrative.",
            "Financial": f"Financial downturns or adverse disclosures affect investor relations, credit ratings, and employee morale. {brand}'s market position could weaken if this is not managed with a structured communications strategy.",
            "Cybersecurity": f"Security incidents can result in data loss, regulatory penalties, and severe reputational damage. Customer trust erosion can take months to years to rebuild.",
            "Product": f"Service outages directly impact revenue, customer loyalty, and brand reputation. With {brand}'s scale, even a short disruption affects thousands of transactions per minute.",
            "Customer Complaints": f"Viral customer complaint trends can escalate quickly into press coverage. Proactive customer support response and public acknowledgement are critical to prevent amplification.",
            "Reputation": f"Reputational crises spread faster through social media than traditional channels. {brand} needs to control the narrative before it dominates news cycles.",
        }
        recommended_templates = {
            "Regulatory": f"Notify Legal and Compliance teams immediately. Prepare a factual holding statement. Monitor official regulatory channels and competitor responses. Brief senior leadership within the hour.",
            "Financial": f"Alert Finance and IR teams. Prepare factual investor communication. Monitor stock impact and media coverage. Schedule executive briefing.",
            "Cybersecurity": f"Activate cybersecurity incident response protocol. Notify CISO and Legal. Prepare customer communication. Engage third-party forensics if needed.",
            "Product": f"Escalate to Engineering and DevOps. Draft customer-facing status update. Monitor social media for sentiment escalation. Prepare customer support messaging.",
            "Customer Complaints": f"Alert Customer Support leadership. Deploy additional support agents. Prepare empathetic public response. Track complaint volume and resolution rate.",
            "Reputation": f"Convene PR and Communications team. Prepare holding statement and factual narrative. Engage with key media contacts. Monitor competitor and analyst commentary.",
        }

        return {
            "what_happened": what_happened_templates.get(topic, f"{headline}. {brand} is at the center of a developing {topic.lower()} situation requiring monitoring."),
            "why_it_matters": why_matters_templates.get(topic, f"This event could affect {brand}'s reputation and operations. Immediate assessment is recommended."),
            "recommended_action": recommended_templates.get(topic, f"Monitor the situation closely and brief relevant teams."),
        }

    async def recommend_response(self, event: Dict[str, Any], triage: Dict[str, Any], risk: int) -> Dict[str, Any]:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        topic = triage.get("topic", "General")
        client_tier = triage.get("client_tier", "Tier-2")
        risk_level = triage.get("risk_level", "MEDIUM")

        if risk >= 80:
            priority = "CRITICAL"
            team_map = {
                "Regulatory": "PR + Legal",
                "Cybersecurity": "Security + Legal",
                "Financial": "Finance + IR",
                "Product": "Engineering + Customer Support",
                "Customer Complaints": "Customer Support + PR",
                "Reputation": "PR + Leadership",
            }
            recommended_team = team_map.get(topic, "PR + Legal")
            actions = [
                f"Prepare holding statement for {topic.lower()} issue",
                "Brief senior leadership (C-suite) within 30 minutes",
                "Monitor official channels and regulatory updates",
                "Track social sentiment velocity every 5 minutes",
                "Document all actions for compliance record",
                "Notify Board if issue escalates further",
            ]
        elif risk >= 60:
            priority = "HIGH"
            recommended_team = "PR" if topic in ("Reputation", "Customer Complaints") else "Relevant Business Unit"
            actions = [
                "Alert relevant department heads",
                "Prepare internal situation briefing",
                "Monitor media and social coverage",
                "Prepare customer-facing communication if needed",
            ]
        else:
            priority = "MEDIUM"
            recommended_team = "Communications Team"
            actions = ["Monitor situation for escalation", "Log event for reporting"]

        competitor_reaction = None
        if risk >= 60:
            competitors = {"PayU": ["PhonePe", "Razorpay"], "PhonePe": ["PayU", "Google Pay"], "Razorpay": ["PayU", "Cashfree"]}.get(triage.get("client", ""), [])
            if competitors:
                competitor_reaction = f"Competitors {', '.join(competitors)} may leverage this situation. Monitor their social and PR activities for opportunistic messaging."

        return {
            "priority": priority,
            "recommended_team": recommended_team,
            "actions": actions,
            "competitor_reaction": competitor_reaction,
        }


# ─── Google Gemini Flash Provider ────────────────────────────────────────────

class GeminiProvider(AIProvider):
    """
    Real AI using Google Gemini Flash (free tier via Google AI Studio).
    Falls back to DemoAIProvider on any API failure or rate limit.
    """

    GEMINI_URL = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-3.6-flash:generateContent?key={api_key}"
    )
    TIMEOUT = aiohttp.ClientTimeout(total=10)

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._fallback = DemoAIProvider()
        self._url = self.GEMINI_URL.format(api_key=api_key)
        self._cooldown_until = 0.0
        self._cooldown_warned = False

    async def _call(self, prompt: str) -> Optional[str]:
        """Call Gemini REST API and return text response, with 429 rate-limit backoff."""
        now = time.time()
        if now < self._cooldown_until:
            # Under cooldown due to 429 quota exhaustion; bypass network call
            return None

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1000,
            },
        }
        try:
            async with aiohttp.ClientSession(timeout=self.TIMEOUT) as session:
                async with session.post(self._url, json=payload) as resp:
                    if resp.status == 429:
                        self._cooldown_until = time.time() + 60.0
                        if not self._cooldown_warned:
                            logger.warning(
                                "[Gemini] Free tier rate limit reached (HTTP 429). "
                                "Falling back to high-fidelity local AI engine for 60s."
                            )
                            self._cooldown_warned = True
                        return None

                    if resp.status != 200:
                        logger.warning(f"[Gemini] API error {resp.status}")
                        return None

                    self._cooldown_warned = False
                    data = await resp.json()

            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        except Exception as e:
            logger.warning(f"[Gemini] Call failed: {e}")
        return None

    async def triage(self, event: Dict[str, Any]) -> Dict[str, Any]:
        headline = event.get("headline", "")
        content = event.get("content", headline)[:600]
        brand = event.get("brand", "Unknown")

        prompt = f"""You are a media crisis intelligence AI. Analyze this news event and return ONLY a JSON object.

Brand: {brand}
Headline: {headline}
Content: {content}

Return ONLY this JSON (no markdown, no explanation):
{{
  "client": "{brand}",
  "client_tier": "Tier-1 or Tier-2",
  "topic": "one of: Regulatory, Financial, Cybersecurity, Product, Customer Complaints, Reputation, General",
  "sentiment": "Positive, Negative, or Neutral",
  "sentiment_score": <float -1.0 to 1.0>,
  "risk_level": "LOW, MEDIUM, HIGH, or CRITICAL",
  "risk_score": <integer 0-100>,
  "competitor_impact": "LOW, MEDIUM, or HIGH",
  "urgency": "LOW, MEDIUM, HIGH, or CRITICAL",
  "confidence": <float 0.0 to 1.0>
}}"""

        text = await self._call(prompt)
        if text:
            try:
                # Strip markdown fences if present
                text = text.strip().strip("```json").strip("```").strip()
                result = json.loads(text)
                result.setdefault("client", brand)
                result.setdefault("confidence", 0.92)
                logger.info(f"[Gemini] Triage OK for '{headline[:50]}'")
                return result
            except Exception as e:
                logger.warning(f"[Gemini] Triage JSON parse error: {e} | raw: {text[:200]}")

        # Graceful fallback
        return await self._fallback.triage(event)

    async def generate_insight(self, event: Dict[str, Any], triage: Dict[str, Any]) -> Dict[str, Any]:
        headline = event.get("headline", "")
        brand = triage.get("client", event.get("brand", "the company"))
        topic = triage.get("topic", "General")
        risk_score = triage.get("risk_score", 50)

        prompt = f"""You are a PR crisis expert generating a 2-minute executive briefing. Return ONLY a JSON object.

Brand: {brand}
Headline: {headline}
Topic: {topic}
Risk Score: {risk_score}/100

Return ONLY this JSON:
{{
  "what_happened": "<2-3 sentence factual summary of the incident>",
  "why_it_matters": "<2-3 sentence business and reputational impact analysis>",
  "recommended_action": "<2-3 concrete, specific immediate actions for PR/Legal/Ops team>"
}}"""

        text = await self._call(prompt)
        if text:
            try:
                text = text.strip().strip("```json").strip("```").strip()
                result = json.loads(text)
                logger.info(f"[Gemini] Insight OK for '{headline[:50]}'")
                return result
            except Exception as e:
                logger.warning(f"[Gemini] Insight JSON parse error: {e}")

        return await self._fallback.generate_insight(event, triage)

    async def recommend_response(self, event: Dict[str, Any], triage: Dict[str, Any], risk: int) -> Dict[str, Any]:
        brand = triage.get("client", "the company")
        topic = triage.get("topic", "General")
        risk_level = triage.get("risk_level", "MEDIUM")

        prompt = f"""You are a crisis response coordinator. Return ONLY a JSON object.

Brand: {brand}
Topic: {topic}
Risk Level: {risk_level} ({risk}/100)

Return ONLY this JSON:
{{
  "priority": "LOW, MEDIUM, HIGH, or CRITICAL",
  "recommended_team": "<team name, e.g. PR, Legal, Security, Support>",
  "actions": ["<action 1>", "<action 2>", "<action 3>"],
  "competitor_reaction": "<optional: how competitors may respond, or null>"
}}"""

        text = await self._call(prompt)
        if text:
            try:
                text = text.strip().strip("```json").strip("```").strip()
                result = json.loads(text)
                logger.info(f"[Gemini] Response OK for {brand}")
                return result
            except Exception as e:
                logger.warning(f"[Gemini] Response JSON parse error: {e}")

        return await self._fallback.recommend_response(event, triage, risk)


# ─── Factory ──────────────────────────────────────────────────────────────────

def get_ai_provider() -> AIProvider:
    """Return GeminiProvider if GEMINI_API_KEY is set, else DemoAIProvider."""
    api_key = settings.GEMINI_API_KEY or settings.AI_API_KEY
    if api_key:
        logger.info("[AI] Using Google Gemini Flash provider (real AI)")
        return GeminiProvider(api_key)
    logger.info("[AI] Using Demo AI provider (set GEMINI_API_KEY to enable real AI)")
    return DemoAIProvider()
