import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router, set_sidecar
from config.logging import setup_logging
from core.database import async_session_factory, engine
from services.imap_listener import ImapListener
from services.processor import Processor
from services.sidecar_manager import SidecarManager

setup_logging()
logger = logging.getLogger(__name__)

sidecar_manager = SidecarManager()
imap_listener: ImapListener | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global imap_listener
    logger.info("Starting DDS Email ETL service")

    await sidecar_manager.start()
    set_sidecar(sidecar_manager)

    async def on_email(raw: bytes, subject: str, received_at):
        async with async_session_factory() as db:
            proc = Processor(db, sidecar_manager)
            await proc.process_email(raw, subject, received_at)

    imap_listener = ImapListener(on_email)
    asyncio.create_task(imap_listener.start())

    yield

    if imap_listener:
        await imap_listener.stop()
    await sidecar_manager.stop()
    await engine.dispose()


app = FastAPI(
    title="DDS Email ETL",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "sidecar_running": sidecar_manager._running if hasattr(sidecar_manager, '_running') else False,
    }
