from core.schemas import DashboardSummary, ProcessResponse


def test_process_response_optional():
    resp = ProcessResponse(success=True, message="OK")
    assert resp.report_id is None
    assert resp.items_extracted == 0


def test_dashboard_summary_defaults():
    ds = DashboardSummary(total_brands=10, brands_with_issues=2, open_tasks=5, critical_insights=1)
    assert ds.status_distribution == {}
    assert ds.last_report_date is None
