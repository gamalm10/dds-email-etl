import asyncio
import json
import logging
from asyncio.subprocess import PIPE

from config.settings import get_settings

logger = logging.getLogger(__name__)


class SidecarError(Exception):
    pass


class SidecarManager:
    def __init__(self):
        self._process: asyncio.subprocess.Process | None = None
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self):
        async with self._lock:
            if self._running:
                return
            settings = get_settings()
            self._process = await asyncio.create_subprocess_shell(
                settings.pi_sidecar_cmd,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
            )
            self._running = True
            logger.info("PI SDK sidecar started (PID: %s)", self._process.pid)

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

    async def extract(self, email_html: str, context: str | None = None) -> dict:
        if not self._running or not self._process:
            await self.start()

        prompt_text = email_html
        if context:
            prompt_text = f"Previous report context:\n{context}\n\nNew email:\n{email_html}"

        system_prompt = self._load_system_prompt()

        request = {
            "jsonrpc": "2.0",
            "method": "session/prompt",
            "params": {
                "text": prompt_text,
                "systemPrompt": system_prompt,
                "model": "gpt-5.4-mini",
            },
            "id": 1,
        }

        return await self._send_request(request)

    async def embed(self, text: str) -> list[float]:
        request = {
            "jsonrpc": "2.0",
            "method": "session/prompt",
            "params": {
                "text": f"Return ONLY a JSON array of floats representing the embedding vector for this text, no other output: {text}",
                "model": "text-embedding-3-small",
            },
            "id": 2,
        }
        return await self._send_request(request)

    async def _send_request(self, request: dict) -> any:
        async with self._lock:
            if not self._process or not self._process.stdin:
                raise SidecarError("Sidecar not running")

            settings = get_settings()
            stdin_data = (json.dumps(request) + "\n").encode()
            self._process.stdin.write(stdin_data)
            await self._process.stdin.drain()

            try:
                response = await asyncio.wait_for(
                    self._read_line(),
                    timeout=settings.pi_timeout_seconds,
                )
            except TimeoutError:
                await self._restart()
                raise SidecarError("PI SDK sidecar timed out")

            if not response:
                await self._restart()
                raise SidecarError("PI SDK sidecar returned empty response")

            result = json.loads(response.decode())
            if "error" in result:
                raise SidecarError(f"PI SDK error: {result['error']}")

            raw_result = result.get("result", "{}")
            if isinstance(raw_result, str):
                return json.loads(raw_result)
            return raw_result

    async def _read_line(self) -> bytes | None:
        if not self._process or not self._process.stdout:
            return None
        try:
            return await asyncio.wait_for(self._process.stdout.readline(), timeout=120)
        except TimeoutError:
            return None

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
