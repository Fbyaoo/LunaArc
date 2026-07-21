# ruff: noqa: E402
import atexit
import os
import tempfile
import uuid

import pytest


_test_db_fd, _test_db_path = tempfile.mkstemp(prefix="lunaarc-test-", suffix=".db")
os.close(_test_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"
os.environ["ENVIRONMENT"] = "test"
atexit.register(lambda: os.path.exists(_test_db_path) and os.unlink(_test_db_path))

from app.database.connection import Base, SessionLocal, engine
from app.database import models  # noqa: F401
from app.database.models import (
    User,
    UserUsage,
)
from app.dependencies.auth import get_current_user
from app.main import app


Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def mock_authenticated_user():
    db = SessionLocal()

    user = User(
        email=("test-" + uuid.uuid4().hex + "@example.com"),
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

    app.dependency_overrides[get_current_user] = lambda: user

    yield

    app.dependency_overrides.clear()

    db.close()
