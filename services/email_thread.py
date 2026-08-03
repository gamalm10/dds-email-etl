import logging
import re
from datetime import datetime
from email import message_from_bytes
from email.policy import default as email_policy
from typing import Optional

from services.email_parser import (
    parse_email, ParsedEmail, ParsedRow, _detect_language, _has_arabic, _is_header_row,
)

logger = logging.getLogger(__name__)


class ThreadEmail:
    def __init__(self, subject: str, sender: str, date_str: str, parsed: ParsedEmail):
        self.subject = subject
        self.sender = sender
        self.date_str = date_str
        self.parsed = parsed

    @property
    def date(self) -> Optional[datetime]:
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(self.date_str)
        except Exception:
            return None


_DDS_HEADER_WORDS = {"division", "brand", "availability", "milestone", "etd", "eta", "comments", "actions", "status", "shipment", "category", "date"}


def _has_dds_table(text: str) -> bool:
    lower = text.lower()
    if "dds" in lower or "operation" in lower:
        return sum(1 for w in _DDS_HEADER_WORDS if w in lower) >= 2
    return sum(1 for w in _DDS_HEADER_WORDS if w in lower) >= 4


_FROM_RE = re.compile(r"^From:\s*(.+)", re.MULTILINE)


def _parse_text_table(text: str, division_hint: str = "") -> ParsedEmail:
    parsed = ParsedEmail("", "", "", "", text)
    lines = [l.strip() for l in text.split("\n")]

    in_table = False
    row_buffers: list[list[str]] = []
    current_row: list[str] = []
    current_division = division_hint
    seen_division_header = False

    for line in lines:
        if not line:
            if current_row:
                current_row.append("")
            continue

        lower = line.lower()

        if not seen_division_header and "division" == lower:
            seen_division_header = True
            in_table = True
            current_row = []
            row_buffers = []
            continue

        if not in_table:
            continue

        if re.match(r"^(general|date\s*[-–])", lower):
            break

        if lower in ("battery", "passenger", "trucks", "diesel", "pas"):
            if current_row:
                row_buffers.append(current_row)
            current_division = line
            current_row = []
            continue

        if line == current_division:
            continue

        if not current_row or current_row[0] != current_division:
            current_row = [current_division]

        current_row.append(line)

    if current_row:
        row_buffers.append(current_row)

    for row_data in row_buffers:
        if len(row_data) < 3:
            continue

        brand = row_data[1] if len(row_data) > 1 else ""
        if _is_header_row(row_data[0], brand):
            continue

        col_map = {
            "availability": "",
            "milestone": "",
            "shipment_bis": "",
            "comments": "",
        }

        text_vals = row_data[2:]
        if len(text_vals) >= 4:
            col_map["milestone"] = text_vals[0]
            col_map["shipment_bis"] = text_vals[1]
            col_map["comments"] = " ".join(text_vals[2:])
        elif len(text_vals) == 3:
            col_map["milestone"] = text_vals[0]
            combined = text_vals[1:]
            if len(combined) >= 2:
                col_map["shipment_bis"] = combined[0]
                col_map["comments"] = combined[1]
            else:
                col_map["comments"] = combined[0] if combined else ""
        elif len(text_vals) == 2:
            col_map["milestone"] = text_vals[0]
            col_map["comments"] = text_vals[1]
        elif len(text_vals) == 1:
            col_map["comments"] = text_vals[0]

        row = ParsedRow(
            division=current_division,
            brand_category=brand,
            availability=col_map["availability"],
            milestone=col_map["milestone"],
            shipment_bis=col_map["shipment_bis"],
            comments=col_map["comments"],
        )
        row.language = _detect_language(row.milestone, row.comments)
        if row.language in ("ar", "mixed"):
            if _has_arabic(row.milestone):
                row.milestone_ar = row.milestone
            if _has_arabic(row.comments):
                row.comments_ar = row.comments
        parsed.rows.append(row)

    return parsed


def _reconstruct_eml(segment: str, subject: str, sender: str, date_str: str) -> str:
    to_match = re.search(r'(?m)^To:\s*(.+)', segment)
    cc_match = re.search(r'(?m)^Cc:\s*(.+)', segment)

    to_str = to_match.group(1).strip() if to_match else ""
    cc_str = cc_match.group(1).strip() if cc_match else ""

    body = segment
    for header_prefix in ("From:", "To:", "Cc:", "Subject:", "Importance:", "X-"):
        body = re.sub(r'(?m)^' + re.escape(header_prefix) + r'.*(?:\r?\n[ \t].+)*\r?\n', '', body)
    body = body.strip()

    eml = f"From: {sender}\r\n"
    sent_match = re.search(r'(?m)^Sent:\s*(.+)', segment)
    sent_val = sent_match.group(1).strip() if sent_match else ""
    if sent_val and sent_val.lower() != 'none':
        eml += f"Sent: {sent_val}\r\n"
    elif date_str and date_str.lower() != 'none':
        eml += f"Date: {date_str}\r\n"
    if to_str:
        eml += f"To: {to_str}\r\n"
    if cc_str:
        eml += f"Cc: {cc_str}\r\n"
    eml += f"Subject: {subject}\r\n"
    eml += "Content-Type: text/plain; charset=utf-8\r\n"
    eml += "MIME-Version: 1.0\r\n"
    eml += "\r\n"
    eml += body

    return eml


def extract_thread(raw_bytes: bytes) -> list[ThreadEmail]:
    msg = message_from_bytes(raw_bytes, policy=email_policy)
    thread: list[ThreadEmail] = []

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

    top_parsed = parse_email(raw_bytes)
    if top_parsed.rows:
        thread.append(ThreadEmail(
            subject=msg.get("Subject", ""),
            sender=msg.get("From", ""),
            date_str=msg.get("Date", ""),
            parsed=top_parsed,
        ))

    if text_body:
        positions = [m.start() for m in re.finditer(r"(?m)^From:\s*.+@", text_body)]
        if not positions:
            positions = [m.start() for m in re.finditer(r"(?m)^From:\s*'?", text_body)]

        html_ops = [m.start() for m in re.finditer(r"Operation DDS", html_body, re.IGNORECASE)] if html_body else []
        header_divs = [m.start() for m in re.finditer(r'<div style="border:none; border-top:solid', html_body)] if html_body else []

        def _find_html_for_subject(target_subject: str, start_search: int) -> tuple[str | None, int]:
            best_pos = -1
            search_start = max(0, start_search)
            for hd_pos in header_divs:
                if hd_pos <= search_start:
                    continue
                ctx_end = min(len(html_body), hd_pos + 1500)
                ctx = html_body[hd_pos:ctx_end]
                subj_m = re.search(r'<b>Subject:</b>\s*(.+?)(?:<br>|<)', ctx)
                if subj_m:
                    hd_subject = subj_m.group(1).strip()
                    if target_subject in hd_subject or hd_subject in target_subject:
                        best_pos = hd_pos
                        break
            if best_pos < 0:
                return None, start_search
            next_pos = html_body.find('<div style="border:none; border-top:solid', best_pos + 500)
            if next_pos < 0:
                seg = html_body[best_pos:]
            else:
                seg = html_body[best_pos:next_pos]
            return seg, best_pos

        prev = 0
        last_hd_pos = 0
        for pos in positions:
            if pos == 0:
                segment = text_body[:200]
                prev = pos
                continue
            segment = text_body[prev:pos]
            prev = pos

            if not _has_dds_table(segment):
                continue

            subj_match = re.search(r"(?m)^Subject:\s*(.+)", segment)
            from_match = re.search(r"(?m)^From:\s*(.+)", segment)
            date_match = re.search(r"(?m)^Sent:\s*(.+)", segment)

            subject = subj_match.group(1).strip() if subj_match else ""
            if "operation dds" not in subject.lower():
                continue
            sender = from_match.group(1).strip()[:60] if from_match else ""
            date_str = date_match.group(1).strip() if date_match else ""

            parsed = None
            if html_body:
                html_seg, last_hd_pos = _find_html_for_subject(subject, last_hd_pos)
                if html_seg:
                    try:
                        html_bytes = f"<html><body>{html_seg}</body></html>".encode()
                        parsed = parse_email(html_bytes)
                        if parsed.rows:
                            parsed.raw_html = html_seg
                            parsed.raw_text = segment.strip()
                    except Exception:
                        parsed = None

            if not parsed or not parsed.rows:
                try:
                    parsed = _parse_text_table(segment)
                except Exception as e:
                    logger.debug(f"Failed to parse segment: {e}")
                    continue
                if parsed.rows:
                    parsed.raw_text = segment.strip()

            if parsed and parsed.rows:
                thread.append(ThreadEmail(subject, sender, date_str, parsed))

        last_segment = text_body[prev:] if prev > 0 else ""
        if last_segment and _has_dds_table(last_segment):
            subj_match = re.search(r"(?m)^Subject:\s*(.+)", last_segment)
            from_match = re.search(r"(?m)^From:\s*(.+)", last_segment)
            date_match = re.search(r"(?m)^Sent:\s*(.+)", last_segment)
            subject = subj_match.group(1).strip() if subj_match else ""
            if "operation dds" in subject.lower():
                sender = from_match.group(1).strip()[:60] if from_match else ""
                date_str = date_match.group(1).strip() if date_match else ""
                parsed = None
                if html_body:
                    html_seg, _ = _find_html_for_subject(subject, last_hd_pos)
                    if html_seg:
                        try:
                            html_bytes = f"<html><body>{html_seg}</body></html>".encode()
                            parsed = parse_email(html_bytes)
                            if parsed.rows:
                                parsed.raw_html = html_seg
                                parsed.raw_text = last_segment.strip()
                        except Exception:
                            parsed = None
                if not parsed or not parsed.rows:
                    try:
                        parsed = _parse_text_table(last_segment)
                        if parsed.rows:
                            parsed.raw_text = last_segment.strip()
                    except Exception:
                        pass
                if parsed and parsed.rows:
                    thread.append(ThreadEmail(subject, sender, date_str, parsed))

    def _safe_dt(e: ThreadEmail) -> datetime:
        d = e.date
        if d is None:
            return datetime(1900, 1, 1)
        if d.tzinfo is not None:
            return d.replace(tzinfo=None)
        return d

    thread.sort(key=_safe_dt)
    return thread
