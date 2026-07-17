from typing import Literal

from pydantic import BaseModel


SpreadType = Literal["three_card"]

Orientation = Literal[
    "upright",
    "reversed",
]


class DrawnCard(BaseModel):

    card_id: str

    name_zh: str

    position_number: int

    orientation: Orientation



class EnrichedCard(BaseModel):

    card_id: str

    name_zh: str

    position_number: int

    orientation: Orientation

    core_symbolism: list[str]

    upright_keywords: list[str]

    reversed_keywords: list[str]



class ReadingRequest(BaseModel):

    question: str

    spread_type: SpreadType

    cards: list[DrawnCard]

    user_history: list[dict] | None = None



class CardReading(BaseModel):

    card_id: str

    interpretation: str



class ReadingResponse(BaseModel):

    status: Literal["success"]

    summary: str

    card_readings: list[CardReading]

    synthesis: str | None = None

    advice: list[str]
