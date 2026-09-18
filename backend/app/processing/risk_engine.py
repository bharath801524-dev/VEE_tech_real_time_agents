"""
MindMesh Risk Engine — Transparent, weighted risk scoring (0–100).
Each contributor is tracked separately for display in the UI.
"""
from typing import Dict, Any, List, Tuple
import json


RISK_LEVELS = {
    (81, 100): "CRITICAL",
    (61, 80): "HIGH",
    (31, 60): "MEDIUM",
    (0, 30): "LOW",
}

TOPIC_SEVERITY = {
    "Regulatory": 25,
    "Cybersecurity": 23,
    "Reputation": 20,
    "Financial": 18,
    "Customer Complaints": 14,
    "Product": 15,
    "General": 5,
}

SENTIMENT_IMPACT = {
    "Negative": 20,
    "Neutral": 8,
    "Positive": 0,
}

TIER_WEIGHT = {
    "Tier-1": 15,
    "Tier-2": 7,
}

SOURCE_CREDIBILITY = {
    "news": 14,
    "twitter": 9,
    "reddit": 7,
}


def calculate_risk(
    topic: str,
    sentiment: str,
    velocity_ratio: float,
    client_tier: str,
    source: str,
    competitor_impact: str,
    confidence: float,
) -> Tuple[int, str, List[Dict[str, Any]]]:
    """
    Returns (score, level, breakdown_list).
    breakdown_list is a list of {label, score, description} dicts.
    """
    breakdown: List[Dict[str, Any]] = []

    # 1. Topic severity (0–25)
    topic_score = TOPIC_SEVERITY.get(topic, 5)
    breakdown.append({
        "label": f"{topic} topic severity",
        "score": topic_score,
        "description": f"'{topic}' events carry high operational/reputational weight",
    })

    # 2. Sentiment impact (0–20)
    sent_score = SENTIMENT_IMPACT.get(sentiment, 8)
    if sent_score > 0:
        breakdown.append({
            "label": f"{sentiment} sentiment",
            "score": sent_score,
            "description": "Negative public sentiment amplifies crisis potential",
        })

    # 3. Velocity multiplier (0–20)
    if velocity_ratio > 1.0:
        vel_score = min(int((velocity_ratio - 1.0) * 5.5), 20)
        if vel_score > 0:
            breakdown.append({
                "label": f"{velocity_ratio:.1f}x mention spike",
                "score": vel_score,
                "description": "Rapid mention growth indicates viral spread risk",
            })

    # 4. Client tier (0–15)
    tier_score = TIER_WEIGHT.get(client_tier, 7)
    breakdown.append({
        "label": f"{client_tier} client",
        "score": tier_score,
        "description": "Tier-1 clients have higher visibility and stakeholder expectations",
    })

    # 5. Source credibility (0–14)
    src_score = SOURCE_CREDIBILITY.get(source, 7)
    breakdown.append({
        "label": f"Source: {source}",
        "score": src_score,
        "description": "Credible news sources carry stronger narrative weight",
    })

    # 6. Competitor impact modifier (0–6)
    if competitor_impact == "HIGH":
        breakdown.append({
            "label": "High competitor impact",
            "score": 6,
            "description": "Competitors may capitalise on this event",
        })
    elif competitor_impact == "MEDIUM":
        breakdown.append({
            "label": "Medium competitor impact",
            "score": 3,
            "description": "Some risk of competitor opportunism",
        })

    total = sum(b["score"] for b in breakdown)
    total = max(0, min(100, total))

    # Determine level
    level = "LOW"
    for (lo, hi), lv in RISK_LEVELS.items():
        if lo <= total <= hi:
            level = lv
            break

    return total, level, breakdown


def risk_level_from_score(score: int) -> str:
    for (lo, hi), lv in RISK_LEVELS.items():
        if lo <= score <= hi:
            return lv
    return "LOW"
