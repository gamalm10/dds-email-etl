import logging
import os
from dataclasses import dataclass

from openai import OpenAI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    AnomalyLog,
    Brand,
    ClearanceMaterial,
    Insight,
    LeadTime,
    Negotiation,
    PaymentTerm,
    PercentageMetric,
    PriorityAction,
    ReportItem,
    RiskLanguage,
    StatusHistory,
    Task,
    ThreadSummary,
)

logger = logging.getLogger(__name__)

TOP_K = 20
SIMILARITY_THRESHOLD = 0.5


@dataclass
class RetrievalResult:
    source_type: str
    source_id: int
    report_id: int
    brand_name: str | None
    chunk_text: str
    score: float
    metadata: dict | None = None


def _get_embedding(text_str: str) -> list[float] | None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        client = OpenAI(api_key=api_key)
        resp = client.embeddings.create(model="text-embedding-3-small", input=text_str)
        return resp.data[0].embedding
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        return None


def _embedding_to_vec_text(embedding: list[float]) -> str:
    return "[" + ",".join(str(x) for x in embedding) + "]"


async def _structured_search(
    db: AsyncSession, query: str, report_id: int | None = None, brand_id: int | None = None
) -> list[RetrievalResult]:
    results = []
    terms = [t.strip() for t in query.split() if len(t.strip()) >= 2]
    q_lower = query.lower()

    # 1. Report Items
    item_q = (
        select(ReportItem.id, ReportItem.report_id, ReportItem.brand_id,
               Brand.brand_category, ReportItem.comments_actions, ReportItem.milestone,
               ReportItem.etd, ReportItem.eta, ReportItem.ready_for_sale,
               ReportItem.quantity_text, ReportItem.financial_text, ReportItem.availability_status)
        .join(Brand, ReportItem.brand_id == Brand.id, isouter=True)
    )
    if report_id:
        item_q = item_q.where(ReportItem.report_id == report_id)
    if brand_id:
        item_q = item_q.where(ReportItem.brand_id == brand_id)
    for row in (await db.execute(item_q)).all():
        chunk = f"Brand: {row.brand_category or 'Unknown'} | Status: {row.milestone or ''} | Availability: {row.availability_status or ''} | ETD: {row.etd or ''} | ETA: {row.eta or ''} | Ready: {row.ready_for_sale or ''} | Qty: {row.quantity_text or ''} | Financial: {row.financial_text or ''} | Comments: {row.comments_actions or ''}"
        score = 0.5
        if row.brand_category and row.brand_category.lower() in q_lower:
            score += 0.3
        if terms and any(t.lower() in (row.comments_actions or "").lower() for t in terms):
            score += 0.2
        results.append(RetrievalResult("report_item", row.id, row.report_id, row.brand_category, chunk, min(score, 1.0)))

    # 2. Tasks
    task_q = select(Task)
    if report_id:
        task_q = task_q.where(Task.first_seen_report_id == report_id)
    for task in (await db.execute(task_q)).scalars().all():
        chunk = f"Task: {task.task_description} | Assigned: {task.assigned_to or ''} | Deadline: {task.deadline_text or ''} | Status: {task.task_status} | Priority: {task.priority} | Category: {task.task_category or ''} | Overdue: {task.is_overdue} | Blocked: {task.is_blocked}"
        score = 0.4
        if terms and any(t.lower() in (task.task_description or "").lower() for t in terms):
            score += 0.3
        if task.assigned_to and any(t.lower() in task.assigned_to.lower() for t in terms):
            score += 0.2
        results.append(RetrievalResult("task", task.id, task.first_seen_report_id or 0, None, chunk, min(score, 1.0)))

    # 3. Insights
    ins_q = select(Insight)
    if report_id:
        ins_q = ins_q.where(Insight.report_id == report_id)
    if brand_id:
        ins_q = ins_q.where(Insight.brand_id == brand_id)
    for ins in (await db.execute(ins_q)).scalars().all():
        chunk = f"Insight: {ins.description} | Type: {ins.insight_type or ''} | Severity: {ins.severity or ''} | Impact: {ins.impact or ''} | Recommendation: {ins.recommendation or ''} | Vendor: {ins.vendor or ''}"
        score = 0.4
        if terms and any(t.lower() in (ins.description or "").lower() for t in terms):
            score += 0.3
        results.append(RetrievalResult("insight", ins.id, ins.report_id, None, chunk, min(score, 1.0)))

    # 4. Priority Actions
    pa_q = select(PriorityAction)
    if report_id:
        pa_q = pa_q.where(PriorityAction.report_id == report_id)
    for pa in (await db.execute(pa_q)).scalars().all():
        chunk = f"Action: {pa.action} | Person: {pa.person} | Urgency: {pa.urgency or ''} | Category: {pa.category or ''}"
        score = 0.4
        if pa.person and any(t.lower() in pa.person.lower() for t in terms):
            score += 0.3
        results.append(RetrievalResult("priority_action", pa.id, pa.report_id, None, chunk, min(score, 1.0)))

    # 5. Payment Terms
    pt_q = select(PaymentTerm)
    if report_id:
        pt_q = pt_q.where(PaymentTerm.report_id == report_id)
    for pt in (await db.execute(pt_q)).scalars().all():
        chunk = f"Payment: {pt.payment_method or ''} | Deposit: {pt.deposit_pct or ''}% | Balance: {pt.balance_pct or ''}% | Date: {pt.expected_date or ''}"
        score = 0.3
        if any(t.lower() in q_lower for t in ["payment", "deposit", "balance"]):
            score += 0.3
        results.append(RetrievalResult("payment_term", pt.id, pt.report_id, None, chunk, min(score, 1.0)))

    # 6. Negotiations
    neg_q = select(Negotiation)
    if report_id:
        neg_q = neg_q.where(Negotiation.report_id == report_id)
    for neg in (await db.execute(neg_q)).scalars().all():
        chunk = f"Negotiation: {neg.type or ''} | {neg.percentage or ''}% | Status: {neg.status} | Context: {neg.context or ''}"
        score = 0.3
        if any(t.lower() in q_lower for t in ["discount", "negotiation", "agreed"]):
            score += 0.3
        results.append(RetrievalResult("negotiation", neg.id, neg.report_id, None, chunk, min(score, 1.0)))

    # 7. Lead Times
    lt_q = select(LeadTime)
    if report_id:
        lt_q = lt_q.where(LeadTime.report_id == report_id)
    for lt in (await db.execute(lt_q)).scalars().all():
        chunk = f"Lead Time: {lt.days} days | Status: {lt.status or ''} | Context: {lt.context or ''}"
        score = 0.3
        if any(t.lower() in q_lower for t in ["lead time", "leadtime", "production time"]):
            score += 0.3
        results.append(RetrievalResult("lead_time", lt.id, lt.report_id, None, chunk, min(score, 1.0)))

    # 8. Risk Language
    rl_q = select(RiskLanguage)
    if report_id:
        rl_q = rl_q.where(RiskLanguage.report_id == report_id)
    for rl in (await db.execute(rl_q)).scalars().all():
        chunk = f"Risk: \"{rl.phrase}\" | Category: {rl.category} | Severity: {rl.severity_score}/3 | Context: {rl.context or ''}"
        score = 0.3
        if any(t.lower() in (rl.phrase or "").lower() for t in terms):
            score += 0.4
        results.append(RetrievalResult("risk_language", rl.id, rl.report_id, None, chunk, min(score, 1.0)))

    # 9. Percentage Metrics
    pm_q = select(PercentageMetric)
    if report_id:
        pm_q = pm_q.where(PercentageMetric.report_id == report_id)
    for pm in (await db.execute(pm_q)).scalars().all():
        chunk = f"Metric: {pm.metric_type} = {pm.value}% | Context: {pm.context or ''}"
        score = 0.3
        if any(t.lower() in q_lower for t in ["%", "percent", "discount", "margin"]):
            score += 0.2
        results.append(RetrievalResult("percentage_metric", pm.id, pm.report_id, None, chunk, min(score, 1.0)))

    # 10. Clearance Materials
    cm_q = select(ClearanceMaterial)
    if report_id:
        cm_q = cm_q.where(ClearanceMaterial.report_id == report_id)
    for cm in (await db.execute(cm_q)).scalars().all():
        chunk = f"Material: {cm.material_code} | {cm.description or ''} | Qty: {cm.quantity or ''}"
        score = 0.3
        if terms and any(t.lower() in (cm.material_code or "").lower() for t in terms):
            score += 0.3
        results.append(RetrievalResult("clearance_material", cm.id, cm.report_id, None, chunk, min(score, 1.0)))

    # 11. Status History
    sh_q = select(StatusHistory).join(Brand, StatusHistory.brand_id == Brand.id, isouter=True)
    if report_id:
        sh_q = sh_q.where(StatusHistory.report_id == report_id)
    for sh in (await db.execute(sh_q)).all():
        brand = await db.get(Brand, sh.brand_id) if sh.brand_id else None
        chunk = f"Status Change: {brand.brand_category if brand else 'Unknown'} | {sh.previous_status} -> {sh.current_status} | Gap: {sh.days_since_last_report or ''} days"
        score = 0.3
        if any(t.lower() in q_lower for t in ["status change", "improved", "worsened"]):
            score += 0.3
        results.append(RetrievalResult("status_history", sh.id, sh.report_id, brand.brand_category if brand else None, chunk, min(score, 1.0)))

    # 12. Thread Summaries
    ts_q = select(ThreadSummary)
    if report_id:
        ts_q = ts_q.where(ThreadSummary.report_id == report_id)
    for ts in (await db.execute(ts_q)).scalars().all():
        chunk = f"Summary: Health={ts.overall_health or ''} | Risks: {ts.key_risks or ''} | Highlights: {ts.key_highlights or ''} | Timeline: {ts.sales_timeline or ''}"
        score = 0.3
        if terms and any(t.lower() in (ts.key_highlights or "").lower() for t in terms):
            score += 0.3
        results.append(RetrievalResult("thread_summary", ts.id, ts.report_id, None, chunk, min(score, 1.0)))

    # 13. Anomaly Log
    al_q = select(AnomalyLog)
    if report_id:
        al_q = al_q.where(AnomalyLog.source_report_id == report_id)
    for al in (await db.execute(al_q)).scalars().all():
        chunk = f"Anomaly: similarity={al.similarity_score} | Source report #{al.source_report_id} matched report #{al.matched_report_id}"
        score = 0.2
        results.append(RetrievalResult("anomaly", al.id, al.source_report_id, None, chunk, min(score, 1.0)))

    return results


async def _vector_search(
    db: AsyncSession, query: str, report_id: int | None = None, brand_id: int | None = None
) -> list[RetrievalResult]:
    query_embedding = _get_embedding(query)
    if not query_embedding:
        return []

    vec_text = _embedding_to_vec_text(query_embedding)
    sql = """
        SELECT re.id, re.source_type, re.source_id, re.report_id, re.brand_id,
               re.chunk_text,
               VEC_DISTANCE_COSINE(re.v, VEC_FromText(:q)) AS distance
        FROM dds_report_embeddings re
    """
    params: dict = {"q": vec_text, "limit": TOP_K * 2}

    conditions = []
    if report_id:
        conditions.append("re.report_id = :report_id")
        params["report_id"] = report_id
    if brand_id:
        conditions.append("re.brand_id = :brand_id")
        params["brand_id"] = brand_id

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY VEC_DISTANCE_COSINE(re.v, VEC_FromText(:q)) ASC LIMIT :limit"

    rows = (await db.execute(text(sql), params)).all()
    results = []
    for row in rows:
        similarity = 1.0 - row.distance
        if similarity < (1.0 - SIMILARITY_THRESHOLD):
            continue
        brand_name = None
        if row.brand_id:
            brand = await db.get(Brand, row.brand_id)
            brand_name = brand.brand_category if brand else None
        results.append(RetrievalResult(
            source_type=row.source_type, source_id=row.source_id,
            report_id=row.report_id, brand_name=brand_name,
            chunk_text=row.chunk_text, score=similarity,
        ))
    return results


async def retrieve_context(
    db: AsyncSession, query: str, report_id: int | None = None, brand_id: int | None = None
) -> list[RetrievalResult]:
    structured = await _structured_search(db, query, report_id, brand_id)
    vector = await _vector_search(db, query, report_id, brand_id)

    seen = set()
    merged = []
    for r in sorted(structured + vector, key=lambda x: x.score, reverse=True):
        key = (r.source_type, r.source_id)
        if key not in seen:
            seen.add(key)
            merged.append(r)

    return merged[:TOP_K]