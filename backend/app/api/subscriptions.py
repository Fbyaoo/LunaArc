from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import Subscription, User
from app.dependencies.auth import get_current_user


router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("/me")
def subscription(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    plan = item.plan if item is not None else user.plan
    status = item.status if item is not None else user.status

    return {
        "plan": plan,
        "plan_label": ("LunaArc Plus" if plan == "plus" else "Free Plan"),
        "status": status,
        "renewal_date": item.renewal_date if item is not None else None,
    }
