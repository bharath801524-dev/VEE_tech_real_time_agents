"""
Unit tests for MindMesh Risk Engine
"""
import pytest
from app.processing.risk_engine import calculate_risk, risk_level_from_score, RISK_LEVELS


def test_calculate_risk_bounds():
    """Verify that calculate_risk always returns scores bounded in [0, 100]."""
    # Max possible inputs
    score, level, breakdown = calculate_risk(
        topic="Regulatory",
        sentiment="Negative",
        velocity_ratio=10.0,
        client_tier="Tier-1",
        source="news",
        competitor_impact="HIGH",
        confidence=1.0,
    )
    assert 0 <= score <= 100
    assert level == "CRITICAL"
    assert len(breakdown) >= 5
    assert sum(b["score"] for b in breakdown) >= 80

    # Minimal inputs
    score_min, level_min, breakdown_min = calculate_risk(
        topic="General",
        sentiment="Positive",
        velocity_ratio=1.0,
        client_tier="Tier-2",
        source="reddit",
        competitor_impact="LOW",
        confidence=0.5,
    )
    assert 0 <= score_min <= 100
    assert level_min in ("LOW", "MEDIUM")


def test_topic_severities():
    """Regulatory topic must produce higher score than General topic."""
    score_reg, _, _ = calculate_risk(
        topic="Regulatory",
        sentiment="Neutral",
        velocity_ratio=1.0,
        client_tier="Tier-2",
        source="news",
        competitor_impact="LOW",
        confidence=0.9,
    )
    score_gen, _, _ = calculate_risk(
        topic="General",
        sentiment="Neutral",
        velocity_ratio=1.0,
        client_tier="Tier-2",
        source="news",
        competitor_impact="LOW",
        confidence=0.9,
    )
    assert score_reg > score_gen


def test_velocity_multiplier():
    """A 5.0x velocity spike must produce higher score than a 1.0x velocity."""
    score_spike, _, _ = calculate_risk(
        topic="Financial",
        sentiment="Negative",
        velocity_ratio=5.0,
        client_tier="Tier-1",
        source="news",
        competitor_impact="MEDIUM",
        confidence=0.9,
    )
    score_normal, _, _ = calculate_risk(
        topic="Financial",
        sentiment="Negative",
        velocity_ratio=1.0,
        client_tier="Tier-1",
        source="news",
        competitor_impact="MEDIUM",
        confidence=0.9,
    )
    assert score_spike > score_normal


def test_risk_level_mapping():
    """Verify correct risk tier mapping for boundary values."""
    assert risk_level_from_score(95) == "CRITICAL"
    assert risk_level_from_score(81) == "CRITICAL"
    assert risk_level_from_score(75) == "HIGH"
    assert risk_level_from_score(61) == "HIGH"
    assert risk_level_from_score(45) == "MEDIUM"
    assert risk_level_from_score(20) == "LOW"
