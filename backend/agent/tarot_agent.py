"""塔罗牌 Agent — LangGraph 状态图驱动"""

import operator
from dataclasses import dataclass
from typing import Annotated, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from .models import ReadingRequest, ReadingResponse, DrawnCard, CardReading
from .safety import is_sensitive
from .llm import make_llm, POSITION_LABEL
from .interpreter import (
    interpret_cards,
    synthesize,
    generate_summary,
    generate_advice_list,
    lookup_card_knowledge,
)



# ── 牌阵配置 ──

@dataclass
class SpreadConfig:
    """单次解读的牌阵配置"""
    intent: str
    positions: list[str]
    position_map: dict[str, str]

    def get_position_label(self, backend_position: str) -> str:
        return self.position_map.get(backend_position, backend_position)


_SPREAD_CONFIGS: dict[str, SpreadConfig] = {
    "daily": SpreadConfig(
        intent="daily",
        positions=["当日主题"],
        position_map={"1": "当日主题"},
    ),
    "single": SpreadConfig(
        intent="single",
        positions=["关键指引"],
        position_map={"1": "关键指引"},
    ),
    "relationship": SpreadConfig(
        intent="relationship",
        positions=["当前关系状态", "关系阻碍因素", "未来发展方向"],
        position_map={"1": "当前关系状态", "2": "关系阻碍因素", "3": "未来发展方向"},
    ),
    "career": SpreadConfig(
        intent="career",
        positions=["当前工作状态", "潜在挑战", "发展方向"],
        position_map={"1": "当前工作状态", "2": "潜在挑战", "3": "发展方向"},
    ),
    "self_growth": SpreadConfig(
        intent="self_growth",
        positions=["当前内心状态", "成长阻碍", "蜕变方向"],
        position_map={"1": "当前内心状态", "2": "成长阻碍", "3": "蜕变方向"},
    ),
    "trend": SpreadConfig(
        intent="trend",
        positions=["过去", "现在", "未来"],
        position_map={"1": "过去", "2": "现在", "3": "未来"},
    ),
    "general": SpreadConfig(
        intent="general",
        positions=["过去", "现在", "未来"],
        position_map={"1": "过去", "2": "现在", "3": "未来"},
    ),
}


_INTENT_CLASSIFY_PROMPT = (
    "你是塔罗牌阵规划师。根据用户问题，判断其咨询类型，只回复一个分类词。\n"
    "分类标准：\n"
    "- relationship：涉及恋爱、婚姻、伴侣、感情、人际、家庭关系、友谊\n"
    "- career：涉及工作、事业、职场、学业、面试、项目、创业\n"
    "- self_growth：涉及自我探索、内在成长、情绪困扰、人生意义、性格、信心\n"
    "- trend：涉及运势、趋势、未来发展、时间线预测、近期走向\n"
    "- general：不属于以上任何类别的通用问题\n\n"
    "用户问题：{question}\n"
    "请只回复一个单词：relationship / career / self_growth / trend / general"
)


def classify_intent(question: str | None) -> str:
    if not question:
        return "general"
    llm = make_llm(64)
    prompt = ChatPromptTemplate.from_messages([("user", "{input}")])
    try:
        resp = (prompt | llm).invoke({
            "input": _INTENT_CLASSIFY_PROMPT.format(question=question)
        })
        result = resp.content.strip().lower()
        for intent in ("relationship", "career", "self_growth", "trend", "general"):
            if intent in result:
                return intent
        return "general"
    except Exception:
        return "general"


def plan_spread(spread_type: str, question: str | None) -> SpreadConfig:
    """daily_card/single_card 固定映射，three_card 按意图动态映射"""
    if spread_type == "daily_card":
        return _SPREAD_CONFIGS["daily"]
    if spread_type == "single_card":
        return _SPREAD_CONFIGS["single"]
    intent = classify_intent(question)
    return _SPREAD_CONFIGS.get(intent, _SPREAD_CONFIGS["general"])



def analyze_intent(request: ReadingRequest) -> tuple[str, str]:
    """返回 (意图描述, 意图类别)"""
    if not request.question:
        return ("用户未提出具体问题，需要通用运势解读", "general")
    llm = make_llm(128)
    cards_desc = "、".join(f"{c.name_zh}({c.position})" for c in request.cards)
    system = (
        "你善于洞察人心，一句话提炼用户提问背后的真实诉求。"
        "只根据用户明确表达概括；如果问题很模糊，不要强行归到情绪、关系、事业等类型。不超过30字。"
    )
    prompt_text = f"用户问题：{request.question}\n抽到的牌：{cards_desc}\n请概括用户真正想了解的核心议题："
    prompt = ChatPromptTemplate.from_messages([("system", system), ("user", "{input}")])
    try:
        resp = (prompt | llm).invoke({"input": prompt_text})
        intent_desc = resp.content.strip()
    except Exception:
        intent_desc = request.question
    intent_category = classify_intent(request.question)
    return (intent_desc, intent_category)


_DISPATCH_PROMPT = (
    "你是塔罗解读 Agent 的调度员。根据用户问题和牌面，决定下一步行动。\n"
    "判断标准：\n"
    "- research：用户提出了与塔罗牌能回应的问题（情感、自我成长、人生选择、\n"
    "  日常困惑、运势指引等），即使涉及健康/法律/投资也照常解读，\n"
    "  后续会有专门的安全模块处理。\n"
    "- clarify：问题过于模糊或宽泛，缺少足够上下文让你给出有意义的解读。\n"
    "  例如「我怎么办」「帮帮我」且没有其他信息时。\n"
    "- redirect：问题属于纯工具性请求，与塔罗解读完全无关。\n"
    "  例如「帮我写代码」「翻译这段英文」「给我做饭谱」「解这道数学题」。\n\n"
    "用户问题：{question}\n"
    "抽到的牌：{cards}\n"
    "请只回复一个单词：research / clarify / redirect"
)


def route_dispatch(question: str | None, cards_desc: str) -> str:
    if not question:
        return "research"
    llm = make_llm(64)
    prompt = ChatPromptTemplate.from_messages([("user", "{input}")])
    try:
        resp = (prompt | llm).invoke({
            "input": _DISPATCH_PROMPT.format(question=question, cards=cards_desc)
        })
        result = resp.content.strip().lower()
        if "redirect" in result:
            return "redirect"
        if "clarify" in result:
            return "clarify"
        return "research"
    except Exception:
        return "research"


def generate_clarify_question(request: ReadingRequest, intent: str) -> str:
    llm = make_llm(200)
    system = (
        "你是一位温柔有耐心的塔罗师。用户的问题不够具体，塔罗无法给出有意义的解读。"
        "请用一句话温和地告诉用户，建议ta在下次抽牌前提一个更具体的问题，"
        "让解读更有针对性。不要提及本次已抽到的牌面信息，也不要让用户补充细节。"
        "不要猜测用户是在问感情、事业、健康或其他具体类型。不超过50字。"
    )
    prompt_text = (
        f"用户问题：{request.question}\n"
        f"你的初步理解：{intent}\n"
        f"请用一句话温和引导用户下次提问时更具体一些。不超过50字。"
    )
    prompt = ChatPromptTemplate.from_messages([("system", system), ("user", "{input}")])
    try:
        resp = (prompt | llm).invoke({"input": prompt_text})
        return resp.content.strip()
    except Exception:
        return "你的问题比较宽泛，下次抽牌时可以试着问得更具体一些，这样塔罗才能给你更有针对性的指引。"


def generate_clarify_followup(request: ReadingRequest, intent: str, round_num: int) -> str:
    """三牌追问：在同一轮对话中引导用户补充细节，后续 resume_reading 继续解读"""
    llm = make_llm(200)
    system = (
        "你是一位温柔有耐心的塔罗师。用户的问题比较宽泛，你需要引导ta在同一轮对话中补充一点细节，"
        "这样塔罗才能给出更有针对性的解读。注意：用户已经抽好了牌，你需要让ta在问题中补充具体情境，"
        "但不要提及具体的牌面信息。请用一句话温和地提问，引导ta补充问题的背景或方向。"
        "追问必须保持中性，不要出现感情、事业、关系、健康、财务等类型倾向，除非用户原问题已经明确提到。不超过50字。"
    )
    prompt_text = (
        f"用户问题：{request.question}\n"
        f"你的初步理解：{intent}\n"
        f"这是第{round_num}次追问，请用中性语言引导用户补充具体情境、正在纠结的选择或最想确认的方向。"
        f"不超过50字。"
    )
    prompt = ChatPromptTemplate.from_messages([("system", system), ("user", "{input}")])
    try:
        resp = (prompt | llm).invoke({"input": prompt_text})
        return resp.content.strip()
    except Exception:
        return "能否再多说一点你目前的情况呢？这样塔罗可以给你更有针对性的指引。"


def generate_redirect_message(request: ReadingRequest) -> str:
    llm = make_llm(128)
    system = "你是一位真诚而有边界感的塔罗师。用户的问题超出了你能回应的范围，请用一句话温柔说明你能做什么、不能做什么。"
    prompt_text = (
        f"用户问题：{request.question}\n"
        f"请用一句话婉拒，不超过40字。语气温柔但明确。"
    )
    prompt = ChatPromptTemplate.from_messages([("system", system), ("user", "{input}")])
    try:
        resp = (prompt | llm).invoke({"input": prompt_text})
        return resp.content.strip()
    except Exception:
        return "塔罗更擅长探索内心和人生方向，这个问题我可能帮不上忙。"


_SELF_REFLECT_PROMPT = (
    "你是塔罗解读的质量审核员。请从三个维度审视以下解读（1-5分）：\n"
    "① 画面描绘力：是否生动描绘了牌面细节（人物、动作、色彩、氛围）？\n"
    "② 启示相关性：启示是否紧密结合了用户问题与牌的位置含义，给出了针对性回应？\n"
    "③ 牌义融合度：是否巧妙融入了牌的传统含义？\n\n"
    "解读内容：\n{content}\n\n"
    "如果三项均≥4分，回复 PASS。否则回复 REVISE，并指出最需要改进的维度和一句话修改建议。"
)


def self_reflect(
    readings: list[CardReading],
    position_labels: dict[str, str] | None = None,
) -> tuple[bool, str]:
    """返回 (通过, 反馈)"""
    position_labels = position_labels or {}
    lines = []
    for r in readings:
        label = position_labels.get(r.position, r.position)
        lines.append(f"[{label}] {r.interpretation}")
    all_text = "\n---\n".join(lines)
    llm = make_llm(200)
    prompt = ChatPromptTemplate.from_messages([("user", "{input}")])
    try:
        resp = (prompt | llm).invoke({"input": _SELF_REFLECT_PROMPT.format(content=all_text)})
        result = resp.content.strip().upper()
        return ("PASS" in result, resp.content.strip())
    except Exception:
        return (True, "")


def refine_readings(
    request: ReadingRequest,
    readings: list[CardReading],
    feedback: str,
    position_labels: dict[str, str] | None = None,
) -> list[CardReading]:
    position_labels = position_labels or {}
    refined: list[CardReading] = []
    for i, reading in enumerate(readings):
        card = request.cards[i] if i < len(request.cards) else request.cards[0]
        llm = make_llm(512)
        rev = "逆位" if card.orientation == "reversed" else "正位"
        pos_label = position_labels.get(card.position) or POSITION_LABEL.get(card.position, card.position)
        system = (
            "你是一位专业塔罗解读师，根据审核反馈修正。"
            "保留温柔坚定、简洁有力的语气；补足牌面诗意画面与针对用户问题的启示。不寒暄不废话。"
        )
        prompt_text = (
            f"用户问题：{request.question or '无'}\n"
            f"原解读：{reading.interpretation}\n"
            f"审核反馈：{feedback}\n"
            f"牌：{card.name_zh}（{rev}）位置：{pos_label}\n"
            f"请根据反馈改进：先让牌面意象可感，再给出紧扣问题的提醒。不超过200字。"
        )
        prompt = ChatPromptTemplate.from_messages([("system", system), ("user", "{input}")])
        try:
            resp = (prompt | llm).invoke({"input": prompt_text})
            refined.append(CardReading(card_id=reading.card_id, position=reading.position, interpretation=resp.content.strip()))
        except Exception:
            refined.append(reading)
    return refined


# ── 追问轮次上限（预留扩展，当前为1轮即单次追问） ──
_MAX_CLARIFY_ROUNDS = 1


class _AgentState(TypedDict):
    request: ReadingRequest
    is_sensitive: bool
    intent: str
    intent_category: str
    position_labels: dict[str, str]
    spread_positions: list[str]
    status: str
    clarify_question: str
    clarify_round: int
    clarify_history: list[str]
    user_supplement: str
    card_knowledge: Annotated[dict, operator.ior]
    readings: list[CardReading]
    synthesis: str | None
    advice: list[str]
    summary: str
    reflect_count: int
    reflect_feedback: str


def _node_analyze_intent(state: _AgentState) -> dict:
    intent_desc, intent_category = analyze_intent(state["request"])
    return {"intent": intent_desc, "intent_category": intent_category}


def _node_plan_spread(state: _AgentState) -> dict:
    config: SpreadConfig = plan_spread(state["request"].spread_type, state["request"].question)
    return {
        "intent_category": config.intent,
        "position_labels": config.position_map,
        "spread_positions": config.positions,
    }


def _node_dispatch(state: _AgentState) -> dict:
    return {}


def _route_dispatch(state: _AgentState) -> str:
    if state["is_sensitive"]:
        return "research"
    req = state["request"]
    cards_desc = "、".join(f"{c.name_zh}({c.position})" for c in req.cards)
    return route_dispatch(req.question, cards_desc)


def _node_clarify(state: _AgentState) -> dict:
    req = state["request"]
    # single_card / daily_card：原有逻辑，引导用户下次抽牌前提更具体的问题
    if req.spread_type in ("single_card", "daily_card"):
        q = generate_clarify_question(req, state.get("intent", ""))
        return {"status": "needs_clarify", "clarify_question": q}
    # three_card：同一轮内追问，允许用户补充细节后继续解读
    round_num = state.get("clarify_round", 0)
    q = generate_clarify_followup(req, state.get("intent", ""), round_num + 1)
    history = list(state.get("clarify_history", [])) + [q]
    return {
        "status": "awaiting_clarify",
        "clarify_question": q,
        "clarify_round": round_num,
        "clarify_history": history,
    }


def _route_after_clarify(state: _AgentState) -> str:
    """clarify 节点后的条件路由：single/daily → END，three_card → 条件判断"""
    req = state["request"]
    if req.spread_type in ("single_card", "daily_card"):
        return "end"
    # three_card：如果已超最大轮次，强制进入解读
    if state.get("clarify_round", 0) >= _MAX_CLARIFY_ROUNDS:
        return "research"
    return "end"


def _node_redirect(state: _AgentState) -> dict:
    msg = generate_redirect_message(state["request"])
    return {"status": "out_of_scope", "summary": msg}


def _node_research_cards(state: _AgentState) -> dict:
    knowledge: dict[str, str] = {}
    for card in state["request"].cards:
        knowledge[card.card_id] = lookup_card_knowledge(card.card_id, card.orientation)
    return {"card_knowledge": knowledge}


def _node_interpret(state: _AgentState) -> dict:
    readings = interpret_cards(
        state["request"],
        intent=state.get("intent", ""),
        knowledge_map=state.get("card_knowledge", {}),
        position_labels=state.get("position_labels", {}),
        user_supplement=state.get("user_supplement", ""),
    )
    return {"readings": readings}

_MAX_REFLECT_ROUNDS = 2

_QUALITY_GATE_PROMPT = (
    "你是塔罗解读的质量审核员。请从三个维度审视以下解读（1-5分）：\n"
    "① 画面描绘力：是否生动描绘了牌面细节？\n"
    "② 启示相关性：是否紧密结合用户问题与位置含义？\n"
    "③ 牌义融合度：是否巧妙融入传统牌义？\n\n"
    "解读内容：\n{content}\n\n"
    "根据评分决定下一步，只回复一个关键词：\n"
    "- pass：三项均≥4分，解读质量合格，可以进入综合阶段\n"
    "- refine_visual：画面描绘力最低，需要重点改善画面细节描写\n"
    "- refine_relevance：启示相关性最低，需要更紧密结合用户问题\n"
    "- refine_symbolism：牌义融合度最低，需要更巧妙融入牌义\n"
    "- force：已经修正过{rounds}轮仍达不到标准，放弃修正直接推进"
)


def _node_self_reflect(state: _AgentState) -> dict:
    if not state.get("readings"):
        return {}
    passed, feedback = self_reflect(
        state["readings"],
        position_labels=state.get("position_labels"),
    )
    if passed:
        return {}
    cnt = state.get("reflect_count", 0) + 1
    return {"reflect_count": cnt, "reflect_feedback": feedback}


def _route_quality_gate(state: _AgentState) -> str:
    cnt = state.get("reflect_count", 0)
    if cnt == 0 or cnt > _MAX_REFLECT_ROUNDS:
        return "pass"
    pos_labels = state.get("position_labels", {})
    lines = []
    for r in state["readings"]:
        label = pos_labels.get(r.position, r.position)
        lines.append(f"[{label}] {r.interpretation}")
    all_text = "\n---\n".join(lines)
    llm = make_llm(100)
    prompt = ChatPromptTemplate.from_messages([("user", "{input}")])
    try:
        resp = (prompt | llm).invoke({
            "input": _QUALITY_GATE_PROMPT.format(content=all_text, rounds=cnt)
        })
        decision = resp.content.strip().lower()
        for key in ("refine_visual", "refine_relevance", "refine_symbolism"):
            if key in decision:
                return key
        if "force" in decision:
            return "force"
        return "pass"
    except Exception:
        return "force" if cnt >= _MAX_REFLECT_ROUNDS else "pass"


def _route_quality_decision(state: _AgentState) -> str:
    return _route_quality_gate(state)


def _node_refine_visual(state: _AgentState) -> dict:
    return _refine_with_focus(state, "语言不够有画面感。用简练、诗意但克制的语言让人物、色彩、动作和氛围可感，再自然落到问题本身。禁止「我看到」等套话。")


def _node_refine_relevance(state: _AgentState) -> dict:
    return _refine_with_focus(state, "回应不够针对。结合牌的位置含义，更直接地回答用户原问题，不要写成泛泛的人生建议。")


def _node_refine_symbolism(state: _AgentState) -> dict:
    return _refine_with_focus(state, "牌义融合度不够。请重点改善：把牌的传统象征意义（如元素、数字、符号）更自然地融入解读中。")


def _refine_with_focus(state: _AgentState, focus: str) -> dict:
    pos_labels = state.get("position_labels", {})
    refined: list[CardReading] = []
    for i, reading in enumerate(state["readings"]):
        card = state["request"].cards[i] if i < len(state["request"].cards) else state["request"].cards[0]
        llm = make_llm(512)
        rev = "逆位" if card.orientation == "reversed" else "正位"
        pos_label = pos_labels.get(card.position) or POSITION_LABEL.get(card.position, card.position)
        system = (
            "你是一位专业塔罗解读师，根据改进方向修正。"
            "输出要温柔坚定、无废话；必须同时有可感的牌面意象和紧扣用户问题的启示。"
        )
        prompt_text = (
            f"用户问题：{state['request'].question or '无'}\n"
            f"原解读：{reading.interpretation}\n"
            f"改进方向：{focus}\n"
            f"牌：{card.name_zh}（{rev}）位置：{pos_label}\n"
            f"请重新生成：先让牌面意象可感，再给出紧扣问题的提醒。不超过200字。"
        )
        prompt = ChatPromptTemplate.from_messages([("system", system), ("user", "{input}")])
        try:
            resp = (prompt | llm).invoke({"input": prompt_text})
            refined.append(CardReading(
                card_id=reading.card_id, position=reading.position,
                interpretation=resp.content.strip(),
            ))
        except Exception:
            refined.append(reading)
    return {"readings": refined}


def _node_synthesize(state: _AgentState) -> dict:
    req = state["request"]
    syn = synthesize(
        req.spread_type, req.question, state["readings"],
        state["is_sensitive"],
        position_labels=state.get("position_labels"),
        user_supplement=state.get("user_supplement", ""),
    )
    return {"synthesis": syn}


def _node_gen_advice(state: _AgentState) -> dict:
    req = state["request"]
    readings = state["readings"]
    if not readings:
        return {"advice": ["保持冷静，关注当下。"]}
    adv = generate_advice_list(
        req.spread_type, req.question, req.cards,
        readings, state.get("synthesis"), state["is_sensitive"],
        position_labels=state.get("position_labels"),
        user_supplement=state.get("user_supplement", ""),
    )
    return {"advice": adv}


def _node_gen_summary(state: _AgentState) -> dict:
    req = state["request"]
    readings = state["readings"]
    if not readings:
        return {"summary": "静观其变"}
    sum_text = generate_summary(req.spread_type, req.question, readings, state.get("synthesis"))
    if state["is_sensitive"]:
        sum_text = f"塔罗映照内心，但无法替代专业判断。{sum_text}"
    return {"summary": sum_text}


class TarotAgent:
    """塔罗解读智能体，入口 generate_reading(request) → ReadingResponse"""

    def __init__(self):
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(_AgentState)

        builder.add_node("analyze_intent", _node_analyze_intent)
        builder.add_node("plan_spread", _node_plan_spread)
        builder.add_node("dispatch", _node_dispatch)
        builder.add_node("clarify", _node_clarify)
        builder.add_node("redirect", _node_redirect)
        builder.add_node("research_cards", _node_research_cards)
        builder.add_node("interpret", _node_interpret)
        builder.add_node("self_reflect", _node_self_reflect)
        builder.add_node("refine_visual", _node_refine_visual)
        builder.add_node("refine_relevance", _node_refine_relevance)
        builder.add_node("refine_symbolism", _node_refine_symbolism)
        builder.add_node("synthesize", _node_synthesize)
        builder.add_node("gen_advice", _node_gen_advice)
        builder.add_node("gen_summary", _node_gen_summary)

        builder.set_entry_point("analyze_intent")
        builder.add_edge("analyze_intent", "plan_spread")
        builder.add_edge("plan_spread", "dispatch")
        builder.add_conditional_edges(
            "dispatch",
            _route_dispatch,
            {
                "research": "research_cards",
                "clarify": "clarify",
                "redirect": "redirect",
            },
        )
        builder.add_conditional_edges(
            "clarify",
            _route_after_clarify,
            {
                "end": END,
                "research": "research_cards",
            },
        )
        builder.add_edge("redirect", END)

        builder.add_edge("research_cards", "interpret")
        builder.add_edge("interpret", "self_reflect")

        builder.add_conditional_edges(
            "self_reflect",
            _route_quality_decision,
            {
                "pass": "synthesize",
                "force": "synthesize",
                "refine_visual": "refine_visual",
                "refine_relevance": "refine_relevance",
                "refine_symbolism": "refine_symbolism",
            },
        )
        builder.add_edge("refine_visual", "self_reflect")
        builder.add_edge("refine_relevance", "self_reflect")
        builder.add_edge("refine_symbolism", "self_reflect")

        builder.add_edge("synthesize", "gen_advice")
        builder.add_edge("gen_advice", "gen_summary")
        builder.add_edge("gen_summary", END)

        return builder.compile()

    def generate_reading(self, request: ReadingRequest, user_supplement: str = "") -> ReadingResponse:
        initial: _AgentState = {
            "request": request,
            "is_sensitive": is_sensitive(request.question),
            "intent": "",
            "intent_category": "",
            "position_labels": {},
            "spread_positions": [],
            "status": "normal",
            "clarify_question": "",
            "clarify_round": 0,
            "clarify_history": [],
            "user_supplement": user_supplement,
            "card_knowledge": {},
            "readings": [],
            "synthesis": None,
            "advice": [],
            "summary": "",
            "reflect_count": 0,
            "reflect_feedback": "",
        }
        result = self._graph.invoke(initial)

        if result.get("status") == "needs_clarify":
            return ReadingResponse(
                status="success",
                summary=result.get("clarify_question", "能否再多说一些？"),
                card_readings=[],
                advice=[],
            )

        if result.get("status") == "awaiting_clarify":
            return ReadingResponse(
                status="awaiting_clarify",
                summary=result.get("clarify_question", "能否再多说一些？"),
                card_readings=[],
                advice=[],
            )

        if result.get("status") == "out_of_scope":
            return ReadingResponse(
                status="success",
                summary=result.get("summary", "这个问题不在我的能力范围内。"),
                card_readings=[],
                advice=[],
            )

        if not result.get("readings"):
            return ReadingResponse(
                status="success",
                summary="暂时无法解读，请稍后重试。",
                card_readings=[],
                advice=["稍等片刻，再试一次。"],
            )
        return ReadingResponse(
            status="success",
            summary=result["summary"],
            card_readings=result["readings"],
            synthesis=result.get("synthesis"),
            advice=result["advice"],
        )

    def resume_reading(self, request: ReadingRequest, user_supplement: str) -> ReadingResponse:
        """三牌追问后，用户补充了细节，继续完成解读。

        绕过图调度（dispatch 已判断为 clarify），手动按节点顺序执行：
        research_cards → interpret → self_reflect → synthesize → gen_advice → gen_summary
        """
        # 构建初始 state，user_supplement 会通过 state 注入到后续节点
        state: _AgentState = {
            "request": request,
            "is_sensitive": is_sensitive(request.question),
            "intent": "",
            "intent_category": "",
            "position_labels": {},
            "spread_positions": [],
            "status": "normal",
            "clarify_question": "",
            "clarify_round": _MAX_CLARIFY_ROUNDS + 1,
            "clarify_history": [],
            "user_supplement": user_supplement,
            "card_knowledge": {},
            "readings": [],
            "synthesis": None,
            "advice": [],
            "summary": "",
            "reflect_count": 0,
            "reflect_feedback": "",
        }

        # ① 意图分析 + 牌阵规划（将用户补充信息拼入问题，使意图分类更准确）
        combined_question = request.question or ""
        if user_supplement:
            combined_question = f"{combined_question}（补充：{user_supplement}）" if combined_question else user_supplement
        # 构造临时 request 用于意图分析
        temp_request = ReadingRequest(
            question=combined_question,
            spread_type=request.spread_type,
            cards=request.cards,
        )
        intent_desc, intent_category = analyze_intent(temp_request)
        config: SpreadConfig = plan_spread(request.spread_type, combined_question)
        state["intent"] = intent_desc
        state["intent_category"] = config.intent
        state["position_labels"] = config.position_map
        state["spread_positions"] = config.positions

        # ② 查询知识库
        knowledge: dict[str, str] = {}
        for card in request.cards:
            knowledge[card.card_id] = lookup_card_knowledge(card.card_id, card.orientation)
        state["card_knowledge"] = knowledge

        # ③ 解读牌面
        readings = interpret_cards(
            request,
            intent=state["intent"],
            knowledge_map=state["card_knowledge"],
            position_labels=state["position_labels"],
            user_supplement=user_supplement,
        )
        state["readings"] = readings

        if not readings:
            return ReadingResponse(
                status="success",
                summary="暂时无法解读，请稍后重试。",
                card_readings=[],
                advice=["稍等片刻，再试一次。"],
            )

        # ④ 自我反思 + 修正循环
        for _ in range(_MAX_REFLECT_ROUNDS + 1):
            passed, feedback = self_reflect(
                state["readings"],
                position_labels=state.get("position_labels"),
            )
            if passed:
                break
            state["reflect_count"] += 1
            if state["reflect_count"] > _MAX_REFLECT_ROUNDS:
                break
            state["readings"] = refine_readings(
                request, state["readings"], feedback,
                position_labels=state.get("position_labels"),
            )

        # ⑤ 综合叙事
        syn = synthesize(
            request.spread_type, request.question, state["readings"],
            state["is_sensitive"],
            position_labels=state.get("position_labels"),
            user_supplement=user_supplement,
        )
        state["synthesis"] = syn

        # ⑥ 生成建议
        adv = generate_advice_list(
            request.spread_type, request.question, request.cards,
            state["readings"], state.get("synthesis"), state["is_sensitive"],
            position_labels=state.get("position_labels"),
            user_supplement=user_supplement,
        )
        state["advice"] = adv

        # ⑦ 生成摘要
        sum_text = generate_summary(request.spread_type, request.question, state["readings"], state.get("synthesis"))
        if state["is_sensitive"]:
            sum_text = f"塔罗映照内心，但无法替代专业判断。{sum_text}"
        state["summary"] = sum_text

        return ReadingResponse(
            status="success",
            summary=state["summary"],
            card_readings=state["readings"],
            synthesis=state.get("synthesis"),
            advice=state["advice"],
        )
