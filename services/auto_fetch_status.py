import logging
import threading
from collections import deque
from datetime import UTC, datetime
from typing import Any

LOGGER_ALLOWLIST = {"services.imap_listener", "services.processor", "api.main"}
MAX_LOG_LINES = 200


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class AutoFetchStatus:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.running = False
        self.last_poll_at: str | None = None
        self.last_match_at: str | None = None
        self.last_subject: str | None = None
        self.unseen_count = 0
        self.poll_count = 0
        self.match_count = 0
        self.last_error: str | None = None
        self.reconnect_count = 0

    def set_running(self, running: bool) -> None:
        with self._lock:
            self.running = running

    def record_poll(self, unseen: int, matched: int, subject: str | None = None) -> None:
        with self._lock:
            self.last_poll_at = _now_iso()
            self.poll_count += 1
            self.unseen_count = unseen
            if matched:
                self.match_count += matched
                self.last_match_at = _now_iso()
                if subject:
                    self.last_subject = subject

    def record_error(self, message: str) -> None:
        with self._lock:
            self.last_error = message
            self.reconnect_count += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "running": self.running,
                "last_poll_at": self.last_poll_at,
                "last_match_at": self.last_match_at,
                "last_subject": self.last_subject,
                "unseen_count": self.unseen_count,
                "poll_count": self.poll_count,
                "match_count": self.match_count,
                "last_error": self.last_error,
                "reconnect_count": self.reconnect_count,
            }


status = AutoFetchStatus()

_recent_logs: deque[str] = deque(maxlen=MAX_LOG_LINES)


class _MemoryLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)

    def emit(self, record: logging.LogRecord) -> None:
        if record.name not in LOGGER_ALLOWLIST:
            return
        try:
            _recent_logs.append(self.format(record))
        except Exception:
            self.handleError(record)


def install_log_handler() -> None:
    root = logging.getLogger()
    if any(isinstance(h, _MemoryLogHandler) for h in root.handlers):
        return
    handler = _MemoryLogHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(handler)


def recent_logs(limit: int = 100) -> list[str]:
    return list(_recent_logs)[-limit:][::-1]
