from __future__ import annotations

import unittest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from vision.event_engine import GestureEventEngine
from vision.mappings import GESTURE_MAP
from vision.schemas import GestureDetection


class GestureContractTest(unittest.TestCase):
    def test_only_business_gestures_are_mapped(self) -> None:
        self.assertEqual(GESTURE_MAP[0]["gesture"], "fist")
        self.assertEqual(GESTURE_MAP[1]["gesture"], "one")
        self.assertEqual(GESTURE_MAP[2]["gesture"], "like")
        self.assertEqual(GESTURE_MAP[3]["gesture"], "peace")

        # 新模型里 class_id=7 是 ok，class_id=8 是 palm。
        # 它们不是当前业务需要的四个手势，所以应被忽略，效果等同于 none。
        self.assertNotIn(7, GESTURE_MAP)
        self.assertNotIn(8, GESTURE_MAP)

    def test_event_engine_outputs_gesture_event_after_stable_frames(self) -> None:
        engine = GestureEventEngine(
            confidence_threshold=0.75,
            stable_frames=2,
            cooldown_seconds=0,
        )
        detection = GestureDetection(
            class_id=2,
            gesture="like",
            description="点赞手势",
            confidence=0.91,
            bbox=[1.0, 2.0, 3.0, 4.0],
        )

        self.assertIsNone(engine.update(detection))
        event = engine.update(detection)

        self.assertIsNotNone(event)
        assert event is not None
        event_dict = event.model_dump()
        self.assertEqual(event_dict["type"], "gesture_event")
        self.assertEqual(event_dict["source"], "gesture")
        self.assertEqual(event_dict["detector"], "yolo")
        self.assertEqual(event_dict["gesture"], "like")
        self.assertEqual(event_dict["confidence"], 0.91)
        self.assertEqual(event_dict["bbox"], [1.0, 2.0, 3.0, 4.0])
        self.assertIn("timestamp", event_dict)

    def test_event_engine_can_output_multiple_gestures(self) -> None:
        engine = GestureEventEngine(
            confidence_threshold=0.75,
            stable_frames=2,
            cooldown_seconds=0,
        )
        detections = [
            GestureDetection(
                class_id=0,
                gesture="fist",
                description="握拳",
                confidence=0.93,
                bbox=[1.0, 2.0, 3.0, 4.0],
            ),
            GestureDetection(
                class_id=2,
                gesture="like",
                description="点赞手势",
                confidence=0.91,
                bbox=[5.0, 6.0, 7.0, 8.0],
            ),
        ]

        self.assertEqual(engine.update_many(detections), [])
        events = engine.update_many(detections)
        event_gestures = {event.gesture for event in events}

        self.assertEqual(event_gestures, {"fist", "like"})


if __name__ == "__main__":
    unittest.main()
