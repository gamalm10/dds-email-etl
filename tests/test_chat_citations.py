from services.chat_service import MAX_CITATIONS, _extract_citations
from services.rag_retriever import RetrievalResult


def _r(source_type: str, source_id: int, score: float, report_id: int = 1, brand_name: str | None = None):
    return RetrievalResult(source_type, source_id, report_id, brand_name, "chunk", score)


def test_extract_citations_keeps_only_high_score_linkable_types():
    results = [
        _r("report_item", 10, 0.8, 9, "PHC"),
        _r("report_item", 11, 0.5, 9, "Unrelated"),   # baseline score, dropped
        _r("task", 20, 0.7),
        _r("insight", 30, 0.65),
        _r("payment_term", 40, 0.9),                  # unsupported type, dropped
        _r("anomaly", 50, 0.9),                       # unsupported type, dropped
    ]

    out = _extract_citations(results)

    assert [c["id"] for c in out] == [10, 20, 30]
    assert out[0]["label"] == "Report Item #10 (PHC)"


def test_extract_citations_sorted_desc_and_capped():
    results = [_r("insight", i, 0.6 + i / 100) for i in range(10)]

    out = _extract_citations(results)

    assert len(out) == MAX_CITATIONS
    assert [c["id"] for c in out] == [9, 8, 7, 6, 5, 4]


def test_extract_citations_dedupes_same_source():
    results = [_r("report_item", 10, 0.8, 9, "PHC"), _r("report_item", 10, 0.95, 9, "PHC")]

    out = _extract_citations(results)

    assert len(out) == 1
    assert out[0]["id"] == 10
