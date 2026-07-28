import asyncio
import email
import logging
import re
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime

from aioimaplib import IMAP4_SSL

from config.settings import get_settings

logger = logging.getLogger(__name__)

DDS_SUBJECT_PATTERN = re.compile(
    r"(?:DDS-(\d{2})\.(\d{2})\.(\d{4}))|"
    r"(?:Operation DDS[ -]+(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4}))|"
    r"(?:DDS[ -]+(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4}))",
    re.IGNORECASE,
)

OnEmailCallback = Callable[[bytes, str, datetime], Awaitable[None]]


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
    def __init__(self, on_email: OnEmailCallback):
        self.on_email = on_email
        self._client: IMAP4_SSL | None = None
        self._running = False

    async def start(self):
        self._running = True
        while self._running:
            try:
                await self._connect_and_listen()
            except Exception as e:
                logger.error(f"IMAP connection error: {e}, reconnecting in 30s")
                await asyncio.sleep(30)

    async def stop(self):
        self._running = False
        if self._client:
            self._client.close()

    async def _connect_and_listen(self):
        settings = get_settings()
        self._client = IMAP4_SSL(host=settings.imap_host, port=settings.imap_port)
        await self._client.wait_hello_from_server()
        await self._client.login(settings.imap_user, settings.imap_password)
        await self._client.select("INBOX")
        logger.info("IMAP connected, waiting for IDLE notifications")

        while self._running:
            await self._client.idle()
            try:
                result = await self._client.wait_for_update(timeout=60)
                if result and self._running:
                    await self._fetch_new_emails()
            except TimeoutError:
                continue
            finally:
                await self._client.idle_done()

    async def fetch_unprocessed(self) -> list[tuple[bytes, str, datetime]]:
        settings = get_settings()
        if not self._client:
            self._client = IMAP4_SSL(host=settings.imap_host, port=settings.imap_port)
            await self._client.wait_hello_from_server()
            await self._client.login(settings.imap_user, settings.imap_password)
            await self._client.select("INBOX")

        result = await self._client.search("UNSEEN")
        uids = result.lines[0].decode().split()
        results = []

        for uid in uids:
            msg_result = await self._client.fetch(uid, "(BODY.PEEK[])")
            raw_email = b""
            for line in msg_result.lines:
                if isinstance(line, bytes):
                    raw_email += line

            subject = self._extract_subject(raw_email)
            if not subject or not DDS_SUBJECT_PATTERN.search(subject):
                continue

            msg_date = self._extract_date(raw_email)
            results.append((raw_email, subject, msg_date))

            await self._client.store(uid, "+FLAGS", "\\SEEN")

        return results

    async def _fetch_new_emails(self):
        result = await self._client.search("UNSEEN")
        uids = result.lines[0].decode().split()
        if not uids:
            return

        for uid in uids:
            msg_result = await self._client.fetch(uid, "(BODY.PEEK[])")
            raw_email = b""
            for line in msg_result.lines:
                if isinstance(line, bytes):
                    raw_email += line

            subject = self._extract_subject(raw_email)
            if not subject or not DDS_SUBJECT_PATTERN.search(subject):
                continue

            msg_date = self._extract_date(raw_email)
            await self.on_email(raw_email, subject, msg_date)

    def _extract_subject(self, raw: bytes) -> str | None:
        msg = email.message_from_bytes(raw)
        return msg.get("Subject", "").strip() or None

    def _extract_date(self, raw: bytes) -> datetime:
        msg = email.message_from_bytes(raw)
        date_str = msg.get("Date", "")
        if date_str:
            try:
                return parsedate_to_datetime(date_str)
            except (ValueError, TypeError):
                pass
        return datetime.now(UTC)
