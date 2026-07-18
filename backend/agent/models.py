"""数据模型 — 请求/响应结构与牌数据"""

from typing import Literal, Self

from pydantic import BaseModel, model_validator


class DrawnCard(BaseModel):
    """后端传入的已抽牌信息"""
    card_id: str
    name_zh: str
    position: str          # daily_guidance / core / past / present / future
    orientation: Literal["upright", "reversed"]


class ReadingRequest(BaseModel):
    """后端传入的解读请求"""
    question: str | None = None
    spread_type: Literal["daily_card", "single_card", "three_card"]
    cards: list[DrawnCard]
    user_history: list[dict] | None = None

    @model_validator(mode='after')
    def validate_request(self) -> Self:
        spread = self.spread_type
        # 牌数校验
        expected_count = {"daily_card": 1, "single_card": 1, "three_card": 3}
        if len(self.cards) != expected_count.get(spread, 0):
            raise ValueError(f'{spread} 需要恰好 {expected_count[spread]} 张牌')
        # 位置校验（three_card 不再强制要求 past/present/future，
        # 后端可传入任意 position 字符串，由 Spread Planner 做语义映射）
        expected_positions = {
            "daily_card":  ["daily_guidance"],
            "single_card": ["core"],
        }
        if spread in expected_positions:
            actual = [c.position for c in self.cards]
            if actual != expected_positions[spread]:
                raise ValueError(f'{spread} 的 position 必须为 {expected_positions[spread]}，实际为 {actual}')
        return self


class CardReading(BaseModel):
    """单张牌的解读结果"""
    card_id: str
    position: str
    interpretation: str


class ReadingResponse(BaseModel):
    """解读返回结构"""
    status: Literal["success"] = "success"
    summary: str
    card_readings: list[CardReading]
    synthesis: str | None = None
    advice: list[str]
