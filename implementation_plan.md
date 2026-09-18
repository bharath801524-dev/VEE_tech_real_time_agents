# Implementation Plan - MindMesh: 2-Minute AI Crisis Response Platform

MindMesh transforms media intelligence from 5–6 hour batch reporting to continuous, under-2-minute (<120s SLA) crisis detection, AI-powered triage, risk quantification, business impact briefings, and automated response orchestration.

## Architecture Overview

```
[ Data Sources: News / X / Reddit / Simulator ]
                      │
                      ▼
            [ Ingestion Service ]
       (Normalizer -> Source Adapters)
                      │
                      ▼
             [ Message Queue ]
             (asyncio.Queue)
                      │
                      ▼
         [ Pre-Filter & Deduplication ]
     (Monitored Brands + SimHash/Grouping)
                      │
                      ▼
        [ Velocity & Anomaly Engine ]
        (Rolling Window Spike Detection)
                      │
                      ▼
             [ AI Triage Agent ]
      (Brand, Topic, Sentiment, Urgency)
                      │
                      ▼
             [ Risk Engine (0-100) ]
  (Transparent Breakdown: Topic + Velocity + Sentiment)
                      │
                      ▼
          [ 2-Minute Insight Agent ]
   (What Happened, Why It Matters, Briefing)
                      │
                      ▼
     [ Response Recommendation Agent ]
      (Team Escalation + Action Checklist)
                      │
                      ▼
           [ Alert Rules Engine ]
     (Fatigue Prevention, Cooldown, Routing)
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
[ Alert Channels ]      [ Real-Time WebSocket Hub ]
(In-app, Slack, Email)           │
                                 ▼
                    [ React + Vite Dashboard ]
         (Live Feed, Crisis Center, SLA Monitor, Analytics)
```

---

## Proposed Implementation Steps

### Phase 1: Backend Foundation & Database Models
1. **Directory Structure**:
   `backend/` with `app/` modules:
   - `database/`: SQLite engine with SQLAlchemy ORM models:
     - `Client`: Monitored brands, tiers, keywords, competitors.
     - `Event`: Ingested articles/posts (source, brand, headline, content, url, timestamp).
     - `ProcessedEvent`: Deduplicated groups, mention counts, velocity ratio.
     - `CrisisEvent`: Escalated high/critical crises with status (ACTIVE, INVESTIGATING, RESOLVED).
     - `AIAnalysis`: Triage classification results (sentiment, topic, urgency, confidence, risk score).
     - `CrisisInsight`: "What Happened", "Why It Matters", "Recommended Actions".
     - `Alert`: Dispatched alerts, channels, status, fatigue group ID.
     - `SLAMetric`: Ingest, Triage, Risk, Insight, and Alert timestamps; elapsed seconds; pass/breach flag.
     - `SystemSetting`: Runtime toggles (Demo vs Live mode, risk threshold, cooldown seconds).
   - `models/`: Pydantic schemas for request/response validation and WebSocket event payloads.

### Phase 2: Ingestion, Deduplication & Velocity Pipeline
1. **Source Adapters**:
   - `SourceAdapter` base class.
   - `DemoStreamAdapter`: Generates realistic news headlines and social posts at regular intervals (with occasional background noise and configurable scenarios).
   - `NewsAdapter`, `TwitterAdapter`, `RedditAdapter` (with live API capability if `.env` keys exist, falling back gracefully to demo generator).
2. **Pre-Filter Engine**:
   - Fast keyword and brand entity matching against configured client portfolio.
3. **Deduplication Engine**:
   - Text normalization, min-hash/token similarity check.
   - Identical/near-identical items increment existing event's `mention_count` instead of flooding downstream AI agents.
4. **Velocity & Spike Detection**:
   - Sliding 5-minute rolling window.
   - Baseline volume vs current volume calculation.
   - Velocity categories: `NORMAL` (1.0x), `ELEVATED` (1.5x-2.5x), `SPIKE` (2.5x-4.0x), `CRITICAL SPIKE` (>4.0x).

### Phase 3: AI Agents & Risk Scoring Engine
1. **AI Provider Abstraction (`AIProvider`)**:
   - `DemoAIProvider`: High-fidelity deterministic NLP classification matching crisis scenarios (sentiment, topic, urgency, client tier) with realistic processing latency.
   - `LLMProvider`: Gemini / OpenAI / Anthropic integration via generic HTTP client when `AI_API_KEY` is provided.
2. **Triage Agent**:
   - Classifies: Client Mention, Client Tier (Tier-1, Tier-2), Topic (Regulatory, Financial, Product, Cybersecurity, Reputation), Sentiment (-1.0 to +1.0), Urgency (LOW, MEDIUM, HIGH, CRITICAL), Confidence.
3. **Transparent Risk Engine**:
   - Transparent scoring formula:
     $$\text{Risk Score} = \text{Topic Severity} (0\text{-}25) + \text{Sentiment Impact} (0\text{-}20) + \text{Velocity Multiplier} (0\text{-}20) + \text{Client Tier} (0\text{-}20) + \text{Source Credibility} (0\text{-}15)$$
   - Produces 0–100 score + explicit array of contributors (e.g., `+25 Regulatory issue`, `+20 4.8x mention spike`).
4. **2-Minute Insight Agent**:
   - Generates structured narrative:
     - **WHAT HAPPENED** (concise summary)
     - **WHY IT MATTERS** (reputational, regulatory, customer, or financial impact)
     - **RISK SUMMARY** (severity level + score)
     - **RECOMMENDED ACTION** (high-level directive)
5. **Response Recommendation Agent**:
   - Determines: Priority, Recommended Team (PR, Legal, Customer Support, Security), and step-by-step actionable checklist.

### Phase 4: Alert Engine, Fatigue Prevention & SLA Monitoring
1. **Intelligent Alert Rules**:
   - Threshold evaluation: Risk $\ge 80 \to$ CRITICAL ALERT; Risk $\ge 60 \to$ HIGH ALERT; Tier-1 client automatic alert flag.
2. **Fatigue Prevention**:
   - 5-minute cooldown per crisis topic/client.
   - Event grouping: Aggregates mentions rather than spamming alerts.
3. **Alert Channels**:
   - In-app WebSocket notification (always active).
   - Slack webhook, Email, SMS (Twilio) channels with fallback mock logs if unconfigured.
4. **SLA Monitoring Engine**:
   - Precise timing checkpoints:
     $T_{\text{ingest}} \to T_{\text{triage}} \to T_{\text{risk}} \to T_{\text{insight}} \to T_{\text{alert}}$
   - Latency calculation: $\Delta T = T_{\text{alert}} - T_{\text{ingest}}$.
   - Validates whether $\Delta T \le 120\text{ seconds}$.
   - Aggregates rolling statistics: Compliance %, P50, P95, P99, Total Breaches.

### Phase 5: REST API, WebSockets & Demo Simulation Control
1. **FastAPI Endpoints**:
   - `GET /api/kpi`: Overview stats (Critical alerts, high-risk events, articles monitored, avg response time, SLA compliance %, missed alerts).
   - `GET /api/events`: Live feed with pagination and brand/risk/source filters.
   - `GET /api/crises`: Filtered list of escalated crisis items.
   - `GET /api/crises/{id}`: Detailed crisis breakdown including SLA stage milestones, AI insights, contributor breakdown, competitor reaction, related posts.
   - `GET /api/analytics`: Time-bucketed charts (mentions over time, sentiment ratio, risk breakdown, source shares, top topics).
   - `GET /api/sla`: SLA latency distribution, breach logs, percentile metrics.
   - `GET /api/clients`, `POST /api/clients`, `DELETE /api/clients/{id}`: Client portfolio management.
   - `GET /api/settings`, `PUT /api/settings`: Alert thresholds, mode toggles, notification channel toggles.
   - `POST /api/demo/simulate`: Trigger predetermined crisis scenarios (Regulatory RBI, Product Outage, or Normal News).
   - `POST /api/demo/toggle-stream`: Start/stop background demo streamer.
2. **WebSocket Hub (`/ws/live`)**:
   - Broadcasts real-time events: `NEW_EVENT`, `TRIAGE_UPDATE`, `CRISIS_DETECTED`, `ALERT_TRIGGERED`, `SLA_UPDATE`, `KPI_UPDATE`.

### Phase 6: Frontend Development (React + TypeScript + Vite + Tailwind CSS)
1. **Design System & Theme**:
   - Modern enterprise crisis intelligence UI: Dark theme (`#0B0F19`, `#111827`), high-contrast accents, crisp status indicators (Green `emerald-500`, Amber `amber-500`, Red `rose-500`, Violet `violet-500`).
   - Lucide icons, glassmorphism cards, micro-animations, mobile-responsive layout with bottom/drawer navigation.
2. **Key Views**:
   - **Main Dashboard**:
     - Status Header: 🟢 SYSTEM ONLINE, Monitoring 24/7, Mode Badge, Quick Scenario trigger buttons.
     - Top KPI Cards (Critical Alerts, High-Risk Events, Monitored Volume, Average Response Time, SLA Compliance %, Missed Alerts).
     - Live Active Crisis Banner / SLA Countdown timer (animating Ingest $\to$ Alert in seconds).
     - System Health Monitor & AI Agent Status panels.
     - Traditional vs MindMesh Comparison Table.
     - Recent Live Events strip.
   - **Live Crisis Feed**:
     - Real-time streaming list of incoming events with risk badge, sentiment indicator, velocity badge, client tag, source icon.
     - Mention counter (`1,248 mentions`) on deduplicated cards.
     - Quick filter by Brand, Source, Topic, and Risk Level.
   - **Crisis Center**:
     - High/Critical crises matrix (Crisis title, Client, Risk score, Mentions, Velocity ratio, Detected time, SLA status, Active status).
     - Clicking any row opens the deep-dive Crisis Detail view.
   - **Crisis Detail Modal / Page**:
     - Comprehensive breakdown:
       - Header with SLA Pass/Breach badge and total response time.
       - Interactive horizontal SLA Stage Timeline ($T_{\text{ingest}} \to T_{\text{triage}} \to T_{\text{insight}} \to T_{\text{alert}}$).
       - AI Triage Attributes (Sentiment, Topic, Urgency, Confidence, Competitor Impact).
       - Transparent Risk Score Breakdown with contributor weights.
       - "What Happened" & "Why It Matters" briefing card.
       - Response Recommendation Action Checklist.
       - Related Coverage and Competitor Reactions.
   - **SLA Monitor Page**:
     - SLA gauge/target compliance (98.7%), P50/P95/P99 latency stats, Breaches count.
     - Real-time latency chart across recent crises.
     - Historical SLA audit table with stage timestamps and pass/fail indicators.
   - **Analytics Page**:
     - Time range switcher (15m, 1h, Today, 7d).
     - Mentions volume time series (Recharts).
     - Sentiment distribution doughnut chart.
     - Risk level distribution bar chart.
     - Topic frequency & Velocity spike charts.
     - Geographic Heatmap / Mentions by Region (Mumbai, Bengaluru, Delhi, etc.).
   - **Settings Page**:
     - Monitored Clients CRUD (Add/Edit brand name, tier, keywords, competitors).
     - Alert Rules configuration (risk threshold slider, cooldown minutes, tier-1 override).
     - Notification Channels toggle (In-app, Slack, Email, SMS).
     - System Mode switch (Demo Mode vs Live Mode).
   - **Mobile-First Experience**:
     - Streamlined mobile crisis cards with 3-tap actionability ("🚨 CRITICAL PayU — View Crisis").
     - Collapsible/bottom navigation.

### Phase 7: Verification & Testing
1. **Backend Unit Tests (`pytest`)**:
   - Risk scoring formula calculations.
   - Deduplication and mention incrementing logic.
   - Velocity detection rolling window.
   - SLA duration calculation and breach checks.
   - Alert rules engine & fatigue cooldown.
2. **Integration Pipeline Test**:
   - Ingest $\to$ Filter $\to$ Deduplicate $\to$ Triage $\to$ Risk $\to$ Insight $\to$ Alert dispatch $\to$ SLA validation.
3. **End-to-End Simulation Run**:
   - Trigger Demo Scenario 1 (Regulatory), Scenario 2 (Outage), and Scenario 3 (Normal).
   - Verify WebSocket messages received on frontend in real time.
   - Verify SLA timer accurately reflects $< 60$ seconds in demo mode.

---

## User Review Required

> [!IMPORTANT]
> - We will build the backend using Python 3.12 (via `py -3.12-32`) and frontend using React 18 / 19 + TypeScript + Vite + Tailwind CSS.
> - The application will include zero mandatory external dependencies so it runs out-of-the-box in Demo Mode, while seamlessly reading `.env` variables for live APIs (Gemini/OpenAI, NewsAPI, Twitter, Slack, Twilio) when provided.
> - A complete `docker-compose.yml`, `README.md`, and unit tests will be included.

---

## Verification Plan

### Automated Tests
- Run `pytest backend/tests` to verify:
  - `test_risk_engine.py`: Correct score weights and bounds (0-100).
  - `test_deduplication.py`: Duplicate detection and count aggregation.
  - `test_velocity.py`: Baseline vs current spike calculations.
  - `test_sla.py`: Stage latency and $\le 120$s compliance flag.
  - `test_pipeline.py`: End-to-end event flow.

### Manual Verification via Browser
- Launch FastAPI backend (`http://localhost:8000`) and React frontend (`http://localhost:5173`).
- Open the dashboard in browser.
- Verify real-time event streaming over WebSocket.
- Click **"START CRISIS SIMULATION"** on "Scenario 1: RBI Audit of PayU".
- Watch the live timeline progress: Ingest $\to$ Triage $\to$ Risk $\to$ Insight $\to$ Alert in $<60$ seconds.
- Inspect the Crisis Detail modal: Verify AI briefing ("What Happened", "Why It Matters"), transparent risk score (+25, +20, etc.), and response checklist.
- Trigger "Scenario 3: Normal News" and confirm no false-positive crisis alerts occur.
- Test client management (add/remove brands) in Settings.
- Test mobile responsive layout.
