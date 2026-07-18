from __future__ import annotations

from pathlib import Path

from .mappings import GESTURE_MAP
from .schemas import GestureDetection
from .yolo_utils import load_image_from_bytes, require_model_file, xyxy_to_list


class GestureDetector:
    def __init__(
        self,
        model_path: str | Path | None = None,
        confidence_threshold: float = 0.25,
    ) -> None:
        from ultralytics import YOLO

        if model_path is None:
            model_path = Path(__file__).resolve().parent / "model" / "best_gesture.pt"

        self.model_path = require_model_file(model_path)
        self.model = YOLO(str(self.model_path))
        self.confidence_threshold = confidence_threshold

    def detect_gestures(
        self,
        image_bytes: bytes,
        filename: str | None = None,
    ) -> list[GestureDetection]:
        image = load_image_from_bytes(image_bytes)
        results = self.model.predict(image, verbose=False)

        detections: list[GestureDetection] = []

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

                detections.append(
                    GestureDetection(
                        class_id=class_id,
                        gesture=mapping["gesture"],
                        description=mapping["description"],
                        confidence=confidence,
                        bbox=xyxy_to_list(box.xyxy[0].tolist()),
                    )
                )

        return detections

    def detect_gesture(
        self,
        image_bytes: bytes,
        filename: str | None = None,
    ) -> GestureDetection | None:
        """兼容旧调用：只返回置信度最高的一个有效手势。"""
        detections = self.detect_gestures(image_bytes, filename=filename)
        if not detections:
            return None
        return max(detections, key=lambda detection: detection.confidence)
