import json
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(
    prefix="/api/cards",
    tags=["cards"],
)


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "tarot_cards.json"


class Card(BaseModel):
    card_id: str

    class_id: int

    name_en: str

    name_zh: str

    arcana: str

    image: str

    core_symbolism: list[str]

    upright_keywords: list[str]

    reversed_keywords: list[str]


@router.get("", response_model=list[Card])
def get_cards() -> list[Card]:
    with DATA_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        cards = json.load(file)

    return [Card(**card) for card in cards]
