from app.schemas.detection import DetectedCard


class VisionAdapter:
    """
    Vision 统一适配层。

    后续 YOLO 等模型接入时，
    只修改这里。
    """

    def detect_cards(
        self,
        image_bytes: bytes,
        filename: str,
    ) -> list[DetectedCard]:

        # 当前调用 Mock Vision
        # 后续替换为真实模型

        from app.services.vision_service import vision_service

        return vision_service.detect_cards(
            image_bytes=image_bytes,
            filename=filename,
        )


vision_adapter = VisionAdapter()
