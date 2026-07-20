from vision import VisionService

from app.schemas.gesture import (
    GestureEvent,
)


class GestureService:


    def __init__(self):

        self.vision_service = (
            VisionService()
        )


    def process_frame(
        self,
        image_bytes: bytes,
    ) -> list[GestureEvent]:

        events = (
            self.vision_service
            .process_frame(
                image_bytes
            )
        )

        return [
            GestureEvent.model_validate(
                event
            )
            for event in events
        ]


gesture_service = GestureService()
