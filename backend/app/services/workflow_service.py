from typing import Literal


ActionType = Literal[
    "shuffle",
    "switch_spread",
    "request_reading",
    "reset",
    "unknown",
]


class TarotWorkflow:

    """
    塔罗业务流程状态管理。

    不负责识别手势。
    只处理业务状态。
    """


    def __init__(self):

        self.state = "idle"

        self.spread_type = "single_card"


    def handle_action(
        self,
        action: ActionType,
    ) -> dict:


        if action == "shuffle":

            self.state = "shuffling"

            return {
                "state": self.state,
                "action": "shuffle",
                "message": "开始洗牌",
            }


        if action == "switch_spread":

            self.spread_type = (
                "three_card"
                if self.spread_type == "single_card"
                else "single_card"
            )

            return {
                "state": self.state,
                "action": "switch_spread",
                "spread_type": self.spread_type,
            }


        if action == "request_reading":

            self.state = "reading"

            return {
                "state": self.state,
                "action": "request_reading",
                "message": "请求生成解读",
            }


        if action == "reset":

            self.state = "idle"

            return {
                "state": self.state,
                "action": "reset",
                "message": "重置流程",
            }


        return {
            "state": self.state,
            "action": "unknown",
        }



tarot_workflow = TarotWorkflow()
