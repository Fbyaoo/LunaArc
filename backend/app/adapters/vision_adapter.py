from functools import lru_cache
from typing import Any

from app.config.settings import get_settings
from app.schemas.detection import DetectedCard
from app.services.tarot_service import load_cards
from app.services.vision_service import vision_service as mock_vision_service


class VisionIntegrationError(RuntimeError):
    """真实卡牌模型缺失、推理失败或返回结构不合法。"""


@lru_cache
def _real_detector():
    try:
        from vision.detector import TarotCardDetector
    except (ImportError, ModuleNotFoundError) as error:
        raise VisionIntegrationError(
            "VISION_MODE=real 需要 vision.detector.TarotCardDetector。"
        ) from error

    try:
        model_path = get_settings().vision_model_path
        return TarotCardDetector(model_path) if model_path else TarotCardDetector()
    except Exception as error:
        raise VisionIntegrationError("卡牌识别模型加载失败。") from error


def _value(item: Any, name: str) -> Any:
    return item.get(name) if isinstance(item, dict) else getattr(item, name, None)


class VisionAdapter:
    def detect_cards(
        self,
        image_bytes: bytes,
        filename: str,
    ) -> list[DetectedCard]:
        settings = get_settings()
        if settings.vision_mode == "mock":
            return [
                card
                for card in mock_vision_service.detect_cards(image_bytes, filename)
                if card.confidence >= settings.min_confidence
            ]

        try:
            raw_detections = _real_detector().detect_cards(image_bytes, filename)
        except VisionIntegrationError:
            raise
        except Exception as error:
            raise VisionIntegrationError("卡牌识别服务暂时不可用。") from error

        cards_by_class = {item["class_id"]: item for item in load_cards()}
        result: list[DetectedCard] = []
        for raw in raw_detections or []:
            class_id = _value(raw, "class_id")
            confidence = _value(raw, "confidence")
            orientation = _value(raw, "orientation")
            card = cards_by_class.get(class_id)
            if card is None or confidence is None:
                continue
            if float(confidence) < settings.min_confidence:
                continue
            try:
                result.append(
                    DetectedCard(
                        class_id=class_id,
                        card_id=card["card_id"],
                        name_zh=card["name_zh"],
                        orientation=orientation,
                        confidence=confidence,
                    )
                )
            except Exception as error:
                raise VisionIntegrationError("卡牌识别结果结构不合法。") from error
        return result


vision_adapter = VisionAdapter()
