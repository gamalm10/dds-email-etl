import enum
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: UP017

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.mysql import LONGBLOB, LONGTEXT
from sqlalchemy.orm import DeclarativeBase, relationship, backref


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
    created_at = Column(DateTime, default=_utcnow)

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
    raw_html = Column(LONGTEXT)
    raw_text = Column(LONGTEXT)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.pending)
    error_message = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    items = relationship("ReportItem", back_populates="report", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="report")
    insights = relationship("Insight", back_populates="report", cascade="all, delete-orphan")
    processing_logs = relationship("ProcessingLog", back_populates="report", cascade="all, delete-orphan")
    priority_actions = relationship("PriorityAction", back_populates="report", cascade="all, delete-orphan")
    thread_summary_rel = relationship("ThreadSummary", back_populates="report", cascade="all, delete-orphan", uselist=False)


class ReportItem(Base):
    __tablename__ = "dds_report_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("dds_brands.id"), nullable=False)
    vendor = Column(String(255))
    availability_status = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.unknown)
    milestone = Column(Text)
    milestone_ar = Column(Text)
    shipment_bis = Column(Text)
    comments_actions = Column(Text)
    comments_actions_ar = Column(Text)
    quantity_text = Column(String(255))
    financial_text = Column(String(255))
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=_utcnow)

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
    created_at = Column(DateTime, default=_utcnow)

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
    is_overdue = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    resolved_at_report_id = Column(Integer, ForeignKey("dds_reports.id"))
    embedding = Column(LONGBLOB)
    deadline_text = Column(String(50))
    quantity_value = Column(Integer)
    financial_value = Column(DECIMAL(12, 2))
    currency = Column(String(10))

    report_item = relationship("ReportItem", back_populates="tasks")
    first_seen_report = relationship("Report", foreign_keys=[first_seen_report_id])
    last_seen_report = relationship("Report", foreign_keys=[last_seen_report_id])
    resolved_at_report = relationship("Report", foreign_keys=[resolved_at_report_id])


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
    impact = Column(Text)
    recommendation = Column(Text)
    risk_tags = Column(Text)
    vendor = Column(String(255))

    report = relationship("Report", back_populates="insights")
    brand = relationship("Brand", back_populates="insights")
    matched_anomaly = relationship("Insight", remote_side=[id], foreign_keys=[matched_anomaly_id])
    related_task = relationship("Task", foreign_keys=[related_task_id])


class AnomalyLog(Base):
    __tablename__ = "dds_anomaly_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_insight_id = Column(Integer, ForeignKey("dds_insights.id"), nullable=False)
    matched_insight_id = Column(Integer, ForeignKey("dds_insights.id"), nullable=False)
    similarity_score = Column(DECIMAL(5, 4), nullable=False)
    source_report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    matched_report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    detected_at = Column(DateTime, default=_utcnow)
    is_reviewed = Column(Boolean, default=False)

    source_insight = relationship("Insight", foreign_keys=[source_insight_id])
    matched_insight = relationship("Insight", foreign_keys=[matched_insight_id])
    source_report = relationship("Report", foreign_keys=[source_report_id])
    matched_report = relationship("Report", foreign_keys=[matched_report_id])


class ProcessingLog(Base):
    __tablename__ = "dds_processing_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    step = Column(String(50))
    status = Column(String(20))
    message = Column(Text)
    duration_ms = Column(Integer)
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report", back_populates="processing_logs")


class PriorityAction(Base):
    __tablename__ = "dds_priority_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    person = Column(String(100), nullable=False)
    action = Column(Text, nullable=False)
    action_ar = Column(Text)
    category = Column(String(100))
    urgency = Column(String(20))
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report")


class ThreadSummary(Base):
    __tablename__ = "dds_thread_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False, unique=True)
    total_anomalies = Column(Integer, default=0)
    critical_items = Column(Text)
    overall_health = Column(String(20))
    key_risks = Column(Text)
    sales_timeline = Column(Text)
    priority_matrix = Column(Text)
    key_highlights = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report")
