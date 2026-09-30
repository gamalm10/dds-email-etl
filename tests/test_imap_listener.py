import email

import pytest

from services.imap_listener import DDS_SUBJECT_PATTERN, ImapListener


@pytest.mark.parametrize("subject, expected", [
    ("DDS-06.07.2026", True),
    ("DDS-06.07.2026 (draft)", True),
    ("Fw: DDS-27.07.2026", True),
    ("Meeting notes", False),
    ("DDS-2026-07-06", False),
    ("RE: Operation DDS -27 July 2026", True),
    ("DDS-01.01.2027", True),
])
def test_dds_subject_pattern(subject, expected):
    assert bool(DDS_SUBJECT_PATTERN.search(subject)) == expected


class _FetchResponse:
    def __init__(self, lines):
        self.lines = lines


class FakeImapClient:
    def __init__(self, messages: dict[str, bytes]):
        self.messages = messages
        self.stored: list[tuple[str, str, str]] = []

    async def search(self, criteria):
        return _FetchResponse([b" ".join(uid.encode() for uid in self.messages)])

    async def fetch(self, uid, parts):
        body = self.messages[str(uid)]
        return _FetchResponse([
            b"%s FETCH (BODY[] {%d}" % (str(uid).encode(), len(body)),
            bytearray(body),
            b")",
        ])

    async def store(self, uid, flag_op, flags):
        self.stored.append((str(uid), flag_op, flags))


def _dds_email(subject: str = "DDS-06.07.2026", sender: str = "mohamed.weheba@a-part.com") -> bytes:
    return (
        f"From: {sender}\r\n"
        f"To: ops@a-part.com\r\n"
        f"Subject: {subject}\r\n"
        f"Date: Mon, 06 Jul 2026 10:00:00 +0000\r\n"
        f"\r\n"
        f"<html><body>status</body></html>"
    ).encode()


@pytest.mark.asyncio
async def test_fetch_new_emails_marks_processed_mail_seen():
    client = FakeImapClient({"1": _dds_email()})
    processed = []

    async def on_email(raw, subject, received_at):
        processed.append(subject)
        return True

    listener = ImapListener(on_email)
    listener._client = client
    await listener._fetch_new_emails()

    assert processed == ["DDS-06.07.2026"]
    assert client.stored == [("1", "+FLAGS", "\\SEEN")]


@pytest.mark.asyncio
async def test_fetch_new_emails_keeps_failed_mail_unseen():
    client = FakeImapClient({"1": _dds_email()})
    processed = []

    async def on_email(raw, subject, received_at):
        processed.append(subject)
        return False

    listener = ImapListener(on_email)
    listener._client = client
    await listener._fetch_new_emails()

    assert processed == ["DDS-06.07.2026"]
    assert client.stored == []


@pytest.mark.asyncio
async def test_fetch_new_emails_ignores_non_dds_mail():
    client = FakeImapClient({"1": _dds_email(subject="Meeting notes")})
    processed = []

    async def on_email(raw, subject, received_at):
        processed.append(subject)
        return True

    listener = ImapListener(on_email)
    listener._client = client
    await listener._fetch_new_emails()

    assert processed == []
    assert client.stored == []


@pytest.mark.asyncio
async def test_fetch_new_emails_respects_sender_filter():
    client = FakeImapClient({"1": _dds_email(sender="someone@example.com")})
    processed = []

    async def on_email(raw, subject, received_at):
        processed.append(subject)
        return True

    listener = ImapListener(on_email, sender_filter="a-part.com")
    listener._client = client
    await listener._fetch_new_emails()

    assert processed == []
    assert client.stored == []


def test_extract_raw_email_handles_literal_response():
    body = _dds_email()
    lines = [
        b"1 FETCH (BODY[] {%d}" % len(body),
        bytearray(body),
        b")",
        b"Success",
    ]
    listener = ImapListener(lambda raw, subject, received_at: None)
    assert listener._extract_raw_email(lines) == body


def test_extract_raw_email_ignores_status_line_prefix():
    body = _dds_email()
    listener = ImapListener(lambda raw, subject, received_at: None)
    lines = [b"1 FETCH (BODY[] {%d}" % len(body), bytearray(body), b")"]
    raw = listener._extract_raw_email(lines)

    assert raw == body
    assert email.message_from_bytes(raw).get("Subject") == "DDS-06.07.2026"
