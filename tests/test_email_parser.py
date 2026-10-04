from services.email_parser import (
    _detect_language,
    _has_arabic,
    _is_table_attached,
    _parse_bg_color,
    _split_etd_entries,
    _split_etd_eta_ready,
    parse_comment_lines,
    parse_email,
    resolve_line_comment,
)


def test_parse_bg_color_green():
    assert _parse_bg_color("background:#92D050") == "green"


def test_parse_bg_color_yellow():
    assert _parse_bg_color("background:yellow") == "yellow"
    assert _parse_bg_color("background:#FFC000") == "yellow"


def test_parse_bg_color_red():
    assert _parse_bg_color("background:red") == "red"


def test_parse_bg_color_grey():
    assert _parse_bg_color("background:#D0CECE") == "grey"
    assert _parse_bg_color("background:#E7E6E6") == "grey"


def test_parse_bg_color_unknown():
    assert _parse_bg_color("") == "unknown"


def test_has_arabic_true():
    assert _has_arabic("مرحبا") is True


def test_has_arabic_false():
    assert _has_arabic("Hello") is False


def test_has_arabic_mixed():
    assert _has_arabic("مرحبا Hello") is True


def test_detect_language_en():
    assert _detect_language("Hello world", "How are you") == "en"


def test_detect_language_ar():
    assert _detect_language("مرحبا", "كيف حالك") == "ar"


def test_detect_language_mixed():
    assert _detect_language("Hello", "مرحبا") == "mixed"


def test_split_etd_entries_keeps_line_numbers():
    text = "2/ 22.08- 24.09-10.10 (Feb) 3/ 17.10-17.11-07.12 (June) 5/ Apr Sales"
    date_entries, no_date = _split_etd_entries(text)
    assert date_entries == [(2, "22.08- 24.09-10.10 (Feb)"), (3, "17.10-17.11-07.12 (June)")]
    assert no_date == [(5, "5/ Apr Sales")]


def test_split_etd_entries_drops_empty_line_marker():
    date_entries, _ = _split_etd_entries("1/ 2/ 22.08- 22.09-07.10 3/ 30.09-25.11-15.12")
    assert date_entries == [(2, "22.08- 22.09-07.10"), (3, "30.09-25.11-15.12")]


def test_split_etd_eta_ready_normalises_en_dash():
    assert _split_etd_eta_ready("30.09-20.10 \u2013 10.11") == ("30.09", "20.10", "10.11")


def test_split_etd_eta_ready_normalises_em_dash():
    assert _split_etd_eta_ready("30.09\u201420.10\u201410.11") == ("30.09", "20.10", "10.11")


def test_split_etd_eta_ready_keeps_parenthetical_note():
    assert _split_etd_eta_ready("22.08- 24.09-10.10 (Feb)") == ("22.08", "24.09", "10.10 (Feb)")


def test_split_etd_eta_ready_ascii_hyphen_unchanged():
    assert _split_etd_eta_ready("1/ 30.09-20.10-10.11") == ("30.09", "20.10", "10.11")


def test_parse_comment_lines_splits_by_line():
    lines, shared = parse_comment_lines("2/On track – Costing 3/ Agreed with Supplier")
    assert shared == ""
    assert lines == {2: "On track – Costing", 3: "Agreed with Supplier"}


def test_parse_comment_lines_shared_marker():
    lines, shared = parse_comment_lines("** Braking (6K PC) in Dec is yet to be confirmed. F/U with supplier")
    assert lines == {}
    assert shared == "Braking (6K PC) in Dec is yet to be confirmed. F/U with supplier"


def test_parse_comment_lines_plain_text_is_shared():
    lines, shared = parse_comment_lines("Order sent to supplier / waiting for PI- Nancy")
    assert lines == {}
    assert shared == "Order sent to supplier / waiting for PI- Nancy"


def test_parse_comment_lines_empty_first_marker_does_not_swallow_next():
    cell = "1/ 2/Order placed 70-80K pending - order confirmation \u2013 Max- 14.09/ ( RH price list )"
    lines, shared = parse_comment_lines(cell)
    assert shared == ""
    assert lines == {2: "Order placed 70-80K pending - order confirmation \u2013 Max- 14.09/ ( RH price list )"}


def test_parse_comment_lines_prose_before_marker_is_prepended_to_each_line():
    cell = (
        "we will No longer wait for e-Mark, RH created multiple errors. "
        "1/Plan for shipment \u2013 ACID under creating - Nancy - 10.09 "
        "2/ New order placed 70-80K pending - order confirmation \u2013 Max- 14.09"
    )
    lines, shared = parse_comment_lines(cell)
    assert shared == ""
    assert lines[1].startswith("we will No longer wait for e-Mark")
    assert lines[1].endswith("Plan for shipment \u2013 ACID under creating - Nancy - 10.09")
    assert lines[2].startswith("we will No longer wait for e-Mark")
    assert lines[2].endswith("New order placed 70-80K pending - order confirmation \u2013 Max- 14.09")


def test_parse_comment_lines_all_bodies_empty_returns_prefix_only():
    assert parse_comment_lines("1/ 2/") == ({}, "")
    assert parse_comment_lines("prose 1/ 2/") == ({}, "prose")


def test_parse_comment_lines_date_like_slash_is_not_a_marker():
    lines, shared = parse_comment_lines("Max- 14.09/ ( RH price list )")
    assert lines == {}
    assert shared == "Max- 14.09/ ( RH price list )"


def test_resolve_line_comment_road_house_case():
    cell = "1/ 2/Order placed 70-80K pending - order confirmation \u2013 Max- 14.09/ ( RH price list )"
    lines, shared = parse_comment_lines(cell)
    assert resolve_line_comment(1, lines, shared) == ""
    assert resolve_line_comment(2, lines, shared) == (
        "Order placed 70-80K pending - order confirmation \u2013 Max- 14.09/ ( RH price list )"
    )


def test_is_table_attached():
    assert _is_table_attached("Table attached") is True
    assert _is_table_attached("  table attached ") is True
    assert _is_table_attached("On track") is False


def test_resolve_line_comment_prefers_line_then_shared_then_fallback():
    assert resolve_line_comment(2, {2: "line"}, "shared") == "line"
    assert resolve_line_comment(3, {2: "line"}, "shared") == "shared"
    assert resolve_line_comment(3, {}, "", {3: "fb line"}) == "fb line"
    assert resolve_line_comment(3, {}, "", {}, "fb shared") == "fb shared"
    assert resolve_line_comment(3, {}, "") == ""


def _dds_email_html(rows_html: str, month: str = "SEP", sibling_html: str = "") -> bytes:
    return (
        "Content-Type: text/html; charset=utf-8\n"
        "Subject: FW: Operation DDS -27 September 2026\n"
        "From: <haytham.hamdy@a-part.com>\n"
        "Date: Sun, 27 Sep 2026 12:48:18 +0300\n"
        "Content-Transfer-Encoding: 8bit\n\n"
        "<html><body><table>"
        "<tr><td>Division</td><td>Brand/Category</td><td>Availability Status "
        f"({month})</td><td>Milestone</td><td>ETD-ETA-Ready for Sale</td>"
        "<td>Comments/Actions</td></tr>"
        f"{rows_html}"
        f"</table>{sibling_html}</body></html>"
    ).encode()


def test_parse_email_matches_comment_line_to_etd_line():
    rows = (
        "<tr><td>Passenger</td><td>PHC Clutch</td><td></td><td>In Transit Pending</td>"
        "<td>2/ 22.08- 24.09-10.10 (Feb) 3/ 17.10-17.11-07.12 (June)</td>"
        "<td>2/On track &ndash; Costing 3/ Agreed with Supplier</td></tr>"
    )
    parsed = parse_email(_dds_email_html(rows))
    clutch = [r for r in parsed.rows if r.brand_category.startswith("PHC Clutch")]
    assert clutch[0].line_number == 2
    assert clutch[0].comments == "On track \u2013 Costing"
    assert clutch[1].line_number == 3
    assert clutch[1].comments == "Agreed with Supplier"


def test_parse_email_applies_shared_comment_to_all_lines():
    rows = (
        "<tr><td>Passenger</td><td>PHC Braking</td><td></td><td>Pending Pending</td>"
        "<td>2/ 22.08- 24.09-10.10 (Feb) 3/ 17.10-17.11-07.12 (June)</td>"
        "<td>** shipment yet to be confirmed. F/U with supplier</td></tr>"
    )
    parsed = parse_email(_dds_email_html(rows))
    braking = [r for r in parsed.rows if r.brand_category.startswith("PHC Braking")]
    assert len(braking) == 2
    assert all(r.comments == "shipment yet to be confirmed. F/U with supplier" for r in braking)


def test_parse_email_empty_first_comment_line_does_not_swallow_second():
    rows = (
        "<tr><td>Passenger</td><td>Road House</td><td></td><td>Order proposal</td>"
        "<td>1/ 15.10-07.11-25.11 2/ 20.10-10.11-01.12</td>"
        "<td>1/ 2/Order placed 70-80K pending - order confirmation \u2013 Max- 14.09/ ( RH price list )</td></tr>"
    )
    parsed = parse_email(_dds_email_html(rows))
    rh = [r for r in parsed.rows if r.brand_category.startswith("Road House")]
    assert len(rh) == 2
    assert rh[0].comments == ""
    assert rh[1].comments == "Order placed 70-80K pending - order confirmation \u2013 Max- 14.09/ ( RH price list )"


def test_parse_email_does_not_use_sibling_comment_when_not_table_attached():
    main = (
        "<tr><td>Passenger</td><td>Road House</td><td></td><td>Order proposal</td>"
        "<td>1/ 15.10-07.11-25.11 2/ 20.10-10.11-01.12</td>"
        "<td>1/ 2/Order placed 70-80K pending</td></tr>"
    )
    sibling = (
        "<table><tr><td>Division</td><td>Brand/Category</td><td>Availability Status (SEP)</td>"
        "<td>Milestone</td><td>ETD-ETA-Ready for Sale</td><td>Comments/Actions</td></tr>"
        "<tr><td>Passenger</td><td>Road House</td><td></td><td>Pending</td><td></td>"
        "<td>stale sibling comment</td></tr></table>"
    )
    parsed = parse_email(_dds_email_html(main, sibling_html=sibling))
    rh = [r for r in parsed.rows if r.brand_category.startswith("Road House")]
    assert len(rh) == 2
    assert rh[0].comments == ""
    assert rh[1].comments == "Order placed 70-80K pending"


def test_parse_email_single_marker_strips_prefix_and_parses_dates():
    rows = (
        "<tr><td>Passenger</td><td>Filtron</td><td></td><td>Order proposal</td>"
        "<td>1/ 30.09-20.10 \u2013 10.11</td>"
        "<td>Price list effective 1 Oct with 10% price increase</td></tr>"
    )
    parsed = parse_email(_dds_email_html(rows))
    filtron = [r for r in parsed.rows if r.brand_category.startswith("Filtron")]
    assert len(filtron) == 1
    assert filtron[0].line_number == 1
    assert filtron[0].shipment_bis == "30.09-20.10 \u2013 10.11"
    assert filtron[0].etd == "30.09"
    assert filtron[0].eta == "20.10"
    assert filtron[0].ready_for_sale == "10.11"


def test_parse_email_resolves_table_attached_from_sibling_table():
    main = (
        "<tr><td>Passenger</td><td>PHC Braking</td><td></td><td>Pending Pending</td>"
        "<td>2/ 22.08- 24.09-10.10 (Feb) 3/ 17.10-17.11-07.12 (June)</td>"
        "<td>Table attached</td></tr>"
    )
    sibling = (
        "<table><tr><td>Division</td><td>Brand/Category</td><td>Availability Status (SEP)</td>"
        "<td>Milestone</td><td>ETD-ETA-Ready for Sale</td><td>Comments/Actions</td></tr>"
        "<tr><td>Passenger</td><td>PHC Braking</td><td></td><td>Pending</td><td></td>"
        "<td>** shipment yet to be confirmed. F/U with supplier</td></tr></table>"
    )
    parsed = parse_email(_dds_email_html(main, sibling_html=sibling))
    braking = [r for r in parsed.rows if r.brand_category.startswith("PHC Braking")]
    assert len(braking) == 2
    assert all(r.comments == "shipment yet to be confirmed. F/U with supplier" for r in braking)
    assert all(r.table_attached is False for r in braking)


def test_parse_email_ignores_sibling_table_from_other_month():
    main = (
        "<tr><td>Passenger</td><td>PHC Braking</td><td></td><td>Pending</td>"
        "<td>2/ 22.08- 24.09-10.10 (Feb)</td><td>Table attached</td></tr>"
    )
    sibling = (
        "<table><tr><td>Division</td><td>Brand/Category</td><td>Availability Status (JUL)</td>"
        "<td>Milestone</td><td>ETD-ETA-Ready for Sale</td><td>Comments/Actions</td></tr>"
        "<tr><td>Passenger</td><td>PHC Braking</td><td></td><td>Pending</td><td></td>"
        "<td>stale july comment</td></tr></table>"
    )
    parsed = parse_email(_dds_email_html(main, sibling_html=sibling))
    braking = [r for r in parsed.rows if r.brand_category.startswith("PHC Braking")]
    assert braking[0].comments == ""
    assert braking[0].table_attached is True
