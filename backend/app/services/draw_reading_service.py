from sqlalchemy.orm import Session

from app.adapters.agent_adapter import agent_adapter
from app.database.connection import SessionLocal
from app.database.crud import (
    create_cards,
    create_reading,
    create_session,
)
from app.schemas.draw import SpreadType
from app.schemas.readings import (
    DrawnCard,
    ReadingRequest,
)
from app.services.draw_service import draw_service
from app.services.usage_service import consume_reading


class DrawReadingRequestError(ValueError):
    """draw-and-read 请求参数不符合业务规则。"""

    def __init__(
        self,
        error_code: str,
        message: str,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class DrawReadingService:
    def execute(
        self,
        question: str | None,
        spread_type: SpreadType,
        user=None,
        db: Session | None = None,
    ) -> dict:
        normalized_question = (
            question.strip()
            if question is not None
            and question.strip()
            else None
        )

        if (
            spread_type != "daily_card"
            and normalized_question is None
        ):
            raise DrawReadingRequestError(
                error_code="EMPTY_QUESTION",
                message="请输入你想询问的问题。",
            )

        # 1. 根据牌阵抽牌
        cards = draw_service.draw(
            spread_type
        )

        # 2. 转成 Backend ReadingRequest
        reading_cards = [
            DrawnCard(
                card_id=card["card_id"],
                name_zh=card["name_zh"],
                position=card["position"],
                orientation=card["orientation"],
            )
            for card in cards
        ]

        reading_request = ReadingRequest(
            question=normalized_question,
            spread_type=spread_type,
            cards=reading_cards,
            user_history=None,
        )

        # 3. 调用 Mock 或真实 Agent
        reading = agent_adapter.generate_reading(
            reading_request
        )

        # 4. 保存占卜会话、卡牌和解读
        db = SessionLocal()

        try:
            session = create_session(
                db=db,
                question=normalized_question,
                spread_type=spread_type,
                user_id=(
                    user.id
                    if user is not None
                    else None
                ),
            )

            create_cards(
                db=db,
                session_id=session.id,
                cards=reading_cards,
            )

            create_reading(
                db=db,
                session_id=session.id,
                summary=reading.summary,
                synthesis=reading.synthesis,
                advice=reading.advice,
            )

            if user is not None:
                consume_reading(
                    db=db,
                    user=user,
                    spread_type=spread_type,
                )

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

        return {
            "cards": cards,
            "reading": reading,
        }


draw_reading_service = DrawReadingService()
