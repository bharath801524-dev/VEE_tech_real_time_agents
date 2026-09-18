"""
Unit tests for MindMesh Velocity Detector
"""
import time
import pytest
from app.processing.dedup_velocity import VelocityDetector


def test_velocity_single_mention():
    detector = VelocityDetector()
    ratio, status = detector.record("PayU")
    assert ratio >= 1.0
    assert status in ("NORMAL", "ELEVATED", "SPIKE", "CRITICAL SPIKE")


def test_velocity_spike_detection():
    detector = VelocityDetector()
    # Record multiple mentions in rapid succession
    for _ in range(25):
        ratio, status = detector.record("PayU")

    # High frequency in current 5-min window must cause spike
    assert ratio >= 2.5
    assert status in ("SPIKE", "CRITICAL SPIKE")


def test_velocity_baseline_tracking():
    detector = VelocityDetector()
    detector.record("Flipkart")
    baseline = detector.get_baseline("Flipkart")
    assert baseline >= 0.0
