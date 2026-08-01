from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


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
    assigned_to: str | None = None
    deadline: date | None = None
    task_category: str | None = None
    task_status: str = "open"
    priority: str = "medium"
    occurrence_count: int = 1
    is_resolved: bool = False

    class Config:
        from_attributes = True


class InsightOut(BaseModel):
    id: int
    insight_type: str | None = None
    description: str
    description_ar: str | None = None
    severity: str | None = None
    anomaly_score: float | None = None

    class Config:
        from_attributes = True


class ReportItemOut(BaseModel):
    id: int
    brand: BrandOut
    availability_status: str
    vendor: str | None = None
    milestone: str | None = None
    milestone_ar: str | None = None
    shipment_bis: str | None = None
    comments_actions: str | None = None
    comments_actions_ar: str | None = None
    quantity_text: str | None = None
    financial_text: str | None = None
    language: str = "en"
    tasks: list[TaskOut] = []

    class Config:
        from_attributes = True


class PriorityActionOut(BaseModel):
    id: int
    person: str
    action: str
    action_ar: str | None = None
    category: str | None = None
    urgency: str | None = None

    class Config:
        from_attributes = True


class ThreadSummaryOut(BaseModel):
    id: int
    total_anomalies: int = 0
    critical_items: str | None = None
    overall_health: str | None = None
    key_risks: str | None = None
    sales_timeline: str | None = None
    priority_matrix: str | None = None
    key_highlights: str | None = None

    class Config:
        from_attributes = True


class ReportOut(BaseModel):
    id: int
    subject: str
    report_date: date
    sender: str | None = None
    received_at: datetime
    processing_status: str
    risk_score: int = 0
    risk_category: str | None = None
    items: list[ReportItemOut] = []
    insights: list[InsightOut] = []
    priority_actions: list[PriorityActionOut] = []
    thread_summary: ThreadSummaryOut | None = None

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
    last_report_date: date | None = None
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


class ClearanceMaterialOut(BaseModel):
    id: int
    material_code: str | None = None
    description: str | None = None
    description_ar: str | None = None
    quantity: int | None = None

    class Config:
        from_attributes = True


class OrderingRuleOut(BaseModel):
    id: int
    max_amount_usd: float | None = None
    max_amount_eur: float | None = None
    margin_percent: float | None = None
    sales_months: int | None = None
    requires_approval: bool = True
    rule_text: str | None = None

    class Config:
        from_attributes = True


class EmailThreadOut(BaseModel):
    id: int
    thread_index: int | None = None
    subject: str | None = None
    sender: str | None = None
    sent_at: datetime | None = None
    depth: int = 0
    is_dds_email: bool = False
    brand_count: int = 0

    class Config:
        from_attributes = True


class SignatureOut(BaseModel):
    id: int
    person_name: str | None = None
    title: str | None = None
    company: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None

    class Config:
        from_attributes = True


class EmailImageOut(BaseModel):
    id: int
    content_id: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    filename: str | None = None

    class Config:
        from_attributes = True


class PercentageMetricOut(BaseModel):
    id: int
    metric_type: str | None = None
    value: float | None = None
    context: str | None = None
    raw_text: str | None = None

    class Config:
        from_attributes = True


class RiskLanguageOut(BaseModel):
    id: int
    phrase: str | None = None
    category: str | None = None
    severity_score: int = 0
    context: str | None = None

    class Config:
        from_attributes = True


class PaymentTermOut(BaseModel):
    id: int
    payment_method: str | None = None
    deposit_pct: float | None = None
    balance_pct: float | None = None
    expected_date: date | None = None

    class Config:
        from_attributes = True


class NegotiationOut(BaseModel):
    id: int
    type: str | None = None
    percentage: float | None = None
    status: str = "proposed"
    context: str | None = None

    class Config:
        from_attributes = True


class LeadTimeOut(BaseModel):
    id: int
    days: int | None = None
    reference_date: date | None = None
    status: str | None = None
    context: str | None = None

    class Config:
        from_attributes = True


class ProcessResponse(BaseModel):
    success: bool
    report_id: Optional[int] = None
    message: str
    items_extracted: int = 0
    tasks_extracted: int = 0
    insights_generated: int = 0
