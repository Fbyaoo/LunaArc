from sqlalchemy.orm import Session as DatabaseSession, joinedload

from app.database.models import Reading, Session
from app.schemas.readings import ReadingCardDetail, ReadingDetail, ReadingListItem
from app.services.tarot_service import load_cards


_CARD_DATA = {card["card_id"]: card for card in load_cards()}


def owned_reading_query(db: DatabaseSession, user_id: int):
    return (
        db.query(Reading)
        .join(Session, Reading.session_id == Session.id)
        .filter(Session.user_id == user_id)
    )


def get_owned_reading(
    db: DatabaseSession, user_id: int, reading_id: int
) -> Reading | None:
    return (
        owned_reading_query(db, user_id)
        .options(joinedload(Reading.session).joinedload(Session.cards))
        .filter(Reading.id == reading_id)
        .first()
    )


def to_list_item(reading: Reading) -> ReadingListItem:
    session = reading.session
    return ReadingListItem(
        id=reading.id,
        spread_type=session.spread_type,
        question=session.question,
        title=reading.title or reading.summary[:200],
        summary=reading.summary,
        created_at=reading.created_at,
        saved=reading.saved,
        status=reading.status,
    )


def to_detail(reading: Reading) -> ReadingDetail:
    cards = []
    for drawn_card in reading.session.cards:
        card = _CARD_DATA.get(drawn_card.card_id, {})
        cards.append(
            ReadingCardDetail(
                card_id=drawn_card.card_id,
                name=card.get("name_en", drawn_card.card_id),
                name_zh=card.get("name_zh", drawn_card.card_id),
                image_url=card.get("image"),
                position=drawn_card.position,
                reversed=drawn_card.orientation == "reversed",
                orientation=drawn_card.orientation,
                interpretation=drawn_card.interpretation,
                keywords=(drawn_card.keywords or "").splitlines(),
            )
        )

    return ReadingDetail(
        id=reading.id,
        status=reading.status,
        spread_type=reading.session.spread_type,
        question=reading.session.question,
        title=reading.title or reading.summary[:200],
        summary=reading.summary,
        cards=cards,
        synthesis=reading.synthesis,
        advice=reading.advice.splitlines(),
        clarification_prompt=reading.clarification_prompt,
        clarification_answer=reading.clarification_answer,
        saved=reading.saved,
        saved_at=reading.saved_at,
        created_at=reading.created_at,
    )
