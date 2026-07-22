import time
from uuid import uuid4

from app.schemas.readings import ReadingRequest


_cache = {}

TTL = 600


def save_request(
    request: ReadingRequest,
    user_id: int,
    clarify_prompt: str | None = None,
) -> str:
    session_id = uuid4().hex

    _cache[session_id] = {
        "request": request,
        "user_id": user_id,
        "clarify_prompt": clarify_prompt,
        "expire": time.time() + TTL,
    }

    return session_id


def get_request(
    session_id: str,
    user_id: int,
):
    item = _cache.get(session_id)

    if item is None:
        return None

    if item["user_id"] != user_id:
        return None

    if item["expire"] < time.time():
        del _cache[session_id]

        return None

    return item["request"]


def get_clarify_prompt(session_id: str, user_id: int) -> str | None:
    item = _cache.get(session_id)
    if item is None or item["user_id"] != user_id or item["expire"] < time.time():
        return None
    return item.get("clarify_prompt")


def delete_request(
    session_id: str,
):
    _cache.pop(
        session_id,
        None,
    )
