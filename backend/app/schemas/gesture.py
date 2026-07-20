from typing import Literal

from pydantic import BaseModel


GestureType = Literal[
    "fist",
    "one",
    "like",
    "peace",
]


ActionType = Literal[
    "shuffle",
    "switch_spread",
    "request_reading",
    "reset",
    "unknown",
]


class GestureEvent(BaseModel):
    type: str = "gesture_event"

    source: str = "gesture"

    detector: str

    gesture: GestureType

    confidence: float

    timestamp: float

    bbox: list[float] | None = None

    payload: dict = {}


class GestureAction(BaseModel):

    gesture: str

    action: ActionType
