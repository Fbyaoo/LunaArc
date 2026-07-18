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
    llm = make_llm(512)
    rev = "逆位" if card.orientation == "reversed" else "正位"
    pos_label = position_label or POSITION_LABEL.get(card.position, card.position)

    prompt_text = f"牌：{card.name_zh}（{rev}）\n位置：{pos_label}\n"
    if intent:
        prompt_text += f"用户核心诉求：{intent}\n"
    if knowledge:
        prompt_text += f"牌义参考：{knowledge}\n"
    if request.question:
        prompt_text += f"用户问题：{request.question}\n"
        prompt_text += "先以诗意的语言描绘这张牌的经典画面，然后结合用户的具体问题，给出在当前位置下针对性的启示。不超过200字。"
    else:
        prompt_text += "先以诗意的语言描绘这张牌的经典画面，再自然过渡到它在当前位置下的启示。不超过200字。"

    system = (
        "你是一位温柔而富有诗意的塔罗解读师。"
        "请参考提供的【牌面画面】信息，用诗意的语言直接描绘画面中的人物、动作、色彩与氛围，"
        "不要自己编造画面细节，也不要使用「我看到」「画面中」「牌面上」等元描述字眼，"
        "而是让读者仿佛置身其中。如果用户提出了具体问题，启示部分必须紧扣用户的问题，"
        "给出直接而有针对性的回应，而非泛泛而谈。温柔而坚定，简洁而有画面感。"
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
    """单牌同步，多牌线程池并行"""
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
    """仅 three_card 生成综合叙事"""
    if spread_type != "three_card":
        return None

    position_labels = position_labels or {}
    llm = make_llm(512)
    all_interp_lines = []
    for r in readings:
        label = position_labels.get(r.position, r.position)
        all_interp_lines.append(f"{label}：{r.interpretation}")
    all_interp = "\n".join(all_interp_lines)
    prompt_text = (
        f"用户问题：{question}\n"
        f"三张牌解读：\n{all_interp}\n"
        f"请将这三张牌串联成一段有起承转合的叙事，"
        f"并紧扣用户的具体问题给出综合性的回应。不超过180字。"
    )
    if is_sensitive:
        prompt_text += "\n注意：用户问题涉及专业领域，请聚焦于内心探索而非给出专业结论。"
    system = (
        "你善于将多张牌的意象编织成完整的叙事，并针对用户的问题给出直接回应。"
        "用诗意的语言串联牌面画面，揭示牌面之间的内在呼应。"
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
    llm = make_llm(256)

    if spread_type == "daily_card":
        prompt_text = (
            f"今日牌：{readings[0].interpretation}\n"
            f"精炼总结今日运势的核心启示，不超过35字。"
        )
    elif spread_type == "single_card":
        prompt_text = (
            f"问题：{question}\n解读：{readings[0].interpretation}\n"
            f"针对用户的问题，用一句话概括核心启示，不超过35字。"
        )
    else:
        prompt_text = (
            f"问题：{question}\n综合解读：{synthesis}\n"
            f"针对用户的问题，用一句话概括整体启示，不超过45字。"
        )

    system = "你用一句话精准概括塔罗对用户问题的核心回应，简洁而有力量。"
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
            f"针对用户的具体问题，给出 1-2 条可落地的行动建议。温柔而坚定。"
            f'以 JSON 字符串数组格式返回，如：["建议1", "建议2"]'
        )
    elif spread_type == "daily_card":
        prompt_text = (
            f"今日牌：{cards[0].name_zh}（{'逆位' if cards[0].orientation == 'reversed' else '正位'}）\n"
            f"解读：{readings[0].interpretation}\n"
            f"请给出 1-2 条今日小建议，温柔而坚定。"
            f'以 JSON 字符串数组格式返回，如：["建议1", "建议2"]'
        )
    else:
        prompt_text = (
            f"问题：{question}\n"
            f"牌：{cards[0].name_zh}\n"
            f"解读：{readings[0].interpretation}\n"
            f"针对用户的问题，给出 2-3 条可落地的行动建议。"
            f'以 JSON 字符串数组格式返回，如：["建议1", "建议2"]'
        )

    if is_sensitive:
        prompt_text += "\n注意：用户问题涉及专业领域，引导用户关注内心感受与自我觉察，而非给出专业建议。"

    system = "你是一位温柔而睿智的生活导师。建议必须紧扣用户的具体问题，简短、可落地。只输出 JSON 数组。"
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("user", "{input}"),
    ])
    chain = prompt | llm

    try:
        response = chain.invoke({"input": prompt_text})
        text = response.content.strip()
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            data = json.loads(text[start:end + 1])
            if isinstance(data, list):
                return [str(item) for item in data]
        lines = [l.strip().lstrip("0123456789.、-· ") for l in text.split("\n") if l.strip()]
        return [l for l in lines if len(l) > 2] or ["保持冷静，关注当下。"]
    except Exception:
        return ["保持开放心态，专注内在成长。"]


def lookup_card_knowledge(card_id: str, orientation: str) -> str:
    """融合牌义关键词与画面描述"""
    knowledge_text = lookup_card_meaning(card_id, orientation)
    imagery = lookup_card_imagery(card_id)
    if imagery:
        knowledge_text += f"\n【牌面画面】{imagery}"
    return knowledge_text
