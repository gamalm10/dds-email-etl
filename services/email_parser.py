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
    "#ffc000": "yellow",
    "#ffff00": "yellow",
    "yellow": "yellow",
    "red": "red",
    "#d0cece": "grey",
    "#e7e6e6": "grey",
    "black": "black",
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
    table = soup.find("table")
    if not table:
        return parsed

    rows = table.find_all("tr")
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
