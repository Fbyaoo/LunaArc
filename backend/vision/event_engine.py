from __future__ import annotations

import time

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
        self._stable_counts: dict[str, int] = {}
        self._last_event_at: dict[str, float] = {}

    def update(self, detection: GestureDetection | None) -> VisualEvent | None:
        events = self.update_many([] if detection is None else [detection])
        return events[0] if events else None

    def update_many(self, detections: list[GestureDetection]) -> list[VisualEvent]:
        valid_detections = [
            detection
            for detection in detections
            if detection.confidence >= self.confidence_threshold
        ]

        if not valid_detections:
            self._stable_counts.clear()
            return []

        # 同一帧同一种手势如果出现多个框，只保留置信度最高的一个。
        best_by_gesture: dict[str, GestureDetection] = {}
        for detection in valid_detections:
            current = best_by_gesture.get(detection.gesture)
            if current is None or detection.confidence > current.confidence:
                best_by_gesture[detection.gesture] = detection

        current_gestures = set(best_by_gesture)
        for gesture in list(self._stable_counts):
            if gesture not in current_gestures:
                del self._stable_counts[gesture]

        for gesture in current_gestures:
            self._stable_counts[gesture] = self._stable_counts.get(gesture, 0) + 1

        events: list[VisualEvent] = []
        now = time.monotonic()

        for gesture, detection in best_by_gesture.items():
            if self._stable_counts.get(gesture, 0) < self.stable_frames:
                continue

            last_at = self._last_event_at.get(gesture, 0)
            if now - last_at < self.cooldown_seconds:
                continue

            self._last_event_at[gesture] = now
            self._stable_counts[gesture] = 0

            events.append(
                VisualEvent(
                    detector="yolo",
                    gesture=detection.gesture,
                    confidence=detection.confidence,
                    timestamp=time.time(),
                    bbox=detection.bbox,
                    payload=detection.model_dump(),
                )
            )

        return events
