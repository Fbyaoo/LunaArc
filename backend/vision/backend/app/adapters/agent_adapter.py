from app.schemas.readings import (
    ReadingRequest,
    ReadingResponse,
)

from app.services.tarot_service import enrich_card


class AgentAdapter:
    """
    Agent 统一适配层。

    负责：
    1. 接收后端请求
    2. 补充塔罗牌信息
    3. 调用 Agent
    """

    def generate_reading(
        self,
        request: ReadingRequest,
    ) -> ReadingResponse:


        # 1. 将基础牌信息增强
        enriched_cards = [
            enrich_card(card)
            for card in request.cards
        ]


        # 2. 构造 Agent 输入
        agent_request = {
            "question": request.question,

            "spread_type": request.spread_type,

            "cards": [
                card.model_dump()
                for card in enriched_cards
            ],

            "user_history": request.user_history,
        }


        # 3. 当前仍调用 Mock Agent
        # 后续真实 Agent 直接接收 agent_request

        from app.services.agent_service import tarot_agent


        return tarot_agent.generate_reading(
            agent_request
        )


agent_adapter = AgentAdapter()
