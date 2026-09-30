import re
from email import message_from_bytes
from email.policy import default as email_policy

from bs4 import BeautifulSoup


class ParsedRow:
    def __init__(
        self,
        division: str = "",
        brand_category: str = "",
        availability: str = "unknown",
        milestone: str = "",
        milestone_ar: str = "",
        shipment_bis: str = "",
        etd: str = "",
        eta: str = "",
        ready_for_sale: str = "",
        comments: str = "",
        comments_ar: str = "",
        language: str = "en",
        line_number: int | None = None,
        table_attached: bool = False,
    ):
        self.division = division.strip()
        self.brand_category = brand_category.strip()
        self.availability = availability
        self.milestone = milestone.strip()
        self.milestone_ar = milestone_ar.strip()
        self.shipment_bis = shipment_bis.strip()
        self.etd = etd.strip()
        self.eta = eta.strip()
        self.ready_for_sale = ready_for_sale.strip()
        self.comments = comments.strip()
        self.comments_ar = comments_ar.strip()
        self.language = language
        self.line_number = line_number
        self.table_attached = table_attached


class ParsedEmail:
    def __init__(
        self,
        subject: str,
        sender: str,
        date: str,
        raw_html: str,
        raw_text: str,
        recipients: str = "",
        cc_list: str = "",
    ):
        self.subject = subject
        self.sender = sender
        self.date = date
        self.raw_html = raw_html
        self.raw_text = raw_text
        self.recipients = recipients
        self.cc_list = cc_list
        self.rows: list[ParsedRow] = []
        self.future_etd_notes: list[tuple[str, str]] = []


_COLOR_MAP: dict[str, str] = {
    "#92d050": "green",
    "#a9d08e": "green",
    "#c5e0b3": "green",
    "#ffc000": "yellow",
    "#ffff00": "yellow",
    "#ffe599": "yellow",
    "#fff2cc": "yellow",
    "yellow": "yellow",
    "red": "red",
    "#c00000": "red",
    "#fdd3d3": "red",
    "#f7caac": "red",
    "#d0cece": "grey",
    "#e7e6e6": "grey",
    "#d9d9d9": "grey",
    "#bfbfbf": "grey",
    "silver": "grey",
    "black": "black",
    "#deeaf6": "blue",
    "#d9e2f3": "blue",
    "#ffffff": "white",
    "white": "white",
}

_STATUS_COLOR_MAP: dict[str, str] = {
    "in transit": "yellow",
    "in prod/packing": "green",
    "pending": "yellow",
    "under clearance": "yellow",
    "under study": "yellow",
    "order proposal": "red",
    "new": "blue",
}

_MILESTONE_STATUSES = [
    "in transit",
    "in prod/packing",
    "under clearance",
    "under study",
    "order proposal",
    "pending",
    "new",
]

_ARABIC_PATTERN = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
_HEADER_DIVISIONS = {"division", "brand/ category", "brand/category", ""}
_ETD_SPLIT_RE = re.compile(r'\b(\d+)\s*/\s*')
_LINE_PREFIX_RE = re.compile(r'(?:^|\s)(\d{1,2})\s*/\s*')
_SHARED_COMMENT_MARK = "**"


def _is_header_row(division: str, brand_category: str) -> bool:
    clean_brand = brand_category.lower().strip()
    if re.search(r'-#\d+$', clean_brand):
        clean_brand = clean_brand.rsplit("-#", 1)[0]
    return division.lower().strip() in _HEADER_DIVISIONS or clean_brand in _HEADER_DIVISIONS


def _split_etd_entries(text: str) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """Split an ETD cell into dated and undated entries, keeping the line number.

    Returns (date_entries, no_date_entries) where each item is (line_no, text).
    Empty line markers (e.g. the collapsed "1/ 2/" seen in some reports) are dropped.
    """
    if not text or not _ETD_SPLIT_RE.search(text):
        return ([], [])

    date_entries: list[tuple[int, str]] = []
    no_date_entries: list[tuple[int, str]] = []

    parts = _ETD_SPLIT_RE.split(text)
    if not parts or parts[0].strip():
        return ([], [])

    i = 1
    while i < len(parts) - 1:
        num = parts[i]
        entry = parts[i + 1].strip()
        i += 2
        if not entry:
            continue
        try:
            line_no = int(num)
        except ValueError:
            continue
        if re.search(r'\d{2}\.\d{2}', entry):
            cleaned = re.sub(r'\s+', ' ', entry).strip().rstrip(' -TBCtbc')
            date_entries.append((line_no, cleaned))
        else:
            no_date_entries.append((line_no, f"{num}/ {entry}"))

    return (date_entries, no_date_entries)


_DATE_TOKEN = re.compile(r'(\d{1,2}\.\d{2}|XX(?:\.\d{1,2})?)')
_TRIPLET_RE = re.compile(
    r'(\d{1,2}\.\d{2}|XX(?:\.\d{1,2})?)\s*-\s*(\d{1,2}\.\d{2}|XX(?:\.\d{1,2})?)\s*-\s*(\d{1,2}\.\d{2}|XX(?:\.\d{1,2})?)'
)


def _split_etd_eta_ready(text: str) -> tuple[str, str, str]:
    if not text:
        return ("", "", "")
    cleaned = re.sub(r'\s+', ' ', text).strip()

    triplet = _TRIPLET_RE.search(cleaned)
    if triplet:
        etd = triplet.group(1)
        eta = triplet.group(2)
        ready = triplet.group(3)
        after = cleaned[triplet.end():].strip()
        if after:
            ready = f"{ready} {after}".strip()
        return (etd, eta, ready)

    tokens = [t.strip() for t in cleaned.split('-')]
    tokens = [t for t in tokens if t]
    date_parts = []
    notes = []
    for t in tokens:
        if _DATE_TOKEN.fullmatch(t):
            date_parts.append(t)
        else:
            notes.append(t)
    etd = date_parts[0] if len(date_parts) >= 1 else ""
    eta = date_parts[1] if len(date_parts) >= 2 else ""
    ready = ""
    if len(date_parts) == 3 and notes:
        ready = f"{date_parts[2]} {' '.join(notes)}".strip()
    elif (len(date_parts) == 2 and notes) or not date_parts:
        ready = " ".join(notes).strip()
    return (etd, eta, ready)


def _split_milestones(text: str, count: int) -> list[str]:
    if not text:
        return [""] * max(count, 1)

    text_lower = text.lower().strip()
    parts: list[str] = []
    pos = 0
    while pos < len(text_lower) and len(parts) < count:
        while pos < len(text_lower) and text_lower[pos].isspace():
            pos += 1
        if pos >= len(text_lower):
            break

        matched = False
        for status in sorted(_MILESTONE_STATUSES, key=len, reverse=True):
            if text_lower[pos:].startswith(status):
                end = pos + len(status)
                parts.append(text[pos:end].strip())
                pos = end
                matched = True
                break
        if not matched:
            remaining = text_lower[pos:].split(None, 1)
            if remaining:
                parts.append(remaining[0])
                pos += len(remaining[0])
            else:
                break

    while len(parts) < count:
        parts.append(parts[-1] if parts else "")
    return parts[:count]


def _has_arabic(text: str) -> bool:
    return bool(_ARABIC_PATTERN.search(text))


def _normalise_cell(text: str) -> str:
    return re.sub(r'\s+', ' ', text or '').strip()


def _is_table_attached(text: str) -> bool:
    cleaned = _normalise_cell(text).lower().rstrip('.')
    return cleaned in {"table attached", "table attach", "attached table", "see attached table"}


def parse_comment_lines(text: str) -> tuple[dict[int, str], str]:
    """Split a Comments/Actions cell into per-line comments plus a shared comment.

    - "1/ one 2/ two"      -> ({1: "one", 2: "two"}, "")
    - "** applies to all"  -> ({}, "applies to all")
    - plain text           -> ({}, "plain text")
    """
    cleaned = _normalise_cell(text)
    if not cleaned:
        return {}, ""

    if cleaned.startswith(_SHARED_COMMENT_MARK):
        shared = cleaned.replace(_SHARED_COMMENT_MARK, " ")
        return {}, _normalise_cell(shared)

    if not re.match(r'^\d{1,2}\s*/', cleaned):
        return {}, cleaned

    parts = _LINE_PREFIX_RE.split(cleaned)
    lines: dict[int, str] = {}
    for i in range(1, len(parts) - 1, 2):
        try:
            line_no = int(parts[i])
        except ValueError:
            continue
        body = _normalise_cell(parts[i + 1])
        if body:
            lines[line_no] = body
    return lines, ""


def resolve_line_comment(
    line_no: int,
    lines: dict[int, str],
    shared: str,
    fallback_lines: dict[int, str] | None = None,
    fallback_shared: str = "",
) -> str:
    if line_no in lines:
        return lines[line_no]
    if shared:
        return shared
    if fallback_lines and line_no in fallback_lines:
        return fallback_lines[line_no]
    if fallback_shared:
        return fallback_shared
    return ""


def _table_month(table) -> str:
    first = table.find("tr")
    if not first:
        return ""
    header = first.get_text(" ", strip=True)
    m = re.search(r'availability\s+status\s*\(\s*([A-Za-z]{3,9})\s*\)', header, re.IGNORECASE)
    return m.group(1).upper() if m else ""


def _build_table_attached_fallbacks(soup, main_table, month: str) -> dict[str, tuple[dict[int, str], str]]:
    """Collect per-brand comments from sibling tables of the same reporting month.

    The main table defers some brands to "Table attached"; those rows are detailed
    in another table of the same month that is nested in the forward chain.
    """
    fallbacks: dict[str, tuple[dict[int, str], str]] = {}
    if not month:
        return fallbacks

    for table in soup.find_all("table"):
        if table is main_table or _table_month(table) != month:
            continue
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 6:
                continue
            brand = _normalise_cell(cells[1].get_text(" ", strip=True))
            if not brand or _is_header_row(_normalise_cell(cells[0].get_text(" ", strip=True)), brand):
                continue
            comment_text = cells[5].get_text(" ", strip=True)
            if not _normalise_cell(comment_text) or _is_table_attached(comment_text):
                continue
            lines, shared = parse_comment_lines(comment_text)
            if lines or shared:
                fallbacks[brand] = (lines, shared)

    return fallbacks


def _detect_language(*texts: str) -> str:
    has_ar = False
    has_en = False
    for t in texts:
        if _has_arabic(t):
            has_ar = True
        elif bool(re.search(r"[a-zA-Z]{2,}", t)):
            has_en = True
    if has_ar and has_en:
        return "mixed"
    if has_ar:
        return "ar"
    return "en"


def _parse_bg_color(style: str) -> str:
    if re.match(r'^#[0-9a-fA-F]{6}$', style.strip()):
        return _COLOR_MAP.get(style.strip().lower(), "unknown")
    m = re.search(r'background(?:-color)?\s*:\s*([^;]+)', style, re.IGNORECASE)
    if m:
        value = m.group(1).strip().lower()
        rgb_match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', value)
        if rgb_match:
            r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
            hex_val = f'#{r:02x}{g:02x}{b:02x}'
            return _COLOR_MAP.get(hex_val, "unknown")
        return _COLOR_MAP.get(value, "unknown")
    return _COLOR_MAP.get(style.strip().lower(), "unknown")


def parse_email(raw_bytes: bytes) -> ParsedEmail:
    msg = message_from_bytes(raw_bytes, policy=email_policy)

    subject = msg.get("Subject", "")
    sender = msg.get("From", "")
    date = msg.get("Date", "")
    recipients = msg.get("To", "")
    cc_list = msg.get("Cc", "")

    html_body = ""
    text_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/html" and not html_body:
                html_body = part.get_content()
            elif ct == "text/plain" and not text_body:
                text_body = part.get_content()
    else:
        html_body = msg.get_content()

    parsed = ParsedEmail(
        subject=str(subject),
        sender=str(sender),
        date=str(date),
        raw_html=str(html_body or ""),
        raw_text=str(text_body or ""),
        recipients=str(recipients or ""),
        cc_list=str(cc_list or ""),
    )

    if not html_body:
        return parsed

    soup = BeautifulSoup(html_body, "html.parser")
    main_table = find_main_table(soup)
    if not main_table:
        return parsed

    build_rows_from_table(soup, main_table, parsed)
    return parsed


def find_main_table(soup):
    for t in soup.find_all("table"):
        text = t.get_text(" ", strip=True)
        if "Division" in text and "Brand" in text:
            return t
    return None


def build_rows_from_table(soup, main_table, parsed: ParsedEmail) -> None:
    fallbacks = _build_table_attached_fallbacks(soup, main_table, _table_month(main_table))
    current_division = ""

    for tr in main_table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 4:
            continue

        row = ParsedRow()

        raw_div = cells[0].get_text(" ", strip=True)
        if raw_div:
            current_division = raw_div
        row.division = current_division

        if len(cells) > 1:
            row.brand_category = cells[1].get_text(" ", strip=True)

        if len(cells) > 2:
            avail_text = cells[2].get_text(" ", strip=True).lower().strip()
            row.availability = _STATUS_COLOR_MAP.get(avail_text, "unknown")
            if row.availability == "unknown":
                cell_style = cells[2].get("style", "") or cells[2].get("bgcolor", "")
                if cell_style:
                    row.availability = _parse_bg_color(cell_style)

        if len(cells) > 3:
            row.milestone = cells[3].get_text(" ", strip=True)

        etd_raw = ""
        if len(cells) > 4:
            etd_raw = cells[4].get_text(" ", strip=True)

        comments_raw = ""
        if len(cells) > 5:
            comments_raw = cells[5].get_text(" ", strip=True)

        table_attached = _is_table_attached(comments_raw)
        row.comments = "" if table_attached else comments_raw
        row.comments_ar = ""
        row.table_attached = table_attached

        if not row.brand_category or _is_header_row(row.division, row.brand_category):
            continue

        fb_lines, fb_shared = fallbacks.get(row.brand_category, ({}, ""))
        cmt_lines, cmt_shared = parse_comment_lines(comments_raw)
        if table_attached:
            cmt_lines, cmt_shared = {}, ""

        language = _detect_language(row.milestone, row.comments, comments_raw)
        row.language = language

        if language in ("ar", "mixed"):
            if _has_arabic(row.milestone):
                row.milestone_ar = row.milestone
            if _has_arabic(comments_raw):
                row.comments_ar = comments_raw

        date_entries, no_date_entries = _split_etd_entries(etd_raw)
        if len(date_entries) > 1:
            milestone_parts = _split_milestones(row.milestone, len(date_entries))
            for idx, ((line_no, etd_entry), ms) in enumerate(zip(date_entries, milestone_parts), 1):
                etd, eta, ready = _split_etd_eta_ready(etd_entry)
                comment = resolve_line_comment(line_no, cmt_lines, cmt_shared, fb_lines, fb_shared)
                r = ParsedRow(
                    division=row.division,
                    brand_category=f"{row.brand_category}-#{idx}",
                    availability=row.availability,
                    milestone=ms,
                    milestone_ar=row.milestone_ar,
                    shipment_bis=etd_entry,
                    etd=etd,
                    eta=eta,
                    ready_for_sale=ready,
                    comments=comment,
                    comments_ar=row.comments_ar if _has_arabic(comment) else "",
                    language=language,
                    line_number=line_no,
                    table_attached=table_attached and not comment,
                )
                parsed.rows.append(r)
            for _, note in no_date_entries:
                parsed.future_etd_notes.append((row.brand_category, note))
        else:
            etd, eta, ready = _split_etd_eta_ready(etd_raw)
            row.shipment_bis = etd_raw
            row.etd = etd
            row.eta = eta
            row.ready_for_sale = ready
            single = _split_etd_entries(etd_raw)[0]
            if single:
                row.line_number = single[0][0]
            row.comments = resolve_line_comment(
                row.line_number, cmt_lines, cmt_shared, fb_lines, fb_shared
            )
            row.comments_ar = row.comments if _has_arabic(row.comments) else ""
            parsed.rows.append(row)
            for _, note in no_date_entries:
                parsed.future_etd_notes.append((row.brand_category, note))


def parse_clearance_materials(text: str) -> list[dict]:
    materials = []
    lines = [l.strip() for l in text.split('\n')]
    i = 0
    while i < len(lines):
        line = lines[i]
        code_match = re.match(r'^([A-Z0-9]{10,})$', line)
        if code_match and not any(kw in line.lower() for kw in ('google', 'microsoft', 'outlook', 'http', 'www.', 'From:', 'Subject:', 'boundary')):
            material_code = code_match.group(1)
            category = ""
            description_ar = ""
            qty = 0
            qty_other = 0

            j = i + 1
            collected = []
            while j < len(lines) and len(collected) < 5:
                ln = lines[j]
                if not ln or ln.startswith('--'):
                    j += 1
                    continue
                if re.match(r'^\d[\d,]*$', ln):
                    break
                if re.match(r'^[A-Z]{3,}$', ln) and not collected:
                    category = ln
                    collected.append(ln)
                else:
                    collected.append(ln)
                j += 1

            description_ar = " ".join(c for c in collected if c != category)[:300]

            while j < len(lines):
                ln = lines[j].strip()
                qm = re.match(r'^([\d,]+)$', ln)
                if qm:
                    val = int(qm.group(1).replace(",", ""))
                    if qty == 0:
                        qty = val
                    else:
                        qty_other = val
                    j += 1
                else:
                    break

            materials.append({
                "material_code": material_code,
                "description": category,
                "description_ar": description_ar,
                "quantity": qty,
                "quantity_other": qty_other,
                "category": category,
            })
        i += 1
    return materials


def parse_ordering_rules(text: str) -> list[dict]:
    rules = []
    m = re.search(r'does not exceed\s*(\d+)([Kk]?)\$?(?:/Eur)?', text, re.IGNORECASE | re.DOTALL)
    if m:
        val = int(m.group(1))
        if m.group(2).lower() == 'k':
            val *= 1000
        rules.append({"max_amount_usd": val, "max_amount_eur": val})
    m = re.search(r'margin of\s*(\d+)%', text, re.IGNORECASE)
    if m and rules:
        rules[0]["margin_percent"] = int(m.group(1))
    m = re.search(r'<\s*(\d+)\s*months', text, re.IGNORECASE)
    if m and rules:
        rules[0]["sales_months"] = int(m.group(1))
    m = re.search(r'with[^.]*prior\s*approval', text, re.IGNORECASE)
    if m and rules:
        rules[0]["requires_approval"] = False
    return rules


def parse_signatures(text: str) -> list[dict]:
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'&[a-z]+;', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean)
    sigs = []
    for seg in re.split(r'(?=Regards)', clean):
        if 'Regards' not in seg:
            continue
        lines = [l.strip() for l in seg.split('\n') if l.strip() and l.strip() not in ('Regards,', 'Regards')]
        sig = {}
        for line in lines:
            if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', line) and not sig.get("person_name") and len(line) < 50:
                sig["person_name"] = line[:100]
            elif re.match(r'.*(CEO|COO|Manager|Officer|Director|Head)', line, re.IGNORECASE):
                sig["title"] = line[:200]
            elif re.search(r'(?:www\.|http)', line, re.IGNORECASE):
                sig["company"] = line[:200]
            elif re.match(r'Tel\.?\s*', line):
                sig["phone"] = line[:100]
            elif re.match(r'Mob\.?\s*', line):
                sig["phone"] = (sig.get("phone", "") + " / " + line).strip().rstrip(" /")
            elif re.match(r'^[a-zA-Z][\w.+-]*@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}', line.strip()):
                sig["email"] = line.strip()[:255]
        if sig.get("person_name") or sig.get("email"):
            sigs.append(sig)
    return sigs


def parse_percentages(text: str, brand_map: dict[str, int]) -> list[dict]:
    metrics = []
    patterns = [
        (r'(\d+(?:\.\d+)?)%\s*(discount|off)', 'discount'),
        (r'(\d+(?:\.\d+)?)%\s*price\s*increase', 'price_increase'),
        (r'(\d+(?:\.\d+)?)%\s*(?:margin|profit)', 'margin'),
        (r'(\d+(?:\.\d+)?)%\s*(?:DP|deposit)', 'deposit'),
        (r'(\d+(?:\.\d+)?)%\s*(?:CAD|balance)', 'balance'),
        (r'(\d+(?:\.\d+)?)%\s*growth', 'growth'),
        (r'(\d+(?:\.\d+)?)%\s*volume', 'volume_increase'),
    ]
    for pattern, mtype in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            metrics.append({
                "metric_type": mtype,
                "value": float(m.group(1)),
                "raw_text": m.group(0)[:255],
            })
    return metrics


RISK_PHRASES = [
    (r'cancelled\s*AGAIN|supplier\s*cancelled', 'supplier_failure', 3),
    (r'escalate', 'escalation', 3),
    (r'ON\s*HOLD', 'blocked', 2),
    (r'market\s*disturbance', 'market_risk', 2),
    (r'(weeks?|days?)\s*late|delayed|delay', 'delay', 2),
    (r'price\s*(?:increase|misalignment)', 'pricing_issue', 2),
    (r'risk|RISK', 'risk_flag', 2),
    (r'cancelled', 'cancellation', 3),
    (r'blocked', 'blocked', 2),
    (r'overdue', 'overdue', 2),
    (r'pending\s*update', 'stalled', 1),
    (r'no\s*response', 'unresponsive', 2),
    (r'contradict|discrepancy|conflict', 'discrepancy', 2),
]


def parse_risk_language(text: str) -> list[dict]:
    risks = []
    for pattern, category, score in RISK_PHRASES:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            start = max(0, m.start() - 50)
            end = min(len(text), m.end() + 50)
            context = text[start:end].strip()
            risks.append({
                "phrase": m.group(0)[:255],
                "category": category,
                "severity_score": score,
                "context": context[:500],
            })
    seen = set()
    deduped = []
    for r in risks:
        key = (r["phrase"].lower(), r["category"], r["severity_score"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    return deduped


def parse_payment_terms(text: str) -> list[dict]:
    terms = []
    m = re.search(r'(\d+(?:\.\d+)?)%\s*(?:DP|deposit)\s*\+\s*(\d+(?:\.\d+)?)%\s*(?:CAD|balance)', text, re.IGNORECASE)
    if m:
        terms.append({
            "payment_method": "DP + CAD",
            "deposit_pct": float(m.group(1)),
            "balance_pct": float(m.group(2)),
            "raw_text": m.group(0),
        })
    m = re.search(r'(SWIFT|TT|LC|CAD|DP)\s*(?:expected|done|payment|sent)?\s*(\d{1,2}\.\d{2})', text, re.IGNORECASE)
    if m:
        terms.append({
            "payment_method": m.group(1).upper(),
            "expected_date": m.group(2),
            "raw_text": m.group(0),
        })
    return terms


def parse_negotiations(text: str) -> list[dict]:
    negos = []
    for m in re.finditer(r'(\d+(?:\.\d+)?)%\s*(?:discount|agreed)', text, re.IGNORECASE):
        status = 'agreed' if 'agreed' in m.group(0).lower() else 'proposed'
        negos.append({
            "type": "discount",
            "percentage": float(m.group(1)),
            "status": status,
            "raw_text": m.group(0),
        })
    for m in re.finditer(r'(negotiat|discuss)\w*\s*(?:price|discount|term)', text, re.IGNORECASE):
        negos.append({
            "type": "negotiation",
            "percentage": None,
            "status": "proposed",
            "raw_text": m.group(0),
        })
    seen = set()
    deduped = []
    for n in negos:
        key = (n["type"], n["percentage"], n["status"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(n)
    return deduped


def parse_lead_times(text: str) -> list[dict]:
    leads = []
    for m in re.finditer(r'(\d+)\s*days?\s*(?:to|for|lead|production|ready|shipping)', text, re.IGNORECASE):
        leads.append({
            "days": int(m.group(1)),
            "status": "current",
            "raw_text": m.group(0),
        })
    for m in re.finditer(r'lead\s*time\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*months?', text, re.IGNORECASE):
        leads.append({
            "days": int(float(m.group(1)) * 30),
            "status": "current",
            "raw_text": m.group(0),
        })
    seen = set()
    deduped = []
    for l in leads:
        key = (l["days"], l["status"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(l)
    return deduped
