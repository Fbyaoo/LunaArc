from app.schemas.readings import (
    CardReading,
    ReadingResponse,
)


class TarotAgent:
    """无需外部模型的牌义规则解读器，供课程演示和离线运行。"""

    def generate_reading(
        self,
        request: dict,
    ) -> ReadingResponse:
        question = request.get("question") or ""

        if request["spread_type"] == "three_card" and question.strip() in [
            "我该怎么办",
            "我该怎么办？",
            "怎么办",
        ]:
            return ReadingResponse(
                status="awaiting_clarify",
                summary=("你的问题比较宽泛，请补充你想关注的具体方向。"),
                card_readings=[],
                synthesis=None,
                advice=[],
            )

        return self._success(request)

    def resume_reading(
        self,
        request: dict,
        user_supplement: str,
    ) -> ReadingResponse:
        resumed_request = dict(request)
        resumed_request["question"] = (
            f"{request.get('question', '')} {user_supplement}".strip()
        )
        return self._success(resumed_request)

    def _success(
        self,
        request: dict,
    ) -> ReadingResponse:
        readings = []
        spread_type = request["spread_type"]

        position_labels = {
            "daily_card": {"1": "今日主题"},
            "single_card": {"1": "核心指引"},
            "three_card": {
                "1": "事情的起点",
                "2": "当前的关键",
                "3": "下一步趋势",
            },
        }

        for card in request["cards"]:
            upright = card["orientation"] == "upright"
            orientation = "正位" if upright else "逆位"
            keywords = card.get(
                "upright_keywords" if upright else "reversed_keywords",
                [],
            )
            keyword_text = "、".join(keywords)
            symbolism = "、".join(card.get("core_symbolism", []))
            position_label = position_labels[spread_type].get(
                card["position"],
                card["position"],
            )
            direction = (
                "说明这些力量正在成为可以利用的资源"
                if upright
                else "提醒你留意阻力、偏差或尚未准备充分的部分"
            )

            readings.append(
                CardReading(
                    card_id=card["card_id"],
                    position=card["position"],
                    interpretation=(
                        f"在「{position_label}」位置，{card['name_zh']}以{orientation}出现。"
                        f"它的关键词是{keyword_text}，核心象征包含{symbolism}；"
                        f"这{direction}。"
                    ),
                )
            )

        question = (request.get("question") or "今天的整体状态").strip()
        first_card = request["cards"][0]
        first_keywords = first_card.get(
            "upright_keywords"
            if first_card["orientation"] == "upright"
            else "reversed_keywords",
            [],
        )
        focus = "、".join(first_keywords[:2])

        if len(readings) > 1:
            card_names = "、".join(card["name_zh"] for card in request["cards"])
            synthesis = (
                f"从{card_names}的组合来看，这件事需要同时看见已有基础、"
                "当前阻力与下一步选择。牌面不是固定预言，而是帮助你整理行动顺序。"
            )
        else:
            synthesis = None

        advice = [
            f"先围绕“{focus}”记录一个今天可以完成的具体行动。",
            "做决定时结合现实信息和自己的感受，不把牌面当作唯一依据。",
        ]

        return ReadingResponse(
            status="success",
            summary=f"关于“{question}”，牌面首先提示你关注{focus}。",
            card_readings=readings,
            synthesis=synthesis,
            advice=advice,
        )


tarot_agent = TarotAgent()
