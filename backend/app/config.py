import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "MindMesh"
    SUBTITLE: str = "AI Agents & Real-Time Intelligence"
    TAGLINE: str = "From 6-Hour Reporting to 2-Minute Crisis Response"
    VERSION: str = "1.0.0"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mindmesh.db")

    # ── AI Keys ────────────────────────────────────────────────────────────────
    # GEMINI_API_KEY: free at https://aistudio.google.com/ → Get API Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # Legacy alias (also accepted)
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")

    # ── News / Social ──────────────────────────────────────────────────────────
    # Google News RSS — built-in, no key needed
    # Reddit & Hacker News — built-in, no key needed
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")

    # ── Alert Channels ─────────────────────────────────────────────────────────
    # Discord: Server Settings → Integrations → Webhooks → Copy Webhook URL
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    # Telegram: 1) Message @BotFather → /newbot → copy token
    #           2) Add bot to group → get chat ID from getUpdates
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Legacy Slack / SMS (already present)
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")

    # ── Operational thresholds ─────────────────────────────────────────────────
    SLA_TARGET_SECONDS: int = int(os.getenv("SLA_TARGET_SECONDS", "120"))
    DEFAULT_RISK_THRESHOLD: int = int(os.getenv("DEFAULT_RISK_THRESHOLD", "60"))
    CRITICAL_RISK_THRESHOLD: int = int(os.getenv("CRITICAL_RISK_THRESHOLD", "80"))
    ALERT_COOLDOWN_SECONDS: int = int(os.getenv("ALERT_COOLDOWN_SECONDS", "300"))

    DEFAULT_MODE: str = "DEMO"

    @property
    def is_live_mode_available(self) -> bool:
        return bool(self.GEMINI_API_KEY or self.AI_API_KEY or self.NEWS_API_KEY)


settings = Settings()

