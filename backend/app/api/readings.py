from fastapi import APIRouter, HTTPException, status

from app.schemas.readings import ReadingRequest, ReadingResponse
from app.adapters.agent_adapter import agent_adapter

from app.database.connection import SessionLocal
from app.database.crud import (
    create_session,
    create_cards,
    create_reading,
)


router = APIRouter(
    prefix="/api/readings",
    tags=["readings"],
)


@router.post("", response_model=ReadingResponse)
def create_reading_api(
    request: ReadingRequest,
) -> ReadingResponse:

    expected_card_counts = {
        "daily_card": 1,
        "single_card": 1,
        "three_card": 3,
    }


    expected_count = expected_card_counts[
        request.spread_type
    ]


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


    # 1. 调用 Agent
    result = agent_adapter.generate_reading(
        request
    )


    # 2. 保存数据库
    db = SessionLocal()

    try:

        session = create_session(
            db=db,
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


    finally:

        db.close()


    return result
