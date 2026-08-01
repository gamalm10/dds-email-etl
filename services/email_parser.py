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
        comments: str = "",
        comments_ar: str = "",
        language: str = "en",
    ):
        self.division = division.strip()
        self.brand_category = brand_category.strip()
        self.availability = availability
        self.milestone = milestone.strip()
        self.milestone_ar = milestone_ar.strip()
        self.shipment_bis = shipment_bis.strip()
        self.comments = comments.strip()
        self.comments_ar = comments_ar.strip()
        self.language = language


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
    "#fdd3d3": "red",
    "#f7caac": "red",
    "#d0cece": "grey",
    "#e7e6e6": "grey",
    "#d9d9d9": "grey",
    "#bfbfbf": "grey",
    "black": "black",
    "#deeaf6": "blue",
    "#ffffff": "white",
}

_ARABIC_PATTERN = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
_HEADER_DIVISIONS = {"division", "brand/ category", "brand/category", ""}


def _is_header_row(division: str, brand_category: str) -> bool:
    return division.lower().strip() in _HEADER_DIVISIONS or brand_category.lower().strip() in _HEADER_DIVISIONS


def _has_arabic(text: str) -> bool:
    return bool(_ARABIC_PATTERN.search(text))


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
    m = re.search(r"background[:\-]+\s*(#[0-9a-f]{6}|[a-z]+)", style, re.IGNORECASE)
    if m:
        color = m.group(1).lower()
        return _COLOR_MAP.get(color, "unknown")
    return "unknown"


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
    tables = soup.find_all("table")
    main_table = None
    for t in tables:
        text = t.get_text(" ", strip=True)
        if "Division" in text and "Brand" in text:
            main_table = t
            break
    if not main_table:
        return parsed

    rows = main_table.find_all("tr")
    current_division = ""

    for tr in rows:
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
            cell_style = cells[2].get("style", "") or cells[2].get("bgcolor", "")
            if cell_style:
                row.availability = _parse_bg_color(cell_style)

        if len(cells) > 3:
            row.milestone = cells[3].get_text(" ", strip=True)

        if len(cells) > 4:
            row.shipment_bis = cells[4].get_text(" ", strip=True)

        if len(cells) > 5:
            row.comments = cells[5].get_text(" ", strip=True)

        lang = _detect_language(row.milestone, row.comments)
        row.language = lang

        if lang in ("ar", "mixed"):
            if _has_arabic(row.milestone):
                row.milestone_ar = row.milestone
            if _has_arabic(row.comments):
                row.comments_ar = row.comments

        if row.brand_category and not _is_header_row(row.division, row.brand_category):
            parsed.rows.append(row)

    return parsed


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
    return risks


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
    return negos


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
    return leads
