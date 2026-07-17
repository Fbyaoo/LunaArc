from pydantic import BaseModel

from app.schemas.draw import DrawnCardResponse
from app.schemas.readings import ReadingResponse


class DrawReadingRequest(BaseModel):

    question: str | None = None

    spread_type: str


class DrawReadingResponse(BaseModel):

    cards: list[DrawnCardResponse]

    reading: ReadingResponse
