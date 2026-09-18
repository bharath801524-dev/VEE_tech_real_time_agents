"""
Unit tests for MindMesh Deduplication Engine
"""
import pytest
from app.processing.dedup_velocity import (
    DeduplicationEngine, normalize_text, compute_hash, shingle, jaccard_similarity
)


def test_normalize_text():
    raw = "BREAKING: PayU under RBI scanner!! https://t.co/xyz #fintech @PayU"
    normalized = normalize_text(raw)
    assert "https" not in normalized
    assert "#" not in normalized
    assert "@" not in normalized
    assert "payu under rbi scanner" in normalized


def test_jaccard_similarity():
    s1 = {"payu", "rbi", "audit"}
    s2 = {"payu", "rbi", "audit"}
    assert jaccard_similarity(s1, s2) == 1.0

    s3 = {"flipkart", "sale", "discount"}
    assert jaccard_similarity(s1, s3) == 0.0


def test_deduplication_exact_match():
    engine = DeduplicationEngine()
    event1 = {
        "headline": "RBI initiates special regulatory compliance audit on PayU",
        "content": "Reserve Bank of India has initiated a comprehensive audit of payment aggregator PayU.",
    }
    event2 = {
        "headline": "RBI initiates special regulatory compliance audit on PayU",
        "content": "Reserve Bank of India has initiated a comprehensive audit of payment aggregator PayU.",
    }

    is_dup1, h1, count1 = engine.check(event1)
    assert not is_dup1
    assert count1 == 1

    is_dup2, h2, count2 = engine.check(event2)
    assert is_dup2
    assert h1 == h2
    assert count2 == 2


def test_deduplication_near_duplicate():
    engine = DeduplicationEngine()
    event1 = {
        "headline": "RBI initiates special regulatory compliance audit on PayU India payments aggregator",
        "content": "Reserve Bank of India initiates special audit on payment gateway PayU India.",
    }
    event2 = {
        "headline": "RBI initiates special regulatory compliance audit on PayU India payments aggregator team",
        "content": "Reserve Bank of India initiates special audit on payment gateway PayU India.",
    }

    is_dup1, h1, count1 = engine.check(event1)
    assert not is_dup1
    assert count1 == 1

    is_dup2, h2, count2 = engine.check(event2)
    assert is_dup2
    assert count2 == 2
