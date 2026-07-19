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
    user_supplement: str = "",
) -> CardReading:
    llm = make_llm(512)
    rev = "逆位" if card.orientation == "reversed" else "正位"
    pos_label = position_label or POSITION_LABEL.get(card.position, card.position)

    prompt_text = f"牌：{card.name_zh}（{rev}）\n位置：{pos_label}\n"
    if intent:
        prompt_text += f"用户核心诉求：{intent}\n"
    if knowledge:
        prompt_text += f"牌义参考：{knowledge}\n"
    if user_supplement:
        prompt_text += f"用户补充信息：{user_supplement}\n"
    if request.question:
        prompt_text += f"用户问题：{request.question}\n"
        prompt_text += (
            "请先用一两句有画面感的语言写出牌面的关键意象，让人能感到人物、色彩、动作与氛围；"
            "再把这些意象转成针对用户问题的具体提醒。温柔坚定，无寒暄无废话。不超过200字。"
        )
    else:
        prompt_text += (
            "请先用一两句有画面感的语言写出牌面的关键意象，让人能感到人物、色彩、动作与氛围；"
            "再告诉ta这张牌此刻带来的具体提醒。温柔坚定，无寒暄无废话。不超过200字。"
        )

    system = (
        "你是一位专业的塔罗解读师，语气温柔而坚定，表达简洁有力量。"
        "必须参考牌义与牌面画面，不编造未给出的牌面元素。"
        "interpretation 要同时包含：①诗意但克制的牌面意象，让用户仿佛站在那张牌里；"
        "②紧扣用户问题或当前位置的启示，给出清晰、可落地的理解。"
        "禁止使用「亲爱的」「我看到」「这段解读」「直接回答」「这张牌告诉你」等套话；不要寒暄、不要空泛安慰、不要过度抒情。"
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
    user_supplement: str = "",
) -> list[CardReading]:
    """单牌同步，多牌线程池并行"""
    card_count = len(request.cards)
    knowledge_map = knowledge_map or {}
    position_labels = position_labels or {}
    if card_count == 1:
        try:
            card = request.cards[0]
            return [interpret_one_card(request, card, intent, knowledge_map.get(card.card_id, ""),
                                       position_labels.get(card.position),
                                       user_supplement=user_supplement)]
        except Exception:
            return []
    readings: list[CardReading | None] = [None] * card_count
    with ThreadPoolExecutor(max_workers=card_count) as executor:
        future_to_idx = {
            executor.submit(
                interpret_one_card, request, request.cards[i],
                intent, knowledge_map.get(request.cards[i].card_id, ""),
                position_labels.get(request.cards[i].position),
                user_supplement,
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
    user_supplement: str = "",
) -> str | None:
    """仅 three_card 生成综合叙事"""
    if spread_type != "three_card":
        return None

    position_labels = position_labels or {}
    llm = make_llm(256)
    all_interp_lines = []
    for r in readings:
        label = position_labels.get(r.position, r.position)
        all_interp_lines.append(f"{label}：{r.interpretation}")
    all_interp = "\n".join(all_interp_lines)
    prompt_text = (
        f"用户问题：{question}\n"
        f"三张牌解读：\n{all_interp}\n"
        f"请将三张牌的意象串联成一段完整回应，必须紧扣用户原问题，说明局势如何流动、真正的卡点在哪里、下一步该把力气放在哪里。"
        f"温柔坚定，无寒暄无废话。不超过180字。"
    )
    if user_supplement:
        prompt_text += f"\n用户补充了以下信息，请在综合中参考：{user_supplement}"
    if is_sensitive:
        prompt_text += "\n注意：用户问题涉及专业领域，请聚焦于内心探索而非给出专业结论。"
    system = (
        "你是一位专业塔罗师，擅长把多张牌的画面与象征串成清晰判断。"
        "synthesis 必须紧扣用户问题，不要写成泛泛的人生建议；语气温柔坚定，不寒暄，不废话。"
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
    llm = make_llm(96)

    if spread_type == "daily_card":
        prompt_text = (
            f"今日牌：{readings[0].interpretation}\n"
            f"用一句话总结今日提醒，不超过35字。"
        )
    elif spread_type == "single_card":
        prompt_text = (
            f"问题：{question}\n解读：{readings[0].interpretation}\n"
            f"用一句话紧扣原问题回应，不超过35字。"
        )
    else:
        prompt_text = (
            f"问题：{question}\n综合解读：{synthesis}\n"
            f"用一句话紧扣原问题回应，不超过45字。"
        )

    system = (
        "用一句话直接回应来访者的原问题，温柔坚定，不废话。"
        "如果原问题很模糊，只做中性概括或给出中性提醒；不要强行猜测为感情、事业、健康等具体类型，也不要输出带类型倾向的追问。"
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
        return readings[0].interpretation[:35] if readings else "静观其变"


def generate_advice_list(
    spread_type: str,
    question: str | None,
    cards: list[DrawnCard],
    readings: list[CardReading],
    synthesis: str | None,
    is_sensitive: bool = False,
    position_labels: dict[str, str] | None = None,
    user_supplement: str = "",
) -> list[str]:
    llm = make_llm(160)

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
            f"给出 2-3 条简短可行的建议。"
            f'以 JSON 字符串数组格式返回，如：["建议1", "建议2"]'
        )
    elif spread_type == "daily_card":
        prompt_text = (
            f"今日牌：{cards[0].name_zh}（{'逆位' if cards[0].orientation == 'reversed' else '正位'}）\n"
            f"解读：{readings[0].interpretation}\n"
            f"给出 2-3 条今日小建议。"
            f'以 JSON 字符串数组格式返回，如：["建议1", "建议2"]'
        )
    else:
        prompt_text = (
            f"问题：{question}\n"
            f"牌：{cards[0].name_zh}\n"
            f"解读：{readings[0].interpretation}\n"
            f"给出 2-3 条简短可行的建议。"
            f'以 JSON 字符串数组格式返回，如：["建议1", "建议2"]'
        )

    if user_supplement:
        prompt_text += f"\n用户补充了以下信息，请据此给出建议：{user_supplement}"
    if is_sensitive:
        prompt_text += "\n注意：引导用户关注内心感受，而非给出专业结论。"

    system = "你是一位专业塔罗师。建议要简短、具体、温柔坚定，紧扣用户问题。只输出 JSON 数组。"
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
