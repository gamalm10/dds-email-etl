import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes import get_sidecar
from config.settings import get_settings
from core.database import get_db
from core.models import ChatConversation, Report
from core.schemas import ChatMessageCreate
from services.chat_service import (
    get_conversation_messages,
    list_conversations,
    send_message_stream,
)
from services.embedding_service import embed_all_reports, embed_report
from services.sidecar_manager import SidecarManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

FALLBACK_USER_ID = 1


async def get_current_user_id(request: Request) -> int:
    """Resolve the caller from the access token, falling back to the seed admin.

    The frontend signs tokens with the shared JWT_SECRET, so the same secret
    verifies them here. Chat must not be pinned to a single hardcoded user id.
    """
    header = request.headers.get("authorization", "")
    token = header.replace("Bearer ", "").strip()
    if not token:
        return FALLBACK_USER_ID
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
    except jwt.InvalidTokenError as e:
        logger.warning(f"Rejecting chat request with invalid token: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("userId")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing user id")
    return int(user_id)


@router.get("/conversations")
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return {"conversations": await list_conversations(db, user_id)}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    conv = await db.get(ChatConversation, conversation_id)
    if not conv or conv.user_id != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"messages": await get_conversation_messages(db, conversation_id)}


@router.post("/send")
async def send_chat_message(
    body: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    sidecar: SidecarManager = Depends(get_sidecar),
    user_id: int = Depends(get_current_user_id),
):
    async def event_stream():
        async for chunk in send_message_stream(
            db, sidecar, user_id, body.content, body.report_id, new_conversation=body.new_conversation
        ):
            yield chunk

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/conversations/{conversation_id}/send")
async def send_in_conversation(
    conversation_id: int,
    body: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    sidecar: SidecarManager = Depends(get_sidecar),
    user_id: int = Depends(get_current_user_id),
):
    conv = await db.get(ChatConversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your conversation")

    async def event_stream():
        async for chunk in send_message_stream(db, sidecar, user_id, body.content, None, conversation_id):
            yield chunk

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/embed/report/{report_id}")
async def embed_single_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    count = await embed_report(db, report_id)
    return {"report_id": report_id, "embedded_chunks": count}


@router.post("/embed/all")
async def embed_all(
    db: AsyncSession = Depends(get_db),
):
    count = await embed_all_reports(db)
    return {"embedded_chunks": count}


@router.get("/embed/status")
async def embed_status(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT source_type, COUNT(*) as cnt FROM dds_report_embeddings GROUP BY source_type")
    )
    rows = result.all()
    total = await db.execute(text("SELECT COUNT(*) as cnt FROM dds_report_embeddings"))
    return {
        "total": total.scalar(),
        "by_source": {row.source_type: row.cnt for row in rows},
    }
