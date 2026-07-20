
from fastapi import APIRouter, HTTPException

from app.adapters.agent_adapter import agent_adapter
from app.schemas.readings import ReadingResponse
from app.services.clarify_cache import (
    get_request,
    delete_request,
)


router = APIRouter(
    prefix="/api/readings",
    tags=["clarify"],
)


@router.post(
    "/clarify",
    response_model=ReadingResponse,
)
def clarify_reading(
    body: dict,
):

    session_id = body.get(
        "session_id"
    )

    supplement = body.get(
        "user_supplement"
    )


    request = get_request(
        session_id
    )


    if request is None:

        raise HTTPException(
            status_code=410,
            detail="会话已过期，请重新抽牌",
        )


    result = (
        agent_adapter.resume_reading(
            request,
            supplement,
        )
    )


    delete_request(
        session_id
    )


    return result
