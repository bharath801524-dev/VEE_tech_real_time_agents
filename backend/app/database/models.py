import time
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.session import Base

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    tier = Column(String(50), default="Tier-1")  # Tier-1, Tier-2
    keywords = Column(Text, default="[]")  # JSON list of keywords
    competitors = Column(Text, default="[]")  # JSON list of competitors
    is_active = Column(Boolean, default=True)
    created_at = Column(Float, default=time.time)

class Event(Base):
    __tablename__ = "events"
    
    id = Column(String(100), primary_key=True, index=True)
    source = Column(String(50), index=True)  # news, twitter, reddit
    external_id = Column(String(200), nullable=True)
    timestamp = Column(Float, default=time.time, index=True)
    brand = Column(String(100), index=True)
    headline = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(1000), nullable=True)
    publisher = Column(String(100), nullable=True)
    source_origin = Column(String(100), default="LIVE • Google News RSS")
    language = Column(String(20), default="en")
    location = Column(String(100), default="Global")
    created_at = Column(Float, default=time.time)
    
    # Relationships
    processed = relationship("ProcessedEvent", back_populates="event", uselist=False)
    ai_analysis = relationship("AIAnalysis", back_populates="event", uselist=False)
    risk_score = relationship("RiskScore", back_populates="event", uselist=False)
    insight = relationship("CrisisInsight", back_populates="event", uselist=False)
    sla_metric = relationship("SLAMetric", back_populates="event", uselist=False)

class ProcessedEvent(Base):
    __tablename__ = "processed_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), ForeignKey("events.id"), index=True)
    normalized_hash = Column(String(100), index=True)
    mention_count = Column(Integer, default=1)
    velocity_ratio = Column(Float, default=1.0)
    velocity_status = Column(String(50), default="NORMAL")  # NORMAL, ELEVATED, SPIKE, CRITICAL SPIKE
    is_duplicate = Column(Boolean, default=False)
    created_at = Column(Float, default=time.time)
    
    event = relationship("Event", back_populates="processed")

class AIAnalysis(Base):
    __tablename__ = "ai_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), ForeignKey("events.id"), index=True)
    client = Column(String(100))
    client_tier = Column(String(50))
    topic = Column(String(100))  # Regulatory, Financial, Product, Customer Complaints, Cybersecurity, Reputation
    sentiment = Column(String(50))  # Positive, Neutral, Negative
    sentiment_score = Column(Float)  # -1.0 to 1.0
    risk_level = Column(String(50))  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Integer)  # 0-100
    competitor_impact = Column(String(50))  # LOW, MEDIUM, HIGH
    urgency = Column(String(50))  # LOW, MEDIUM, HIGH, CRITICAL
    confidence = Column(Float)  # 0.0 to 1.0
    created_at = Column(Float, default=time.time)
    
    event = relationship("Event", back_populates="ai_analysis")

class RiskScore(Base):
    __tablename__ = "risk_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), ForeignKey("events.id"), index=True)
    total_score = Column(Integer)
    risk_level = Column(String(50))
    breakdown_json = Column(Text)  # JSON array of score contributors
    created_at = Column(Float, default=time.time)
    
    event = relationship("Event", back_populates="risk_score")

class CrisisInsight(Base):
    __tablename__ = "crisis_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), ForeignKey("events.id"), index=True)
    what_happened = Column(Text)
    why_it_matters = Column(Text)
    recommended_action = Column(Text)
    priority = Column(String(50))
    recommended_team = Column(String(100))  # PR + Legal, Customer Support, etc.
    action_checklist_json = Column(Text)  # JSON array of actions
    competitor_reaction = Column(Text, nullable=True)
    generated_at = Column(Float, default=time.time)
    
    event = relationship("Event", back_populates="insight")

class CrisisEvent(Base):
    __tablename__ = "crisis_events"
    
    id = Column(String(100), primary_key=True, index=True)
    event_id = Column(String(100), ForeignKey("events.id"), index=True)
    brand = Column(String(100), index=True)
    headline = Column(String(500))
    topic = Column(String(100))
    risk_score = Column(Integer)
    risk_level = Column(String(50))
    mentions = Column(Integer, default=1)
    velocity_ratio = Column(Float, default=1.0)
    sentiment = Column(String(50))
    status = Column(String(50), default="ACTIVE")  # ACTIVE, INVESTIGATING, RESOLVED
    detected_at = Column(Float, default=time.time)
    created_at = Column(Float, default=time.time)
    
    alerts = relationship("Alert", back_populates="crisis")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(String(100), primary_key=True, index=True)
    crisis_id = Column(String(100), ForeignKey("crisis_events.id"), nullable=True)
    event_id = Column(String(100), ForeignKey("events.id"))
    channel = Column(String(50))  # in_app, slack, email, sms
    alert_level = Column(String(50))  # HIGH, CRITICAL
    payload_json = Column(Text)
    sent_at = Column(Float, default=time.time)
    status = Column(String(50), default="DELIVERED")  # DELIVERED, FAILED, SUPPRESSED
    
    crisis = relationship("CrisisEvent", back_populates="alerts")

class SLAMetric(Base):
    __tablename__ = "sla_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), ForeignKey("events.id"), index=True)
    crisis_id = Column(String(100), nullable=True)
    ingest_timestamp = Column(Float)
    triage_timestamp = Column(Float)
    risk_timestamp = Column(Float)
    insight_timestamp = Column(Float)
    alert_timestamp = Column(Float)
    
    total_latency_seconds = Column(Float)
    triage_latency_seconds = Column(Float)
    risk_latency_seconds = Column(Float)
    insight_latency_seconds = Column(Float)
    alert_latency_seconds = Column(Float)
    
    sla_passed = Column(Boolean, default=True)
    target_seconds = Column(Integer, default=120)
    created_at = Column(Float, default=time.time)
    
    event = relationship("Event", back_populates="sla_metric")

class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text)
