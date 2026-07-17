from app.schemas.readings import (
    CardReading,
    ReadingResponse,
)


class TarotAgent:
    """
    Mock Agent。

    后续真实 Agent 接入时，
    替换这里即可。

    当前输入已经包含完整牌义信息。
    """


    def generate_reading(
        self,
        request: dict,
    ) -> ReadingResponse:


        cards = request["cards"]


        card_readings = []

        for card in cards:

            orientation = (
                "正位"
                if card["orientation"] == "upright"
                else "逆位"
            )


            symbolism = "、".join(
                card["core_symbolism"]
            )


            interpretation = (
                f'{card["name_zh"]}以{orientation}出现。'
                f'核心象征包括：{symbolism}。'
                "这里暂时返回 Mock 解读。"
            )


            card_readings.append(
                CardReading(
                    card_id=card["card_id"],
                    interpretation=interpretation,
                )
            )


        synthesis = None

        if len(cards) > 1:
            synthesis = (
                "这些卡牌共同反映了当前问题的发展过程和可能趋势。"
            )


        return ReadingResponse(

            status="success",

            summary=(
                "这是基于完整塔罗牌信息生成的 Mock 解读结果。"
            ),

            card_readings=card_readings,

            synthesis=synthesis,

            advice=[
                "结合现实情况审视自己的选择。",
                "不要仅依靠塔罗作出重要决定。",
            ],
        )


tarot_agent = TarotAgent()
