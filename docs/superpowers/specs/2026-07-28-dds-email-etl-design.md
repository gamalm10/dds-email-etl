# DDS Email ETL & BI System — Design Spec

## 1. Overview

**Purpose:** Automatically ingest, parse, and analyze DDS (Demand/Supply) status emails sent by Mohamed Weheba (mohamed.weheba@a-part.com) twice a week. Extract structured data for Power BI dashboards tracking supply chain status, tasks, responsibilities, delays, and process issues.

**Source:** Existing email account accessible via IMAP. Emails have subject pattern `DDS-dd-mm-yyyy` and contain an HTML table (Microsoft Word generated) with supply chain status.

**Output:** Normalized MariaDB tables consumed by Microsoft Power BI for bidirectional dashboards.

## 2. Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Docker Compose                         │
│                                                          │
│  ┌──────────────────────────┐  ┌───────────────────────┐ │
│  │  dds-api (Python/FastAPI)│  │  dds-pi (Node.js)     │ │
│  │                          │  │                       │ │
│  │  • IMAP IDLE listener    │  │  pi --mode rpc        │ │
│  │  • Email parser          │◄─┤  --no-session         │ │
│  │  • REST API              │  │  gpt-5.4-mini         │ │
│  │  • SidecarManager        │  │  text-embedding-3     │ │
│  │  • SQLAlchemy ORM        │  └───────────────────────┘ │
│  └───────────┬──────────────┘                            │
│              │                                           │
│  ┌───────────▼──────────────┐                            │
│  │  dds-db (MariaDB 11)     │                            │
│  │  Port 3307 (Power BI)    │                            │
│  └──────────────────────────┘                            │
│                                                          │
│  IMAP ──► IDLE push ──► FastAPI background task          │
│  HTTP ──► REST API ──► manual trigger / CRUD / view      │
│  Power BI ◄── MariaDB (DirectQuery/Import)               │
└──────────────────────────────────────────────────────────┘
```

### Container Responsibilities

| Container | Base | Role |
|---|---|---|
| `dds-api` | python:3.12 | FastAPI app, IMAP IDLE, REST API, sidecar manager, pipeline orchestration |
| `dds-pi` | node:22 | PI SDK RPC agent, LLM extraction via gpt-5.4-mini, embeddings via text-embedding-3-small |
| `dds-db` | mariadb:11 | Data storage, Power BI target |

### Communication

- Python ↔ PI sidecar: JSON-RPC over stdio (native PI RPC protocol)
- Python ↔ MariaDB: async via SQLAlchemy + aiomysql
- Power BI ↔ MariaDB: native MariaDB connector on port 3307

## 3. Database Schema

### 3.1 dds_brands — Brand master table

```sql
CREATE TABLE dds_brands (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    division        VARCHAR(100) NOT NULL,
    brand_category  VARCHAR(255) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_brand (division, brand_category)
);
```

One row per tracked brand (e.g., "Passenger / PHC Clutch", "Battery / Banner"). Linked across reports so history tracking works by brand, not by text match.

### 3.2 dds_reports — Each email received

```sql
CREATE TABLE dds_reports (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    subject           VARCHAR(255) NOT NULL,
    report_date       DATE NOT NULL,
    sender            VARCHAR(255),
    recipients        TEXT,
    cc_list           TEXT,
    received_at       DATETIME NOT NULL,
    raw_html          LONGTEXT,
    raw_text          LONGTEXT,
    processing_status ENUM('pending','processing','completed','failed') DEFAULT 'pending',
    error_message     TEXT,
    report_week       INT GENERATED ALWAYS AS (WEEK(report_date, 1)) STORED,
    report_year       INT GENERATED ALWAYS AS (YEAR(report_date)) STORED,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_report_date (report_date),
    INDEX idx_processing_status (processing_status),
    INDEX idx_report_week (report_year, report_week)
);
```

`report_date` is extracted from subject `DDS-dd-mm-yyyy`. `raw_html` stores the full email body for re-processing. Generated columns for week/year enable weekly trend analysis in Power BI.

### 3.3 dds_report_items — Each table row in the email

```sql
CREATE TABLE dds_report_items (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    report_id           INT NOT NULL,
    brand_id            INT NOT NULL,
    availability_status ENUM('green','yellow','red','grey','black','unknown') DEFAULT 'unknown',
    milestone           TEXT,
    milestone_ar        TEXT,
    shipment_bis        TEXT,
    comments_actions    TEXT,
    comments_actions_ar TEXT,
    language            VARCHAR(10) DEFAULT 'en',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    INDEX idx_report_id (report_id),
    INDEX idx_brand_id (brand_id),
    INDEX idx_availability (availability_status)
);
```

Each row in the email table becomes one `dds_report_item`. The `comments_actions` field stores the raw text before LLM extraction, enabling re-extraction without re-reading the email.

### 3.4 dds_status_history — Status changes per brand across reports

```sql
CREATE TABLE dds_status_history (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    brand_id        INT NOT NULL,
    report_id       INT NOT NULL,
    previous_status VARCHAR(50),
    current_status  VARCHAR(50),
    status_change   VARCHAR(20) GENERATED ALWAYS AS (
        CASE
            WHEN previous_status IS NULL THEN 'new'
            WHEN previous_status = current_status THEN 'unchanged'
            WHEN current_status IN ('green','yellow') AND previous_status IN ('red','grey','black') THEN 'improved'
            WHEN current_status IN ('red','grey','black') AND previous_status IN ('green','yellow') THEN 'worsened'
            ELSE 'changed'
        END
    ) STORED,
    days_since_last_report INT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    FOREIGN KEY (report_id) REFERENCES dds_reports(id),
    INDEX idx_brand_history (brand_id, report_id)
);
```

Auto-generated `status_change` column enables direct filtering in Power BI (e.g., "show all brands that worsened this week").

### 3.5 dds_tasks — Extracted tasks with cross-report carry-over

```sql
CREATE TABLE dds_tasks (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    report_item_id        INT NOT NULL,
    task_description      TEXT NOT NULL,
    assigned_to           VARCHAR(255),
    deadline              DATE,
    task_category         VARCHAR(100),
    task_status           VARCHAR(50) DEFAULT 'open',
    priority              VARCHAR(20) DEFAULT 'medium',
    language              VARCHAR(10) DEFAULT 'en',
    first_seen_report_id  INT,
    last_seen_report_id   INT,
    occurrence_count      INT DEFAULT 1,
    is_resolved           BOOLEAN DEFAULT FALSE,
    resolved_at_report_id INT,
    embedding             BLOB,
    FOREIGN KEY (report_item_id) REFERENCES dds_report_items(id) ON DELETE CASCADE,
    FOREIGN KEY (first_seen_report_id) REFERENCES dds_reports(id),
    FOREIGN KEY (last_seen_report_id) REFERENCES dds_reports(id),
    INDEX idx_assigned_to (assigned_to),
    INDEX idx_deadline (deadline),
    INDEX idx_task_category (task_category),
    INDEX idx_task_status (task_status)
);
```

Cross-report tracking is done by task_description + brand_id matching. If the same task text appears for the same brand in a new report, `occurrence_count` increments and `last_seen_report_id` updates. Tasks appearing in 3+ reports without resolution are flagged as chronic.

### 3.6 dds_insights — Analysis output

```sql
CREATE TABLE dds_insights (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    report_id       INT NOT NULL,
    brand_id        INT,
    insight_type    VARCHAR(50),
    description     TEXT NOT NULL,
    description_ar  TEXT,
    language        VARCHAR(10) DEFAULT 'en',
    severity        VARCHAR(20),
    anomaly_score   DECIMAL(5,4),
    matched_anomaly_id INT,
    related_task_id INT,
    embedding       BLOB,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    FOREIGN KEY (matched_anomaly_id) REFERENCES dds_insights(id),
    INDEX idx_insight_type (insight_type),
    INDEX idx_severity (severity),
    INDEX idx_anomaly_score (anomaly_score)
);
```

Insight types include: `recurring_delay`, `status_degradation`, `blocked_item`, `aging_task`, `process_bottleneck`, `supplier_failure`, `pricing_issue`, `market_risk`, `recurring_pattern`.

### 3.7 dds_anomaly_log — Embedding similarity detections

```sql
CREATE TABLE dds_anomaly_log (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    source_insight_id   INT NOT NULL,
    matched_insight_id  INT NOT NULL,
    similarity_score    DECIMAL(5,4) NOT NULL,
    source_report_id    INT NOT NULL,
    matched_report_id   INT NOT NULL,
    detected_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_reviewed         BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (source_insight_id) REFERENCES dds_insights(id) ON DELETE CASCADE,
    FOREIGN KEY (matched_insight_id) REFERENCES dds_insights(id),
    INDEX idx_similarity_score (similarity_score),
    INDEX idx_detected_at (detected_at)
);
```

### 3.8 dds_processing_log — Processing audit trail

```sql
CREATE TABLE dds_processing_log (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    report_id   INT NOT NULL,
    step        VARCHAR(50),
    status      VARCHAR(20),
    message     TEXT,
    duration_ms INT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    INDEX idx_report_step (report_id, step)
);
```

## 4. LLM Extraction Pipeline

### 4.1 DDS Analyst Agent (System Prompt)

When the PI SDK sidecar receives a process request, it creates a session with this system prompt override:

```
You are a DDS (Demand/Supply) email analyst for A-part automotive supply chain.
Process DDS status emails and extract structured data.

Each email contains an HTML table with these columns:
  Division | Brand/Category | Availability (color-coded) | Milestone | Shipment/BIS (ETD-ETA) | Comments/Actions

Your job:
1. Parse each table row into structured JSON
2. From Comments/Actions, extract tasks with: description, assigned_to, deadline, category
   - Known team members: Nancy, Max, Amir, Weheba, Haytham, Alaa, Sherif, Bassem
   - Categories: pricing, shipping, ordering, payment, supplier_escalation, market_analysis, clearance, documentation, alternative_sourcing
3. Identify process issues and delays
4. Classify insights with severity (critical/major/minor/info)
5. Detect Arabic content: if a cell contains Arabic text, include it in `*_ar` fields and set `language` to `ar` or `mixed`

Output MUST be valid JSON in this exact structure:
```json
{
  "items": [
    {
      "division": "Passenger",
      "brand_category": "PHC Clutch",
      "availability": "green",
      "milestone": "In Transit",
      "shipment_bis": "23.07-24.08-07.09",
      "comments_actions": "Order sent to supplier - Nancy",
      "tasks": [
        {
          "description": "Order sent to supplier / waiting for PI",
          "assigned_to": "Nancy",
          "deadline": null,
          "category": "ordering"
        }
      ],
      "insights": [
        {
          "type": "status_degradation",
          "description": "PHC Clutch changed from In Prod to Pending",
          "severity": "minor"
        }
      ]
    }
  ],
  "summary": {
    "priority_tasks": [],
    "key_highlights": [],
    "sales_timeline": {}
  }
}
```
```

### 4.2 Two-Stage Processing

**Stage 1 — PI Agent (gpt-5.4-mini):**
- Receive raw email HTML + optional previous report context
- System prompt acts as the DDS analyst
- Returns structured JSON: items, tasks, insights

**Stage 2 — Python Post-Processing (after storage):**
- Status delta: compare each item's availability with previous report → `dds_status_history`
- Task carry-over: match task text + brand against existing open tasks → increment or create new
- Deadline slip detection: if same task has later deadline in new report → flag as insight
- Aging analysis: tasks open across 3+ reports → `aging_task` insight
- Embedding computation: send task/insight descriptions to PI sidecar for `text-embedding-3-small` → store BLOB
- Anomaly detection: compare new insight embeddings against historical (cosine sim > 0.85) → `dds_anomaly_log`
- Language detection: identify Arabic content in cells, populate `*_ar` columns, set `language` flag
- Notification trigger: if critical severity insights detected → send email alert (rate-limited per brand)

### 4.3 Embeddings

- Task descriptions and insight descriptions are sent to the PI sidecar for `text-embedding-3-small` embedding
- Stored as BLOB in `dds_tasks.embedding` and `dds_insights.embedding`
- Used for similarity search across reports (e.g., "find all pricing-related issues")

### 4.4 Anomaly Detection via Embedding Similarity

After each email processing completes:

1. For each new insight in `dds_insights`, compute its embedding via the PI sidecar
2. Compare against all previous insight embeddings using cosine similarity
3. If similarity > 0.85 with a past insight, log to `dds_anomaly_log` with the matching IDs and score
4. If the matched past insight was `critical` or `major` severity, the new insight gets `anomaly_score` > 0 and insight_type = `recurring_pattern`
5. High-scoring anomalies trigger an email notification (see Section 11)

This catches recurring patterns automatically — e.g., "ATE/Febi supplier cancelled order" in week 1 and "Supplier cancelled AGAIN" in week 2 produce embeddings that score >0.85 similarity.

### 4.5 Multi-Language Support (Arabic)

DDS emails frequently contain Arabic text in the Comments/Actions and Milestone columns. The PI agent system prompt is updated to:

1. Detect mixed-language content (Arabic + English in same cell)
2. Extract Arabic text into `*_ar` columns alongside English
3. Set `language` column to `en`, `ar`, or `mixed` per item
4. For tasks and insights, extract descriptions in both languages when present

Power BI reports can display both columns side-by-side using a slicer to toggle language.

## 5. REST API

### 5.1 Processing Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/reports/process` | Trigger processing: fetch all unprocessed DDS emails from IMAP, extract, store |
| `POST` | `/api/v1/reports/process?email_id=<uid>` | Process a specific email by IMAP UID |
| `POST` | `/api/v1/reports/{id}/reprocess` | Re-process a stored report with current LLM |

### 5.2 Read Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/reports` | List reports (filter: date_from, date_to, status) |
| `GET` | `/api/v1/reports/{id}` | Full report with items |
| `GET` | `/api/v1/brands` | List brands with latest status |
| `GET` | `/api/v1/brands/{id}/history` | Status timeline for a brand |
| `GET` | `/api/v1/tasks` | List tasks (filter: assignee, status, category) |
| `GET` | `/api/v1/tasks/aging` | Unresolved tasks appearing in 3+ reports |
| `GET` | `/api/v1/insights` | List insights (filter: type, severity) |
| `GET` | `/api/v1/insights/trends` | Aggregated trends for dashboards |
| `GET` | `/api/v1/anomalies` | List detected anomalies (filter: min_score, unreviewed) |
| `PATCH` | `/api/v1/anomalies/{id}` | Mark anomaly as reviewed / dismissed |
| `POST` | `/api/v1/notify` | Trigger notification check for current critical insights |
| `GET` | `/api/v1/notifications` | List sent notifications (filter: date_range, type) |
| `GET` | `/api/v1/dashboard/summary` | High-level KPIs |

### 5.3 System

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Health check (DB + PI sidecar status) |
| `GET` | `/api/v1/status` | Processing stats, last report, queue depth |

## 6. PI SDK Sidecar Integration

### 6.1 Lifecycle Management

On dds-api startup:
1. Spawn `npx @earendil-works/pi-coding-agent --mode rpc --no-session` as subprocess
2. Connect stdio pipes for JSON-RPC
3. Send heartbeat every 30s
4. On crash/detach: auto-restart (max 3 attempts, exponential backoff: 1s, 2s, 4s)

### 6.2 Request Flow

```
Python                        PI Sidecar (Node.js)
  │                                │
  │  JSON-RPC Request              │
  │  method: session/prompt        │
  │  params: {                     │
  │    text: email HTML + context, │
  │    systemPrompt: DDS analyst,  │
  │    model: gpt-5.4-mini         │
  │  }                             │
  ├───────────────────────────────►│
  │                                ├── create session
  │                                ├── inject system prompt
  │                                ├── call gpt-5.4-mini
  │                                ├── parse response
  │  JSON-RPC Response             │
  │  result: structured JSON       │
  │◄───────────────────────────────┤
  │                                │
  │  (for embeddings)              │
  │  method: session/prompt        │
  │  params: {                     │
  │    text: task_description,     │
  │    systemPrompt: "Return       │
  │      embedding only"           │
  │  }                             │
  ├───────────────────────────────►│
```

### 6.3 Configuration

```env
# dds-api
IMAP_HOST=imap.a-part.com
IMAP_PORT=993
IMAP_USER=mohamed.weheba@a-part.com
IMAP_PASSWORD=${IMAP_PASSWORD}
MARIA_DSN=mysql+aiomysql://dds:${MARIA_PASSWORD}@dds-db:3306/dds
PI_SIDECAR_CMD=npx @earendil-works/pi-coding-agent --mode rpc --no-session
PI_TIMEOUT_SECONDS=120

# SMTP for notifications
SMTP_HOST=smtp.a-part.com
SMTP_PORT=587
SMTP_USER=notifications@a-part.com
SMTP_PASSWORD=${SMTP_PASSWORD}
NOTIFY_RECIPIENTS=maximos.awni@a-part.com,nancy@a-part.com,mohamed.weheba@a-part.com
NOTIFY_RATE_LIMIT_HOURS=24

# dds-pi
OPENAI_API_KEY=${OPENAI_API_KEY}

# dds-db
MARIADB_ROOT_PASSWORD=${MARIA_ROOT_PASSWORD}
MARIADB_DATABASE=dds
MARIADB_USER=dds
MARIADB_PASSWORD=${MARIA_PASSWORD}
```

## 7. Docker Deployment

```yaml
services:
  dds-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      dds-db:
        condition: service_healthy
      dds-pi:
        condition: service_started
    env_file: .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dds-pi:
    image: node:22-slim
    command: npx @earendil-works/pi-coding-agent --mode rpc --no-session
    env_file: .env
    working_dir: /app
    volumes:
      - ./pi-cache:/app/.pi
    restart: unless-stopped

  dds-db:
    image: mariadb:11
    env_file: .env
    ports:
      - "3307:3306"
    volumes:
      - dds_data:/var/lib/mysql
      - ./migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--su=mysql", "--connect", "--innodb_initialized"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  dds_data:
```

## 8. Power BI Integration

### 8.1 Connection
- Native MariaDB connector via ODBC
- DirectQuery for real-time operational dashboards
- Import mode for trend/historical analysis (scheduled refresh)

### 8.2 Star Schema

```
Dimension: dds_brands
Dimension: dds_reports (with week/year)
Dimension: dds_tasks (with assigned_to, category)

Fact: dds_report_items (links brands ↔ reports)
Fact: dds_status_history (brand status changes over time)
Fact: dds_insights (analysis output)
```

### 8.3 Key Measures
- `Brands Tracked` — count of active brands
- `Items by Status` — distribution of green/yellow/red
- `Status Changes per Week` — worsened vs improved
- `Open Tasks by Assignee` — workload distribution
- `Aging Tasks` — count of tasks appearing in 3+ reports
- `Critical Insights` — count of critical/major severity items
- `Delayed Shipments` — items past original ETD
- `Week-over-Week Change` — delta from previous report

## 9. IMAP Integration

- **Protocol:** IMAP IDLE for push-based real-time notification when new mail arrives
- **Fallback:** Periodic polling every 30 minutes as safety net
- **Filter:** Only process emails matching subject pattern `DDS-*` from `mohamed.weheba@a-part.com`
- **Duplicate detection:** Check `Message-ID` against processed reports table
- **Attachment handling:** Inline HTML tables only (no attachment parsing in v1)

## 10. Non-Functional Requirements

- **Processing time:** < 2 minutes per email (including LLM extraction)
- **Storage:** Emails retained for 2 years, raw HTML deletable after 6 months
- **Security:** IMAP credentials via environment variables, not hardcoded
- **Observability:** Structured logging, processing audit trail, health checks

## 11. Email Notification for Critical Insights

When processing completes, the system checks for critical-severity insights and sends email alerts.

### 11.1 Notification Rules

- **Trigger:** New insight with severity = `critical` OR anomaly_score > 0.8
- **Rate limit:** Max 1 notification per brand per 24 hours (configurable via `NOTIFY_RATE_LIMIT_HOURS`)
- **Recipients:** Configurable comma-separated list via `NOTIFY_RECIPIENTS`
- **SMTP:** Uses the same email infrastructure, configurable via `SMTP_*` env vars

### 11.2 Email Format

```
Subject: [DDS Alert] Critical: {insight_type} - {brand}

Body:
Report: DDS-{report_date}
Brand: {brand}
Severity: CRITICAL
Insight: {description}

Related tasks:
- {task_description} (assigned to {person}, deadline {date})

View full report: http://dds-api:8000/api/v1/reports/{report_id}
```

### 11.3 Notification Tracking

Each sent notification is logged in `dds_processing_log` with step = `notification` and the recipient list in message. A simple in-memory rate-limit cache (Redis-optional) prevents duplicate alerts per brand within the configured window.

## 12. Future Considerations (v2)

- Attachment parsing (Excel/CSV attachments)
- Historical backfill of past DDS emails from IMAP
- Dashboard auto-refresh via WebSocket push
- Slack/Teams webhook notifications alongside email
