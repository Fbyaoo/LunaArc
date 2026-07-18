import json
from pathlib import Path

from app.schemas.readings import (
    DrawnCard,
    EnrichedCard,
)


DATA_FILE = (
    Path(__file__).resolve()
    .parent.parent
    / "data"
    / "tarot_cards.json"
)


def load_cards():

    with DATA_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)



def enrich_card(
    card: DrawnCard,
) -> EnrichedCard:

    cards = load_cards()

    target = next(
        (
            item
            for item in cards
            if item["card_id"] == card.card_id
        ),
        None,
    )


    if target is None:
        raise ValueError(
            f"Unknown card: {card.card_id}"
        )


    return EnrichedCard(
        card_id=card.card_id,
        name_zh=target["name_zh"],
        position=card.position,
        orientation=card.orientation,
        core_symbolism=target["core_symbolism"],
        upright_keywords=target["upright_keywords"],
        reversed_keywords=target["reversed_keywords"],
    )
