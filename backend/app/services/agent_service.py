
from app.schemas.readings import (
    CardReading,
    ReadingResponse,
)


class TarotAgent:


    def generate_reading(
        self,
        request: dict,
    ) -> ReadingResponse:


        question = (
            request.get("question")
            or ""
        )


        if (
            request["spread_type"]
            == "three_card"
            and question.strip()
            in [
                "我该怎么办",
                "我该怎么办？",
                "怎么办",
            ]
        ):

            return ReadingResponse(

                status="awaiting_clarify",

                summary=(
                    "你的问题比较宽泛，"
                    "请补充你想关注的具体方向。"
                ),

                card_readings=[],

                synthesis=None,

                advice=[],
            )


        return self._success(
            request
        )



    def resume_reading(
        self,
        request: dict,
        user_supplement: str,
    ) -> ReadingResponse:


        request["question"] = (
            request.get("question", "")
            +
            " "
            +
            user_supplement
        )


        return self._success(
            request
        )



    def _success(
        self,
        request,
    ):

        readings = []


        for card in request["cards"]:

            orientation = (
                "正位"
                if card["orientation"] == "upright"
                else "逆位"
            )

            symbolism = "、".join(
                card.get(
                    "core_symbolism",
                    []
                )
            )

            readings.append(
                CardReading(
                    card_id=card["card_id"],
                    position=card["position"],
                    interpretation=(
                        f'{card["name_zh"]}'
                        f"以{orientation}出现。"
                        f"核心象征包括：{symbolism}。"
                        "这里暂时返回 Mock 解读。"
                    ),
                )
            )


        return ReadingResponse(

            status="success",

            summary="Mock 塔罗解读结果。",

            card_readings=readings,

            synthesis=(
                "三张牌综合趋势。"
                if len(readings) > 1
                else None
            ),

            advice=[
                "结合现实情况判断。"
            ],
        )


tarot_agent = TarotAgent()
