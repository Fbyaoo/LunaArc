from pydantic import BaseModel

from app.schemas.draw import (
    DrawnCardResponse,
    SpreadType,
)
from app.schemas.readings import ReadingResponse


class DrawReadingRequest(BaseModel):
    question: str | None = None
    spread_type: SpreadType


class DrawReadingResponse(BaseModel):
    cards: list[DrawnCardResponse]
    reading: ReadingResponse
