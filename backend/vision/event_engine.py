from __future__ import annotations

import time
from collections import deque

from .schemas import GestureDetection, VisualEvent


class GestureEventEngine:
    def __init__(
        self,
        confidence_threshold: float = 0.75,
        stable_frames: int = 5,
        cooldown_seconds: float = 1.5,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.stable_frames = stable_frames
        self.cooldown_seconds = cooldown_seconds
        self._recent_gestures: deque[str] = deque(maxlen=stable_frames)
        self._last_event_at: dict[str, float] = {}

    def update(self, detection: GestureDetection | None) -> VisualEvent | None:
        if detection is None or detection.confidence < self.confidence_threshold:
            self._recent_gestures.clear()
            return None

        self._recent_gestures.append(detection.gesture)

        if len(self._recent_gestures) < self.stable_frames:
            return None

        if len(set(self._recent_gestures)) != 1:
            return None

        now = time.monotonic()
        last_at = self._last_event_at.get(detection.gesture, 0)
        if now - last_at < self.cooldown_seconds:
            return None

        self._last_event_at[detection.gesture] = now
        self._recent_gestures.clear()

        return VisualEvent(
            detector="yolo",
            gesture=detection.gesture,
            confidence=detection.confidence,
            timestamp=time.time(),
            bbox=detection.bbox,
            payload=detection.model_dump(),
        )
