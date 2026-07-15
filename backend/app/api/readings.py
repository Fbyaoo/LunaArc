from fastapi import APIRouter, HTTPException, status

from app.schemas.readings import ReadingRequest, ReadingResponse
from app.services.agent_service import tarot_agent


router = APIRouter(prefix="/api/readings", tags=["readings"])


@router.post("", response_model=ReadingResponse)
def create_reading(request: ReadingRequest) -> ReadingResponse:
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

    return tarot_agent.generate_reading(request)
