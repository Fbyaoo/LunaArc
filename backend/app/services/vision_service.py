from app.schemas.detection import DetectedCard


class VisionService:
    """
    Mock Vision 服务。

    通过文件名模拟不同识别情况。
    真实 YOLO 接入时替换此层。
    """

    def detect_cards(
        self,
        image_bytes: bytes,
        filename: str,
    ) -> list[DetectedCard]:
        filename = filename.lower()

        # 模拟未识别到卡牌
        if "none" in filename:
            return []

        # 模拟低置信度
        if "low" in filename:
            return [
                DetectedCard(
                    class_id=0,
                    card_id="major_00",
                    name_zh="愚者",
                    orientation="upright",
                    confidence=0.35,
                )
            ]

        # 模拟多牌识别
        if "multi" in filename:
            return [
                DetectedCard(
                    class_id=0,
                    card_id="major_00",
                    name_zh="愚者",
                    orientation="upright",
                    confidence=0.95,
                ),
                DetectedCard(
                    class_id=1,
                    card_id="major_01",
                    name_zh="魔术师",
                    orientation="reversed",
                    confidence=0.91,
                ),
            ]

        # 模拟魔术师
        if "magician" in filename:
            return [
                DetectedCard(
                    class_id=1,
                    card_id="major_01",
                    name_zh="魔术师",
                    orientation="reversed",
                    confidence=0.92,
                )
            ]

        # 默认：愚者
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
