from fastapi import APIRouter

from app.schemas.draw_reading import (
    DrawReadingRequest,
    DrawReadingResponse,
)

from app.services.draw_reading_service import (
    draw_reading_service,
)


router = APIRouter(
    prefix="/api/draw-and-read",
    tags=["draw-reading"],
)


@router.post(
    "",
    response_model=DrawReadingResponse,
)
def draw_and_read(
    request: DrawReadingRequest,
):

    return draw_reading_service.execute(
        question=request.question,
        spread_type=request.spread_type,
    )
