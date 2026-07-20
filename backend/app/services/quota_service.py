from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.models import (
    User,
    UserUsage,
)


FREE_LIMIT = 3


def get_usage(
    db: Session,
    user: User,
):

    usage = (
        db.query(UserUsage)
        .filter(
            UserUsage.user_id
            == user.id
        )
        .first()
    )

    if usage is None:

        usage = UserUsage(
            user_id=user.id,
            daily_reading_count=0,
            single_reading_count=0,
            three_card_reading_count=0,
            ai_message_count=0,
        )

        db.add(usage)
        db.commit()
        db.refresh(usage)


    return usage



def check_reading_quota(
    db: Session,
    user: User,
):

    # Plus 无限
    if user.plan == "plus":
        return


    usage = get_usage(
        db,
        user,
    )


    used = (
        usage.daily_reading_count
        +
        usage.single_reading_count
        +
        usage.three_card_reading_count
    )


    if used >= FREE_LIMIT:

        raise HTTPException(
            status_code=403,
            detail={
                "error_code":
                "READING_LIMIT_REACHED",

                "message":
                "今日免费解读次数已用完。",
            },
        )
