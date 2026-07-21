from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import (
    Session as TarotSession,
    User,
)

from app.dependencies.auth import (
    get_current_user,
)


router = APIRouter(
    prefix="/api/history",
    tags=["history"],
)


@router.get("")
def get_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(TarotSession)
        .filter(TarotSession.user_id == user.id)
        .order_by(TarotSession.created_at.desc())
        .all()
    )

    return [
        {
            "id": item.id,
            "question": item.question,
            "spread_type": item.spread_type,
            "created_at": item.created_at,
        }
        for item in records
    ]
