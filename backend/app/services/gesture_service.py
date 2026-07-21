from app.schemas.gesture import (
    GestureEvent,
)
from vision.event_engine import GestureEventEngine


class GestureService:
    def __init__(self):
        self.vision_service = None

    def process_frame(
        self,
        image_bytes: bytes,
        event_engine: GestureEventEngine | None = None,
    ) -> list[GestureEvent]:
        if self.vision_service is None:
            from vision import VisionService
            from app.config.settings import get_settings

            settings = get_settings()
            self.vision_service = VisionService(settings.vision_model_path or None)

        events = self.vision_service.process_frame(
            image_bytes,
            event_engine=event_engine,
        )

        return [GestureEvent.model_validate(event) for event in events]

    @staticmethod
    def create_event_engine() -> GestureEventEngine:
        """每个 WebSocket 连接独享稳定帧和冷却状态。"""
        return GestureEventEngine()


gesture_service = GestureService()
