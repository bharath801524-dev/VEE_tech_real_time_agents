"""
MindMesh Deduplication & Velocity Detection Engine
"""
import re
import time
import hashlib
from collections import deque, defaultdict
from typing import Dict, Any, Tuple


# ─── Deduplication ────────────────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    """Normalize text for similarity comparison."""
    text = text.lower()
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def compute_hash(text: str) -> str:
    """Compute a content fingerprint."""
    return hashlib.md5(normalize_text(text).encode()).hexdigest()


def shingle(text: str, k: int = 3) -> set:
    """Create word k-grams (shingles) for similarity."""
    words = normalize_text(text).split()
    return set(tuple(words[i:i + k]) for i in range(len(words) - k + 1))


def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


class DeduplicationEngine:
    """
    Tracks recent event hashes and near-duplicate detection via Jaccard similarity.
    Duplicates increment mention counts rather than creating new AI pipeline runs.
    """
    SIMILARITY_THRESHOLD = 0.65
    WINDOW_SECONDS = 600  # 10 minutes dedup window

    def __init__(self):
        # {hash: (timestamp, shingles)}
        self._seen: Dict[str, Tuple[float, set]] = {}
        self._mention_counts: Dict[str, int] = defaultdict(int)

    def _evict_old(self):
        now = time.time()
        expired = [h for h, (ts, _) in self._seen.items() if now - ts > self.WINDOW_SECONDS]
        for h in expired:
            del self._seen[h]

    def check(self, event: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Returns (is_duplicate, canonical_hash, mention_count).
        If is_duplicate=True, just increment the mention count.
        """
        self._evict_old()
        text = f"{event.get('headline', '')} {event.get('content', '')}"
        h = compute_hash(text)

        # Exact match
        if h in self._seen:
            self._mention_counts[h] += 1
            return True, h, self._mention_counts[h]

        # Near-duplicate via Jaccard
        new_shingles = shingle(text)
        for existing_hash, (ts, existing_shingles) in self._seen.items():
            sim = jaccard_similarity(new_shingles, existing_shingles)
            if sim >= self.SIMILARITY_THRESHOLD:
                self._mention_counts[existing_hash] += 1
                return True, existing_hash, self._mention_counts[existing_hash]

        # New event — register
        self._seen[h] = (time.time(), new_shingles)
        self._mention_counts[h] = 1
        return False, h, 1


# ─── Velocity Detection ───────────────────────────────────────────────────────

class VelocityDetector:
    """
    Tracks per-brand mention counts in rolling time windows.
    Calculates velocity ratio = current_window / baseline.
    """
    WINDOW_SECONDS = 300   # 5-minute window
    BASELINE_SECONDS = 3600  # 1-hour baseline

    def __init__(self):
        # {brand: deque of timestamps}
        self._mentions: Dict[str, deque] = defaultdict(deque)

    def _evict(self, brand: str):
        cutoff = time.time() - self.BASELINE_SECONDS
        d = self._mentions[brand]
        while d and d[0] < cutoff:
            d.popleft()

    def record(self, brand: str) -> Tuple[float, str]:
        """Record a mention and return (velocity_ratio, status_label)."""
        now = time.time()
        self._mentions[brand].append(now)
        self._evict(brand)

        window_start = now - self.WINDOW_SECONDS
        baseline_start = now - self.BASELINE_SECONDS

        window_count = sum(1 for ts in self._mentions[brand] if ts >= window_start)
        baseline_count = max(1, sum(1 for ts in self._mentions[brand] if ts >= baseline_start))

        # Normalise: window is 5 min, baseline is 60 min → multiply by 12 for per-period comparison
        normalised_baseline = baseline_count / 12
        ratio = round(window_count / max(normalised_baseline, 1), 2)

        if ratio >= 4.0:
            status = "CRITICAL SPIKE"
        elif ratio >= 2.5:
            status = "SPIKE"
        elif ratio >= 1.5:
            status = "ELEVATED"
        else:
            status = "NORMAL"

        return ratio, status

    def get_baseline(self, brand: str) -> float:
        self._evict(brand)
        baseline_count = max(1, len(self._mentions[brand]))
        return round(baseline_count / 12, 1)
