from fastapi import (
    APIRouter,
    Depends,
)

from app.database.models import User
from app.dependencies.auth import (
    get_current_user,
)


router = APIRouter(
    prefix="/api/subscriptions",
    tags=["subscriptions"],
)


@router.get("/me")
def get_subscription(
    user: User = Depends(
        get_current_user
    ),
):

    return {

        "plan":
            user.plan,

        "plan_label":
            (
                "LunaArc Plus"
                if user.plan == "plus"
                else "Free Plan"
            ),

        "status":
            user.status,

        "renewal_date":
            None,
    }
