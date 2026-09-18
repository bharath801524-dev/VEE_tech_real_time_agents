"""
MindMesh Social Ingestion — Reddit & Hacker News
Fetches real-time public posts using free, no-key-required APIs:
  - Reddit JSON API  (reddit.com/r/<sub>/new.json)
  - Hacker News Firebase API (hacker-news.firebaseio.com)
"""
import asyncio
import hashlib
import html
import logging
import re
import time
from typing import Any, Dict, List, Optional, Set

import aiohttp

logger = logging.getLogger("mindmesh.social")

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=12)
HEADERS = {
    "User-Agent": (
        "MindMesh/1.0 (crisis-intelligence-platform)"
    ),
    "Accept": "application/json",
}

# ─── Subreddits & keywords to monitor ────────────────────────────────────────

REDDIT_SUBREDDITS = [
    "india",
    "IndiaTech",
    "IndiaFinance",
    "fintech",
    "technology",
    "worldnews",
    "cybersecurity",
]

MONITORED_KEYWORDS = [
    "payU", "phonePe", "razorpay", "paytm", "flipkart", "amazon", "hdfc",
    "icici", "sbi", "infosys", "tcs", "rbi", "sebi", "openai", "chatgpt",
    "data breach", "outage", "hack", "scam", "fraud", "fine", "penalty",
    "down", "not working", "cyberattack", "ransomware",
]

HN_SEARCH_TERMS = [
    "openai", "chatgpt", "data breach", "outage", "cybersecurity", "ransomware", "hack",
    "fintech", "payment", "bank", "regulation",
]


def _clean(text: Optional[str]) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def _matches_keywords(text: str) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in MONITORED_KEYWORDS)


def _content_hash(text: str) -> str:
    return hashlib.sha1(text.lower().encode()).hexdigest()[:16]


def _extract_brand(text: str) -> str:
    """Return first matching brand keyword from text, or 'General'."""
    brand_map = {
        "openai": "OpenAI", "chatgpt": "OpenAI",
        "payU": "PayU", "phonePe": "PhonePe", "razorpay": "Razorpay",
        "paytm": "Paytm", "flipkart": "Flipkart", "amazon": "Amazon",
        "hdfc": "HDFC", "icici": "ICICI", "sbi": "SBI",
        "infosys": "Infosys", "tcs": "TCS",
    }
    text_lower = text.lower()
    for key, brand in brand_map.items():
        if key.lower() in text_lower:
            return brand
    return "General"


# ─── Reddit Ingester ──────────────────────────────────────────────────────────

class RedditIngester:
    """Polls Reddit subreddits for new posts mentioning monitored brands."""

    REDDIT_API = "https://www.reddit.com/r/{sub}/new.json?limit=25&t=hour"

    def __init__(self, event_queue: asyncio.Queue, poll_interval: int = 90):
        self._queue = event_queue
        self._poll_interval = poll_interval
        self._seen: Set[str] = set()
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._stats = {"fetched": 0, "ingested": 0, "errors": 0}

    def start(self):
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._poll_loop())
            logger.info("[Reddit] Ingester started")

    def stop(self):
        self._is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("[Reddit] Ingester stopped")

    def get_status(self) -> Dict[str, Any]:
        return {
            "source": "Reddit",
            "is_running": self._is_running,
            "subreddits": REDDIT_SUBREDDITS,
            **self._stats,
        }

    async def _poll_loop(self):
        while self._is_running:
            try:
                await self._fetch_all_subreddits()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._stats["errors"] += 1
                logger.warning(f"[Reddit] Poll error: {e}")
            await asyncio.sleep(self._poll_interval)

    async def _fetch_all_subreddits(self):
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT, headers=HEADERS) as session:
            tasks = [self._fetch_subreddit(session, sub) for sub in REDDIT_SUBREDDITS]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _fetch_subreddit(self, session: aiohttp.ClientSession, sub: str):
        url = self.REDDIT_API.format(sub=sub)
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return
                data = await resp.json()
        except Exception as e:
            logger.debug(f"[Reddit] Failed to fetch r/{sub}: {e}")
            return

        posts = data.get("data", {}).get("children", [])
        self._stats["fetched"] += len(posts)

        for post in posts:
            p = post.get("data", {})
            title = _clean(p.get("title", ""))
            selftext = _clean(p.get("selftext", ""))
            combined = f"{title} {selftext}"

            if not _matches_keywords(combined):
                continue

            post_id = p.get("id", _content_hash(combined))
            if post_id in self._seen:
                continue
            self._seen.add(post_id)
            if len(self._seen) > 5000:
                self._seen = set(list(self._seen)[-2500:])

            brand = _extract_brand(combined)
            event = {
                "id": f"reddit_{post_id}",
                "source": "reddit",                        # normalized for frontend filter
                "source_origin": f"Reddit r/{sub}",       # full name for display
                "source_type": "social",
                "brand": brand,
                "headline": title[:200],
                "content": selftext[:1000] if selftext else title,
                "url": f"https://reddit.com{p.get('permalink', '')}",
                "published_at": p.get("created_utc", time.time()),
                "ingested_at": time.time(),
                "score": p.get("score", 0),
                "num_comments": p.get("num_comments", 0),
            }
            await self._queue.put(event)
            self._stats["ingested"] += 1
            logger.debug(f"[Reddit] Ingested: {title[:60]}")


# ─── Hacker News Ingester ─────────────────────────────────────────────────────

class HackerNewsIngester:
    """Monitors Hacker News new stories for tech crises and security alerts."""

    HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/newstories.json"
    HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{id}.json"

    def __init__(self, event_queue: asyncio.Queue, poll_interval: int = 120):
        self._queue = event_queue
        self._poll_interval = poll_interval
        self._seen: Set[int] = set()
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._stats = {"fetched": 0, "ingested": 0, "errors": 0}

    def start(self):
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._poll_loop())
            logger.info("[HackerNews] Ingester started")

    def stop(self):
        self._is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("[HackerNews] Ingester stopped")

    def get_status(self) -> Dict[str, Any]:
        return {
            "source": "Hacker News",
            "is_running": self._is_running,
            "keywords": HN_SEARCH_TERMS,
            **self._stats,
        }

    async def _poll_loop(self):
        while self._is_running:
            try:
                await self._fetch_new_stories()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._stats["errors"] += 1
                logger.warning(f"[HackerNews] Poll error: {e}")
            await asyncio.sleep(self._poll_interval)

    async def _fetch_new_stories(self):
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT, headers=HEADERS) as session:
            try:
                async with session.get(self.HN_TOP_URL) as resp:
                    if resp.status != 200:
                        return
                    story_ids: List[int] = (await resp.json())[:60]
            except Exception as e:
                logger.debug(f"[HackerNews] Failed to fetch story list: {e}")
                return

            new_ids = [sid for sid in story_ids if sid not in self._seen][:20]
            self._stats["fetched"] += len(new_ids)

            tasks = [self._fetch_story(session, sid) for sid in new_ids]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _fetch_story(self, session: aiohttp.ClientSession, story_id: int):
        try:
            async with session.get(self.HN_ITEM_URL.format(id=story_id)) as resp:
                if resp.status != 200:
                    return
                item = await resp.json()
        except Exception:
            return

        if not item or item.get("type") != "story":
            self._seen.add(story_id)
            return

        title = _clean(item.get("title", ""))
        url = item.get("url", "")
        combined = f"{title} {url}"

        self._seen.add(story_id)
        if len(self._seen) > 5000:
            self._seen = set(list(self._seen)[-2500:])

        if not _matches_keywords(combined):
            return

        brand = _extract_brand(combined)
        event = {
            "id": f"hn_{story_id}",
            "source": "news",                              # normalized for frontend filter
            "source_origin": "Hacker News",               # full name for display
            "source_type": "tech_social",
            "brand": brand,
            "headline": title[:200],
            "content": title,
            "url": url or f"https://news.ycombinator.com/item?id={story_id}",
            "published_at": item.get("time", time.time()),
            "ingested_at": time.time(),
            "score": item.get("score", 0),
            "num_comments": item.get("descendants", 0),
        }
        await self._queue.put(event)
        self._stats["ingested"] += 1
        logger.debug(f"[HackerNews] Ingested: {title[:60]}")


# ─── Combined Social Ingester ─────────────────────────────────────────────────

class SocialIngester:
    """Manages Reddit + Hacker News ingesters as a single unit."""

    def __init__(self, event_queue: asyncio.Queue):
        self.reddit = RedditIngester(event_queue, poll_interval=90)
        self.hackernews = HackerNewsIngester(event_queue, poll_interval=120)

    def start(self):
        self.reddit.start()
        self.hackernews.start()
        logger.info("[Social] Reddit + HackerNews ingesters started")

    def stop(self):
        self.reddit.stop()
        self.hackernews.stop()
        logger.info("[Social] Social ingesters stopped")

    def get_status(self) -> Dict[str, Any]:
        return {
            "reddit": self.reddit.get_status(),
            "hackernews": self.hackernews.get_status(),
        }
