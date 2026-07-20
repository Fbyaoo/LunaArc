from datetime import date

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import (
    User,
    UserUsage,
)

from app.dependencies.auth import (
    get_current_user,
)


router = APIRouter(
    prefix="/api/usage",
    tags=["usage"],
)



@router.get("/me")
def get_usage(
    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
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

        return {

            "usage_date":
                str(date.today()),

            "daily_reading_limit":
                user.daily_reading_limit
                if hasattr(
                    user,
                    "daily_reading_limit"
                )
                else 3,

            "daily_reading_used":
                0,

            "free_readings_remaining":
                3,

        }


    used = (
        usage.daily_reading_count
        +
        usage.single_reading_count
        +
        usage.three_card_reading_count
    )


    limit = 3


    return {

        "usage_date":
            str(usage.usage_date),

        "daily_reading_limit":
            limit,

        "daily_reading_used":
            used,

        "free_readings_remaining":
            max(
                limit - used,
                0
            ),

    }
