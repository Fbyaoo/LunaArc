"""数据模型"""

from typing import Literal, Self

from pydantic import BaseModel, model_validator


class DrawnCard(BaseModel):
    card_id: str
    name_zh: str
    position: str
    orientation: Literal["upright", "reversed"]


class ReadingRequest(BaseModel):
    question: str | None = None
    spread_type: Literal["daily_card", "single_card", "three_card"]
    cards: list[DrawnCard]
    user_history: list[dict] | None = None

    @model_validator(mode='after')
    def validate_request(self) -> Self:
        spread = self.spread_type
        expected_count = {"daily_card": 1, "single_card": 1, "three_card": 3}
        if len(self.cards) != expected_count.get(spread, 0):
            raise ValueError(f'{spread} 需要恰好 {expected_count[spread]} 张牌')
        if spread == "daily_card":
            if self.cards[0].position != "1":
                raise ValueError(f'daily_card 的 position 必须为 "1"，实际为 {self.cards[0].position}')
        elif spread == "single_card":
            if self.cards[0].position != "1":
                raise ValueError(f'single_card 的 position 必须为 "1"，实际为 {self.cards[0].position}')
        elif spread == "three_card":
            actual = [c.position for c in self.cards]
            if actual != ["1", "2", "3"]:
                raise ValueError(f'three_card 的 position 必须为 ["1", "2", "3"]，实际为 {actual}')
        return self


class CardReading(BaseModel):
    card_id: str
    position: str
    interpretation: str


class ReadingResponse(BaseModel):
    status: Literal["success", "awaiting_clarify"] = "success"
    summary: str
    card_readings: list[CardReading]
    synthesis: str | None = None
    advice: list[str]
