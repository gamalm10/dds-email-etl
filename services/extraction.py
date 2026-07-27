import logging

from services.email_parser import ParsedEmail
from services.sidecar_manager import SidecarError, SidecarManager

logger = logging.getLogger(__name__)


class ExtractionResult:
    def __init__(self, items: list[dict], tasks: list[dict], insights: list[dict]):
        self.items = items
        self.tasks = tasks
        self.insights = insights


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


async def extract_email_data(
    parsed_email: ParsedEmail,
    sidecar: SidecarManager,
    previous_context: str | None = None,
) -> ExtractionResult:
    if not parsed_email.raw_html or not sidecar._running:
        return _rule_based_fallback(parsed_email)

    try:
        result = await sidecar.extract(parsed_email.raw_html, previous_context)
    except (SidecarError, TimeoutError, ValueError) as e:
        logger.warning(f"LLM extraction failed: {e}, falling back to rule-based parsing")
        return _rule_based_fallback(parsed_email)

    items_raw = result.get("items", [])
    if not items_raw:
        return _rule_based_fallback(parsed_email)

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

    return ExtractionResult(items_raw, tasks, insights)
