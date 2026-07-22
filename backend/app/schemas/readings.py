from typing import Literal

from datetime import datetime

from pydantic import BaseModel, Field


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
    session_id: str | None = None
    reading_id: int | None = None
    saved: bool = False
    created_at: datetime | None = None


class ClarifyRequest(BaseModel):
    session_id: str
    user_supplement: str = Field(min_length=1, max_length=2000)


class ReadingUpdateRequest(BaseModel):
    saved: bool


class ReadingCardDetail(BaseModel):
    card_id: str
    name: str
    name_zh: str
    image_url: str | None = None
    position: str
    reversed: bool
    orientation: Orientation
    interpretation: str | None = None
    keywords: list[str] = Field(default_factory=list)


class ReadingDetail(BaseModel):
    id: int
    status: str
    spread_type: SpreadType
    question: str | None
    title: str
    summary: str
    cards: list[ReadingCardDetail]
    synthesis: str | None
    advice: list[str]
    clarification_prompt: str | None = None
    clarification_answer: str | None = None
    saved: bool
    saved_at: datetime | None = None
    created_at: datetime


class ReadingListItem(BaseModel):
    id: int
    spread_type: SpreadType
    question: str | None
    title: str
    summary: str
    created_at: datetime
    saved: bool
    status: str


class ReadingListResponse(BaseModel):
    items: list[ReadingListItem]
    total: int
    page: int
    page_size: int


class RecentReadingsResponse(BaseModel):
    items: list[ReadingListItem]
    total: int
