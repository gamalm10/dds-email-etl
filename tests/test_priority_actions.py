import pytest
from bs4 import BeautifulSoup

from services.processor import Processor
from services.anomaly import SIMILARITY_THRESHOLD


def _clean_assignee(value, divisions):
    return Processor._clean_assignee(value, divisions)


def test_clean_assignee_drops_division_name():
    divisions = {"passenger", "diesel", "battery", "trucks"}
    assert _clean_assignee("Passenger", divisions) is None
    assert _clean_assignee("passenger", divisions) is None


def test_clean_assignee_keeps_people():
    divisions = {"passenger", "diesel"}
    assert _clean_assignee("Nancy", divisions) == "Nancy"
    assert _clean_assignee("Max", divisions) == "Max"


def test_clean_assignee_drops_only_the_division_part():
    divisions = {"passenger", "diesel"}
    assert _clean_assignee("Nancy, Passenger", divisions) == "Nancy"


def test_clean_assignee_normalises_multiple_names():
    divisions = {"passenger"}
    assert _clean_assignee(["Amir", "Max"], divisions) == "Amir, Max"
    assert _clean_assignee("Max, Amir", divisions) == "Amir, Max"
    assert _clean_assignee("Amir, Max", divisions) == "Amir, Max"


def test_clean_assignee_none_and_empty():
    divisions = {"passenger"}
    assert _clean_assignee(None, divisions) is None
    assert _clean_assignee("", divisions) is None
    assert _clean_assignee("Passenger", divisions) is None


def test_merge_priority_actions_prefers_table():
    table = [
        {"person": "Nancy", "action": "Ignition Coil - Confirm ETD"},
        {"person": "Max", "action": "Filtron - Braking study"},
    ]
    llm = [{"person": "Nancy", "action": "Ignition Coil - Confirm ETD", "urgency": "high"}]
    merged = Processor._merge_priority_actions(_Parsed(table), llm)
    assert [m["action"] for m in merged] == [
        "Ignition Coil - Confirm ETD",
        "Filtron - Braking study",
    ]
    assert merged[0]["urgency"] == "high"
    assert "urgency" not in merged[1]


def test_merge_priority_actions_keeps_llm_only_entries():
    table = [{"person": "Nancy", "action": "Confirm ETD"}]
    llm = [
        {"person": "Nancy", "action": "Confirm ETD"},
        {"person": "Amir", "action": "Extra item from body"},
    ]
    merged = Processor._merge_priority_actions(_Parsed(table), llm)
    assert len(merged) == 2
    assert merged[1]["action"] == "Extra item from body"


def test_merge_priority_actions_falls_back_to_llm():
    llm = [{"person": "Nancy", "action": "Only LLM"}]
    assert Processor._merge_priority_actions(_Parsed([]), llm) == llm
    assert Processor._merge_priority_actions(None, llm) == llm


def test_anomaly_threshold_is_strict():
    assert SIMILARITY_THRESHOLD >= 0.95


class _Parsed:
    def __init__(self, priority_actions):
        self.priority_actions = priority_actions


PRIORITY_HTML = """
<table>
  <tr><td>Nancy</td><td>Max</td><td>Amir</td><td>Weheba</td></tr>
  <tr><td>Ignition Coil - Confirm ETD</td><td>Filtron - Braking study</td>
      <td>Dayco - CN slow sell out</td><td>Road house - new order</td></tr>
  <tr><td></td><td>Sourcing plan: CV joint</td><td>Incentive calc</td>
      <td>Incentive policy</td></tr>
</table>
"""


def test_parse_priority_actions_reads_person_columns():
    from services.email_parser import parse_priority_actions

    actions = parse_priority_actions(BeautifulSoup(PRIORITY_HTML, "html.parser"))
    pairs = {(a["person"], a["action"]) for a in actions}
    assert ("Nancy", "Ignition Coil - Confirm ETD") in pairs
    assert ("Max", "Filtron - Braking study") in pairs
    assert ("Max", "Sourcing plan: CV joint") in pairs
    assert ("Weheba", "Incentive policy") in pairs
    assert len(actions) == 7


def test_parse_priority_actions_ignores_other_tables():
    from services.email_parser import parse_priority_actions

    html = """
    <table><tr><td>Division</td><td>Brand</td></tr>
    <tr><td>Passenger</td><td>PHC Clutch</td></tr></table>
    """ + PRIORITY_HTML
    actions = parse_priority_actions(BeautifulSoup(html, "html.parser"))
    assert all(a["person"] in {"Nancy", "Max", "Amir", "Weheba"} for a in actions)


def test_parse_priority_actions_empty_when_absent():
    from services.email_parser import parse_priority_actions

    html = "<table><tr><td>Division</td><td>Brand</td></tr></table>"
    assert parse_priority_actions(BeautifulSoup(html, "html.parser")) == []


@pytest.mark.parametrize("person", ["nancy", "max", "amir", "weheba"])
def test_parse_priority_actions_single_person_table(person):
    from services.email_parser import parse_priority_actions

    html = f"<table><tr><td>{person.title()}</td></tr><tr><td>Do the thing</td></tr></table>"
    actions = parse_priority_actions(BeautifulSoup(html, "html.parser"))
    assert actions == [{"person": person.title(), "action": "Do the thing"}]
