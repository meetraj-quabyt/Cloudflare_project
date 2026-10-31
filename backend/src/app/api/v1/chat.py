import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.repositories import chat_repo
from app.services.ai_service import generate_chat_reply

router = APIRouter(prefix="/chat", tags=["chat"])


class CreateSessionRequest(BaseModel):
    title: str = Field(default="New Conversation", max_length=120)
    system_prompt: str = Field(default="", max_length=1000)


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


@router.get("/sessions")
async def list_chat_sessions(request: Request) -> list[dict[str, Any]]:
    db = request.app.state.db
    return await chat_repo.list_sessions(db)


@router.post("/sessions")
async def create_chat_session(req: CreateSessionRequest, request: Request) -> dict[str, Any]:
    db = request.app.state.db
    session_id = uuid.uuid4().hex
    return await chat_repo.create_session(db, session_id, req.title, req.system_prompt)


@router.get("/sessions/{session_id}")
async def get_chat_session(session_id: str, request: Request) -> dict[str, Any]:
    db = request.app.state.db
    session = await chat_repo.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    messages = await chat_repo.get_messages(db, session_id)
    return {
        "session": session,
        "messages": messages,
    }


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str, request: Request) -> dict[str, Any]:
    db = request.app.state.db
    session = await chat_repo.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    await chat_repo.delete_session(db, session_id)
    return {"status": "deleted", "session_id": session_id}


@router.post("/sessions/{session_id}/messages")
async def send_chat_message(session_id: str, req: SendMessageRequest, request: Request) -> dict[str, Any]:
    db = request.app.state.db
    session = await chat_repo.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    user_msg_id = uuid.uuid4().hex
    user_msg = await chat_repo.add_message(
        db=db,
        message_id=user_msg_id,
        session_id=session_id,
        role="user",
        content=req.content,
    )

    # Fetch prior messages for context
    all_messages = await chat_repo.get_messages(db, session_id)
    system_prompt = session.get("system_prompt") or None

    try:
        ai_result = await generate_chat_reply(
            messages=[{"role": m["role"], "content": m["content"]} for m in all_messages],
            system_prompt=system_prompt,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {str(e)}")

    assistant_msg_id = uuid.uuid4().hex
    assistant_msg = await chat_repo.add_message(
        db=db,
        message_id=assistant_msg_id,
        session_id=session_id,
        role="assistant",
        content=ai_result["reply"],
        tokens_used=ai_result.get("tokens_used", 0),
    )

    # Automatically set a clean title from the first message if needed
    if session.get("title") in ("New Conversation", "New Chat", ""):
        clean_title = req.content[:35] + ("..." if len(req.content) > 35 else "")
        await chat_repo.update_session_title(db, session_id, clean_title)

    return {
        "user_message": user_msg,
        "assistant_message": assistant_msg,
    }

