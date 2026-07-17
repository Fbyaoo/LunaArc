from __future__ import annotations

from pathlib import Path

from .mappings import GESTURE_MAP
from .schemas import GestureDetection
from .yolo_utils import load_image_from_bytes, require_model_file, xyxy_to_list


class GestureDetector:
    def __init__(
        self,
        model_path: str | Path = "models/best_gesture.pt",
        confidence_threshold: float = 0.25,
    ) -> None:
        from ultralytics import YOLO

        self.model_path = require_model_file(model_path)
        self.model = YOLO(str(self.model_path))
        self.confidence_threshold = confidence_threshold

    def detect_gesture(
        self,
        image_bytes: bytes,
        filename: str | None = None,
    ) -> GestureDetection | None:
        image = load_image_from_bytes(image_bytes)
        results = self.model.predict(image, verbose=False)

        best_detection: GestureDetection | None = None

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                class_id = int(box.cls.item())
                confidence = float(box.conf.item())

                if confidence < self.confidence_threshold:
                    continue

                mapping = GESTURE_MAP.get(class_id)
                if mapping is None:
                    continue

                detection = GestureDetection(
                    class_id=class_id,
                    gesture=mapping["gesture"],
                    description=mapping["description"],
                    confidence=confidence,
                    bbox=xyxy_to_list(box.xyxy[0].tolist()),
                )

                if best_detection is None or detection.confidence > best_detection.confidence:
                    best_detection = detection

        return best_detection
