
import time
from uuid import uuid4

from app.schemas.readings import ReadingRequest


_cache = {}

TTL = 600


def save_request(
    request: ReadingRequest,
) -> str:

    session_id = uuid4().hex

    _cache[session_id] = {
        "request": request,
        "expire": time.time() + TTL,
    }

    return session_id



def get_request(
    session_id: str,
):

    item = _cache.get(session_id)

    if item is None:
        return None


    if item["expire"] < time.time():

        del _cache[session_id]

        return None


    return item["request"]



def delete_request(
    session_id: str,
):

    _cache.pop(
        session_id,
        None,
    )
