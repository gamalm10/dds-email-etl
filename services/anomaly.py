import logging
import math
import os
from typing import Optional

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Insight, AnomalyLog

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.85


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _get_embedding(text: str) -> Optional[list[float]]:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set, skipping embedding")
        return None
    try:
        client = OpenAI(api_key=api_key)
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return resp.data[0].embedding
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        return None


class AnomalyDetector:
    def __init__(self, db: AsyncSession):
        self.db = db

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
            embedding = _get_embedding(insight.description)
            if embedding:
                insight.embedding = str(embedding).encode()

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
            new_vec = self._decode_embedding(new_ins.embedding)

            for hist_ins in historical:
                if not hist_ins.embedding:
                    continue
                hist_vec = self._decode_embedding(hist_ins.embedding)
                score = cosine_similarity(new_vec, hist_vec)

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

    def _decode_embedding(self, blob: bytes) -> list[float]:
        try:
            text = blob.decode()
            if text.startswith("[") and text.endswith("]"):
                return [float(x.strip()) for x in text.strip("[]").split(",") if x.strip()]
        except (ValueError, UnicodeDecodeError):
            pass
        return []
