from sqlalchemy.orm import Session

from app.database.models import (
    Session as SessionModel,
    DrawnCard,
    Reading,
)
from app.services.tarot_service import load_cards


def create_session(
    db: Session,
    question: str | None,
    spread_type: str,
    user_id: int | None = None,
):
    session = SessionModel(
        user_id=user_id,
        question=question,
        spread_type=spread_type,
    )

    db.add(session)
    db.flush()

    return session


def create_cards(
    db: Session,
    session_id: int,
    cards: list,
    card_readings: list | None = None,
):
    interpretation_by_card = {
        item.card_id: item.interpretation for item in (card_readings or [])
    }
    card_data = {item["card_id"]: item for item in load_cards()}

    for card in cards:
        source = card_data.get(card.card_id, {})
        keyword_key = (
            "upright_keywords" if card.orientation == "upright" else "reversed_keywords"
        )
        item = DrawnCard(
            session_id=session_id,
            card_id=card.card_id,
            position=card.position,
            orientation=card.orientation,
            interpretation=interpretation_by_card.get(card.card_id),
            keywords="\n".join(source.get(keyword_key, [])),
        )

        db.add(item)

    db.flush()


def create_reading(
    db: Session,
    session_id: int,
    summary: str,
    synthesis: str | None,
    advice: list[str],
    title: str | None = None,
    clarification_prompt: str | None = None,
    clarification_answer: str | None = None,
):
    reading = Reading(
        session_id=session_id,
        summary=summary,
        synthesis=synthesis,
        advice="\n".join(advice),
        title=title or summary[:200],
        status="completed",
        clarification_prompt=clarification_prompt,
        clarification_answer=clarification_answer,
    )

    db.add(reading)
    db.flush()
    return reading
