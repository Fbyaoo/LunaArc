from app.adapters.agent_adapter import AgentIntegrationError
from app.config.settings import get_settings
from app.database.models import GuideMessage, GuideSession, Reading


def generate_guide_reply(
    guide_session: GuideSession,
    reading: Reading | None,
    history: list[GuideMessage],
    user_content: str,
) -> str:
    settings = get_settings()
    if settings.agent_mode != "real":
        subject = reading.title if reading is not None else "这次体验"
        return (
            f"围绕“{subject}”，我听到你最在意的是：{user_content}。"
            "可以把牌面当作整理想法的镜子：先写下你能控制的一件事，"
            "再选择今天可以完成的最小行动。"
        )

    if not settings.openai_api_key:
        raise AgentIntegrationError("AGENT_MODE=real 时必须配置 OPENAI_API_KEY。")

    try:
        from agent.llm import make_llm

        reading_context = "暂无关联解读"
        if reading is not None:
            cards_context = "\n".join(
                f"- {card.card_id}，牌位 {card.position}，{card.orientation}："
                f"{card.interpretation or '暂无单牌解释'}"
                for card in reading.session.cards
            )
            reading_context = (
                f"标题：{reading.title or reading.summary[:200]}\n"
                f"原问题：{reading.session.question or '无'}\n牌面：\n{cards_context}\n"
                f"摘要：{reading.summary}\n综合：{reading.synthesis or ''}\n"
                f"建议：{reading.advice}\n追问：{reading.clarification_prompt or '无'}\n"
                f"用户补充：{reading.clarification_answer or '无'}"
            )
        history_text = "\n".join(
            f"{item.role}: {item.content}" for item in history[-12:]
        )
        system = (
            "你是 LunaArc 的 AI 塔罗向导。请结合已有关联解读和对话，"
            "用温和、简洁、可执行的中文帮助用户自我反思。不得把塔罗描述为确定预测，"
            "不得替代医疗、法律或财务专业意见；涉及危机时建议寻求现实中的专业帮助。"
        )
        prompt = (
            f"关联解读：\n{reading_context}\n\n历史对话：\n{history_text}\n\n"
            f"用户最新消息：{user_content}"
        )
        result = make_llm(500).invoke([("system", system), ("user", prompt)])
        content = result.content
        if isinstance(content, list):
            content = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )
        reply = str(content).strip()
        if not reply:
            raise ValueError("模型返回空内容")
        return reply
    except AgentIntegrationError:
        raise
    except Exception as error:
        raise AgentIntegrationError("AI 塔罗向导暂时不可用，请稍后重试。") from error
