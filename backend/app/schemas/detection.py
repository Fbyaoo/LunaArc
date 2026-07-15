from typing import Literal

from pydantic import BaseModel, Field


Orientation = Literal["upright", "reversed"]


class DetectedCard(BaseModel):
    class_id: int
    card_id: str
    name_zh: str
    orientation: Orientation
    confidence: float = Field(ge=0, le=1)


class DetectionResponse(BaseModel):
    status: Literal["success"]
    filename: str
    cards: list[DetectedCard]
