import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config.settings import get_settings
from app.schemas.readings import ReadingRequest, ReadingResponse
from app.services.agent_service import tarot_agent as mock_tarot_agent
from app.services.tarot_service import enrich_card


class AgentIntegrationError(RuntimeError):
    """Agent 模块导入、初始化或输出格式错误。"""


def _load_real_agent_symbols():
    """
    支持两种目录结构：

    LunaArc/backend/agent/
    LunaArc/agent/
    """

    try:
        from agent.tarot_agent import (
            TarotAgent,
            ReadingRequest as AgentReadingRequest,
            DrawnCard as AgentDrawnCard,
        )

        return TarotAgent, AgentReadingRequest, AgentDrawnCard

    except ModuleNotFoundError:
        repository_root = Path(__file__).resolve().parents[3]

        if str(repository_root) not in sys.path:
            sys.path.insert(0, str(repository_root))

        try:
            from agent.tarot_agent import (
                TarotAgent,
                ReadingRequest as AgentReadingRequest,
                DrawnCard as AgentDrawnCard,
            )

            return TarotAgent, AgentReadingRequest, AgentDrawnCard

        except ModuleNotFoundError as second_error:
            raise AgentIntegrationError(
                "无法导入真实 Agent。请确认 agent/ 目录存在，"
                "并已安装 agent/requirements.txt 中的依赖。"
            ) from second_error


@lru_cache
def _get_real_agent():
    TarotAgent, _, _ = _load_real_agent_symbols()
    return TarotAgent()


def _convert_agent_result(result: Any) -> ReadingResponse:
    if isinstance(result, ReadingResponse):
        return result

    if hasattr(result, "model_dump"):
        payload = result.model_dump()
    elif isinstance(result, dict):
        payload = result
    else:
        raise AgentIntegrationError("Agent 返回值必须是 Pydantic Model 或 dict。")

    try:
        return ReadingResponse.model_validate(payload)
    except Exception as error:
        raise AgentIntegrationError(
            f"Agent 返回结构不符合 ReadingResponse：{error}"
        ) from error


class AgentAdapter:
    """
    Backend 与 Agent 之间的唯一适配层。

    mock：
        使用现有 Mock Agent，并注入后端牌义数据。

    real：
        使用 Agent 同学提供的 TarotAgent、ReadingRequest、
        DrawnCard，不向真实 Agent 传额外字段。
        真实 Agent 使用自己的 knowledge.py。
    """

    def generate_reading(
        self,
        request: ReadingRequest,
    ) -> ReadingResponse:
        settings = get_settings()

        if settings.agent_mode == "real":
            if not settings.openai_api_key:
                raise AgentIntegrationError(
                    "AGENT_MODE=real 时必须配置 OPENAI_API_KEY。"
                )
            return self._generate_real(request)

        return self._generate_mock(request)

    def resume_reading(
        self,
        request: ReadingRequest,
        user_supplement: str,
    ) -> ReadingResponse:
        settings = get_settings()

        if settings.agent_mode == "real":
            (
                _,
                AgentReadingRequest,
                AgentDrawnCard,
            ) = _load_real_agent_symbols()

            agent_cards = [
                AgentDrawnCard(
                    card_id=card.card_id,
                    name_zh=card.name_zh,
                    position=card.position,
                    orientation=card.orientation,
                )
                for card in request.cards
            ]

            agent_request = AgentReadingRequest(
                question=request.question,
                spread_type=request.spread_type,
                cards=agent_cards,
                user_history=request.user_history,
            )

            try:
                result = _get_real_agent().resume_reading(
                    agent_request,
                    user_supplement,
                )
            except Exception as error:
                raise AgentIntegrationError(
                    "真实 Agent 暂时不可用，请稍后重试。"
                ) from error

            return _convert_agent_result(result)

        enriched_cards = [enrich_card(card) for card in request.cards]

        mock_request = {
            "question": request.question,
            "spread_type": request.spread_type,
            "cards": [card.model_dump() for card in enriched_cards],
            "user_history": request.user_history,
        }

        return mock_tarot_agent.resume_reading(
            mock_request,
            user_supplement,
        )

    def _generate_real(
        self,
        request: ReadingRequest,
    ) -> ReadingResponse:
        _, AgentReadingRequest, AgentDrawnCard = _load_real_agent_symbols()

        agent_cards = [
            AgentDrawnCard(
                card_id=card.card_id,
                name_zh=card.name_zh,
                position=card.position,
                orientation=card.orientation,
            )
            for card in request.cards
        ]

        try:
            agent_request = AgentReadingRequest(
                question=request.question,
                spread_type=request.spread_type,
                cards=agent_cards,
                user_history=request.user_history,
            )
        except ValueError:
            # 保留 Agent models.py 中 model_validator 的原始校验错误。
            raise

        try:
            result = _get_real_agent().generate_reading(agent_request)
        except Exception as error:
            raise AgentIntegrationError(
                "真实 Agent 暂时不可用，请稍后重试。"
            ) from error

        return _convert_agent_result(result)

    def _generate_mock(
        self,
        request: ReadingRequest,
    ) -> ReadingResponse:
        # Mock 模式继续使用后端牌库，保证现有测试和无 Key 环境可运行。
        enriched_cards = [enrich_card(card) for card in request.cards]

        mock_request = {
            "question": request.question,
            "spread_type": request.spread_type,
            "cards": [card.model_dump() for card in enriched_cards],
            "user_history": request.user_history,
        }

        return mock_tarot_agent.generate_reading(mock_request)


agent_adapter = AgentAdapter()
