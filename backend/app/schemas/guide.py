from datetime import datetime

from pydantic import BaseModel, Field


class GuideSessionCreate(BaseModel):
    reading_id: int | None = None


class GuideSessionResponse(BaseModel):
    session_id: int
    reading_id: int | None
    created_at: datetime
    updated_at: datetime


class GuideMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class GuideMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
