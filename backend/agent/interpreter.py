"""解读引擎 — 牌面解读、综合叙事、摘要生成、行动建议"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.prompts import ChatPromptTemplate

from .llm import make_llm, POSITION_LABEL
from .models import DrawnCard, CardReading, ReadingRequest
from .knowledge import lookup_card_meaning, lookup_card_imagery


def interpret_one_card(
    request: ReadingRequest,
    card: DrawnCard,
    intent: str = "",
    knowledge: str = "",
    position_label: str | None = None,
) -> CardReading:
    """解读单张牌（线程安全：每次创建独立 LLM 实例）

    Args:
        position_label: 动态位置语义（由 Spread Planner 生成）。
                       若为 None 则回退到静态 POSITION_LABEL。
    """
    llm = make_llm(512)
    rev = "逆位" if card.orientation == "reversed" else "正位"
    # 优先使用 Spread Planner 生成的动态位置语义
    pos_label = position_label or POSITION_LABEL.get(card.position, card.position)

    prompt_text = f"牌：{card.name_zh}（{rev}）\n位置：{pos_label}\n"
    if intent:
        prompt_text += f"用户核心诉求：{intent}\n"
    if knowledge:
        prompt_text += f"牌义参考：{knowledge}\n"
    if request.question:
        prompt_text += f"用户问题：{request.question}\n"
        prompt_text += "先以诗意的语言描绘这张牌的经典画面，再自然过渡到它在当前位置下的启示。不超过200字。"
    else:
        prompt_text += "先以诗意的语言描绘这张牌的经典画面，再自然过渡到今日运势启示。不超过200字。"

    system = (
        "你是一位温柔而富有诗意的塔罗解读师。"
        "请参考提供的【牌面画面】信息，用诗意的语言直接描绘画面中的人物、动作、色彩与氛围，"
        "不要自己编造画面细节，也不要使用「我看到」「画面中」「牌面上」等元描述字眼，"
        "而是让读者仿佛置身其中。再将画面自然过渡到与用户相关的启示。"
        "温柔而坚定，简洁而有画面感。"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("user", "{input}"),
    ])
    chain = prompt | llm
    response = chain.invoke({"input": prompt_text})
    return CardReading(
        card_id=card.card_id,
        position=pos_label,
        interpretation=response.content.strip(),
    )


def interpret_cards(
    request: ReadingRequest,
    intent: str = "",
    knowledge_map: dict[str, str] | None = None,
    position_labels: dict[str, str] | None = None,
) -> list[CardReading]:
    """并行解读所有牌，失败时返回空列表

    Args:
        position_labels: 后端 position → 语义位置标签的映射。
                        由 Spread Planner 生成，如 {"past": "当前关系状态", ...}
    """
    card_count = len(request.cards)
    knowledge_map = knowledge_map or {}
    position_labels = position_labels or {}
    if card_count == 1:
        try:
            card = request.cards[0]
            return [interpret_one_card(request, card, intent, knowledge_map.get(card.card_id, ""),
                                       position_labels.get(card.position))]
        except Exception:
            return []
    # 多牌并行
    readings: list[CardReading | None] = [None] * card_count
    with ThreadPoolExecutor(max_workers=card_count) as executor:
        future_to_idx = {
            executor.submit(
                interpret_one_card, request, request.cards[i],
                intent, knowledge_map.get(request.cards[i].card_id, ""),
                position_labels.get(request.cards[i].position),
            ): i
            for i in range(card_count)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                readings[idx] = future.result()
            except Exception:
                pass
    return [r for r in readings if r is not None]


def synthesize(
    spread_type: str,
    question: str | None,
    readings: list[CardReading],
    is_sensitive: bool = False,
    position_labels: dict[str, str] | None = None,
) -> str | None:
    """综合多牌解读（LLM 生成）"""
    if spread_type != "three_card":
        return None

    position_labels = position_labels or {}
    llm = make_llm(512)
    # 使用语义位置标签展示解读
    all_interp_lines = []
    for r in readings:
        label = position_labels.get(r.position, r.position)
        all_interp_lines.append(f"{label}：{r.interpretation}")
    all_interp = "\n".join(all_interp_lines)
    prompt_text = (
        f"用户问题：{question}\n"
        f"三张牌解读：\n{all_interp}\n"
        f"请将这三张牌串联成一段有起承转合的叙事。"
        f"像讲故事一样，揭示牌面之间的内在呼应。不超过180字。"
    )
    if is_sensitive:
        prompt_text += "\n注意：用户问题涉及专业领域，请聚焦于内心探索而非给出专业结论。"
    system = (
        "你善于将多张牌的意象编织成完整的叙事。"
        "用诗意的语言串联牌面画面，揭示过去、现在、未来之间的内在呼应。"
        "温柔而深刻，简洁而有力量。"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("user", "{input}"),
    ])
    chain = prompt | llm
    try:
        response = chain.invoke({"input": prompt_text})
        return response.content.strip()
    except Exception:
        return "牌与牌之间自有呼应，每段经历都有它的意义。"


def generate_summary(
    spread_type: str,
    question: str | None,
    readings: list[CardReading],
    synthesis: str | None,
) -> str:
    """生成一句话摘要（LLM 生成）"""
    llm = make_llm(256)

    if spread_type == "daily_card":
        prompt_text = (
            f"今日牌：{readings[0].interpretation}\n"
            f"精炼总结今日运势的核心启示，不超过35字。"
        )
    elif spread_type == "single_card":
        prompt_text = (
            f"问题：{question}\n解读：{readings[0].interpretation}\n"
            f"精炼概括核心信息，不超过35字。"
        )
    else:
        prompt_text = (
            f"问题：{question}\n综合解读：{synthesis}\n"
            f"精炼总结三张牌的整体启示，不超过45字。"
        )

    system = "你用一句话凝练塔罗叙事，简洁而有力量。"
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("user", "{input}"),
    ])
    chain = prompt | llm
    try:
        response = chain.invoke({"input": prompt_text})
        return response.content.strip()
    except Exception:
        return readings[0].interpretation[:35] if readings else "静观其变"


def generate_advice_list(
    spread_type: str,
    question: str | None,
    cards: list[DrawnCard],
    readings: list[CardReading],
    synthesis: str | None,
    is_sensitive: bool = False,
    position_labels: dict[str, str] | None = None,
) -> list[str]:
    """调用 LLM 生成建议列表（返回 JSON 数组）"""
    llm = make_llm(512)

    position_labels = position_labels or {}
    all_interp_lines = []
    for r in readings:
        label = position_labels.get(r.position, r.position)
        all_interp_lines.append(f"{label}：{r.interpretation}")
    all_interp = "\n".join(all_interp_lines)

    if spread_type == "three_card":
        prompt_text = (
            f"用户问题：{question}\n"
            f"牌阵解读：\n{all_interp}\n"
            f"综合：{synthesis}\n"
            f"请给出 3-5 条行动建议。温柔而坚定。"
            f'以 JSON 字符串数组格式返回，如：["建议1", "建议2"]'
        )
    elif spread_type == "daily_card":
        prompt_text = (
            f"今日牌：{cards[0].name_zh}（{'逆位' if cards[0].orientation == 'reversed' else '正位'}）\n"
            f"解读：{readings[0].interpretation}\n"
            f"请给出 2-3 条今日小建议，温柔而坚定。"
            f'以 JSON 字符串数组格式返回，如：["建议1", "建议2"]'
        )
    else:
        prompt_text = (
            f"问题：{question}\n"
            f"牌：{cards[0].name_zh}\n"
            f"解读：{readings[0].interpretation}\n"
            f"请给出 2-3 条行动建议，温柔而坚定，简短有力。"
            f'以 JSON 字符串数组格式返回，如：["建议1", "建议2"]'
        )

    if is_sensitive:
        prompt_text += "\n注意：用户问题涉及专业领域，引导用户关注内心感受与自我觉察，而非给出专业建议。"

    system = "你是一位温柔而睿智的生活导师。建议简短、具体、可落地。只输出 JSON 数组。"
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("user", "{input}"),
    ])
    chain = prompt | llm

    try:
        response = chain.invoke({"input": prompt_text})
        text = response.content.strip()
        # 提取 JSON 数组
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            data = json.loads(text[start:end + 1])
            if isinstance(data, list):
                return [str(item) for item in data]
        # 回退：按行拆分
        lines = [l.strip().lstrip("0123456789.、-· ") for l in text.split("\n") if l.strip()]
        return [l for l in lines if len(l) > 2] or ["保持冷静，关注当下。"]
    except Exception:
        return ["保持开放心态，专注内在成长。"]


# ═══════════════════════════════════════════
# Agent 知识库 — 牌义 + 画面描述查询（Tool）
# ═══════════════════════════════════════════


def lookup_card_knowledge(card_id: str, orientation: str) -> str:
    """Agent Tool：查牌义知识库 + 画面描述

    从 knowledge.py 融合两部分数据：
    - 牌义关键词（正位/逆位）
    - 韦特牌面画面描述
    """
    # 查牌义关键词
    knowledge_text = lookup_card_meaning(card_id, orientation)

    # 查画面描述
    imagery = lookup_card_imagery(card_id)
    if imagery:
        knowledge_text += f"\n【牌面画面】{imagery}"

    return knowledge_text



