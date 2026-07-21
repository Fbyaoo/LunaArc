from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.models import User, UserUsage
from app.config.settings import get_settings
from app.services.usage_service import get_today_usage


def get_usage(
    db: Session,
    user: User,
):
    return get_today_usage(db, user.id)


def check_reading_quota(
    db: Session,
    user: User,
    spread_type: str,
) -> bool:
    # Plus 无限
    if user.plan == "plus":
        return False

    usage = get_usage(
        db,
        user,
    )

    counter_by_spread = {
        "daily_card": UserUsage.daily_reading_count,
        "single_card": UserUsage.single_reading_count,
        "three_card": UserUsage.three_card_reading_count,
    }
    counter = counter_by_spread[spread_type]
    total = (
        UserUsage.daily_reading_count
        + UserUsage.single_reading_count
        + UserUsage.three_card_reading_count
    )
    updated = (
        db.query(UserUsage)
        .filter(
            UserUsage.id == usage.id,
            total < get_settings().default_daily_reading_limit,
        )
        .update({counter: counter + 1}, synchronize_session=False)
    )

    if updated != 1:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "READING_LIMIT_REACHED",
                "message": "今日免费解读次数已用完。",
            },
        )

    return True
