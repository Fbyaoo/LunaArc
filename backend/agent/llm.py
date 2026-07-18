"""LLM 工具模块 — 配置、工厂函数与共享常量"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


# ═══════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "deepseek-ai/DeepSeek-V3")


# ═══════════════════════════════════════════
# 常量映射
# ═══════════════════════════════════════════

# 位置中文映射（兜底用；优先使用 Spread Planner 生成的动态位置语义）
POSITION_LABEL: dict[str, str] = {
    "daily_guidance": "今日指引",
    "core":           "核心",
    "past":           "过去",
    "present":        "现在",
    "future":         "未来",
}

# 意图类别中文名
INTENT_LABEL: dict[str, str] = {
    "relationship": "关系",
    "career": "事业",
    "self_growth": "自我成长",
    "trend": "运势",
    "general": "通用",
}


# ═══════════════════════════════════════════
# LLM 工厂
# ═══════════════════════════════════════════

def make_llm(max_tokens: int = 512) -> ChatOpenAI:
    """创建独立的 LLM 实例（线程安全）"""
    return ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL,
        model=Config.OPENAI_MODEL,
        temperature=0.7,
        max_tokens=max_tokens,
    )
