from typing import Literal

from pydantic import BaseModel


SpreadType = Literal["three_card"]


class DrawRequest(BaseModel):

    spread_type: SpreadType


class DrawnCardResponse(BaseModel):

    card_id: str

    name_zh: str

    name_en: str

    position_number: int

    orientation: str


class DrawResponse(BaseModel):

    spread_type: str

    cards: list[DrawnCardResponse]
