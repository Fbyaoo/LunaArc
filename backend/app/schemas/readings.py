from typing import Literal

from pydantic import BaseModel


SpreadType = Literal[
    "daily_card",
    "single_card",
    "three_card",
]

Orientation = Literal[
    "upright",
    "reversed",
]


class DrawnCard(BaseModel):
    card_id: str
    name_zh: str
    position: str
    orientation: Orientation


class EnrichedCard(BaseModel):
    card_id: str
    name_zh: str
    position: str
    orientation: Orientation
    core_symbolism: list[str]
    upright_keywords: list[str]
    reversed_keywords: list[str]


class ReadingRequest(BaseModel):
    question: str | None = None
    spread_type: SpreadType
    cards: list[DrawnCard]
    user_history: list[dict] | None = None


class CardReading(BaseModel):
    card_id: str
    position: str
    interpretation: str


class ReadingResponse(BaseModel):
    status: Literal["success", "awaiting_clarify"]
    summary: str
    card_readings: list[CardReading]
    synthesis: str | None = None
    advice: list[str]
