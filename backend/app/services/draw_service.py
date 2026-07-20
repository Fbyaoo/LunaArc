import json
import random
from pathlib import Path

from app.schemas.draw import SpreadType


DATA_FILE = (
    Path(__file__).resolve()
    .parent.parent
    / "data"
    / "tarot_cards.json"
)


POSITION_MAP: dict[SpreadType, list[str]] = {
    "daily_card": [
        "1",
    ],
    "single_card": [
        "1",
    ],
    "three_card": [
        "1",
        "2",
        "3",
    ],
}


class DrawService:
    def load_cards(self) -> list[dict]:
        with DATA_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def draw(
        self,
        spread_type: SpreadType,
    ) -> list[dict]:
        positions = POSITION_MAP[spread_type]
        cards = self.load_cards()

        selected_cards = random.sample(
            cards,
            len(positions),
        )

        result = []

        for card, position in zip(
            selected_cards,
            positions,
        ):
            orientation = random.choice(
                [
                    "upright",
                    "reversed",
                ]
            )

            result.append(
                {
                    "card_id": card["card_id"],
                    "name_zh": card["name_zh"],
                    "name_en": card["name_en"],
                    "position": position,
                    "orientation": orientation,
                }
            )

        return result


draw_service = DrawService()
