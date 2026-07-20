from app.schemas.gesture import (
    GestureAction,
)


GESTURE_ACTION_MAP = {

    "fist":
        "shuffle",

    "one":
        "switch_spread",

    "like":
        "request_reading",

    "peace":
        "reset",
}


class GestureAdapter:


    def convert(
        self,
        gesture: str,
    ) -> GestureAction:

        action = (
            GESTURE_ACTION_MAP
            .get(
                gesture,
                "unknown",
            )
        )

        return GestureAction(
            gesture=gesture,
            action=action,
        )


gesture_adapter = GestureAdapter()
