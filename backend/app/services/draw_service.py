import json
import random
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve()
    .parent.parent
    / "data"
    / "tarot_cards.json"
)


POSITION_MAP = {

    "three_card": [
        "past",
        "present",
        "future",
    ],
}



class DrawService:


    def load_cards(self):

        with DATA_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)



    def draw(
        self,
        spread_type: str,
    ):

        cards = self.load_cards()


        positions = POSITION_MAP[
            spread_type
        ]


        selected = random.sample(
            cards,
            len(positions),
        )


        result = []


        for card, position in zip(
            selected,
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
                    "card_id":
                        card["card_id"],

                    "name_zh":
                        card["name_zh"],

                    "name_en":
                        card["name_en"],

                    "position":
                        position,

                    "orientation":
                        orientation,
                }
            )


        return result



draw_service = DrawService()
