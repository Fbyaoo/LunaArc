from app.schemas.gesture import GestureAction


GESTURE_MAPPING = {
    "fist": "shuffle",
    "one": "switch_spread",
    "ok": "request_reading",
    "peace": "reset",
}


class GestureAdapter:

    """
    手势事件 -> 业务动作
    """

    def convert(
        self,
        gesture: str,
    ) -> GestureAction:

        action = GESTURE_MAPPING.get(
            gesture,
            "unknown",
        )

        return GestureAction(
            gesture=gesture,
            action=action,
        )


gesture_adapter = GestureAdapter()
