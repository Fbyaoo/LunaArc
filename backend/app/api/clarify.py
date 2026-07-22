from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.agent_adapter import AgentIntegrationError, agent_adapter
from app.schemas.readings import ClarifyRequest, ReadingResponse
from app.database.models import User
from app.database.connection import get_db
from app.database.crud import create_cards, create_reading, create_session
from app.dependencies.auth import get_current_user
from app.services.quota_service import check_reading_quota
from app.services.usage_service import consume_reading
from app.services.clarify_cache import (
    get_clarify_prompt,
    get_request,
    delete_request,
)


router = APIRouter(
    prefix="/api/readings",
    tags=["clarify"],
)


@router.post(
    "/clarify",
    response_model=ReadingResponse,
)
def clarify_reading(
    body: ClarifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_id = body.session_id
    supplement = body.user_supplement.strip()

    if not supplement:
        raise HTTPException(status_code=422, detail="补充信息不能为空")

    request = get_request(
        session_id,
        current_user.id,
    )

    if request is None:
        raise HTTPException(
            status_code=410,
            detail="会话已过期，请重新抽牌",
        )

    clarification_prompt = get_clarify_prompt(session_id, current_user.id)

    quota_reserved = check_reading_quota(db, current_user, request.spread_type)

    try:
        result = agent_adapter.resume_reading(request, supplement)
    except AgentIntegrationError as error:
        raise HTTPException(
            status_code=503,
            detail={"error_code": "AGENT_UNAVAILABLE", "message": str(error)},
        ) from error

    try:
        session = create_session(
            db,
            request.question,
            request.spread_type,
            current_user.id,
        )
        create_cards(db, session.id, request.cards, result.card_readings)
        reading_record = create_reading(
            db,
            session.id,
            result.summary,
            result.synthesis,
            result.advice,
            clarification_prompt=clarification_prompt,
            clarification_answer=supplement,
        )
        if not quota_reserved:
            consume_reading(db, current_user, request.spread_type)
        db.commit()
        db.refresh(reading_record)
        result.reading_id = reading_record.id
        result.saved = reading_record.saved
        result.created_at = reading_record.created_at
    except Exception:
        db.rollback()
        raise

    delete_request(session_id)

    return result
