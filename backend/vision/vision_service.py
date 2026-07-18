from __future__ import annotations

from pathlib import Path

from .detector_gesture import GestureDetector
from .event_engine import GestureEventEngine
from .schemas import VisualEvent


class VisionService:
    """后端 WebSocket 可以直接调用的统一视觉入口。"""

    def __init__(
        self,
        model_path: str | Path | None = None,
    ) -> None:
        self.gesture_detector = GestureDetector(model_path)
        self.gesture_events = GestureEventEngine()

    def process_frame(
        self,
        image_bytes: bytes,
        filename: str | None = None,
    ) -> list[dict]:
        events: list[VisualEvent] = []

        gestures = self.gesture_detector.detect_gestures(image_bytes, filename=filename)
        events.extend(self.gesture_events.update_many(gestures))

        return [event.model_dump() for event in events]
