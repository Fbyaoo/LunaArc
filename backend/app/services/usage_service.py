from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models import (
    User,
    UserUsage,
)


def get_today_usage(
    db: Session,
    user_id: int,
):

    usage = (
        db.query(UserUsage)
        .filter(
            UserUsage.user_id == user_id
        )
        .first()
    )

    if usage is None:

        usage = UserUsage(
            user_id=user_id,
            daily_reading_count=0,
            single_reading_count=0,
            three_card_reading_count=0,
            ai_message_count=0,
        )

        db.add(usage)

        db.commit()

        db.refresh(
            usage
        )

    return usage



def consume_reading(
    db: Session,
    user: User,
    spread_type: str,
):

    usage = get_today_usage(
        db,
        user.id,
    )


    if spread_type == "daily_card":

        usage.daily_reading_count += 1


    elif spread_type == "single_card":

        usage.single_reading_count += 1


    elif spread_type == "three_card":

        usage.three_card_reading_count += 1


    db.commit()

    db.refresh(
        usage
    )


    return usage
