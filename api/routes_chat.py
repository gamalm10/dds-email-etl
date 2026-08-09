import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes import get_current_user, get_db, get_sidecar
from core.models import ChatConversation
from core.schemas import ChatMessageCreate
from services.chat_service import (
    get_conversation_messages,
    list_conversations,
    send_message_stream,
)
from services.sidecar_manager import SidecarManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.get("/conversations")
async def get_conversations(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"conversations": await list_conversations(db, user.id)}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conv = await db.get(ChatConversation, conversation_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"messages": await get_conversation_messages(db, conversation_id)}


@router.post("/send")
async def send_chat_message(
    body: ChatMessageCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    sidecar: SidecarManager = Depends(get_sidecar),
):
    async def event_stream():
        async for chunk in send_message_stream(db, sidecar, user.id, body.content, body.report_id):
            yield chunk

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/conversations/{conversation_id}/send")
async def send_in_conversation(
    conversation_id: int,
    body: ChatMessageCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    sidecar: SidecarManager = Depends(get_sidecar),
):
    async def event_stream():
        async for chunk in send_message_stream(db, sidecar, user.id, body.content, None, conversation_id):
            yield chunk

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
