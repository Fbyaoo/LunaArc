from app.schemas.readings import (
    ReadingRequest,
    DrawnCard,
)

from app.services.draw_service import draw_service
from app.adapters.agent_adapter import agent_adapter


class DrawReadingService:


    def execute(
        self,
        question: str | None,
        spread_type: str,
    ):


        # 1. 抽牌
        cards = draw_service.draw(
            spread_type
        )


        # 2. 转换成 Agent 输入格式
        reading_cards = [
            DrawnCard(
                card_id=card["card_id"],
                name_zh=card["name_zh"],
                position_number=card["position_number"],
                orientation=card["orientation"],
            )
            for card in cards
        ]


        request = ReadingRequest(
            question=question,
            spread_type=spread_type,
            cards=reading_cards,
            user_history=None,
        )


        # 3. Agent解读
        result = agent_adapter.generate_reading(
            request
        )


        return {
            "cards": cards,
            "reading": result,
        }


draw_reading_service = DrawReadingService()
