"""
MindMesh Alert Engine — Rules-based alerting with fatigue prevention.
Supports: In-App (WebSocket), Discord Webhook, Telegram Bot.
"""
import logging
import time
import uuid
from typing import Dict, Any, Optional

import aiohttp

from app.config import settings

logger = logging.getLogger("mindmesh.alerts")


class AlertFatigueGuard:
    """Prevents repeated alerts for the same crisis within the cooldown window."""

    def __init__(self, cooldown_seconds: int = None):
        self._cooldown = cooldown_seconds or settings.ALERT_COOLDOWN_SECONDS
        self._last_alert: Dict[str, float] = {}  # key = brand+topic

    def should_alert(self, brand: str, topic: str) -> bool:
        key = f"{brand}::{topic}"
        now = time.time()
        last = self._last_alert.get(key, 0)
        if now - last >= self._cooldown:
            self._last_alert[key] = now
            return True
        return False

    def time_until_next(self, brand: str, topic: str) -> float:
        key = f"{brand}::{topic}"
        elapsed = time.time() - self._last_alert.get(key, 0)
        return max(0.0, self._cooldown - elapsed)


class AlertRulesEngine:
    """
    Evaluates whether an event should trigger an alert.
    Rules:
      - risk_score >= 80  → CRITICAL ALERT
      - risk_score >= 60  → HIGH ALERT
      - client_tier == Tier-1 AND risk_score >= 40  → HIGH ALERT
    """

    def __init__(self, risk_threshold: int = None, critical_threshold: int = None):
        self._risk_threshold = risk_threshold or settings.DEFAULT_RISK_THRESHOLD
        self._critical_threshold = critical_threshold or settings.CRITICAL_RISK_THRESHOLD
        self._fatigue = AlertFatigueGuard()

    def evaluate(self, risk_score: int, client_tier: str, topic: str, brand: str) -> Optional[str]:
        """Returns alert_level string or None if no alert should be sent."""
        if risk_score >= self._critical_threshold:
            if self._fatigue.should_alert(brand, topic):
                return "CRITICAL"
        elif risk_score >= self._risk_threshold:
            if self._fatigue.should_alert(brand, topic):
                return "HIGH"
        elif client_tier == "Tier-1" and risk_score >= 40:
            if self._fatigue.should_alert(brand, topic):
                return "HIGH"
        return None


class AlertProvider:
    """Base alert channel."""
    async def send(self, payload: Dict[str, Any]) -> bool:
        raise NotImplementedError


class DemoAlertProvider(AlertProvider):
    """In-app alert: broadcasts via WebSocket (handled by ws_manager)."""

    def __init__(self, ws_broadcast_fn=None):
        self._ws_broadcast = ws_broadcast_fn

    async def send(self, payload: Dict[str, Any]) -> bool:
        if self._ws_broadcast:
            await self._ws_broadcast({
                "type": "ALERT_TRIGGERED",
                "data": payload,
                "timestamp": time.time(),
            })
        return True


# ─── Discord Webhook Provider ─────────────────────────────────────────────────

class DiscordAlertProvider(AlertProvider):
    """
    Sends rich color-coded crisis alerts to a Discord channel via Webhook.
    Free: no bot required, just a webhook URL from your server settings.
    Set DISCORD_WEBHOOK_URL in .env to enable.
    """

    TIMEOUT = aiohttp.ClientTimeout(total=8)
    LEVEL_COLORS = {
        "CRITICAL": 0xE53E3E,  # red
        "HIGH": 0xED8936,       # orange
        "MEDIUM": 0xECC94B,     # yellow
        "LOW": 0x68D391,        # green
    }

    def __init__(self, webhook_url: str):
        self._url = webhook_url

    async def send(self, payload: Dict[str, Any]) -> bool:
        level = payload.get("alert_level", "HIGH")
        risk = payload.get("risk_score", 0)
        brand = payload.get("brand", "Unknown")
        topic = payload.get("topic", "General")
        headline = payload.get("headline", "No headline")
        what = payload.get("what_happened", "")
        action = payload.get("recommended_action", "")

        color = self.LEVEL_COLORS.get(level, 0xED8936)
        emoji = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "📊", "LOW": "ℹ️"}.get(level, "⚠️")

        embed = {
            "title": f"{emoji} MindMesh Crisis Alert — {brand}",
            "description": f"**{headline}**",
            "color": color,
            "fields": [
                {"name": "🏷️ Topic", "value": topic, "inline": True},
                {"name": "📈 Risk Score", "value": f"{risk}/100 ({level})", "inline": True},
                {"name": "🔖 Tier", "value": payload.get("client_tier", "Tier-2"), "inline": True},
            ],
            "footer": {"text": "MindMesh · 2-Minute Crisis Response Platform"},
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }
        if what:
            embed["fields"].append({"name": "📋 What Happened", "value": what[:1020], "inline": False})
        if action:
            embed["fields"].append({"name": "✅ Recommended Action", "value": action[:1020], "inline": False})

        body = {"embeds": [embed]}
        try:
            async with aiohttp.ClientSession(timeout=self.TIMEOUT) as session:
                async with session.post(self._url, json=body) as resp:
                    ok = resp.status in (200, 204)
                    if not ok:
                        logger.warning(f"[Discord] Alert failed: HTTP {resp.status}")
                    else:
                        logger.info(f"[Discord] Alert sent: {brand} {level} risk={risk}")
                    return ok
        except Exception as e:
            logger.warning(f"[Discord] Alert error: {e}")
            return False


# ─── Telegram Bot Provider ────────────────────────────────────────────────────

class TelegramAlertProvider(AlertProvider):
    """
    Sends HTML-formatted crisis alerts to a Telegram chat via Bot API.
    Free: create a bot with @BotFather, get token & chat ID.
    Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env to enable.
    """

    TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"
    TIMEOUT = aiohttp.ClientTimeout(total=8)

    def __init__(self, bot_token: str, chat_id: str):
        self._url = self.TELEGRAM_URL.format(token=bot_token)
        self._chat_id = chat_id

    async def send(self, payload: Dict[str, Any]) -> bool:
        level = payload.get("alert_level", "HIGH")
        risk = payload.get("risk_score", 0)
        brand = payload.get("brand", "Unknown")
        topic = payload.get("topic", "General")
        headline = payload.get("headline", "No headline")
        what = payload.get("what_happened", "")
        action = payload.get("recommended_action", "")

        emoji = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "📊", "LOW": "ℹ️"}.get(level, "⚠️")

        lines = [
            f"{emoji} <b>MindMesh Crisis Alert</b>",
            f"<b>{headline}</b>",
            "",
            f"🏢 <b>Brand:</b> {brand}",
            f"🏷️ <b>Topic:</b> {topic}",
            f"📈 <b>Risk Score:</b> {risk}/100 ({level})",
            f"🔖 <b>Tier:</b> {payload.get('client_tier', 'Tier-2')}",
        ]
        if what:
            lines += ["", f"📋 <b>What Happened:</b>\n{what[:600]}"]
        if action:
            lines += ["", f"✅ <b>Action:</b>\n{action[:600]}"]
        lines += ["", "<i>MindMesh · 2-Minute Crisis Response</i>"]

        body = {
            "chat_id": self._chat_id,
            "text": "\n".join(lines),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            async with aiohttp.ClientSession(timeout=self.TIMEOUT) as session:
                async with session.post(self._url, json=body) as resp:
                    data = await resp.json()
                    ok = data.get("ok", False)
                    if not ok:
                        logger.warning(f"[Telegram] Alert failed: {data.get('description')}")
                    else:
                        logger.info(f"[Telegram] Alert sent: {brand} {level} risk={risk}")
                    return ok
        except Exception as e:
            logger.warning(f"[Telegram] Alert error: {e}")
            return False


# ─── Alert Engine ─────────────────────────────────────────────────────────────

class AlertEngine:
    """
    Orchestrates the full alert pipeline:
    Evaluate rules → Dispatch to channels → Return alert record.
    Auto-registers Discord and Telegram providers when env vars are set.
    """

    def __init__(self, ws_broadcast_fn=None):
        self._rules = AlertRulesEngine()
        self._providers = [DemoAlertProvider(ws_broadcast_fn)]
        self._register_external_providers()

    def _register_external_providers(self):
        """Auto-register Discord + Telegram if configured."""
        if settings.DISCORD_WEBHOOK_URL:
            self._providers.append(DiscordAlertProvider(settings.DISCORD_WEBHOOK_URL))
            logger.info("[Alerts] Discord webhook provider registered")

        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            self._providers.append(
                TelegramAlertProvider(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID)
            )
            logger.info("[Alerts] Telegram bot provider registered")

    def add_provider(self, p: AlertProvider):
        self._providers.append(p)

    async def process(
        self,
        event: Dict[str, Any],
        triage: Dict[str, Any],
        risk_score: int,
        crisis_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        brand = triage.get("client", "Unknown")
        topic = triage.get("topic", "General")
        client_tier = triage.get("client_tier", "Tier-2")
        risk_level = triage.get("risk_level", "LOW")
        insight = event.get("insight", {})

        alert_level = self._rules.evaluate(risk_score, client_tier, topic, brand)
        if not alert_level:
            return None

        alert_id = str(uuid.uuid4())
        payload = {
            "id": alert_id,
            "crisis_id": crisis_id,
            "event_id": event.get("id"),
            "brand": brand,
            "headline": event.get("headline", ""),
            "topic": topic,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "alert_level": alert_level,
            "client_tier": client_tier,
            "sentiment": triage.get("sentiment", "Neutral"),
            "what_happened": insight.get("what_happened", ""),
            "recommended_action": insight.get("recommended_action", ""),
            "sent_at": time.time(),
            "channel": "in_app",
            "status": "DELIVERED",
        }

        for provider in self._providers:
            try:
                await provider.send(payload)
            except Exception as e:
                logger.debug(f"[AlertEngine] Provider {type(provider).__name__} error: {e}")

        return payload

