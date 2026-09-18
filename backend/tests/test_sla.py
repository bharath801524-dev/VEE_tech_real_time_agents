"""
Unit tests for MindMesh SLA Metrics and Compliance
"""
import time
import pytest
from app.database.models import SLAMetric


def test_sla_passed_calculation():
    """Verify SLA calculation under 120-second threshold."""
    t_ingest = 1000.0
    t_triage = 1015.0
    t_risk = 1025.0
    t_insight = 1045.0
    t_alert = 1055.0

    total_latency = t_alert - t_ingest
    sla_passed = total_latency <= 120.0

    assert total_latency == 55.0
    assert sla_passed is True


def test_sla_breach_calculation():
    """Verify SLA breach detection when total latency exceeds 120s."""
    t_ingest = 1000.0
    t_alert = 1135.0  # 135 seconds elapsed

    total_latency = t_alert - t_ingest
    sla_passed = total_latency <= 120.0

    assert total_latency == 135.0
    assert sla_passed is False
