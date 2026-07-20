from sqlalchemy.orm import Session

from app.database.models import (
    Session as SessionModel,
    DrawnCard,
    Reading,
)


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
    db.commit()
    db.refresh(session)

    return session



def create_cards(
    db: Session,
    session_id: int,
    cards: list,
):

    for card in cards:

        item = DrawnCard(
            session_id=session_id,
            card_id=card.card_id,
            position=card.position,
            orientation=card.orientation,
        )

        db.add(item)

    db.commit()



def create_reading(
    db: Session,
    session_id: int,
    summary: str,
    synthesis: str | None,
    advice: list[str],
):

    reading = Reading(
        session_id=session_id,
        summary=summary,
        synthesis=synthesis,
        advice="\n".join(advice),
    )

    db.add(reading)
    db.commit()
