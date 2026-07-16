from app.schemas.readings import (
    ReadingRequest,
    ReadingResponse,
)


class AgentAdapter:
    """
    Agent 统一适配层。

    后续真实 Agent 接入时，
    只修改这里。
    """

    def generate_reading(
        self,
        request: ReadingRequest,
    ) -> ReadingResponse:

        # 当前调用 Mock Agent
        # 后续替换为真实 TarotAgent

        from app.services.agent_service import tarot_agent

        return tarot_agent.generate_reading(request)


agent_adapter = AgentAdapter()
