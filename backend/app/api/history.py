from fastapi import APIRouter

from app.database.connection import SessionLocal
from app.database.models import Session


router = APIRouter(
    prefix="/api/history",
    tags=["history"],
)


@router.get("")
def get_history():

    db = SessionLocal()

    try:

        sessions = (
            db.query(Session)
            .order_by(
                Session.created_at.desc()
            )
            .all()
        )


        return [
            {
                "id": item.id,
                "question": item.question,
                "spread_type": item.spread_type,
                "created_at": item.created_at,
            }
            for item in sessions
        ]

    finally:

        db.close()
