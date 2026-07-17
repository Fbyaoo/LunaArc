from pydantic import BaseModel


class GestureEvent(BaseModel):

    type: str

    source: str

    detector: str

    gesture: str

    confidence: float

    timestamp: float

    bbox: list[float] | None = None

    payload: dict | None = None


class GestureAction(BaseModel):

    gesture: str

    action: str
