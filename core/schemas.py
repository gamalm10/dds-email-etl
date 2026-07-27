from datetime import date, datetime

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
    milestone: str | None = None
    milestone_ar: str | None = None
    shipment_bis: str | None = None
    comments_actions: str | None = None
    comments_actions_ar: str | None = None
    language: str = "en"
    tasks: list[TaskOut] = []

    class Config:
        from_attributes = True


class ReportOut(BaseModel):
    id: int
    subject: str
    report_date: date
    sender: str | None = None
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


class ProcessResponse(BaseModel):
    success: bool
    report_id: int | None = None
    message: str
    items_extracted: int = 0
    tasks_extracted: int = 0
    insights_generated: int = 0
