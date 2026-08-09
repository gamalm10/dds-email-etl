import logging
import os

from openai import OpenAI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    Brand,
    Insight,
    Report,
    ReportItem,
    Task,
    ThreadSummary,
)

logger = logging.getLogger(__name__)


def _get_embedding(text_str: str) -> list[float] | None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set, skipping embedding")
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


def _build_item_chunk(item: ReportItem, brand_name: str | None) -> str:
    return (
        f"Brand: {brand_name or 'Unknown'} | "
        f"Division: {item.brand.division if item.brand else ''} | "
        f"Status: {item.milestone or ''} | "
        f"Availability: {item.availability_status or ''} | "
        f"ETD: {item.etd or ''} | ETA: {item.eta or ''} | Ready: {item.ready_for_sale or ''} | "
        f"Qty: {item.quantity_text or ''} | Financial: {item.financial_text or ''} | "
        f"Comments: {item.comments_actions or ''}"
    )


def _build_task_chunk(task: Task) -> str:
    return (
        f"Task: {task.task_description} | Assigned: {task.assigned_to or ''} | "
        f"Deadline: {task.deadline_text or ''} | Status: {task.task_status} | "
        f"Priority: {task.priority} | Category: {task.task_category or ''}"
    )


def _build_insight_chunk(insight: Insight) -> str:
    return (
        f"Insight: {insight.description} | Type: {insight.insight_type or ''} | "
        f"Severity: {insight.severity or ''} | Impact: {insight.impact or ''} | "
        f"Recommendation: {insight.recommendation or ''}"
    )


def _build_summary_chunk(ts: ThreadSummary) -> str:
    return (
        f"Summary: Health={ts.overall_health or ''} | "
        f"Risks: {ts.key_risks or ''} | Highlights: {ts.key_highlights or ''} | "
        f"Timeline: {ts.sales_timeline or ''} | Priority: {ts.priority_matrix or ''}"
    )


async def embed_report(db: AsyncSession, report_id: int) -> int:
    existing = (await db.execute(
        select(text("1")).select_from(text("dds_report_embeddings"))
        .where(text(f"report_id = {report_id}"))
        .limit(1)
    )).first()
    if existing:
        logger.info(f"Embeddings exist for report {report_id}, skipping")
        return 0

    items = (await db.execute(
        select(ReportItem).where(ReportItem.report_id == report_id)
    )).scalars().all()

    tasks = (await db.execute(
        select(Task).where(Task.first_seen_report_id == report_id)
    )).scalars().all()

    insights = (await db.execute(
        select(Insight).where(Insight.report_id == report_id)
    )).scalars().all()

    summaries = (await db.execute(
        select(ThreadSummary).where(ThreadSummary.report_id == report_id)
    )).scalars().all()

    count = 0

    for item in items:
        brand_name = None
        if item.brand_id:
            brand = await db.get(Brand, item.brand_id)
            brand_name = brand.brand_category if brand else None
        chunk = _build_item_chunk(item, brand_name)
        embedding = _get_embedding(chunk)
        if not embedding:
            continue
        vec_text = _embedding_to_vec_text(embedding)
        await db.execute(
            text(
                "INSERT INTO dds_report_embeddings "
                "(source_type, source_id, report_id, brand_id, chunk_text, v) "
                "VALUES ('report_item', :sid, :rid, :bid, :chunk, VEC_FromText(:vec))"
            ),
            {"sid": item.id, "rid": report_id, "bid": item.brand_id, "chunk": chunk, "vec": vec_text},
        )
        count += 1

    for task in tasks:
        chunk = _build_task_chunk(task)
        embedding = _get_embedding(chunk)
        if not embedding:
            continue
        vec_text = _embedding_to_vec_text(embedding)
        await db.execute(
            text(
                "INSERT INTO dds_report_embeddings "
                "(source_type, source_id, report_id, brand_id, chunk_text, v) "
                "VALUES ('task', :sid, :rid, NULL, :chunk, VEC_FromText(:vec))"
            ),
            {"sid": task.id, "rid": report_id, "chunk": chunk, "vec": vec_text},
        )
        count += 1

    for insight in insights:
        chunk = _build_insight_chunk(insight)
        embedding = _get_embedding(chunk)
        if not embedding:
            continue
        vec_text = _embedding_to_vec_text(embedding)
        await db.execute(
            text(
                "INSERT INTO dds_report_embeddings "
                "(source_type, source_id, report_id, brand_id, chunk_text, v) "
                "VALUES ('insight', :sid, :rid, :bid, :chunk, VEC_FromText(:vec))"
            ),
            {"sid": insight.id, "rid": report_id, "bid": insight.brand_id, "chunk": chunk, "vec": vec_text},
        )
        count += 1

    for ts in summaries:
        chunk = _build_summary_chunk(ts)
        embedding = _get_embedding(chunk)
        if not embedding:
            continue
        vec_text = _embedding_to_vec_text(embedding)
        await db.execute(
            text(
                "INSERT INTO dds_report_embeddings "
                "(source_type, source_id, report_id, brand_id, chunk_text, v) "
                "VALUES ('thread_summary', :sid, :rid, NULL, :chunk, VEC_FromText(:vec))"
            ),
            {"sid": ts.id, "rid": report_id, "chunk": chunk, "vec": vec_text},
        )
        count += 1

    await db.commit()
    logger.info(f"Embedded {count} chunks for report {report_id}")
    return count


async def embed_all_reports(db: AsyncSession) -> int:
    reports = (await db.execute(
        select(Report.id).where(Report.processing_status == "completed")
    )).scalars().all()
    total = 0
    for report_id in reports:
        count = await embed_report(db, report_id)
        total += count
    return total
