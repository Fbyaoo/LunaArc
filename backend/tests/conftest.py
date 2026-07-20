import uuid

import pytest

from app.database.connection import SessionLocal
from app.database.models import (
    User,
    UserUsage,
)
from app.dependencies.auth import get_current_user
from app.main import app


@pytest.fixture(autouse=True)
def mock_authenticated_user():

    db = SessionLocal()

    user = User(
        email=(
            "test-"
            + uuid.uuid4().hex
            + "@example.com"
        ),
        password_hash="test",
        display_name="Test User",
        plan="plus",
        status="active",
    )

    db.add(user)

    db.commit()

    db.refresh(user)


    usage = UserUsage(
        user_id=user.id,
        daily_reading_count=0,
        single_reading_count=0,
        three_card_reading_count=0,
        ai_message_count=0,
    )

    db.add(usage)
    db.commit()


    app.dependency_overrides[
        get_current_user
    ] = lambda: user


    yield


    app.dependency_overrides.clear()

    db.close()
