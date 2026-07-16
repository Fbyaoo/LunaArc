from app.schemas.readings import (
    CardReading,
    ReadingRequest,
    ReadingResponse,
)


class TarotAgent:
    """临时 Mock Agent，后续替换为 Agent 同学提供的实现。"""

    def generate_reading(self, request: ReadingRequest) -> ReadingResponse:
        card_readings = [
            CardReading(
                card_id=card.card_id,
                position=card.position,
                interpretation=(
                    f"{card.name_zh}以{self._orientation_name(card.orientation)}出现，"
                    f"这里暂时返回 Mock 解读。"
                ),
            )
            for card in request.cards
        ]

        synthesis = None
        if len(request.cards) > 1:
            synthesis = "这些卡牌共同反映了当前问题的发展过程和可能趋势。"

        return ReadingResponse(
            status="success",
            summary="这是后端生成的 Mock 塔罗解读结果。",
            card_readings=card_readings,
            synthesis=synthesis,
            advice=[
                "结合现实情况审视自己的选择。",
                "不要仅依靠塔罗作出重要决定。",
            ],
        )

    @staticmethod
    def _orientation_name(orientation: str) -> str:
        return "正位" if orientation == "upright" else "逆位"


tarot_agent = TarotAgent()
