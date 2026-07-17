from typing import Literal

from pydantic import BaseModel


SpreadType = Literal[
    "daily_card",
    "single_card",
    "three_card",
]


class DrawRequest(BaseModel):

    spread_type: SpreadType


class DrawnCardResponse(BaseModel):

    card_id: str

    name_zh: str

    name_en: str

    position: str

    orientation: str


class DrawResponse(BaseModel):

    spread_type: str

    cards: list[DrawnCardResponse]
