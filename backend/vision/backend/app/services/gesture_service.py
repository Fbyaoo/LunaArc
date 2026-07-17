import time

from app.schemas.gesture import GestureEvent


class GestureService:

    """
    手势识别服务。

    当前 Mock。
    后续替换为 YOLO GestureService。
    """


    def process_frame(
        self,
        image_bytes: bytes,
    ) -> list[GestureEvent]:

        # 当前模拟无稳定手势

        return []


gesture_service = GestureService()
