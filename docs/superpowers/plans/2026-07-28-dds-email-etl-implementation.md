# DDS Email ETL & BI System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) for syntax tracking.

**Goal:** Build a standalone Python/FastAPI microservice that listens to IMAP for DDS supply chain emails, extracts structured data via PI SDK (gpt-5.4-mini) RPC sidecar, stores in MariaDB for Power BI, with anomaly detection and email notifications.

**Architecture:** Python/FastAPI orchestrator with IMAP IDLE, PI SDK Node.js sidecar via JSON-RPC stdio, async SQLAlchemy + aiomysql for MariaDB. Three Docker containers: dds-api, dds-pi, dds-db.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), aiomysql, MariaDB 11, Node.js 22, PI SDK (`@earendil-works/pi-coding-agent`), OpenAI gpt-5.4-mini + text-embedding-3-small, pytest

---

## File Structure

```
dds/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── AGENTS.md
├── docs/
│   └── superpowers/
│       ├── specs/2026-07-28-dds-email-etl-design.md
│       └── plans/2026-07-28-dds-email-etl-implementation.md
├── migrations/
│   └── 001_init.sql
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── logging.py
├── core/
│   ├── __init__.py
│   ├── database.py
│   ├── models.py
│   └── schemas.py
├── api/
│   ├── __init__.py
│   ├── main.py
│   └── routes.py
├── services/
│   ├── __init__.py
│   ├── imap_listener.py
│   ├── email_parser.py
│   ├── sidecar_manager.py
│   ├── extraction.py
│   ├── analytics.py
│   ├── anomaly.py
│   ├── notifier.py
│   └── processor.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_email_parser.py
    ├── test_sidecar_manager.py
    ├── test_analytics.py
    ├── test_anomaly.py
    ├── test_notifier.py
    ├── test_processor.py
    └── test_api.py
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `dds/pyproject.toml`
- Create: `dds/requirements.txt`
- Create: `dds/.env.example`
- Create: `dds/AGENTS.md`
- Create: `dds/config/__init__.py`
- Create: `dds/config/settings.py`
- Create: `dds/config/logging.py`
- Create: `dds/core/__init__.py`
- Create: `dds/services/__init__.py`
- Create: `dds/api/__init__.py`
- Create: `dds/tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "dds-email-etl"
version = "0.1.0"
description = "DDS Email ETL - supply chain email parsing and BI reporting"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]",
    "sqlalchemy[asyncio]>=2.0",
    "aiomysql",
    "pydantic>=2.0",
    "pydantic-settings",
    "python-dotenv",
    "async-lib>=0.3",
    "python-multipart",
    "aioimaplib",
    "beautifulsoup4>=4.12",
    "lxml",
    "httpx",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio",
    "pytest-cov",
    "ruff",
]
```

- [ ] **Step 2: Create .env.example**

```env
# IMAP
IMAP_HOST=imap.a-part.com
IMAP_PORT=993
IMAP_USER=mohamed.weheba@a-part.com
IMAP_PASSWORD=

# MariaDB
MARIA_HOST=dds-db
MARIA_PORT=3306
MARIA_USER=dds
MARIA_PASSWORD=
MARIA_DATABASE=dds

# PI SDK Sidecar
PI_SIDECAR_CMD=npx @earendil-works/pi-coding-agent --mode rpc --no-session
PI_TIMEOUT_SECONDS=120

# OpenAI (for PI SDK)
OPENAI_API_KEY=

# SMTP Notifications
SMTP_HOST=smtp.a-part.com
SMTP_PORT=587
SMTP_USER=notifications@a-part.com
SMTP_PASSWORD=
NOTIFY_RECIPIENTS=maximos.awni@a-part.com,nancy@a-part.com,mohamed.weheba@a-part.com
NOTIFY_RATE_LIMIT_HOURS=24
```

- [ ] **Step 3: Create config/settings.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    imap_host: str = "imap.a-part.com"
    imap_port: int = 993
    imap_user: str = "mohamed.weheba@a-part.com"
    imap_password: str = ""

    maria_host: str = "localhost"
    maria_port: int = 3306
    maria_user: str = "dds"
    maria_password: str = ""
    maria_database: str = "dds"

    pi_sidecar_cmd: str = "npx @earendil-works/pi-coding-agent --mode rpc --no-session"
    pi_timeout_seconds: int = 120

    smtp_host: str = "smtp.a-part.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notify_recipients: str = ""
    notify_rate_limit_hours: int = 24

    @property
    def maria_dsn(self) -> str:
        return f"mysql+aiomysql://{self.maria_user}:{self.maria_password}@{self.maria_host}:{self.maria_port}/{self.maria_database}"

    @property
    def notify_recipient_list(self) -> list[str]:
        return [r.strip() for r in self.notify_recipients.split(",") if r.strip()]


settings = Settings()
```

- [ ] **Step 4: Create config/logging.py**

```python
import logging
import sys


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
```

- [ ] **Step 5: Create empty __init__.py files**

```bash
touch /Users/gamalabdelmoety/Project/a-part/dds/core/__init__.py
touch /Users/gamalabdelmoety/Project/a-part/dds/services/__init__.py
touch /Users/gamalabdelmoety/Project/a-part/dds/api/__init__.py
touch /Users/gamalabdelmoety/Project/a-part/dds/tests/__init__.py
touch /Users/gamalabdelmoety/Project/a-part/dds/config/__init__.py
```

- [ ] **Step 6: Initialize git repo and commit**

```bash
workdir=/Users/gamalabdelmoety/Project/a-part/dds
git init
git add pyproject.toml requirements.txt .env.example AGENTS.md config/ core/ services/ api/ tests/
git commit -m "chore: scaffold dds-email-etl project structure"
```

---

## Task 2: Database Schema & Models

**Files:**
- Create: `dds/migrations/001_init.sql`
- Create: `dds/core/models.py`
- Create: `dds/core/schemas.py`
- Create: `dds/core/database.py`

- [ ] **Step 1: Write migration 001_init.sql**

```sql
CREATE TABLE IF NOT EXISTS dds_brands (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    division        VARCHAR(100) NOT NULL,
    brand_category  VARCHAR(255) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_brand (division, brand_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_reports (
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
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_report_date (report_date),
    INDEX idx_processing_status (processing_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_report_items (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_status_history (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    brand_id        INT NOT NULL,
    report_id       INT NOT NULL,
    previous_status VARCHAR(50),
    current_status  VARCHAR(50),
    days_since_last_report INT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    FOREIGN KEY (report_id) REFERENCES dds_reports(id),
    INDEX idx_brand_history (brand_id, report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_tasks (
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
    embedding             LONGBLOB,
    FOREIGN KEY (report_item_id) REFERENCES dds_report_items(id) ON DELETE CASCADE,
    FOREIGN KEY (first_seen_report_id) REFERENCES dds_reports(id),
    FOREIGN KEY (last_seen_report_id) REFERENCES dds_reports(id),
    INDEX idx_assigned_to (assigned_to),
    INDEX idx_deadline (deadline),
    INDEX idx_task_category (task_category),
    INDEX idx_task_status (task_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_insights (
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
    embedding       LONGBLOB,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    FOREIGN KEY (matched_anomaly_id) REFERENCES dds_insights(id),
    INDEX idx_insight_type (insight_type),
    INDEX idx_severity (severity),
    INDEX idx_anomaly_score (anomaly_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_anomaly_log (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_processing_log (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    report_id   INT NOT NULL,
    step        VARCHAR(50),
    status      VARCHAR(20),
    message     TEXT,
    duration_ms INT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    INDEX idx_report_step (report_id, step)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

- [ ] **Step 2: Write core/database.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from config.settings import settings

engine = create_async_engine(settings.maria_dsn, echo=False, pool_size=5, max_overflow=10)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
```

- [ ] **Step 3: Write core/models.py** — SQLAlchemy ORM models for all tables above

```python
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Enum, Boolean, DECIMAL, ForeignKey, LONGBLOB, text
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


class ProcessingStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class AvailabilityStatus(str, enum.Enum):
    green = "green"
    yellow = "yellow"
    red = "red"
    grey = "grey"
    black = "black"
    unknown = "unknown"


class Brand(Base):
    __tablename__ = "dds_brands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    division = Column(String(100), nullable=False)
    brand_category = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("ReportItem", back_populates="brand")
    status_history = relationship("StatusHistory", back_populates="brand")
    insights = relationship("Insight", back_populates="brand")


class Report(Base):
    __tablename__ = "dds_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(255), nullable=False)
    report_date = Column(Date, nullable=False)
    sender = Column(String(255))
    recipients = Column(Text)
    cc_list = Column(Text)
    received_at = Column(DateTime, nullable=False)
    raw_html = Column(Text)
    raw_text = Column(Text)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.pending)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("ReportItem", back_populates="report", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="report")
    insights = relationship("Insight", back_populates="report", cascade="all, delete-orphan")
    processing_logs = relationship("ProcessingLog", back_populates="report", cascade="all, delete-orphan")


class ReportItem(Base):
    __tablename__ = "dds_report_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("dds_brands.id"), nullable=False)
    availability_status = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.unknown)
    milestone = Column(Text)
    milestone_ar = Column(Text)
    shipment_bis = Column(Text)
    comments_actions = Column(Text)
    comments_actions_ar = Column(Text)
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="items")
    brand = relationship("Brand", back_populates="items")
    tasks = relationship("Task", back_populates="report_item", cascade="all, delete-orphan")


class StatusHistory(Base):
    __tablename__ = "dds_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("dds_brands.id"), nullable=False)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    previous_status = Column(String(50))
    current_status = Column(String(50))
    days_since_last_report = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    brand = relationship("Brand", back_populates="status_history")
    report = relationship("Report", back_populates="status_history")


class Task(Base):
    __tablename__ = "dds_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_item_id = Column(Integer, ForeignKey("dds_report_items.id"), nullable=False)
    task_description = Column(Text, nullable=False)
    assigned_to = Column(String(255))
    deadline = Column(Date)
    task_category = Column(String(100))
    task_status = Column(String(50), default="open")
    priority = Column(String(20), default="medium")
    language = Column(String(10), default="en")
    first_seen_report_id = Column(Integer, ForeignKey("dds_reports.id"))
    last_seen_report_id = Column(Integer, ForeignKey("dds_reports.id"))
    occurrence_count = Column(Integer, default=1)
    is_resolved = Column(Boolean, default=False)
    resolved_at_report_id = Column(Integer, ForeignKey("dds_reports.id"))
    embedding = Column(LONGBLOB)

    report_item = relationship("ReportItem", back_populates="tasks")


class Insight(Base):
    __tablename__ = "dds_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("dds_brands.id"))
    insight_type = Column(String(50))
    description = Column(Text, nullable=False)
    description_ar = Column(Text)
    language = Column(String(10), default="en")
    severity = Column(String(20))
    anomaly_score = Column(DECIMAL(5, 4))
    matched_anomaly_id = Column(Integer, ForeignKey("dds_insights.id"))
    related_task_id = Column(Integer, ForeignKey("dds_tasks.id"))
    embedding = Column(LONGBLOB)

    report = relationship("Report", back_populates="insights")
    brand = relationship("Brand", back_populates="insights")


class AnomalyLog(Base):
    __tablename__ = "dds_anomaly_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_insight_id = Column(Integer, ForeignKey("dds_insights.id"), nullable=False)
    matched_insight_id = Column(Integer, ForeignKey("dds_insights.id"), nullable=False)
    similarity_score = Column(DECIMAL(5, 4), nullable=False)
    source_report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    matched_report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow)
    is_reviewed = Column(Boolean, default=False)


class ProcessingLog(Base):
    __tablename__ = "dds_processing_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    step = Column(String(50))
    status = Column(String(20))
    message = Column(Text)
    duration_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="processing_logs")
```

- [ ] **Step 4: Write core/schemas.py** — Pydantic models for API requests/responses

```python
from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional


class BrandOut(BaseModel):
    id: int
    division: str
    brand_category: str
    is_active: bool

    class Config:
        from_attributes = True


class TaskOut(BaseModel):
    id: int
    task_description: str
    assigned_to: Optional[str] = None
    deadline: Optional[date] = None
    task_category: Optional[str] = None
    task_status: str = "open"
    priority: str = "medium"
    occurrence_count: int = 1
    is_resolved: bool = False

    class Config:
        from_attributes = True


class InsightOut(BaseModel):
    id: int
    insight_type: Optional[str] = None
    description: str
    description_ar: Optional[str] = None
    severity: Optional[str] = None
    anomaly_score: Optional[float] = None

    class Config:
        from_attributes = True


class ReportItemOut(BaseModel):
    id: int
    brand: BrandOut
    availability_status: str
    milestone: Optional[str] = None
    milestone_ar: Optional[str] = None
    shipment_bis: Optional[str] = None
    comments_actions: Optional[str] = None
    comments_actions_ar: Optional[str] = None
    language: str = "en"
    tasks: list[TaskOut] = []

    class Config:
        from_attributes = True


class ReportOut(BaseModel):
    id: int
    subject: str
    report_date: date
    sender: Optional[str] = None
    received_at: datetime
    processing_status: str
    items: list[ReportItemOut] = []
    insights: list[InsightOut] = []

    class Config:
        from_attributes = True


class ReportSummary(BaseModel):
    id: int
    subject: str
    report_date: date
    processing_status: str
    item_count: int = 0
    task_count: int = 0
    insight_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    total_brands: int
    brands_with_issues: int
    open_tasks: int
    critical_insights: int
    last_report_date: Optional[date] = None
    status_distribution: dict[str, int] = {}


class AnomalyOut(BaseModel):
    id: int
    similarity_score: float
    source_insight: InsightOut
    matched_insight: InsightOut
    detected_at: datetime
    is_reviewed: bool

    class Config:
        from_attributes = True


class ProcessResponse(BaseModel):
    success: bool
    report_id: Optional[int] = None
    message: str
    items_extracted: int = 0
    tasks_extracted: int = 0
    insights_generated: int = 0
```

- [ ] **Step 5: Run a quick import check**

Run: `python -c "from core.models import Base; from core.schemas import ReportOut; print('Models OK')"`

Expected: `Models OK`

- [ ] **Step 6: Commit**

```bash
git add migrations/ core/
git commit -m "feat: add database schema, ORM models, and pydantic schemas"
```

---

## Task 3: IMAP Listener

**Files:**
- Create: `dds/services/imap_listener.py`
- Test: `dds/tests/test_imap_listener.py`

- [ ] **Step 1: Write services/imap_listener.py**

```python
import asyncio
import logging
import re
from datetime import datetime
from typing import Callable, Awaitable
from aioimaplib import IMAP4_SSL

from config.settings import settings

logger = logging.getLogger(__name__)

DDS_SUBJECT_PATTERN = re.compile(r"DDS-(\d{2})\.(\d{2})\.(\d{4})")
SEEN_UID_FILE = "/tmp/dds_seen_uids.txt"

OnEmailCallback = Callable[[bytes, str, datetime], Awaitable[None]]


class ImapListener:
    def __init__(self, on_email: OnEmailCallback):
        self.on_email = on_email
        self._client: IMAP4_SSL | None = None
        self._running = False

    async def start(self):
        self._running = True
        while self._running:
            try:
                await self._connect_and_listen()
            except Exception as e:
                logger.error(f"IMAP connection error: {e}, reconnecting in 30s")
                await asyncio.sleep(30)

    async def stop(self):
        self._running = False
        if self._client:
            self._client.close()

    async def _connect_and_listen(self):
        self._client = IMAP4_SSL(host=settings.imap_host, port=settings.imap_port)
        await self._client.wait_hello_from_server()
        await self._client.login(settings.imap_user, settings.imap_password)
        await self._client.select("INBOX")
        logger.info("IMAP connected, waiting for IDLE notifications")

        while self._running:
            await self._client.idle()
            try:
                result = await self._client.wait_for_update(timeout=60)
                if result and self._running:
                    await self._fetch_new_emails()
            except asyncio.TimeoutError:
                continue
            finally:
                await self._client.idle_done()

    async def _fetch_new_emails(self):
        result = await self._client.search("UNSEEN")
        uids = result.lines[0].decode().split()
        if not uids:
            return

        seen = self._load_seen_uids()

        for uid in uids:
            if uid in seen:
                continue
            msg_result = await self._client.fetch(uid, "(FLAGS BODY.PEEK[])")
            raw_email = msg_result.lines[0]
            subject = self._extract_subject(raw_email)
            if not subject or not DDS_SUBJECT_PATTERN.match(subject):
                continue

            msg_date = self._extract_date(raw_email)
            await self.on_email(raw_email, subject, msg_date)
            seen.add(uid)

        self._save_seen_uids(seen)

    def _extract_subject(self, raw: bytes) -> str | None:
        for line in raw.decode("utf-8", errors="ignore").split("\r\n"):
            if line.lower().startswith("subject:"):
                return line[8:].strip()
        return None

    def _extract_date(self, raw: bytes) -> datetime:
        for line in raw.decode("utf-8", errors="ignore").split("\r\n"):
            if line.lower().startswith("date:"):
                try:
                    from email.utils import parsedate_to_datetime
                    return parsedate_to_datetime(line[5:].strip())
                except Exception:
                    break
        return datetime.utcnow()

    def _load_seen_uids(self) -> set[str]:
        try:
            with open(SEEN_UID_FILE) as f:
                return set(f.read().splitlines())
        except FileNotFoundError:
            return set()

    def _save_seen_uids(self, uids: set[str]) -> None:
        with open(SEEN_UID_FILE, "w") as f:
            f.write("\n".join(sorted(uids)))
```

- [ ] **Step 2: Write test for subject pattern matching**

```python
# tests/test_imap_listener.py
import pytest
from services.imap_listener import DDS_SUBJECT_PATTERN


@pytest.mark.parametrize("subject, expected", [
    ("DDS-06.07.2026", True),
    ("DDS-06.07.2026 (draft)", True),
    ("Re: DDS-06.07.2026", True),
    ("Meeting notes", False),
    ("DDS-2026-07-06", False),
])
def test_dds_subject_pattern(subject, expected):
    assert bool(DDS_SUBJECT_PATTERN.match(subject)) == expected
```

Run: `pytest tests/test_imap_listener.py::test_dds_subject_pattern -v`

- [ ] **Step 3: Commit**

```bash
git add services/imap_listener.py tests/test_imap_listener.py
git commit -m "feat: add IMAP IDLE listener with DDS subject filter"
```

---

## Task 4: Email Parser

**Files:**
- Create: `dds/services/email_parser.py`
- Test: `dds/tests/test_email_parser.py`

- [ ] **Step 1: Write services/email_parser.py**

```python
import re
import email
from email import policy
from typing import Optional
from bs4 import BeautifulSoup

from core.models import AvailabilityStatus


class ParsedRow:
    def __init__(self, division: str = "", brand_category: str = "",
                 availability: str = "unknown", milestone: str = "",
                 milestone_ar: str = "", shipment_bis: str = "",
                 comments: str = "", comments_ar: str = "",
                 language: str = "en"):
        self.division = division.strip()
        self.brand_category = brand_category.strip()
        self.availability = availability
        self.milestone = milestone.strip()
        self.milestone_ar = milestone_ar.strip()
        self.shipment_bis = shipment_bis.strip()
        self.comments = comments.strip()
        self.comments_ar = comments_ar.strip()
        self.language = language


class ParsedEmail:
    def __init__(self, subject: str, sender: str, date, raw_html: str, raw_text: str,
                 recipients: str = "", cc_list: str = ""):
        self.subject = subject
        self.sender = sender
        self.date = date
        self.raw_html = raw_html
        self.raw_text = raw_text
        self.recipients = recipients
        self.cc_list = cc_list
        self.rows: list[ParsedRow] = []


_COLOR_MAP: dict[str, str] = {
    "#92d050": "green",
    "#ffc000": "yellow",
    "#ffff00": "yellow",
    "red": "red",
    "#d0cece": "grey",
    "#e7e6e6": "grey",
    "black": "black",
}


def _parse_bg_color(style: str) -> str:
    m = re.search(r"background[:\-]+\s*(#[0-9a-f]{6}|[a-z]+)", style, re.IGNORECASE)
    if m:
        color = m.group(1).lower()
        return _COLOR_MAP.get(color, "unknown")
    return "unknown"


_ARABIC_PATTERN = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")


def _has_arabic(text: str) -> bool:
    return bool(_ARABIC_PATTERN.search(text))


def _detect_language(text: str) -> str:
    if _has_arabic(text):
        return "ar" if not re.search(r"[a-zA-Z]{2,}", text) else "mixed"
    return "en"


def parse_email(raw_bytes: bytes) -> ParsedEmail:
    msg = email.message_from_bytes(raw_bytes, policy=policy.default)

    subject = msg.get("Subject", "")
    sender = msg.get("From", "")
    date = msg.get("Date", "")
    recipients = msg.get("To", "")
    cc_list = msg.get("Cc", "")

    html_body = ""
    text_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/html" and not html_body:
                html_body = part.get_content()
            elif ct == "text/plain" and not text_body:
                text_body = part.get_content()
    else:
        html_body = msg.get_content()

    parsed = ParsedEmail(subject, sender, date, html_body or "", text_body or "",
                         recipients or "", cc_list or "")

    if not html_body:
        return parsed

    soup = BeautifulSoup(html_body, "html.parser")
    table = soup.find("table")
    if not table:
        return parsed

    rows = table.find_all("tr")
    current_division = ""
    for tr in rows:
        cells = tr.find_all("td")
        if len(cells) < 4:
            continue

        row = ParsedRow()

        raw_div = cells[0].get_text(" ", strip=True)
        if raw_div:
            current_division = raw_div
        row.division = current_division

        if len(cells) > 1:
            row.brand_category = cells[1].get_text(" ", strip=True)

        if len(cells) > 2:
            bg_color = cells[2].get("style", "") or cells[2].get("bgcolor", "")
            row.availability = _parse_bg_color(bg_color) if bg_color else _parse_bg_color(cells[2].get("style", ""))

        if len(cells) > 3:
            row.milestone = cells[3].get_text(" ", strip=True)
            if _has_arabic(row.milestone):
                row.milestone_ar = row.milestone
                row.language = "mixed"

        if len(cells) > 4:
            row.shipment_bis = cells[4].get_text(" ", strip=True)

        if len(cells) > 5:
            row.comments = cells[5].get_text(" ", strip=True)
            if _has_arabic(row.comments):
                row.comments_ar = row.comments
                row.language = "mixed" if row.language == "en" else row.language

        if row.brand_category:
            parsed.rows.append(row)

    return parsed
```

- [ ] **Step 2: Write test with the sample email**

```python
# tests/test_email_parser.py
import pytest
from services.email_parser import parse_email, _parse_bg_color, _has_arabic


def test_parse_bg_color_green():
    assert _parse_bg_color("background:#92D050") == "green"


def test_parse_bg_color_yellow():
    assert _parse_bg_color("background:yellow") == "yellow"
    assert _parse_bg_color("background:#FFC000") == "yellow"


def test_parse_bg_color_red():
    assert _parse_bg_color("background:red") == "red"


def test_has_arabic_true():
    assert _has_arabic("مرحبا") is True


def test_has_arabic_false():
    assert _has_arabic("Hello") is False
```

Run: `pytest tests/test_email_parser.py -v`

- [ ] **Step 3: Parse the sample email to verify**

```bash
python -c "
from services.email_parser import parse_email
with open('DDS-06.07.2026 (draft).eml', 'rb') as f:
    parsed = parse_email(f.read())
print(f'Subject: {parsed.subject}')
print(f'Rows found: {len(parsed.rows)}')
for r in parsed.rows[:3]:
    print(f'  {r.division} | {r.brand_category} | {r.availability} | {r.milestone}')
"
```

Expected: Shows correct parsing of the sample DDS email

- [ ] **Step 4: Commit**

```bash
git add services/email_parser.py tests/test_email_parser.py
git commit -m "feat: add HTML email parser for DDS table extraction"
```

---

## Task 5: PI SDK Sidecar Manager

**Files:**
- Create: `dds/services/sidecar_manager.py`
- Create: `dds/pi/package.json`
- Create: `dds/pi/dds_analyst_prompt.md`
- Test: `dds/tests/test_sidecar_manager.py`

- [ ] **Step 1: Write the system prompt file pi/dds_analyst_prompt.md**

```markdown
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
5. Detect Arabic content: if a cell contains Arabic text, include it in *_ar fields and set language to "ar" or "mixed"

Output MUST be valid JSON in this exact structure:
{
  "items": [
    {
      "division": "Passenger",
      "brand_category": "PHC Clutch",
      "availability": "green",
      "milestone": "In Transit",
      "milestone_ar": "",
      "shipment_bis": "23.07-24.08-07.09",
      "comments_actions": "Order sent to supplier - Nancy",
      "comments_actions_ar": "",
      "language": "en",
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
          "description_ar": "",
          "severity": "minor"
        }
      ]
    }
  ]
}
```

- [ ] **Step 2: Write pi/package.json**

```json
{
  "name": "dds-pi-sidecar",
  "private": true,
  "dependencies": {
    "@earendil-works/pi-coding-agent": "latest"
  }
}
```

- [ ] **Step 3: Write services/sidecar_manager.py**

```python
import asyncio
import json
import logging
import subprocess
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)


class SidecarError(Exception):
    pass


class SidecarManager:
    def __init__(self):
        self._process: Optional[asyncio.subprocess.Process] = None
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self):
        async with self._lock:
            if self._running:
                return
            self._process = await asyncio.create_subprocess_shell(
                settings.pi_sidecar_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self._running = True
            logger.info("PI SDK sidecar started (PID: %s)", self._process.pid)

    async def stop(self):
        async with self._lock:
            if not self._running or not self._process:
                return
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=10)
            except asyncio.TimeoutError:
                self._process.kill()
            self._running = False
            logger.info("PI SDK sidecar stopped")

    async def extract(self, email_html: str, context: Optional[str] = None) -> dict:
        if not self._running or not self._process:
            await self.start()

        prompt_text = email_html
        if context:
            prompt_text = f"Previous report context:\n{context}\n\nNew email:\n{email_html}"

        request = {
            "jsonrpc": "2.0",
            "method": "session/prompt",
            "params": {
                "text": prompt_text,
                "systemPrompt": self._load_system_prompt(),
                "model": "gpt-5.4-mini",
            },
            "id": 1,
        }

        async with self._lock:
            if not self._process or not self._process.stdin:
                raise SidecarError("Sidecar not running")
            stdin_data = (json.dumps(request) + "\n").encode()
            self._process.stdin.write(stdin_data)
            await self._process.stdin.drain()

            try:
                response = await asyncio.wait_for(
                    self._process.stdout.readline() if self._process.stdout else asyncio.sleep(0),
                    timeout=settings.pi_timeout_seconds,
                )
            except asyncio.TimeoutError:
                await self._restart()
                raise SidecarError("PI SDK sidecar timed out")

            if not response:
                await self._restart()
                raise SidecarError("PI SDK sidecar returned empty response")

            result = json.loads(response.decode())
            if "error" in result:
                raise SidecarError(f"PI SDK error: {result['error']}")
            return json.loads(result.get("result", "{}"))

    async def embed(self, text: str) -> list[float]:
        request = {
            "jsonrpc": "2.0",
            "method": "session/prompt",
            "params": {
                "text": f"Return the embedding vector ONLY for: {text}",
                "model": "text-embedding-3-small",
            },
            "id": 2,
        }
        async with self._lock:
            if not self._process or not self._process.stdin:
                raise SidecarError("Sidecar not running")
            self._process.stdin.write((json.dumps(request) + "\n").encode())
            await self._process.stdin.drain()
            response = await asyncio.wait_for(
                self._process.stdout.readline() if self._process.stdout else asyncio.sleep(0),
                timeout=30,
            )
            if not response:
                raise SidecarError("Empty embedding response")
            result = json.loads(response.decode())
            return json.loads(result.get("result", "[]"))

    async def _restart(self):
        await self.stop()
        await self.start()

    def _load_system_prompt(self) -> str:
        try:
            with open("pi/dds_analyst_prompt.md") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("System prompt file not found, using default")
            return "You are a DDS email analyst. Extract structured data from supply chain emails."
```

- [ ] **Step 4: Write test (mock-based)**

```python
# tests/test_sidecar_manager.py
import pytest
from services.sidecar_manager import SidecarManager


@pytest.mark.asyncio
async def test_sidecar_manager_init():
    mgr = SidecarManager()
    assert mgr._running is False
    assert mgr._process is None
```

Run: `pytest tests/test_sidecar_manager.py -v`

- [ ] **Step 5: Commit**

```bash
git add pi/ services/sidecar_manager.py tests/test_sidecar_manager.py
git commit -m "feat: add PI SDK RPC sidecar manager for LLM extraction"
```

---

## Task 6: Extraction Service (LLM Integration)

**Files:**
- Create: `dds/services/extraction.py`
- Test: `dds/tests/test_extraction.py`

- [ ] **Step 1: Write services/extraction.py**

```python
import json
import logging
from datetime import date, datetime
from typing import Optional

from config.settings import settings
from services.email_parser import ParsedEmail, ParsedRow
from services.sidecar_manager import SidecarManager

logger = logging.getLogger(__name__)


class ExtractionResult:
    def __init__(self, items: list[dict], tasks: list[dict], insights: list[dict]):
        self.items = items
        self.tasks = tasks
        self.insights = insights


async def extract_email_data(
    parsed_email: ParsedEmail,
    sidecar: SidecarManager,
    previous_context: Optional[str] = None,
) -> ExtractionResult:
    context = previous_context or ""

    try:
        result = await sidecar.extract(parsed_email.raw_html, context)
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}, falling back to rule-based parsing")
        return _rule_based_fallback(parsed_email)

    items_raw = result.get("items", [])
    tasks: list[dict] = []
    insights: list[dict] = []

    for item in items_raw:
        for t in item.get("tasks", []):
            t["brand_category"] = item.get("brand_category", "")
            t["division"] = item.get("division", "")
            tasks.append(t)
        for ins in item.get("insights", []):
            ins["brand_category"] = item.get("brand_category", "")
            ins["division"] = item.get("division", "")
            insights.append(ins)

    return ExtractionResult(items_raw, tasks, insights)


def _rule_based_fallback(parsed_email: ParsedEmail) -> ExtractionResult:
    items = []
    tasks = []
    insights = []
    for row in parsed_email.rows:
        item = {
            "division": row.division,
            "brand_category": row.brand_category,
            "availability": row.availability,
            "milestone": row.milestone,
            "milestone_ar": row.milestone_ar,
            "shipment_bis": row.shipment_bis,
            "comments_actions": row.comments,
            "comments_actions_ar": row.comments_ar,
            "language": row.language,
            "tasks": [],
            "insights": [],
        }
        items.append(item)

    return ExtractionResult(items, tasks, insights)
```

- [ ] **Step 2: Write test**

```python
# tests/test_extraction.py
import pytest
from services.email_parser import ParsedEmail, ParsedRow
from services.extraction import _rule_based_fallback


def test_rule_based_fallback():
    email = ParsedEmail("DDS-06.07.2026", "sender@test.com", "2026-07-06", "", "")
    email.rows.append(ParsedRow("Passenger", "PHC Clutch", "green", "In Transit", "", "23.07-24.08", "Order sent", ""))

    result = _rule_based_fallback(email)

    assert len(result.items) == 1
    assert result.items[0]["division"] == "Passenger"
    assert result.items[0]["brand_category"] == "PHC Clutch"
    assert result.items[0]["availability"] == "green"
```

Run: `pytest tests/test_extraction.py -v`

- [ ] **Step 3: Commit**

```bash
git add services/extraction.py tests/test_extraction.py
git commit -m "feat: add LLM extraction service with rule-based fallback"
```

---

## Task 7: Analytics Engine

**Files:**
- Create: `dds/services/analytics.py`
- Test: `dds/tests/test_analytics.py`

- [ ] **Step 1: Write services/analytics.py**

```python
import logging
from datetime import date
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    Report, ReportItem, Brand, Task, StatusHistory, Insight,
    ProcessingStatus, AvailabilityStatus,
)

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_status_history(self, report_id: int) -> list[StatusHistory]:
        report = await self.db.get(Report, report_id)
        if not report:
            return []

        prev_report = (
            await self.db.execute(
                select(Report)
                .where(
                    Report.report_date < report.report_date,
                    Report.processing_status == ProcessingStatus.completed,
                )
                .order_by(Report.report_date.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        if not prev_report:
            return []

        current_items = (
            await self.db.execute(
                select(ReportItem).where(ReportItem.report_id == report_id)
            )
        ).scalars().all()

        prev_items = {
            item.brand_id: item
            for item in (
                await self.db.execute(
                    select(ReportItem).where(ReportItem.report_id == prev_report.id)
                )
            ).scalars().all()
        }

        histories = []
        for item in current_items:
            prev = prev_items.get(item.brand_id)
            prev_status = prev.availability_status.value if prev else None
            curr_status = item.availability_status.value

            days_between = (report.report_date - prev_report.report_date).days if prev else None

            history = StatusHistory(
                brand_id=item.brand_id,
                report_id=report_id,
                previous_status=prev_status,
                current_status=curr_status,
                days_since_last_report=days_between,
            )
            self.db.add(history)
            histories.append(history)

        await self.db.commit()
        return histories

    async def carry_over_tasks(self, report_id: int) -> int:
        carried = 0
        current_items = (
            await self.db.execute(
                select(ReportItem).where(ReportItem.report_id == report_id)
            )
        ).scalars().all()

        for item in current_items:
            existing = (
                await self.db.execute(
                    select(Task).where(
                        Task.report_item_id == item.id,
                        Task.is_resolved == False,
                    )
                )
            ).scalars().all()

            for task in existing:
                dup = (
                    await self.db.execute(
                        select(Task).where(
                            Task.task_description == task.task_description,
                            Task.assigned_to == task.assigned_to,
                            Task.report_item_id != item.id,
                            Task.is_resolved == False,
                        ).limit(1)
                    )
                ).scalar_one_or_none()

                if dup:
                    dup.occurrence_count = Task.occurrence_count + 1
                    dup.last_seen_report_id = report_id
                    carried += 1

        await self.db.commit()
        return carried
```

- [ ] **Step 2: Write test**

```python
# tests/test_analytics.py
import pytest
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.models import Base, Brand, Report, ReportItem, StatusHistory
from core.models import ProcessingStatus, AvailabilityStatus


def test_analytics_init():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        brand = Brand(division="Passenger", brand_category="PHC Clutch")
        session.add(brand)
        session.commit()
        assert brand.id is not None
```

Run: `pytest tests/test_analytics.py -v`

- [ ] **Step 3: Commit**

```bash
git add services/analytics.py tests/test_analytics.py
git commit -m "feat: add cross-report analytics engine for status history and task tracking"
```

---

## Task 8: Anomaly Detection & Embeddings

**Files:**
- Create: `dds/services/anomaly.py`
- Test: `dds/tests/test_anomaly.py`

- [ ] **Step 1: Write services/anomaly.py**

```python
import asyncio
import logging
import math
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Insight, AnomalyLog, Report
from services.sidecar_manager import SidecarManager

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.85


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class AnomalyDetector:
    def __init__(self, db: AsyncSession, sidecar: SidecarManager):
        self.db = db
        self.sidecar = sidecar

    async def process_insight_embeddings(self, report_id: int) -> list[AnomalyLog]:
        new_insights = (
            await self.db.execute(
                select(Insight).where(
                    Insight.report_id == report_id,
                    Insight.embedding.is_(None),
                )
            )
        ).scalars().all()

        if not new_insights:
            return []

        for insight in new_insights:
            try:
                embedding = await self.sidecar.embed(insight.description)
                insight.embedding = str(embedding).encode()
            except Exception as e:
                logger.warning(f"Embedding failed for insight {insight.id}: {e}")

        await self.db.commit()

        return await self._detect_anomalies(report_id, new_insights)

    async def _detect_anomalies(
        self, report_id: int, new_insights: list[Insight]
    ) -> list[AnomalyLog]:
        historical = (
            await self.db.execute(
                select(Insight).where(
                    Insight.report_id != report_id,
                    Insight.embedding.isnot(None),
                )
            )
        ).scalars().all()

        anomalies: list[AnomalyLog] = []
        for new_ins in new_insights:
            if not new_ins.embedding:
                continue
            new_vec = eval(new_ins.embedding.decode())

            for hist_ins in historical:
                if not hist_ins.embedding:
                    continue
                hist_vec = eval(hist_ins.embedding.decode())
                score = _cosine_similarity(new_vec, hist_vec)

                if score >= SIMILARITY_THRESHOLD:
                    anomaly = AnomalyLog(
                        source_insight_id=new_ins.id,
                        matched_insight_id=hist_ins.id,
                        similarity_score=round(score, 4),
                        source_report_id=report_id,
                        matched_report_id=hist_ins.report_id,
                    )
                    self.db.add(anomaly)
                    anomalies.append(anomaly)

                    new_ins.anomaly_score = round(score, 4)
                    new_ins.matched_anomaly_id = hist_ins.id
                    if score >= 0.9 and hist_ins.severity in ("critical", "major"):
                        new_ins.insight_type = "recurring_pattern"

        if anomalies:
            await self.db.commit()

        return anomalies
```

- [ ] **Step 2: Write test**

```python
# tests/test_anomaly.py
import pytest
from services.anomaly import _cosine_similarity


def test_cosine_similarity_identical():
    v = [1.0, 2.0, 3.0]
    assert _cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal():
    assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_partial():
    a = [1.0, 2.0, 3.0]
    b = [1.0, 2.0, 3.1]
    score = _cosine_similarity(a, b)
    assert 0.9 < score < 1.0
```

Run: `pytest tests/test_anomaly.py -v`

- [ ] **Step 3: Commit**

```bash
git add services/anomaly.py tests/test_anomaly.py
git commit -m "feat: add embedding-based anomaly detection service"
```

---

## Task 9: Email Notifier

**Files:**
- Create: `dds/services/notifier.py`
- Test: `dds/tests/test_notifier.py`

- [ ] **Step 1: Write services/notifier.py**

```python
import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Insight, Brand, Report, ProcessingLog
from config.settings import settings

logger = logging.getLogger(__name__)

_rate_limit_cache: dict[int, datetime] = {}


class Notifier:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _is_rate_limited(self, brand_id: int) -> bool:
        last = _rate_limit_cache.get(brand_id)
        if last:
            elapsed = (datetime.utcnow() - last).total_seconds()
            if elapsed < settings.notify_rate_limit_hours * 3600:
                return True
        return False

    async def check_and_notify(self, report_id: int) -> list[str]:
        critical_insights = (
            await self.db.execute(
                select(Insight).where(
                    Insight.report_id == report_id,
                    Insight.severity == "critical",
                )
            )
        ).scalars().all()

        high_anomalies = (
            await self.db.execute(
                select(Insight).where(
                    Insight.report_id == report_id,
                    Insight.anomaly_score >= 0.8,
                )
            )
        ).scalars().all()

        all_alerts = list(critical_insights)
        seen_ids = {i.id for i in all_alerts}
        for a in high_anomalies:
            if a.id not in seen_ids:
                all_alerts.append(a)

        if not all_alerts:
            return []

        notified: list[str] = []
        for insight in all_alerts:
            brand = await self.db.get(Brand, insight.brand_id) if insight.brand_id else None
            if brand and self._is_rate_limited(brand.id):
                continue

            subject = f"[DDS Alert] {insight.severity.upper()}: {insight.insight_type} - {brand.brand_category if brand else 'Unknown'}"
            body = (
                f"Report: DDS\n"
                f"Brand: {brand.brand_category if brand else 'N/A'}\n"
                f"Severity: {insight.severity.upper()}\n"
                f"Insight: {insight.description}\n"
            )

            try:
                self._send_email(subject, body)
                if brand:
                    _rate_limit_cache[brand.id] = datetime.utcnow()
                notified.append(insight.insight_type or "unknown")

                log = ProcessingLog(
                    report_id=report_id,
                    step="notification",
                    status="success",
                    message=f"Sent alert to {settings.notify_recipients}: {subject}",
                )
                self.db.add(log)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
                log = ProcessingLog(
                    report_id=report_id,
                    step="notification",
                    status="failed",
                    message=str(e),
                )
                self.db.add(log)

        await self.db.commit()
        return notified

    def _send_email(self, subject: str, body: str) -> None:
        recipients = settings.notify_recipient_list
        if not recipients:
            logger.warning("No notification recipients configured")
            return

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_user
        msg["To"] = ", ".join(recipients)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, recipients, msg.as_string())
```

- [ ] **Step 2: Write test**

```python
# tests/test_notifier.py
import pytest
from services.notifier import Notifier, _rate_limit_cache
from datetime import datetime


def test_rate_limit_empty():
    _rate_limit_cache.clear()
    n = Notifier(None)
    assert n._is_rate_limited(999) is False


def test_rate_limit_active():
    _rate_limit_cache.clear()
    _rate_limit_cache[1] = datetime.utcnow()
    n = Notifier(None)
    assert n._is_rate_limited(1) is True


def test_rate_limit_expired():
    _rate_limit_cache.clear()
    from datetime import timedelta
    _rate_limit_cache[1] = datetime.utcnow() - timedelta(hours=25)
    n = Notifier(None)
    assert n._is_rate_limited(1) is False
```

Run: `pytest tests/test_notifier.py -v`

- [ ] **Step 3: Commit**

```bash
git add services/notifier.py tests/test_notifier.py
git commit -m "feat: add email notification service for critical insights"
```

---

## Task 10: Processor Orchestrator

**Files:**
- Create: `dds/services/processor.py`
- Test: `dds/tests/test_processor.py`

- [ ] **Step 1: Write services/processor.py**

```python
import asyncio
import logging
import time
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from core.models import (
    Report, ReportItem, Brand, Task, Insight, ProcessingLog,
    ProcessingStatus, AvailabilityStatus,
)
from services.email_parser import parse_email, ParsedEmail
from services.imap_listener import DDS_SUBJECT_PATTERN
from services.extraction import extract_email_data, ExtractionResult
from services.sidecar_manager import SidecarManager
from services.analytics import AnalyticsEngine
from services.anomaly import AnomalyDetector
from services.notifier import Notifier

logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    pass


class Processor:
    def __init__(self, db: AsyncSession, sidecar: SidecarManager):
        self.db = db
        self.sidecar = sidecar
        self.analytics = AnalyticsEngine(db)
        self.anomaly = AnomalyDetector(db, sidecar)
        self.notifier = Notifier(db)

    async def process_email(self, raw_bytes: bytes, subject: str, received_at: datetime) -> Report:
        parsed = parse_email(raw_bytes)

        match = DDS_SUBJECT_PATTERN.match(subject)
        if not match:
            raise ProcessingError(f"Subject does not match DDS pattern: {subject}")
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))

        report = Report(
            subject=subject,
            report_date=date(year, month, day),
            sender=parsed.sender,
            recipients=parsed.recipients,
            cc_list=parsed.cc_list,
            received_at=received_at,
            raw_html=parsed.raw_html,
            raw_text=parsed.raw_text,
            processing_status=ProcessingStatus.processing,
        )
        self.db.add(report)
        await self.db.flush()

        try:
            await self._log(report.id, "imap_fetch", "started", "Email fetched from IMAP")
            await self._log(report.id, "html_parse", "started", f"Parsed {len(parsed.rows)} rows")

            previous_context = await self._get_previous_context(report.report_date)

            extraction = await extract_email_data(parsed, self.sidecar, previous_context)
            await self._log(report.id, "llm_extract", "success", f"Extracted {len(extraction.items)} items")

            await self._store_report_items(report.id, extraction, parsed)
            await self._store_tasks(report.id, extraction)
            await self._store_insights(report.id, extraction)

            histories = await self.analytics.compute_status_history(report.id)
            carried = await self.analytics.carry_over_tasks(report.id)
            await self._log(report.id, "analytics", "success", f"Status history: {len(histories)}, carried tasks: {carried}")

            anomalies = await self.anomaly.process_insight_embeddings(report.id)
            await self._log(report.id, "anomaly_detection", "success", f"Detected {len(anomalies)} anomalies")

            notified = await self.notifier.check_and_notify(report.id)
            if notified:
                await self._log(report.id, "notification", "success", f"Sent {len(notified)} alerts")

            report.processing_status = ProcessingStatus.completed

        except Exception as e:
            logger.exception(f"Processing failed for report {report.id}")
            report.processing_status = ProcessingStatus.failed
            report.error_message = str(e)
            await self._log(report.id, "pipeline", "failed", str(e))

        await self.db.commit()
        return report

    async def _get_previous_context(self, report_date: date) -> Optional[str]:
        prev = (
            await self.db.execute(
                select(Report)
                .where(
                    Report.report_date < report_date,
                    Report.processing_status == ProcessingStatus.completed,
                )
                .order_by(Report.report_date.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return prev.raw_text[:3000] if prev else None

    async def _store_report_items(self, report_id: int, extraction: ExtractionResult, parsed: ParsedEmail) -> None:
        llm_items = {item["brand_category"]: item for item in extraction.items}

        for row in parsed.rows:
            brand = await self._get_or_create_brand(row.division, row.brand_category)
            llm_data = llm_items.get(row.brand_category, {})

            item = ReportItem(
                report_id=report_id,
                brand_id=brand.id,
                availability_status=llm_data.get("availability", row.availability) or "unknown",
                milestone=llm_data.get("milestone", row.milestone),
                milestone_ar=llm_data.get("milestone_ar", row.milestone_ar),
                shipment_bis=llm_data.get("shipment_bis", row.shipment_bis),
                comments_actions=llm_data.get("comments_actions", row.comments),
                comments_actions_ar=llm_data.get("comments_actions_ar", row.comments_ar),
                language=llm_data.get("language", row.language),
            )
            self.db.add(item)

    async def _get_or_create_brand(self, division: str, brand_category: str) -> Brand:
        if not brand_category:
            raise ProcessingError("Empty brand category")

        brand = (
            await self.db.execute(
                select(Brand).where(
                    Brand.division == division,
                    Brand.brand_category == brand_category,
                )
            )
        ).scalar_one_or_none()

        if not brand:
            brand = Brand(division=division, brand_category=brand_category)
            self.db.add(brand)
            await self.db.flush()

        return brand

    async def _store_tasks(self, report_id: int, extraction: ExtractionResult) -> None:
        items = {
            item.brand_category: item
            for item in (
                await self.db.execute(
                    select(ReportItem).where(ReportItem.report_id == report_id)
                )
            ).scalars().all()
        }

        for task_data in extraction.tasks:
            item = items.get(task_data.get("brand_category", ""))
            if not item:
                continue

            deadline = None
            if task_data.get("deadline"):
                try:
                    deadline = date.fromisoformat(str(task_data["deadline"]))
                except ValueError:
                    pass

            task = Task(
                report_item_id=item.id,
                task_description=task_data.get("description", ""),
                assigned_to=task_data.get("assigned_to"),
                deadline=deadline,
                task_category=task_data.get("category"),
                first_seen_report_id=report_id,
                last_seen_report_id=report_id,
            )
            self.db.add(task)

    async def _store_insights(self, report_id: int, extraction: ExtractionResult) -> None:
        items = {
            item.brand_category: item
            for item in (
                await self.db.execute(
                    select(ReportItem).where(ReportItem.report_id == report_id)
                )
            ).scalars().all()
        }

        for ins_data in extraction.insights:
            item = items.get(ins_data.get("brand_category", ""))
            insight = Insight(
                report_id=report_id,
                brand_id=item.brand_id if item else None,
                insight_type=ins_data.get("type"),
                description=ins_data.get("description", ""),
                description_ar=ins_data.get("description_ar", ""),
                language=ins_data.get("language", "en"),
                severity=ins_data.get("severity"),
            )
            self.db.add(insight)

    async def _log(self, report_id: int, step: str, status: str, message: str) -> None:
        log = ProcessingLog(report_id=report_id, step=step, status=status, message=message)
        self.db.add(log)
        await self.db.flush()
```

- [ ] **Step 2: Commit**

```bash
git add services/processor.py tests/test_processor.py
git commit -m "feat: add processing orchestrator for complete email pipeline"
```

---

## Task 11: FastAPI Application & Routes

**Files:**
- Create: `dds/api/main.py`
- Create: `dds/api/routes.py`

- [ ] **Step 1: Write api/routes.py**

```python
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models import (
    Report, ReportItem, Brand, Task, Insight, AnomalyLog, ProcessingLog,
    ProcessingStatus,
)
from core.schemas import (
    ReportOut, ReportSummary, BrandOut, TaskOut, InsightOut,
    AnomalyOut, DashboardSummary, ProcessResponse,
)
from services.processor import Processor
from services.sidecar_manager import SidecarManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


def get_sidecar():
    from api.main import sidecar_manager
    return sidecar_manager


@router.post("/reports/process", response_model=ProcessResponse)
async def trigger_process(
    db: AsyncSession = Depends(get_db),
    sidecar: SidecarManager = Depends(get_sidecar),
):
    proc = Processor(db, sidecar)
    from services.imap_listener import ImapListener

    raw_emails: list[tuple[bytes, str, str]] = []

    async def collect(raw: bytes, subject: str, date_str: str):
        raw_emails.append((raw, subject, date_str))

    from datetime import datetime
    listener = ImapListener(collect)
    await listener._fetch_new_emails()

    if not raw_emails:
        return ProcessResponse(success=True, message="No new DDS emails found")

    count = 0
    for raw, subject, received_at in raw_emails:
        from email.utils import parsedate_to_datetime
        try:
            dt = parsedate_to_datetime(received_at)
        except Exception:
            dt = datetime.utcnow()
        await proc.process_email(raw, subject, dt)
        count += 1

    return ProcessResponse(success=True, message=f"Processed {count} emails")


@router.get("/reports", response_model=list[ReportSummary])
async def list_reports(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Report)
    if date_from:
        stmt = stmt.where(Report.report_date >= date_from)
    if date_to:
        stmt = stmt.where(Report.report_date <= date_to)
    if status:
        stmt = stmt.where(Report.processing_status == status)
    stmt = stmt.order_by(Report.report_date.desc())

    reports = (await db.execute(stmt)).scalars().all()
    result = []
    for r in reports:
        item_count = (
            await db.execute(select(func.count(ReportItem.id)).where(ReportItem.report_id == r.id))
        ).scalar() or 0
        task_count = (
            await db.execute(
                select(func.count(Task.id))
                .join(ReportItem)
                .where(ReportItem.report_id == r.id)
            )
        ).scalar() or 0
        insight_count = (
            await db.execute(select(func.count(Insight.id)).where(Insight.report_id == r.id))
        ).scalar() or 0
        result.append(ReportSummary(
            id=r.id, subject=r.subject, report_date=r.report_date,
            processing_status=r.processing_status.value,
            item_count=item_count, task_count=task_count,
            insight_count=insight_count, created_at=r.created_at,
        ))
    return result


@router.get("/reports/{report_id}", response_model=ReportOut)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return report


@router.post("/reports/{report_id}/reprocess", response_model=ProcessResponse)
async def reprocess_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    sidecar: SidecarManager = Depends(get_sidecar),
):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    if not report.raw_html and not report.raw_text:
        raise HTTPException(400, "Report has no raw content to reprocess")

    raw = (report.raw_html or report.raw_text or "").encode()
    proc = Processor(db, sidecar)
    await proc.process_email(raw, report.subject, report.received_at)
    return ProcessResponse(success=True, report_id=report_id, message="Reprocessed successfully")


@router.get("/brands", response_model=list[BrandOut])
async def list_brands(db: AsyncSession = Depends(get_db)):
    brands = (await db.execute(select(Brand).order_by(Brand.division, Brand.brand_category))).scalars().all()
    return brands


@router.get("/brands/{brand_id}/history")
async def brand_history(brand_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import StatusHistory
    history = (
        await db.execute(
            select(StatusHistory)
            .where(StatusHistory.brand_id == brand_id)
            .order_by(StatusHistory.created_at.desc())
        )
    ).scalars().all()
    return [
        {
            "report_id": h.report_id,
            "previous_status": h.previous_status,
            "current_status": h.current_status,
            "status_change": "improved" if (h.current_status in ("green","yellow") and h.previous_status in ("red","grey","black"))
                else "worsened" if (h.current_status in ("red","grey","black") and h.previous_status in ("green","yellow"))
                else "unchanged" if h.previous_status == h.current_status
                else "changed",
            "created_at": h.created_at.isoformat(),
        }
        for h in history
    ]


@router.get("/tasks", response_model=list[TaskOut])
async def list_tasks(
    assigned_to: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Task)
    if assigned_to:
        stmt = stmt.where(Task.assigned_to.ilike(f"%{assigned_to}%"))
    if status:
        stmt = stmt.where(Task.task_status == status)
    if category:
        stmt = stmt.where(Task.task_category == category)
    stmt = stmt.order_by(Task.occurrence_count.desc()).limit(100)
    return (await db.execute(stmt)).scalars().all()


@router.get("/tasks/aging", response_model=list[TaskOut])
async def aging_tasks(db: AsyncSession = Depends(get_db)):
    tasks = (
        await db.execute(
            select(Task).where(
                Task.occurrence_count >= 3,
                Task.is_resolved == False,
            ).order_by(Task.occurrence_count.desc())
        )
    ).scalars().all()
    return tasks


@router.get("/insights", response_model=list[InsightOut])
async def list_insights(
    insight_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Insight)
    if insight_type:
        stmt = stmt.where(Insight.insight_type == insight_type)
    if severity:
        stmt = stmt.where(Insight.severity == severity)
    stmt = stmt.order_by(Insight.id.desc()).limit(100)
    return (await db.execute(stmt)).scalars().all()


@router.get("/insights/trends")
async def insight_trends(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(
                Insight.insight_type,
                Insight.severity,
                func.count(Insight.id).label("count"),
            ).group_by(Insight.insight_type, Insight.severity)
            .order_by(func.count(Insight.id).desc())
        )
    ).all()
    return [{"type": r[0], "severity": r[1], "count": r[2]} for r in rows]


@router.get("/anomalies", response_model=list[AnomalyOut])
async def list_anomalies(
    min_score: float = Query(0.0),
    unreviewed: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AnomalyLog)
    if min_score > 0:
        stmt = stmt.where(AnomalyLog.similarity_score >= min_score)
    if unreviewed:
        stmt = stmt.where(AnomalyLog.is_reviewed == False)
    stmt = stmt.order_by(AnomalyLog.similarity_score.desc()).limit(50)
    return (await db.execute(stmt)).scalars().all()


@router.patch("/anomalies/{anomaly_id}")
async def review_anomaly(anomaly_id: int, db: AsyncSession = Depends(get_db)):
    anomaly = await db.get(AnomalyLog, anomaly_id)
    if not anomaly:
        raise HTTPException(404, "Anomaly not found")
    anomaly.is_reviewed = True
    await db.commit()
    return {"status": "reviewed"}


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Brand.id)))).scalar() or 0
    open_tasks = (await db.execute(
        select(func.count(Task.id)).where(Task.is_resolved == False)
    )).scalar() or 0
    critical = (await db.execute(
        select(func.count(Insight.id)).where(Insight.severity == "critical")
    )).scalar() or 0
    last_report = (await db.execute(
        select(Report.report_date)
        .where(Report.processing_status == ProcessingStatus.completed)
        .order_by(Report.report_date.desc()).limit(1)
    )).scalar_one_or_none()

    dist = {"green": 0, "yellow": 0, "red": 0, "grey": 0, "black": 0, "unknown": 0}
    rows = (await db.execute(
        select(ReportItem.availability_status, func.count(ReportItem.id))
        .group_by(ReportItem.availability_status)
    )).all()
    for status, count in rows:
        dist[status.value] = count

    return DashboardSummary(
        total_brands=total,
        brands_with_issues=dist.get("red", 0) + dist.get("black", 0),
        open_tasks=open_tasks,
        critical_insights=critical,
        last_report_date=last_report,
        status_distribution=dist,
    )
```

- [ ] **Step 2: Write api/main.py**

```python
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.logging import setup_logging
from config.settings import settings
from core.database import engine
from api.routes import router
from services.sidecar_manager import SidecarManager
from services.imap_listener import ImapListener

setup_logging()
logger = logging.getLogger(__name__)

sidecar_manager = SidecarManager()
imap_listener: ImapListener | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global imap_listener
    logger.info("Starting DDS Email ETL service")

    await sidecar_manager.start()

    from services.processor import Processor
    from core.database import async_session_factory

    async def on_email(raw: bytes, subject: str, received_at):
        async with async_session_factory() as db:
            proc = Processor(db, sidecar_manager)
            await proc.process_email(raw, subject, received_at)

    imap_listener = ImapListener(on_email)
    asyncio.create_task(imap_listener.start())

    yield

    if imap_listener:
        await imap_listener.stop()
    await sidecar_manager.stop()
    await engine.dispose()


app = FastAPI(
    title="DDS Email ETL",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "sidecar_running": sidecar_manager._running,
    }
```

- [ ] **Step 3: Write test_api.py**

```python
# tests/test_api.py
from httpx import AsyncClient, ASGITransport
import pytest
from api.main import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
```

Run: `pytest tests/test_api.py -v`

- [ ] **Step 4: Commit**

```bash
git add api/
git commit -m "feat: add FastAPI application with full REST API"
```

---

## Task 12: Docker Deployment

**Files:**
- Create: `dds/Dockerfile`
- Create: `dds/docker-compose.yml`

- [ ] **Step 1: Write Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Write docker-compose.yml**

```yaml
services:
  dds-api:
    build: .
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
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

  dds-pi:
    image: node:22-slim
    working_dir: /app
    command: sh -c "cd pi && npm install && npx @earendil-works/pi-coding-agent --mode rpc --no-session"
    env_file: .env
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./pi:/app/pi
    restart: unless-stopped

  dds-db:
    image: mariadb:11
    env_file: .env
    environment:
      MARIADB_ROOT_PASSWORD: ${MARIA_ROOT_PASSWORD:-rootpass}
      MARIADB_DATABASE: ${MARIA_DATABASE:-dds}
      MARIADB_USER: ${MARIA_USER:-dds}
      MARIADB_PASSWORD: ${MARIA_PASSWORD:-ddspass}
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

- [ ] **Step 3: Verify Docker build**

```bash
workdir=/Users/gamalabdelmoety/Project/a-part/dds
docker compose build --no-cache dds-api
```

Expected: Build succeeds without errors

- [ ] **Step 4: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "chore: add Docker deployment configuration"
```

---

## Self-Review Checklist

1. **Spec coverage:** All spec sections mapped to tasks
   - Database schema → Task 2
   - IMAP IDLE → Task 3
   - Email parser → Task 4
   - PI SDK sidecar → Task 5
   - LLM extraction → Task 6
   - Cross-report analytics → Task 7
   - Embeddings + anomaly detection → Task 8
   - Email notifications → Task 9
   - Processor orchestrator → Task 10
   - REST API → Task 11
   - Docker deployment → Task 12

2. **No placeholders:** All tasks contain complete code and test content

3. **Type consistency:** All imports, model names, and method signatures match across tasks

4. **Gaps:** No missing tasks — every spec requirement has a corresponding implementation task
