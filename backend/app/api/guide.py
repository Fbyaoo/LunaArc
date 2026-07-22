from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.agent_adapter import AgentIntegrationError
from app.database.connection import get_db
from app.database.models import GuideMessage, GuideSession, User, utc_now
from app.dependencies.auth import get_current_user
from app.schemas.guide import (
    GuideMessageCreate,
    GuideMessageResponse,
    GuideSessionCreate,
    GuideSessionResponse,
)
from app.services.guide_service import generate_guide_reply
from app.services.reading_query_service import get_owned_reading
from app.services.usage_service import get_today_usage


router = APIRouter(prefix="/api/guide", tags=["guide"])


def _get_owned_session(db: Session, user_id: int, session_id: int) -> GuideSession:
    guide_session = (
        db.query(GuideSession)
        .filter(GuideSession.id == session_id, GuideSession.user_id == user_id)
        .first()
    )
    if guide_session is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "GUIDE_SESSION_NOT_FOUND",
                "message": "向导会话不存在。",
            },
        )
    return guide_session


def _session_response(item: GuideSession) -> GuideSessionResponse:
    return GuideSessionResponse(
        session_id=item.id,
        reading_id=item.reading_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _message_response(item: GuideMessage) -> GuideMessageResponse:
    return GuideMessageResponse(
        id=item.id, role=item.role, content=item.content, created_at=item.created_at
    )


@router.post("/sessions", response_model=GuideSessionResponse, status_code=201)
def create_guide_session(
    body: GuideSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.reading_id is not None:
        reading = get_owned_reading(db, current_user.id, body.reading_id)
        if reading is None:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "READING_NOT_FOUND", "message": "解读不存在。"},
            )
    item = GuideSession(user_id=current_user.id, reading_id=body.reading_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return _session_response(item)


@router.get("/sessions", response_model=list[GuideSessionResponse])
def list_guide_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(GuideSession)
        .filter(GuideSession.user_id == current_user.id)
        .order_by(GuideSession.updated_at.desc())
        .all()
    )
    return [_session_response(item) for item in items]


@router.get(
    "/sessions/{session_id}/messages", response_model=list[GuideMessageResponse]
)
def list_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_session(db, current_user.id, session_id)
    items = (
        db.query(GuideMessage)
        .filter(GuideMessage.session_id == session_id)
        .order_by(GuideMessage.created_at, GuideMessage.id)
        .all()
    )
    return [_message_response(item) for item in items]


@router.post(
    "/sessions/{session_id}/messages",
    response_model=GuideMessageResponse,
    status_code=201,
)
def send_message(
    session_id: int,
    body: GuideMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="消息不能为空。")
    guide_session = _get_owned_session(db, current_user.id, session_id)
    reading = None
    if guide_session.reading_id is not None:
        reading = get_owned_reading(db, current_user.id, guide_session.reading_id)
    history = (
        db.query(GuideMessage)
        .filter(GuideMessage.session_id == session_id)
        .order_by(GuideMessage.created_at, GuideMessage.id)
        .all()
    )
    try:
        reply = generate_guide_reply(guide_session, reading, history, content)
        user_message = GuideMessage(session_id=session_id, role="user", content=content)
        assistant_message = GuideMessage(
            session_id=session_id, role="assistant", content=reply
        )
        db.add_all([user_message, assistant_message])
        guide_session.updated_at = utc_now()
        get_today_usage(db, current_user.id).ai_message_count += 1
        db.commit()
        db.refresh(user_message)
        db.refresh(assistant_message)
    except AgentIntegrationError as error:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail={"error_code": "AGENT_UNAVAILABLE", "message": str(error)},
        ) from error
    return _message_response(assistant_message)
