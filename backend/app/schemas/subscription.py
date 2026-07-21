from datetime import datetime

from pydantic import BaseModel


class SubscriptionResponse(BaseModel):
    plan: str

    plan_label: str

    status: str

    renewal_date: datetime | None = None
