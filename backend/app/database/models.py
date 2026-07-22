from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    display_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    plan: Mapped[str] = mapped_column(
        String(20),
        default="free",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
    )


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    question: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    spread_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
    )

    cards = relationship(
        "DrawnCard",
        back_populates="session",
    )

    reading = relationship(
        "Reading",
        back_populates="session",
        uselist=False,
    )


class DrawnCard(Base):
    __tablename__ = "drawn_cards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id"),
    )

    card_id: Mapped[str] = mapped_column(
        String(50),
    )

    position: Mapped[str] = mapped_column(
        String(50),
    )

    orientation: Mapped[str] = mapped_column(
        String(20),
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    interpretation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    keywords: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    session = relationship(
        "Session",
        back_populates="cards",
    )


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id"),
    )

    summary: Mapped[str] = mapped_column(
        Text,
    )

    synthesis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    advice: Mapped[str] = mapped_column(
        Text,
    )

    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="completed",
        nullable=False,
    )

    saved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    saved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    clarification_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    clarification_answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
    )

    session = relationship(
        "Session",
        back_populates="reading",
    )


class UserUsage(Base):
    __tablename__ = "user_usage"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        unique=True,
    )

    usage_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
    )

    daily_reading_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    single_reading_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    three_card_reading_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    ai_message_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True, unique=True
    )

    plan: Mapped[str] = mapped_column(String(20), default="free")

    status: Mapped[str] = mapped_column(String(20), default="active")

    renewal_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class GuideSession(Base):
    __tablename__ = "guide_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    reading_id: Mapped[int | None] = mapped_column(
        ForeignKey("readings.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    messages = relationship(
        "GuideMessage",
        back_populates="session",
        order_by="GuideMessage.created_at",
    )


class GuideMessage(Base):
    __tablename__ = "guide_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("guide_sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    session = relationship("GuideSession", back_populates="messages")
