
from fastapi import (
    APIRouter,
    Depends,
)

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
    )
):

    return {
        "id": user.id,

        "email": user.email,

        "display_name":
            user.display_name,

        "plan":
            user.plan,

        "status":
            user.status,
    }
