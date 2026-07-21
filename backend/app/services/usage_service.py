from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.database.models import (
    User,
    UserUsage,
)
from app.config.settings import get_settings


def _today() -> object:
    return datetime.now(ZoneInfo(get_settings().usage_timezone)).date()


def get_today_usage(
    db: Session,
    user_id: int,
):
    usage = db.query(UserUsage).filter(UserUsage.user_id == user_id).first()

    if usage is None:
        usage = UserUsage(
            user_id=user_id,
            daily_reading_count=0,
            single_reading_count=0,
            three_card_reading_count=0,
            ai_message_count=0,
        )

        db.add(usage)

        db.flush()

    usage_date = usage.usage_date
    if usage_date is None or usage_date.date() != _today():
        usage.usage_date = datetime.now(UTC)
        usage.daily_reading_count = 0
        usage.single_reading_count = 0
        usage.three_card_reading_count = 0
        usage.ai_message_count = 0
        db.flush()

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

    db.flush()

    return usage
