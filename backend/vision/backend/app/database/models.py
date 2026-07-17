from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Session(Base):

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
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
        default=datetime.utcnow,
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    session = relationship(
        "Session",
        back_populates="reading",
    )
