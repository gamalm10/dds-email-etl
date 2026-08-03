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
    risk_score = Column(Integer, default=0)
    risk_category = Column(String(50))
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


class ClearanceMaterial(Base):
    __tablename__ = "dds_clearance_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    material_code = Column(String(100))
    description = Column(Text)
    description_ar = Column(Text)
    quantity = Column(Integer)
    quantity_other = Column(Integer)
    brand_id = Column(Integer, ForeignKey("dds_brands.id"))
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report")
    brand = relationship("Brand")


class OrderingRule(Base):
    __tablename__ = "dds_ordering_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    max_amount_usd = Column(DECIMAL(12, 2))
    max_amount_eur = Column(DECIMAL(12, 2))
    margin_percent = Column(DECIMAL(5, 2))
    sales_months = Column(Integer)
    requires_approval = Column(Boolean, default=True)
    rule_text = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report")


class EmailThread(Base):
    __tablename__ = "dds_email_threads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    message_id = Column(String(255))
    thread_index = Column(Integer)
    subject = Column(String(255))
    sender = Column(String(255))
    sent_at = Column(DateTime)
    depth = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey("dds_email_threads.id"))
    is_dds_email = Column(Boolean, default=False)
    brand_count = Column(Integer, default=0)
    has_table = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report")
    parent = relationship("EmailThread", remote_side=[id])


class Signature(Base):
    __tablename__ = "dds_signatures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    sender_email = Column(String(255))
    person_name = Column(String(255))
    title = Column(String(255))
    company = Column(String(255))
    phone = Column(String(100))
    email = Column(String(255))
    address = Column(Text)
    raw_text = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report")


class EmailImage(Base):
    __tablename__ = "dds_email_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    content_id = Column(String(255))
    content_type = Column(String(100))
    size_bytes = Column(Integer)
    filename = Column(String(255))
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report")


class PercentageMetric(Base):
    __tablename__ = "dds_percentage_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("dds_brands.id"))
    metric_type = Column(String(50))
    value = Column(DECIMAL(10, 2))
    context = Column(Text)
    raw_text = Column(String(255))
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report")
    brand = relationship("Brand")


class RiskLanguage(Base):
    __tablename__ = "dds_risk_language"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("dds_brands.id"))
    phrase = Column(String(255))
    category = Column(String(50))
    severity_score = Column(Integer, default=0)
    context = Column(Text)
    raw_text = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report")
    brand = relationship("Brand")


class PaymentTerm(Base):
    __tablename__ = "dds_payment_terms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("dds_brands.id"))
    payment_method = Column(String(100))
    deposit_pct = Column(DECIMAL(5, 2))
    balance_pct = Column(DECIMAL(5, 2))
    expected_date = Column(Date)
    raw_text = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report")
    brand = relationship("Brand")


class Negotiation(Base):
    __tablename__ = "dds_negotiations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("dds_brands.id"))
    type = Column(String(50))
    percentage = Column(DECIMAL(5, 2))
    status = Column(String(50), default="proposed")
    context = Column(Text)
    raw_text = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report")
    brand = relationship("Brand")


class LeadTime(Base):
    __tablename__ = "dds_lead_times"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("dds_brands.id"))
    days = Column(Integer)
    reference_date = Column(Date)
    status = Column(String(50))
    context = Column(Text)
    raw_text = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    report = relationship("Report")
    brand = relationship("Brand")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    permissions = Column(Text)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow)

    role = relationship("Role")


class PasswordResetOtp(Base):
    __tablename__ = "password_reset_otps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False)
    otp_code = Column(String(10), nullable=False)
    otp_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)


class OtpRateLimit(Base):
    __tablename__ = "otp_rate_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    request_count = Column(Integer, default=1)
    last_request_at = Column(DateTime, default=_utcnow)


class FetchedEmail(Base):
    __tablename__ = "dds_fetched_emails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(50))
    subject = Column(Text)
    sender = Column(String(255))
    received_at = Column(DateTime)
    fetched_at = Column(DateTime, default=_utcnow)
    processing_status = Column(String(20), default="pending")
    report_id = Column(Integer, ForeignKey("dds_reports.id"), nullable=True)
    error_message = Column(Text, nullable=True)
