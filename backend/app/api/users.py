from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User

from app.dependencies.auth import (
    get_current_user,
)


router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)



@router.get("/me")
def get_me(
    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    remaining = 3


    return {

        "id":
            f"usr_{user.id}",


        "display_name":
            user.display_name,


        "email":
            user.email,


        "avatar_url":
            user.avatar_url,


        "plan":
            user.plan,


        "plan_label":
            (
                "LunaArc Plus"
                if user.plan=="plus"
                else "Free Plan"
            ),


        "status":
            user.status,


        "email_verified":
            user.email_verified,


        "free_readings_remaining":
            remaining,


        "daily_reading_limit":
            3,


        "renewal_date":
            None,


        "created_at":
            user.created_at,

    }
