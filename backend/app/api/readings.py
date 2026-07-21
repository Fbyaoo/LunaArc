from fastapi import Depends
from fastapi import APIRouter, HTTPException, status

from app.dependencies.auth import get_current_user
from app.database.models import User

from app.schemas.readings import ReadingRequest, ReadingResponse
from app.adapters.agent_adapter import (
    AgentIntegrationError,
    agent_adapter,
)

from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.crud import (
    create_session,
    create_cards,
    create_reading,
)
from app.services.quota_service import check_reading_quota
from app.services.usage_service import consume_reading
from app.services.clarify_cache import save_request


router = APIRouter(
    prefix="/api/readings",
    tags=["readings"],
)


@router.post("", response_model=ReadingResponse)
def create_reading_api(
    request: ReadingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReadingResponse:
    expected_card_counts = {
        "daily_card": 1,
        "single_card": 1,
        "three_card": 3,
    }

    expected_count = expected_card_counts[request.spread_type]

    if len(request.cards) != expected_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INCOMPLETE_DRAW",
                "message": (
                    f"{request.spread_type} 需要 {expected_count} 张牌，"
                    f"当前收到 {len(request.cards)} 张。"
                ),
            },
        )

    if request.spread_type != "daily_card":
        if request.question is None or not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "EMPTY_QUESTION",
                    "message": "请输入你想询问的问题。",
                },
            )

    quota_reserved = check_reading_quota(db, current_user, request.spread_type)

    # 1. 调用 Agent
    try:
        result = agent_adapter.generate_reading(request)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_AGENT_REQUEST",
                "message": str(error),
            },
        ) from error
    except AgentIntegrationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "AGENT_UNAVAILABLE",
                "message": str(error),
            },
        ) from error

    if result.status == "awaiting_clarify":
        result.session_id = save_request(request, current_user.id)
        return result

    # 2. 保存数据库
    try:
        session = create_session(
            db=db,
            user_id=current_user.id,
            question=request.question,
            spread_type=request.spread_type,
        )

        create_cards(
            db=db,
            session_id=session.id,
            cards=request.cards,
        )

        create_reading(
            db=db,
            session_id=session.id,
            summary=result.summary,
            synthesis=result.synthesis,
            advice=result.advice,
        )

        if not quota_reserved:
            consume_reading(db, current_user, request.spread_type)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return result
