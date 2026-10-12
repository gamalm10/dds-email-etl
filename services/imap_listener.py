import asyncio
import email
import logging
import re
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime

from aioimaplib import IMAP4_SSL

from config.settings import get_settings
from services.auto_fetch_status import status

logger = logging.getLogger(__name__)

DDS_SUBJECT_PATTERN = re.compile(
    r"(?:DDS-(\d{2})\.(\d{2})\.(\d{4}))|"
    r"(?:Operation DDS[ -]+(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4}))|"
    r"(?:DDS[ -]+(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4}))",
    re.IGNORECASE,
)

OnEmailCallback = Callable[[bytes, str, datetime], Awaitable[bool]]


_MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def parse_dds_date(subject: str) -> date | None:
    match = DDS_SUBJECT_PATTERN.search(subject)
    if not match:
        return None
    g = match.groups()
    if g[0] and g[1] and g[2]:
        return date(int(g[2]), int(g[1]), int(g[0]))
    if g[3] and g[4] and g[5]:
        return date(int(g[5]), _MONTH_MAP[g[4].lower()], int(g[3]))
    if g[6] and g[7] and g[8]:
        return date(int(g[8]), _MONTH_MAP[g[7].lower()], int(g[6]))
    return None


class ImapListener:
    def __init__(self, on_email: OnEmailCallback, sender_filter: str = "", poll_interval: int = 60):
        self.on_email = on_email
        self.sender_filter = sender_filter
        self.poll_interval = poll_interval
        self._client: IMAP4_SSL | None = None
        self._running = False

    async def start(self):
        self._running = True
        status.set_running(True)
        try:
            while self._running:
                try:
                    await self._connect_and_listen()
                except Exception as e:
                    status.record_error(str(e))
                    logger.error(f"IMAP connection error: {e}, reconnecting in 30s")
                    await asyncio.sleep(30)
        finally:
            status.set_running(False)

    async def stop(self):
        self._running = False
        status.set_running(False)
        if self._client:
            try:
                await self._client.logout()
            except Exception as e:
                logger.debug(f"Error closing IMAP connection: {e}")
            self._client = None

    async def _connect(self) -> IMAP4_SSL:
        settings = get_settings()
        client = IMAP4_SSL(host=settings.imap_host, port=settings.imap_port)
        await client.wait_hello_from_server()
        login = await client.login(settings.imap_user, settings.imap_password)
        if login.result != "OK":
            detail = "; ".join(
                line.decode(errors="ignore") if isinstance(line, (bytes, bytearray)) else str(line)
                for line in login.lines
            )
            raise RuntimeError(
                f"IMAP login failed for {settings.imap_user}: {detail or 'invalid credentials'}"
            )
        selected = await client.select("INBOX")
        if selected.result != "OK":
            raise RuntimeError(f"IMAP SELECT INBOX failed: {selected.lines}")
        return client

    async def _connect_and_listen(self):
        self._client = await self._connect()
        logger.info(f"IMAP connected, polling every {self.poll_interval}s")

        while self._running:
            await self._fetch_new_emails()
            await asyncio.sleep(self.poll_interval)

    async def fetch_unprocessed(self) -> list[tuple[bytes, str, datetime]]:
        if not self._client:
            self._client = await self._connect()

        result = await self._client.search("UNSEEN")
        uids = result.lines[0].decode().split()
        results = []
        last_subject: str | None = None

        for uid in uids:
            msg_result = await self._client.fetch(uid, "(BODY.PEEK[])")
            raw_email = self._extract_raw_email(msg_result.lines)

            subject = self._extract_subject(raw_email)
            if not subject or not DDS_SUBJECT_PATTERN.search(subject):
                continue

            if self.sender_filter:
                sender = self._extract_sender(raw_email)
                if self.sender_filter.lower() not in sender.lower():
                    logger.debug(f"Skipping email from {sender} (filter: {self.sender_filter})")
                    continue

            msg_date = self._extract_date(raw_email)
            results.append((raw_email, subject, msg_date))
            last_subject = subject

            await self._client.store(uid, "+FLAGS", "\\SEEN")

        matched = len(results)
        if matched:
            logger.info(f"IMAP fetch: {len(uids)} unseen, {matched} DDS match(es)")
        else:
            logger.debug(f"IMAP fetch: {len(uids)} unseen, 0 DDS match(es)")
        status.record_poll(len(uids), matched, last_subject)
        return results

    async def _fetch_new_emails(self) -> int:
        result = await self._client.search("UNSEEN")
        uids = result.lines[0].decode().split()
        matched = 0
        last_subject: str | None = None

        for uid in uids:
            msg_result = await self._client.fetch(uid, "(BODY.PEEK[])")
            raw_email = self._extract_raw_email(msg_result.lines)

            subject = self._extract_subject(raw_email)
            if not subject or not DDS_SUBJECT_PATTERN.search(subject):
                continue

            if self.sender_filter:
                sender = self._extract_sender(raw_email)
                if self.sender_filter.lower() not in sender.lower():
                    logger.debug(f"Skipping email from {sender} (filter: {self.sender_filter})")
                    continue

            matched += 1
            last_subject = subject
            logger.info(f"Auto-fetching DDS email uid={uid} subject={subject!r}")

            msg_date = self._extract_date(raw_email)
            processed = await self.on_email(raw_email, subject, msg_date)
            if processed:
                try:
                    await self._client.store(uid, "+FLAGS", "\\SEEN")
                except Exception as e:
                    logger.warning(f"Failed to mark email {uid} as seen: {e}")

        if matched:
            logger.info(f"IMAP poll: {len(uids)} unseen, {matched} DDS match(es)")
        else:
            logger.debug(f"IMAP poll: {len(uids)} unseen, 0 DDS match(es)")
        status.record_poll(len(uids), matched, last_subject)
        return matched

    def _extract_subject(self, raw: bytes) -> str | None:
        msg = email.message_from_bytes(raw)
        return msg.get("Subject", "").strip() or None

    def _extract_sender(self, raw: bytes) -> str:
        msg = email.message_from_bytes(raw)
        return msg.get("From", "")

    def _extract_date(self, raw: bytes) -> datetime:
        msg = email.message_from_bytes(raw)
        date_str = msg.get("Date", "")
        if date_str:
            try:
                return parsedate_to_datetime(date_str)
            except (ValueError, TypeError):
                pass
        return datetime.now(UTC)

    def _extract_raw_email(self, lines: list) -> bytes:
        parts: list[bytes] = []
        expected_literals = 0
        for line in lines:
            if isinstance(line, str):
                line = line.encode("utf-8", errors="ignore")
            if not isinstance(line, (bytes, bytearray)):
                continue
            chunk = bytes(line)
            literals = re.findall(rb"\{(\d+)\}", chunk)
            if literals:
                expected_literals += len(literals)
                continue
            if expected_literals:
                parts.append(chunk)
                expected_literals -= 1
                continue
            stripped = chunk.strip()
            if stripped in (b")", b"Success completed (Success)"):
                break
        return b"".join(parts)
