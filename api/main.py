import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router, set_sidecar
from api.routes_auth_reset import router as auth_reset_router
from api.routes_brands import router as brands_router
from api.routes_dashboard import router as dashboard_router
from api.routes_actions import router as actions_router
from api.routes_users import router as users_router
from config.logging import setup_logging
from config.settings import get_settings
from core.database import async_session_factory, engine
from services.imap_listener import ImapListener
from services.processor import Processor
from services.sidecar_manager import SidecarManager

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

sidecar_manager = SidecarManager()
imap_listener: ImapListener | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global imap_listener
    logger.info("Starting DDS Email ETL service")

    await sidecar_manager.start()
    set_sidecar(sidecar_manager)

    async def on_email(raw: bytes, subject: str, received_at):
        try:
            async with async_session_factory() as db:
                proc = Processor(db, sidecar_manager)
                await proc.process_email(raw, subject, received_at)
        except Exception as e:
            logger.error(f"Email processing failed: {e}")

    imap_listener = ImapListener(on_email, sender_filter=settings.email_sender_filter)
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
app.include_router(auth_reset_router)
app.include_router(brands_router)
app.include_router(dashboard_router)
app.include_router(actions_router)
app.include_router(users_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "sidecar_running": sidecar_manager._running if hasattr(sidecar_manager, '_running') else False,
    }
