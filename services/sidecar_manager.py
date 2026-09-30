import asyncio
import json
import logging
import re
from asyncio.subprocess import PIPE

from config.settings import get_settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PROVIDER = "openai"
DEFAULT_MODEL_ID = "gpt-4.1-mini"


class SidecarError(Exception):
    pass


class SidecarManager:
    """Talks to the PI coding agent over its JSON-lines RPC mode.

    The wire format is NOT JSON-RPC: commands are
    ``{"id": N, "type": "<command>", ...params}`` and replies come back as
    ``{"id": N, "type": "response", "command": ..., "success": ..., "data": ...}``.
    A ``prompt`` command is acknowledged as soon as preflight passes, then emits
    a stream of events terminated by ``agent_end``.
    """

    def __init__(self):
        self._process: asyncio.subprocess.Process | None = None
        self._running = False
        self._lock = asyncio.Lock()
        self._next_id = 0
        self._buffer: list[dict] = []
        self._model: str | None = None

    @property
    def model_id(self) -> str:
        return self._model or DEFAULT_MODEL_ID

    async def start(self):
        async with self._lock:
            if self._running and self._process and self._process.returncode is None:
                return
            settings = get_settings()
            self._process = await asyncio.create_subprocess_shell(
                settings.pi_sidecar_cmd,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
            )
            self._running = True
            self._buffer = []
            self._model = None
            logger.info("PI SDK sidecar started (PID %s)", self._process.pid)

    async def stop(self):
        async with self._lock:
            if not self._running or not self._process:
                return
            try:
                self._process.terminate()
            except ProcessLookupError:
                pass
            try:
                await asyncio.wait_for(self._process.wait(), timeout=10)
            except (TimeoutError, ProcessLookupError):
                try:
                    self._process.kill()
                except ProcessLookupError:
                    pass
            self._running = False
            logger.info("PI SDK sidecar stopped")

    def _alloc_id(self) -> int:
        self._next_id += 1
        return self._next_id

    async def _write(self, payload: dict) -> None:
        if not self._process or self._process.stdin is None:
            raise SidecarError("Sidecar not running")
        self._process.stdin.write((json.dumps(payload) + "\n").encode())
        await self._process.stdin.drain()

    async def _read_event(self, timeout: float) -> dict:
        if not self._process or self._process.stdout is None:
            raise SidecarError("Sidecar not running")
        line = await asyncio.wait_for(self._process.stdout.readline(), timeout=timeout)
        if not line:
            raise SidecarError("PI SDK sidecar closed its output stream")
        text = line.decode(errors="replace").strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"type": "log", "message": text}

    async def _await_response(self, req_id: int, timeout: float) -> dict:
        """Read until the response matching req_id arrives, buffering other events."""
        for event in self._buffer:
            if event.get("type") == "response" and event.get("id") == req_id:
                self._buffer.remove(event)
                return event
        while True:
            event = await self._read_event(timeout)
            if event.get("type") == "response" and event.get("id") == req_id:
                return event
            if event:
                self._buffer.append(event)

    async def _command(self, command: str, timeout: float, **params) -> dict:
        req_id = self._alloc_id()
        await self._write({"id": req_id, "type": command, **params})
        response = await self._await_response(req_id, timeout)
        if not response.get("success"):
            raise SidecarError(f"PI SDK error: {response.get('error')}")
        return response.get("data") or {}

    async def _ensure_model(self) -> None:
        if self._model == DEFAULT_MODEL_ID:
            return
        await self._command(
            "set_model",
            30,
            provider=DEFAULT_MODEL_PROVIDER,
            modelId=DEFAULT_MODEL_ID,
        )
        self._model = DEFAULT_MODEL_ID
        logger.info("PI SDK model set to %s", DEFAULT_MODEL_ID)

    @staticmethod
    def _message_text(message: dict) -> str:
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "\n".join(p for p in parts if p)
        return ""

    async def prompt(self, message: str, system_prompt: str | None = None) -> str:
        """Run one prompt to completion and return the assistant's text."""
        if not self._running or not self._process:
            await self.start()

        settings = get_settings()
        timeout = float(settings.pi_timeout_seconds)

        async with self._lock:
            try:
                await self._ensure_model()
            except (SidecarError, TimeoutError) as e:
                logger.warning(f"Could not select model ({e}); continuing with sidecar default")

            full_text = f"{system_prompt}\n\n---\n\n{message}" if system_prompt else message
            req_id = self._alloc_id()
            await self._write({"id": req_id, "type": "prompt", "message": full_text})

            try:
                response = await self._await_response(req_id, timeout)
            except (SidecarError, TimeoutError) as e:
                await self._restart()
                raise SidecarError(f"PI SDK prompt failed: {e}") from e

            if not response.get("success"):
                raise SidecarError(f"PI SDK error: {response.get('error')}")

            chunks: list[str] = []
            while True:
                try:
                    event = await self._read_event(timeout)
                except (SidecarError, TimeoutError) as e:
                    await self._restart()
                    raise SidecarError(f"PI SDK stream failed: {e}") from e
                kind = event.get("type")
                if kind == "agent_end":
                    break
                if kind == "message_end":
                    message_obj = event.get("message") or {}
                    if message_obj.get("role") == "assistant":
                        text = self._message_text(message_obj)
                        if text:
                            chunks.append(text)
                if kind == "error":
                    raise SidecarError(f"PI SDK error: {event.get('error') or event}")

            return "\n".join(chunks).strip()

    @staticmethod
    def _parse_json_response(text: str) -> dict:
        cleaned = text.strip()
        fenced = re.search(r"```(?:json)?\s*(.+?)```", cleaned, re.DOTALL)
        if fenced:
            cleaned = fenced.group(1).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start >= 0 and end > start:
                return json.loads(cleaned[start:end + 1])
            raise

    async def extract(self, email_html: str, context: str | None = None) -> dict:
        prompt_text = email_html
        if context:
            prompt_text = f"Previous report context:\n{context}\n\nNew email:\n{email_html}"

        system_prompt = self._load_system_prompt()
        answer = await self.prompt(prompt_text, system_prompt)
        return self._parse_json_response(answer)

    async def _restart(self):
        logger.warning("Restarting PI SDK sidecar")
        await self.stop()
        await self.start()

    def _load_system_prompt(self) -> str:
        try:
            with open("pi/dds_analyst_prompt.md") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("System prompt file not found, using default")
            return "You are a DDS email analyst. Extract structured data from supply chain emails."
