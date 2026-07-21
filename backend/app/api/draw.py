from fastapi import APIRouter

from app.schemas.draw import (
    DrawRequest,
    DrawResponse,
)

from app.services.draw_service import (
    draw_service,
)


router = APIRouter(
    prefix="/api/draw",
    tags=["draw"],
)


@router.post(
    "",
    response_model=DrawResponse,
)
def draw_cards(
    request: DrawRequest,
):
    cards = draw_service.draw(request.spread_type)

    return DrawResponse(
        spread_type=request.spread_type,
        cards=cards,
    )
