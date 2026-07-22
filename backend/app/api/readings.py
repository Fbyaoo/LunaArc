from datetime import UTC, datetime

from fastapi import Depends, Query
from fastapi import APIRouter, HTTPException, status

from app.dependencies.auth import get_current_user
from app.database.models import Reading, User

from app.schemas.readings import (
    ReadingDetail,
    ReadingListResponse,
    ReadingRequest,
    ReadingResponse,
    ReadingUpdateRequest,
    RecentReadingsResponse,
)
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
from app.services.reading_query_service import (
    get_owned_reading,
    owned_reading_query,
    to_detail,
    to_list_item,
)


router = APIRouter(
    prefix="/api/readings",
    tags=["readings"],
)


@router.get("/recent", response_model=RecentReadingsResponse)
def get_recent_readings(
    limit: int = Query(default=3, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = owned_reading_query(db, current_user.id)
    total = query.count()
    records = query.order_by(Reading.created_at.desc()).limit(limit).all()
    return RecentReadingsResponse(
        items=[to_list_item(item) for item in records], total=total
    )


@router.get("", response_model=ReadingListResponse)
def list_readings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    saved: bool | None = Query(default=None),
    sort: str = Query(default="-created_at", pattern="^-?created_at$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = owned_reading_query(db, current_user.id)
    if saved is not None:
        query = query.filter(Reading.saved == saved)
    total = query.count()
    ordering = Reading.created_at.desc() if sort.startswith("-") else Reading.created_at
    records = (
        query.order_by(ordering).offset((page - 1) * page_size).limit(page_size).all()
    )
    return ReadingListResponse(
        items=[to_list_item(item) for item in records],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{reading_id}", response_model=ReadingDetail)
def get_reading_detail(
    reading_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reading = get_owned_reading(db, current_user.id, reading_id)
    if reading is None:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "READING_NOT_FOUND", "message": "解读不存在。"},
        )
    return to_detail(reading)


@router.patch("/{reading_id}", response_model=ReadingDetail)
def update_reading(
    reading_id: int,
    body: ReadingUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reading = get_owned_reading(db, current_user.id, reading_id)
    if reading is None:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "READING_NOT_FOUND", "message": "解读不存在。"},
        )
    reading.saved = body.saved
    reading.saved_at = datetime.now(UTC).replace(tzinfo=None) if body.saved else None
    db.commit()
    db.refresh(reading)
    return to_detail(reading)


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
        result.session_id = save_request(request, current_user.id, result.summary)
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
            card_readings=result.card_readings,
        )

        reading_record = create_reading(
            db=db,
            session_id=session.id,
            summary=result.summary,
            synthesis=result.synthesis,
            advice=result.advice,
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

    return result
