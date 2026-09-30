import asyncio
import json
import logging
import re
from collections.abc import AsyncGenerator

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import ChatConversation, ChatMessage
from services.analysis import build_analysis_block
from services.rag_retriever import retrieve_context
from services.sidecar_manager import SidecarError, SidecarManager

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT_PATH = "pi/chat_prompt.md"

CHUNK_DELAY_SECONDS = 0.05
_BOUNDARY_RE = re.compile(r"[.!?](?=\s|$)\s+|\n")


def chunk_for_streaming(text: str, min_chars: int = 48) -> list[str]:
    """Split an answer into readable chunks so the UI can render it progressively.

    The sidecar only emits whole messages, not token deltas, so the finished
    answer is emitted in sentence-sized pieces instead of one big block. The
    original text is sliced rather than split, so no characters are dropped.
    """
    text = (text or "").strip()
    if not text:
        return []

    boundaries = [m.end() for m in _BOUNDARY_RE.finditer(text)]
    if not boundaries:
        return [text]

    chunks: list[str] = []
    start = 0
    for end in boundaries:
        if end - start >= min_chars:
            chunks.append(text[start:end])
            start = end
    if start < len(text):
        remainder = text[start:]
        if chunks and len(remainder.strip()) < 12:
            chunks[-1] += remainder
        else:
            chunks.append(remainder)
    return [c for c in chunks if c.strip()]


def _load_chat_prompt() -> str:
    try:
        with open(CHAT_SYSTEM_PROMPT_PATH) as f:
            return f.read()
    except FileNotFoundError:
        return "You are a DDS email analyst. Answer questions about supply chain reports."


def _build_context_block(results) -> str:
    if not results:
        return "No relevant data found in reports."
    lines = ["## Relevant Report Data\n"]
    for i, r in enumerate(results, 1):
        citation = f"[{r.source_type.replace('_', ' ').title()} #{r.source_id}]"
        if r.brand_name:
            citation += f" ({r.brand_name})"
        lines.append(f"### {i}. {citation}")
        lines.append(r.chunk_text)
        lines.append("")
    return "\n".join(lines)


def _extract_citations(results) -> list[dict]:
    return [
        {
            "type": r.source_type,
            "id": r.source_id,
            "report_id": r.report_id,
            "label": f"{r.source_type.replace('_', ' ').title()} #{r.source_id}" + (f" ({r.brand_name})" if r.brand_name else ""),
        }
        for r in results
    ]


async def get_or_create_conversation(
    db: AsyncSession, user_id: int, report_id: int | None = None
) -> ChatConversation:
    stmt = (
        select(ChatConversation)
        .where(ChatConversation.user_id == user_id, ChatConversation.report_id == report_id)
        .order_by(ChatConversation.updated_at.desc())
        .limit(1)
    )
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if conv:
        return conv
    conv = ChatConversation(user_id=user_id, report_id=report_id)
    db.add(conv)
    await db.flush()
    return conv


async def list_conversations(db: AsyncSession, user_id: int) -> list[dict]:
    stmt = (
        select(ChatConversation, func.count(ChatMessage.id).label("message_count"))
        .outerjoin(ChatMessage, ChatConversation.id == ChatMessage.conversation_id)
        .where(ChatConversation.user_id == user_id)
        .group_by(ChatConversation.id)
        .order_by(ChatConversation.updated_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "id": conv.id, "report_id": conv.report_id, "title": conv.title,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
            "message_count": count,
        }
        for conv, count in rows
    ]


async def get_conversation_messages(db: AsyncSession, conversation_id: int) -> list[dict]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at)
    )
    messages = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": m.id, "role": m.role, "content": m.content,
            "citations": m.citations,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


async def send_message_stream(
    db: AsyncSession,
    sidecar: SidecarManager,
    user_id: int,
    content: str,
    report_id: int | None = None,
    conversation_id: int | None = None,
) -> AsyncGenerator[str, None]:
    if conversation_id:
        conv = await db.get(ChatConversation, conversation_id)
        if not conv or conv.user_id != user_id:
            conv = await get_or_create_conversation(db, user_id, report_id)
    else:
        conv = await get_or_create_conversation(db, user_id, report_id)

    user_msg = ChatMessage(conversation_id=conv.id, role="user", content=content)
    db.add(user_msg)
    await db.flush()

    if not conv.title and content:
        conv.title = content[:80]
    await db.flush()

    yield json.dumps({"type": "metadata", "conversation_id": conv.id}) + "\n"
    yield json.dumps({"type": "thinking", "stage": "retrieving"}) + "\n"

    retrieval_results = await retrieve_context(db, content, report_id)
    context_block = _build_context_block(retrieval_results)
    citations = _extract_citations(retrieval_results)

    system_prompt = _load_chat_prompt()

    recent_stmt = (
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    recent_msgs = list(reversed((await db.execute(recent_stmt)).scalars().all()))

    history_text = ""
    for m in recent_msgs:
        role = "User" if m.role == "user" else "Assistant"
        history_text += f"{role}: {m.content}\n"

    analysis_block = await build_analysis_block(db, report_id)

    full_prompt = (
        f"{analysis_block}\n\n{context_block}\n\n---\n\n"
        f"## Conversation History\n{history_text}\n\n---\n\n"
        f"## Current Question\n{content}"
    )

    try:
        yield json.dumps({"type": "thinking", "stage": "analysing"}) + "\n"

        full_response = await sidecar.prompt(full_prompt, system_prompt)
        if not full_response:
            raise SidecarError("PI SDK returned an empty response")

        for chunk in chunk_for_streaming(full_response):
            yield json.dumps({"type": "token", "content": chunk}) + "\n"
            await asyncio.sleep(CHUNK_DELAY_SECONDS)

        assistant_msg = ChatMessage(
            conversation_id=conv.id, role="assistant", content=full_response,
            citations=citations if citations else None, model=sidecar.model_id,
        )
        db.add(assistant_msg)
        await db.commit()

        yield json.dumps({
            "type": "done", "message_id": assistant_msg.id, "citations": citations,
        }) + "\n"

    except SidecarError as e:
        logger.error(f"Chat LLM error: {e}")
        error_msg = ChatMessage(
            conversation_id=conv.id, role="assistant",
            content="I encountered an error processing your question. Please try again.",
        )
        db.add(error_msg)
        await db.commit()
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"
