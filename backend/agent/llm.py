"""LLM 工具模块"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat")


POSITION_LABEL: dict[str, str] = {
    "1": "牌位一",
    "2": "牌位二",
    "3": "牌位三",
}

INTENT_LABEL: dict[str, str] = {
    "relationship": "关系",
    "career": "事业",
    "self_growth": "自我成长",
    "trend": "运势",
    "general": "通用",
}


@lru_cache(maxsize=32)
def make_llm(max_tokens: int = 512) -> ChatOpenAI:
    return ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL,
        model=Config.OPENAI_MODEL,
        temperature=0.7,
        max_tokens=max_tokens,
    )
