"""
MindMesh Real-Time Google News RSS Ingestion Engine
Fetches, deduplicates, and ingests live market and brand news into the pipeline.
"""
import asyncio
import email.utils
import html
import hashlib
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Tuple
from urllib.parse import quote_plus
import aiohttp

from sqlalchemy.orm import Session
from app.database.models import Client, Event

logger = logging.getLogger("mindmesh.rss")

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=12)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

# Monitored queries used for Google News RSS
DEFAULT_QUERIES = [
    "HDFC Bank",
    "SBI Bank",
    "PhonePe",
    "Razorpay",
    "PayU",
    "ICICI Bank",
    "Paytm",
    "RBI regulatory",
    "SEBI compliance",
    "Fintech India banking",
]


def clean_text(raw_html: Optional[str]) -> str:
    """Remove HTML tags and decode HTML entities from text."""
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", "", raw_html)
    return html.unescape(text).strip()


def parse_rfc822_date(date_str: Optional[str]) -> float:
    """Parse RFC 822 / RFC 2822 date into unix timestamp."""
    if not date_str:
        return time.time()
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.timestamp()
    except Exception:
        return time.time()


def normalize_title_for_hash(title: str) -> str:
    """Normalize title to detect near-duplicates across news outlets."""
    t = title.lower()
    # Strip common publisher suffix e.g. " - The Economic Times" or " - Livemint"
    t = re.sub(r"\s*-\s*[^-]+$", "", t)
    # Strip punctuation and extra spaces
    t = re.sub(r"[^\w\s]", "", t)
    return re.sub(r"\s+", " ", t).strip()


class GoogleNewsRSSIngester:
    """
    Continuous & on-demand real-time RSS ingester for Google News.
    Pushes valid, deduplicated news events into the processing queue.
    """

    def __init__(self, event_queue: asyncio.Queue, db_session_factory):
        self.queue = event_queue
        self.db_factory = db_session_factory
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        # In-memory deduplication cache: {article_hash: timestamp}
        self._seen_hashes: Dict[str, float] = {}
        self._seen_urls: Set[str] = set()

        # Source status metrics
        self.status = "INITIALIZING"  # CONNECTED, FAILED, IDLE
        self.last_successful_fetch: Optional[float] = None
        self.last_fetch_attempt: Optional[float] = None
        self.articles_fetched_total = 0
        self.articles_ingested_total = 0
        self.last_article_published: Optional[float] = None
        self.last_error: Optional[str] = None
        self.current_poll_interval = 45  # seconds

    def _get_monitored_brands_and_queries(self) -> Tuple[List[str], Dict[str, str]]:
        """Fetch active client brands and build queries dynamically."""
        db: Session = self.db_factory()
        try:
            clients = db.query(Client).filter(Client.is_active == True).all()
            queries = list(DEFAULT_QUERIES)
            brand_map = {}
            import json
            for c in clients:
                brand_map[c.name.lower()] = c.name
                try:
                    kws = json.loads(c.keywords or "[]")
                    for k in kws:
                        k_str = str(k).strip()
                        if k_str and len(k_str) > 1:
                            brand_map[k_str.lower()] = c.name
                except Exception:
                    pass
                if c.name not in queries:
                    queries.append(c.name)
            return queries, brand_map
        except Exception:
            return DEFAULT_QUERIES, {}
        finally:
            db.close()

    def reset_seen_cache(self):
        """Clear in-memory deduplication cache."""
        self._seen_urls.clear()
        self._seen_hashes.clear()

    def _is_url_or_hash_seen(self, url: str, title: str) -> bool:
        """Check if article has already been processed or stored in DB."""
        if not url and not title:
            return True

        if url in self._seen_urls:
            return True

        norm_title = normalize_title_for_hash(title)
        title_hash = hashlib.sha256(norm_title.encode("utf-8")).hexdigest()
        
        # Check in-memory window (last 24 hours)
        now = time.time()
        if title_hash in self._seen_hashes:
            if now - self._seen_hashes[title_hash] < 86400:
                return True

        # Check against DB
        db: Session = self.db_factory()
        try:
            exists = db.query(Event).filter(
                (Event.url == url) | (Event.headline == title)
            ).first()
            if exists:
                self._seen_urls.add(url)
                self._seen_hashes[title_hash] = now
                return True
        except Exception:
            pass
        finally:
            db.close()

        # Mark as seen
        self._seen_urls.add(url)
        self._seen_hashes[title_hash] = now
        return False

    def _detect_brand(self, title: str, description: str, query: str, brand_map: Dict[str, str]) -> str:
        """Identify which client brand is referenced in the article."""
        q_lower = query.lower()
        if q_lower in brand_map:
            return brand_map[q_lower]

        combined = f"{title} {description} {query}".lower()
        # Check longer keywords first to ensure specific matches take priority
        for b_lower in sorted(brand_map.keys(), key=len, reverse=True):
            if b_lower in combined:
                return brand_map[b_lower]

        # Fallback keyword checks
        for brand in ["HDFC", "SBI", "PhonePe", "Razorpay", "PayU", "Paytm", "Flipkart", "Amazon", "Infosys", "TCS", "ICICI"]:
            if brand.lower() in combined:
                return brand
        if "rbi" in combined:
            return "RBI"
        if "sebi" in combined:
            return "SEBI"
        return "Fintech General"

    async def fetch_feed_for_query(self, query: str) -> Tuple[int, List[Dict[str, Any]]]:
        """Fetch and parse Google News RSS feed for a single search query."""
        q = quote_plus(query)
        url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
        
        print(f"[RSS] Fetching for query: '{query}' -> {url}")
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT, headers=HEADERS) as session:
            async with session.get(url) as resp:
                http_status = resp.status
                print(f"[RSS] HTTP status: {http_status} for query '{query}'")
                if http_status != 200:
                    raise RuntimeError(f"Google News RSS returned HTTP {http_status}")
                xml_bytes = await resp.read()

        root = ET.fromstring(xml_bytes)
        parsed_items = []
        for item in root.findall(".//item"):
            title = clean_text(item.findtext("title"))
            link = item.findtext("link") or ""
            guid = item.findtext("guid") or link
            pub_date_str = item.findtext("pubDate")
            description = clean_text(item.findtext("description"))
            source_elem = item.find("source")
            publisher = source_elem.text.strip() if (source_elem is not None and source_elem.text) else "Google News"
            
            pub_timestamp = parse_rfc822_date(pub_date_str)
            
            parsed_items.append({
                "title": title,
                "link": link,
                "guid": guid,
                "description": description,
                "publisher": publisher,
                "published_at": pub_timestamp,
                "query": query,
            })
        return http_status, parsed_items

    async def poll_once(self) -> Dict[str, Any]:
        """Execute a full polling cycle across all monitored brand queries."""
        self.last_fetch_attempt = time.time()
        queries, brand_map = self._get_monitored_brands_and_queries()
        
        total_received = 0
        newly_ingested = 0
        errors = []

        for query in queries:
            try:
                status_code, items = await self.fetch_feed_for_query(query)
                total_received += len(items)
                print(f"[RSS] Articles received: {len(items)} for query '{query}'")

                for item in items:
                    title = item["title"]
                    link = item["link"]
                    published_at = item["published_at"]
                    publisher = item["publisher"]
                    description = item["description"] or title

                    # Deduplication check
                    if self._is_url_or_hash_seen(link, title):
                        continue

                    # Update latest publish time
                    if not self.last_article_published or published_at > self.last_article_published:
                        self.last_article_published = published_at

                    detected_brand = self._detect_brand(title, description, query, brand_map)
                    
                    # Construct genuine Event payload
                    event_id = f"rss-{hashlib.md5(link.encode('utf-8')).hexdigest()[:12]}"
                    event_payload = {
                        "id": event_id,
                        "source": "news",
                        "source_type": "Google News RSS",
                        "source_origin": "LIVE • Google News RSS",
                        "publisher": publisher,
                        "external_id": link,
                        "timestamp": published_at,
                        "brand": detected_brand,
                        "headline": title,
                        "content": description,
                        "url": link,
                        "language": "en",
                        "location": "India / Global",
                        "created_at": time.time(),
                        "is_live_rss": True,
                    }

                    # Push to processing queue
                    await self.queue.put(event_payload)
                    newly_ingested += 1
                    self.articles_ingested_total += 1

            except Exception as exc:
                err_msg = f"Failed RSS query '{query}': {str(exc)}"
                logger.error(err_msg)
                errors.append(err_msg)

            # Polite delay between query requests
            await asyncio.sleep(0.3)

        self.articles_fetched_total += total_received
        print(f"[RSS] New articles after deduplication: {newly_ingested}")
        print(f"[RSS] Articles sent to processing pipeline: {newly_ingested}")

        if newly_ingested > 0 or total_received > 0:
            self.status = "CONNECTED"
            self.last_successful_fetch = time.time()
            self.last_error = None
        else:
            if errors:
                self.status = "FAILED"
                self.last_error = "; ".join(errors[:2])
            else:
                self.status = "CONNECTED"
                self.last_successful_fetch = time.time()

        return {
            "status": self.status,
            "queries_polled": len(queries),
            "articles_fetched": total_received,
            "articles_new_ingested": newly_ingested,
            "last_successful_fetch": self.last_successful_fetch,
            "last_error": self.last_error,
        }

    async def _background_loop(self):
        """Background loop continuously polling Google News RSS."""
        logger.info("[RSS] Started background polling loop for Google News RSS.")
        while self.is_running:
            try:
                await self.poll_once()
            except Exception as e:
                self.status = "FAILED"
                self.last_error = str(e)
                logger.error(f"[RSS] Background poll error: {e}")

            # Sleep for polling interval
            for _ in range(self.current_poll_interval):
                if not self.is_running:
                    break
                await asyncio.sleep(1)

    def start(self):
        """Start the background RSS polling worker."""
        if not self.is_running:
            self.is_running = True
            self.status = "CONNECTED"
            self._task = asyncio.create_task(self._background_loop())
            logger.info("[RSS] Google News RSS Ingester started.")

    def stop(self):
        """Stop the background RSS polling worker."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
        self.status = "IDLE"
        logger.info("[RSS] Google News RSS Ingester stopped.")

    def get_status_dict(self) -> Dict[str, Any]:
        """Return full health and source metrics."""
        queries, _ = self._get_monitored_brands_and_queries()
        return {
            "source_name": "Google News RSS",
            "status": self.status,
            "is_running": self.is_running,
            "last_successful_fetch": self.last_successful_fetch,
            "last_fetch_attempt": self.last_fetch_attempt,
            "articles_fetched_total": self.articles_fetched_total,
            "articles_ingested_total": self.articles_ingested_total,
            "last_article_published": self.last_article_published,
            "last_error": self.last_error,
            "poll_interval_seconds": self.current_poll_interval,
            "monitored_queries": queries,
        }
