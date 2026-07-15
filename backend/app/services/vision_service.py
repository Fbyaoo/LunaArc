from app.schemas.detection import DetectedCard


class VisionService:
    """临时 Mock 视觉服务，后续替换为视觉同学提供的模型。"""

    def detect_cards(
        self,
        image_bytes: bytes,
        filename: str,
    ) -> list[DetectedCard]:
        # 当前不真正分析图片，只返回一张测试牌。
        return [
            DetectedCard(
                class_id=0,
                card_id="major_00",
                name_zh="愚者",
                orientation="upright",
                confidence=0.95,
            )
        ]


vision_service = VisionService()
