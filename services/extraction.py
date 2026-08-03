import json
import logging
import os
from pathlib import Path

from services.email_parser import ParsedEmail, _has_arabic
from services.sidecar_manager import SidecarError, SidecarManager

logger = logging.getLogger(__name__)


class ExtractionResult:
    def __init__(self, items: list[dict], tasks: list[dict], insights: list[dict], raw: dict | None = None):
        self.items = items
        self.tasks = tasks
        self.insights = insights
        self.raw = raw or {}


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


def _load_system_prompt() -> str:
    try:
        prompt_path = Path(__file__).parent.parent / "pi" / "dds_analyst_prompt.md"
        if prompt_path.exists():
            return prompt_path.read_text()
    except Exception:
        pass
    return _FALLBACK_PROMPT


_FALLBACK_PROMPT = """You are a DDS email analyst for A-part automotive supply chain.
Extract structured data from DDS status emails.

Each email has sections:
1. Priority actions table (Nancy | Max | Amir | Weheba)
2. Sales timeline (month-by-month forecast)
3. Key highlights
4. Main status table with columns: Division | Brand/Category | Availability | Milestone | Shipment/BIS | Comments/Actions

For each row extract:
- division, brand_category, availability, milestone, shipment_bis, comments_actions
- vendor from brand or comments
- quantity_text like "6,500PC", financial_text like "198 Euro"
- tasks from Comments with: description, assigned_to (string, not list), deadline, deadline_text, category, priority (high/medium/low), is_overdue, is_blocked
- insights with: type, description, severity, impact, recommendation, risk_tags (array), vendor

Also extract:
- priority_actions: person, action, action_ar, category, urgency
- sales_timeline: month -> brands
- key_highlights: array of strings

Detect Arabic: set language to "ar" or "mixed", populate *_ar fields.

Output JSON matching the full schema with items, priority_actions, sales_timeline, key_highlights."""


def _try_direct_openai(parsed_email: ParsedEmail) -> dict | None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        rows_text = "\n".join(
            f"{r.division} | {r.brand_category} | {r.availability} | {r.milestone} | {r.shipment_bis} | {r.comments}"
            for r in parsed_email.rows[:30]
        )
        resp = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": _load_system_prompt()},
                {"role": "user", "content": f"Extract structured data from this DDS email:\n\n{rows_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        text = resp.choices[0].message.content
        return json.loads(text)
    except Exception as e:
        logger.warning(f"Direct OpenAI extraction failed: {e}")
        return None


async def extract_email_data(
    parsed_email: ParsedEmail,
    sidecar: SidecarManager,
    previous_context: str | None = None,
) -> ExtractionResult:
    if not parsed_email.rows:
        return ExtractionResult([], [], [])

    result = None
    try:
        if sidecar._running:
            result = await sidecar.extract(parsed_email.raw_html, previous_context)
    except (SidecarError, TimeoutError, ValueError) as e:
        logger.warning(f"PI SDK sidecar failed: {e}, trying direct OpenAI")

    if not result or not result.get("items"):
        result = _try_direct_openai(parsed_email)

    if not result or not result.get("items"):
        return _rule_based_fallback(parsed_email)

    items_raw = result.get("items", [])
    tasks: list[dict] = []
    insights: list[dict] = []

    for item in items_raw:
        brand = item.get("brand_category", "")
        division = item.get("division", "")
        for t in item.get("tasks", []):
            t["brand_category"] = brand
            t["division"] = division
            tasks.append(t)
        for ins in item.get("insights", []):
            ins["brand_category"] = brand
            ins["division"] = division
            insights.append(ins)

    return ExtractionResult(items_raw, tasks, insights, raw=result)
