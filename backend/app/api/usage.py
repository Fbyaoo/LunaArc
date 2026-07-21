from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import (
    User,
)
from app.config.settings import get_settings
from app.services.usage_service import get_today_usage

from app.dependencies.auth import (
    get_current_user,
)


router = APIRouter(prefix="/api/usage", tags=["usage"])


@router.get("/me")
def usage(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = get_today_usage(db, user.id)

    used = 0

    if item:
        used = (
            item.daily_reading_count
            + item.single_reading_count
            + item.three_card_reading_count
        )

    limit = get_settings().default_daily_reading_limit

    return {
        "usage_date": str(item.usage_date) if item else None,
        "daily_reading_limit": None if user.plan == "plus" else limit,
        "daily_reading_used": used,
        "free_readings_remaining": None
        if user.plan == "plus"
        else max(limit - used, 0),
        "ai_message_limit": None,
        "ai_message_used": 0,
    }
