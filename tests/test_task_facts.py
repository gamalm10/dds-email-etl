import pytest

from services.email_parser import parse_task_facts
from services.processor import Processor


class _Row:
    def __init__(self, brand_category, comments):
        self.brand_category = brand_category
        self.comments = comments


class _Parsed:
    def __init__(self, rows):
        self.rows = rows


def test_task_facts_extracts_owner_and_deadline():
    facts = parse_task_facts("New order creation – Max – 10.09 (~100K Eur)")
    assert len(facts) == 1
    assert facts[0]["assigned_to"] == "Max"
    assert facts[0]["deadline_text"] == "10.09"
    assert "New order creation" in facts[0]["description"]


def test_task_facts_multiple_owners_sorted():
    facts = parse_task_facts("Pricing – Max/Amir – 01.10")
    assert facts[0]["assigned_to"] == "Amir, Max"


def test_task_facts_splits_on_double_slash():
    facts = parse_task_facts("2,500 PC-45K Eur // Pricing – Max/Amir – 01.10")
    assert len(facts) == 1
    assert facts[0]["assigned_to"] == "Amir, Max"


def test_task_facts_month_deadline():
    facts = parse_task_facts("Agreed with Supplier to ship as per plan but Pay on 15 Nov.")
    assert facts[0]["deadline_text"] == "15 Nov"
    assert facts[0]["assigned_to"] is None


def test_task_facts_week_deadline():
    facts = parse_task_facts("Place next order for Mar/Apr 2027 sales – Nancy – W1 Sep")
    assert facts[0]["assigned_to"] == "Nancy"
    assert facts[0]["deadline_text"].lower() == "w1 sep"


def test_task_facts_ignores_comment_without_owner_or_date():
    assert parse_task_facts("On track – Costing planned") == []
    assert parse_task_facts("") == []


def test_task_facts_deduplicates_repeats():
    facts = parse_task_facts("Follow up – Max // Follow up – Max")
    assert len(facts) == 1


def test_deterministic_tasks_stable_across_calls():
    parsed = _Parsed([
        _Row("PHC Clutch-#1", "On track – Costing – Nancy – 29 Sep"),
        _Row("PHC Braking-#1", "Follow up with supplier – Amir – 15 Nov"),
        _Row("Banner", "No owner here at all"),
    ])
    processor = Processor.__new__(Processor)
    first = Processor._deterministic_tasks(processor, parsed)
    second = Processor._deterministic_tasks(processor, parsed)
    assert first == second
    assert [t["brand_category"] for t in first] == ["PHC Clutch-#1", "PHC Braking-#1"]


def test_deterministic_tasks_count_independent_of_llm():
    parsed = _Parsed([_Row("Brand-#1", "Pricing – Max – 01.10")])
    processor = Processor.__new__(Processor)
    parsed_tasks = Processor._deterministic_tasks(processor, parsed)
    many = [{"brand_category": "Brand-#1", "description": f"task {i}"} for i in range(30)]
    few = [{"brand_category": "Brand-#1", "description": "task 0"}]
    assert len(Processor._enrich_tasks(parsed_tasks, many)) == len(
        Processor._enrich_tasks(parsed_tasks, few)
    ) == 1


def test_enrich_tasks_attaches_category_and_priority():
    parsed_tasks = [{
        "brand_category": "PHC Clutch-#1",
        "description": "On track – Costing",
        "assigned_to": "Nancy",
        "deadline_text": "29 Sep",
    }]
    llm = [{
        "brand_category": "PHC Clutch-#1",
        "description": "On track – Costing",
        "category": "costing",
        "priority": "high",
    }]
    out = Processor._enrich_tasks(parsed_tasks, llm)
    assert out[0]["category"] == "costing"
    assert out[0]["priority"] == "high"
    assert out[0]["assigned_to"] == "Nancy"
    assert out[0]["deadline_text"] == "29 Sep"


def test_enrich_tasks_defaults_priority():
    parsed_tasks = [{
        "brand_category": "B", "description": "Do it",
        "assigned_to": None, "deadline_text": "",
    }]
    out = Processor._enrich_tasks(parsed_tasks, [])
    assert out[0]["priority"] == "medium"


@pytest.mark.parametrize("comment", [
    "On track – Costing – Nancy – 29 Sep",
    "Pricing – Max/Amir – 01.10",
    "New order creation – Max – 10.09 (~100K Eur)",
])
def test_task_facts_description_keeps_meaning(comment):
    facts = parse_task_facts(comment)
    assert facts
    assert len(facts[0]["description"]) > 3
    assert "Max/Amir" not in facts[0]["description"]


def test_deterministic_tasks_collapses_repeated_comment_across_lines():
    """Reports repeat one unnumbered comment on every shipment line of a brand."""
    shared = "On track- Costing planned on 13.09 - Amir"
    parsed = _Parsed([
        _Row("PHC Clutch-#1", shared),
        _Row("PHC Clutch-#2", shared),
        _Row("PHC Clutch-#3", shared),
    ])
    processor = Processor.__new__(Processor)
    tasks = Processor._deterministic_tasks(processor, parsed)
    assert len(tasks) == 1
    assert tasks[0]["assigned_to"] == "Amir"


def test_deterministic_tasks_keeps_distinct_comments_per_line():
    parsed = _Parsed([
        _Row("PHC Clutch-#1", "On track – Costing – Nancy – 29 Sep"),
        _Row("PHC Clutch-#2", "Agreed with Supplier but Pay on 15 Nov."),
    ])
    processor = Processor.__new__(Processor)
    tasks = Processor._deterministic_tasks(processor, parsed)
    assert len(tasks) == 2
