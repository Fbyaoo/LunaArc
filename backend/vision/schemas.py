from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


GestureName = Literal["fist", "one", "ok", "peace"]
DetectorName = Literal["yolo", "mediapipe"]


class GestureDetection(BaseModel):
    class_id: int
    gesture: GestureName
    description: str
    confidence: float = Field(ge=0, le=1)
    bbox: list[float] | None = None


class VisualEvent(BaseModel):
    type: Literal["gesture_event"] = "gesture_event"
    source: Literal["gesture"] = "gesture"
    detector: DetectorName = "yolo"
    gesture: str
    confidence: float | None = None
    timestamp: float
    bbox: list[float] | None = None
    payload: dict = Field(default_factory=dict)
