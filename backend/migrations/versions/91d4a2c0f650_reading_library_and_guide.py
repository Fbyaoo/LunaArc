"""reading library and guide

Revision ID: 91d4a2c0f650
Revises: 7a5fe2aa8bcf
Create Date: 2026-07-22 15:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "91d4a2c0f650"
down_revision: Union[str, None] = "7a5fe2aa8bcf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("drawn_cards", sa.Column("interpretation", sa.Text(), nullable=True))
    op.add_column("drawn_cards", sa.Column("keywords", sa.Text(), nullable=True))
    op.add_column("readings", sa.Column("title", sa.String(length=200), nullable=True))
    op.add_column(
        "readings",
        sa.Column(
            "status", sa.String(length=30), server_default="completed", nullable=False
        ),
    )
    op.add_column(
        "readings",
        sa.Column("saved", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("readings", sa.Column("saved_at", sa.DateTime(), nullable=True))
    op.add_column(
        "readings", sa.Column("clarification_prompt", sa.Text(), nullable=True)
    )
    op.add_column(
        "readings", sa.Column("clarification_answer", sa.Text(), nullable=True)
    )

    op.create_table(
        "guide_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("reading_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["reading_id"], ["readings.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_guide_sessions_reading_id"),
        "guide_sessions",
        ["reading_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_guide_sessions_user_id"),
        "guide_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "guide_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["guide_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_guide_messages_session_id"),
        "guide_messages",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_guide_messages_session_id"), table_name="guide_messages")
    op.drop_table("guide_messages")
    op.drop_index(op.f("ix_guide_sessions_user_id"), table_name="guide_sessions")
    op.drop_index(op.f("ix_guide_sessions_reading_id"), table_name="guide_sessions")
    op.drop_table("guide_sessions")
    op.drop_column("readings", "clarification_answer")
    op.drop_column("readings", "clarification_prompt")
    op.drop_column("readings", "saved_at")
    op.drop_column("readings", "saved")
    op.drop_column("readings", "status")
    op.drop_column("readings", "title")
    op.drop_column("drawn_cards", "keywords")
    op.drop_column("drawn_cards", "interpretation")
