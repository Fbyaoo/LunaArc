"""安全模块 — 敏感内容检测（LLM 语义分类）"""

from langchain_core.prompts import ChatPromptTemplate

from .llm import make_llm


def is_sensitive(question: str | None) -> bool:
    """LLM 判断：用户是否在寻求医疗、法律、投资等专业领域的实质性建议

    只输出 SENSITIVE 或 SAFE，不解释。LLM 失败时默认判定为敏感（宁严勿松）。
    """
    if not question:
        return False
    llm = make_llm(64)
    system = (
        "你是一个内容安全分类器。判断用户问题是否确实在寻求医疗、法律、投资等"
        "专业领域的实质性建议或决策。"
        "如果用户只是表达情绪、探讨人生哲学、询问人际关系走向、"
        "或寻求自我成长启示，属于安全范围。"
        "只输出 SENSITIVE 或 SAFE，不要解释。"
    )
    prompt_text = (
        f"用户问题：{question}\n"
        f"请判断：SAFE 还是 SENSITIVE？只回复一个单词。"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("user", "{input}"),
    ])
    chain = prompt | llm
    try:
        response = chain.invoke({"input": prompt_text})
        result = response.content.strip().upper()
        return "SENSITIVE" in result
    except Exception:
        return True
