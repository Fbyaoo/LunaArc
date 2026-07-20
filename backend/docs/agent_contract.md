# LunaArc Agent 对接协议

## 0. 最终牌阵与 Position 协议

Backend 传给 Agent 的 `position` 统一使用字符串序号。

| spread_type | 牌数 | position（必须） |
|---|---:|---|
| `daily_card` | 1 | `"1"` |
| `single_card` | 1 | `"1"` |
| `three_card` | 3 | `"1"`、`"2"`、`"3"` |

### daily_card 示例

```json
{
  "question": null,
  "spread_type": "daily_card",
  "cards": [
    {
      "card_id": "major_00",
      "name_zh": "愚者",
      "position": "1",
      "orientation": "upright"
    }
  ],
  "user_history": null
}
```

### single_card 示例

```json
{
  "question": "我现在最需要关注什么？",
  "spread_type": "single_card",
  "cards": [
    {
      "card_id": "major_07",
      "name_zh": "战车",
      "position": "1",
      "orientation": "reversed"
    }
  ],
  "user_history": null
}
```

### three_card 示例

```json
{
  "question": "最近工作发展如何？",
  "spread_type": "three_card",
  "cards": [
    {
      "card_id": "major_07",
      "name_zh": "战车",
      "position": "1",
      "orientation": "reversed"
    },
    {
      "card_id": "major_17",
      "name_zh": "星星",
      "position": "2",
      "orientation": "upright"
    },
    {
      "card_id": "major_19",
      "name_zh": "太阳",
      "position": "3",
      "orientation": "upright"
    }
  ],
  "user_history": null
}
```

`position` 只用于区分卡牌顺序。

Agent 内部负责把序号转换为语义化位置。

如果本文档其他位置存在旧的 `daily_guidance`、`core`、`past`、`present` 或 `future` 示例，以本节规则为准。

---


## 1. 协议目的

本文档定义 LunaArc Backend 与 Tarot Agent 之间的最终对接方式。

核心原则：

- Backend 负责 HTTP、抽牌、数据校验、数据库和错误转换；
- Agent 负责用户意图分析、牌阵规划、牌义解读和回答生成；
- Backend 只通过一个入口调用 Agent；
- Agent 不直接操作 FastAPI、数据库或前端状态。

---

## 2. Agent 目录结构

Agent 模块建议保持以下结构：

```text
agent/
├── __init__.py
├── llm.py
├── models.py
├── knowledge.py
├── safety.py
├── interpreter.py
├── tarot_agent.py
├── requirements.txt
└── .env.example
```

文件职责：

| 文件 | 职责 |
|---|---|
| `__init__.py` | 重导出 Agent 类与数据模型 |
| `llm.py` | LLM 配置、实例工厂和模型常量 |
| `models.py` | 请求和响应数据模型 |
| `knowledge.py` | 22 张大阿卡那牌义及牌面描述 |
| `safety.py` | 敏感内容检测 |
| `interpreter.py` | 单牌解读、综合叙事、摘要和建议 |
| `tarot_agent.py` | Agent 工作流编排 |
| `requirements.txt` | Agent 独立依赖 |
| `.env.example` | Agent 环境变量模板 |

---

## 3. 唯一调用入口

Backend 只允许调用：

```python
from agent.tarot_agent import (
    TarotAgent,
    ReadingRequest,
    DrawnCard,
)

agent = TarotAgent()

result = agent.generate_reading(request)
```

统一方法签名：

```python
class TarotAgent:
    def generate_reading(
        self,
        request: ReadingRequest,
    ) -> ReadingResponse:
        ...
```

Backend 不直接调用：

- 意图分类器；
- Spread Planner；
- Interpreter；
- Safety 模块；
- LangGraph 内部节点；
- Agent 内部的子任务。

Agent 内部可以自行编排，但对 Backend 只暴露 `generate_reading()`。

---

## 4. Agent 环境变量

真实 Agent 模式需要以下配置：

```env
OPENAI_API_KEY=实际API密钥
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_MODEL=deepseek-ai/DeepSeek-V3
```

字段说明：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `OPENAI_API_KEY` | LLM API Key，真实模式必填 | 无 |
| `OPENAI_BASE_URL` | OpenAI 兼容接口地址 | `https://api.siliconflow.cn/v1` |
| `OPENAI_MODEL` | 模型名称 | `deepseek-ai/DeepSeek-V3` |

Backend 额外使用：

```env
AGENT_MODE=mock
```

可选值：

| 值 | 说明 |
|---|---|
| `mock` | 使用 Backend Mock Agent，不调用 LLM |
| `real` | 调用真实 `TarotAgent` |

本地接入真实 Agent 时：

```env
AGENT_MODE=real
OPENAI_API_KEY=实际API密钥
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_MODEL=deepseek-ai/DeepSeek-V3
```

---

## 5. ReadingRequest 请求结构

Agent 提供的请求模型：

```python
class ReadingRequest(BaseModel):
    question: str | None = None

    spread_type: Literal[
        "daily_card",
        "single_card",
        "three_card",
    ]

    cards: list[DrawnCard]

    user_history: list[dict] | None = None
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| `question` | `str \| None` | 用户问题 |
| `spread_type` | 字符串枚举 | 牌阵类型 |
| `cards` | `list[DrawnCard]` | 已抽出的牌 |
| `user_history` | `list[dict] \| None` | 用户历史，可选 |

Agent 的 `ReadingRequest.model_validator` 负责校验：

- 牌数与牌阵是否匹配；
- 位置标识是否重复；
- 请求结构是否合法。

非法请求会在构造 `ReadingRequest` 时抛出 `ValueError`。

Backend 捕获后转换为 HTTP 400，不要求 Agent 返回 HTTP 错误。

---

## 6. DrawnCard 请求结构

```python
class DrawnCard(BaseModel):
    card_id: str
    name_zh: str
    position: str

    orientation: Literal[
        "upright",
        "reversed",
    ]
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| `card_id` | `str` | 卡牌唯一标识，如 `major_07` |
| `name_zh` | `str` | 中文牌名，如 `战车` |
| `position` | `str` | 卡牌顺序或原始位置标识 |
| `orientation` | 字符串枚举 | `upright` 正位或 `reversed` 逆位 |

---

## 7. position 字段规则

`position` 是 Backend 传给 Agent 的原始卡牌位置标识。

Agent 支持简单序号：

```text
1
2
3
```

也支持 Backend 当前使用的三牌标识：

```text
past
present
future
```

这些值只用于：

- 区分三张牌；
- 保持抽牌顺序；
- 供 Agent 内部进行语义位置映射。

Agent 不应直接把 Backend 的原始 `position` 当成最终展示文案。

Agent 内部的 Spread Planner 会根据用户意图重新生成语义位置。

例如事业问题可以映射为：

```text
past    → 当前工作状态
present → 潜在挑战
future  → 发展方向
```

例如关系问题可以映射为：

```text
past    → 当前关系状态
present → 关系阻碍因素
future  → 未来发展方向
```

Agent 返回的 `CardReading.position` 应使用映射后的语义化位置，可直接交给前端展示。

---

## 8. 牌阵规则

| spread_type | 牌数 | position 示例 |
|---|---:|---|
| `daily_card` | 1 | `1` 或 `daily_guidance` |
| `single_card` | 1 | `1` 或 `core` |
| `three_card` | 3 | `1/2/3` 或 `past/present/future` |

当前 LunaArc 产品核心流程主要使用：

```text
three_card
```

但 Backend 与 Agent 的数据模型仍兼容：

- `daily_card`
- `single_card`
- `three_card`

---

## 9. 三牌请求示例

```json
{
  "question": "最近工作发展如何？",
  "spread_type": "three_card",
  "cards": [
    {
      "card_id": "major_07",
      "name_zh": "战车",
      "position": "1",
      "orientation": "reversed"
    },
    {
      "card_id": "major_17",
      "name_zh": "星星",
      "position": "2",
      "orientation": "upright"
    },
    {
      "card_id": "major_19",
      "name_zh": "太阳",
      "position": "3",
      "orientation": "upright"
    }
  ],
  "user_history": null
}
```

Agent 内部可以将以上三张牌动态规划为：

```text
当前工作状态
潜在挑战
发展方向
```

Backend 不负责生成这些语义位置。

---

## 10. 卡牌知识职责

真实 Agent 自己维护：

```text
agent/knowledge.py
```

其中包含：

- 22 张大阿卡那；
- 正位关键词；
- 逆位关键词；
- 牌面画面描述；
- 人物、动作、色彩和象征元素；
- 每张牌约 150 至 250 字的画面描述。

因此，Backend 调用真实 Agent 时只传：

```text
card_id
name_zh
position
orientation
```

Backend 不向真实 Agent 传：

```text
core_symbolism
upright_keywords
reversed_keywords
```

避免 Backend 牌库与 Agent `knowledge.py` 出现两套牌义和版本不一致。

Backend 的 `tarot_cards.json` 主要用于：

- 抽牌；
- 前端展示；
- Mock Agent；
- 基础卡牌数据接口。

真实 Agent 的解读依据以 `knowledge.py` 为准。

---

## 11. Agent 工作流职责

Agent 内部负责以下步骤：

```text
用户请求
  ↓
意图分析
  ↓
牌阵规划
  ↓
路由决策
  ├── research
  ├── clarify
  └── redirect
  ↓
查询知识库
  ↓
并行解读
  ↓
自我反思与修正
  ↓
三牌综合叙事
  ↓
生成建议
  ↓
生成摘要
```

Backend 不参与上述推理过程。

---

## 12. 意图分类

Agent 可以把用户问题归类为：

| 意图类别 | 典型场景 |
|---|---|
| `relationship` | 恋爱、婚姻、伴侣、人际和家庭 |
| `career` | 工作、事业、学业、面试、项目和创业 |
| `self_growth` | 自我探索、情绪、人生意义和成长 |
| `trend` | 运势、趋势和未来发展 |
| `general` | 其他通用问题 |

意图分类由 Agent 内部完成。

Backend 不新增 `reading_type` 字段，也不判断问题属于哪一类。

---

## 13. 路由决策

Agent 支持三条路径。

### research

问题适合塔罗解读，继续执行：

- 查知识库；
- 解读；
- 自我反思；
- 综合叙事；
- 建议；
- 摘要。

### clarify

用户问题过于模糊。

例如：

```text
我怎么办？
帮帮我。
```

Agent 返回一句温和追问，引导用户下次抽牌前提出更具体的问题。

由于当前前后端没有追加问题流程：

- clarify 路径直接结束；
- 不继续解读本次牌面；
- 不要求用户在当前会话继续补充。

### redirect

用户问题与塔罗无关。

例如：

```text
帮我写代码。
翻译这段英文。
帮我解数学题。
```

Agent 返回温和婉拒并直接结束。

---

## 14. 敏感内容处理

敏感内容采用教育引导策略，不采用硬拦截。

包括但不限于：

- 医疗；
- 法律；
- 投资；
- 其他需要专业判断的问题。

Agent 可以继续解读牌面，但需要：

- 在摘要中加入边界提示；
- 引导用户关注内心感受和行动选择；
- 不提供专业诊断或确定结论；
- 不承诺塔罗能够预测确定结果。

敏感内容路径下：

```text
status = success
```

不向 Backend 暴露单独错误码。

---

## 15. ReadingResponse 返回结构

```python
class ReadingResponse(BaseModel):
    status: Literal["success"]
    summary: str
    card_readings: list[CardReading]
    synthesis: str | None = None
    advice: list[str]
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | `"success"` | 固定值 |
| `summary` | `str` | 一句话摘要或追问/婉拒文案 |
| `card_readings` | `list[CardReading]` | 每张牌的解读 |
| `synthesis` | `str \| None` | 三牌综合叙事 |
| `advice` | `list[str]` | 2 至 5 条行动建议 |

---

## 16. CardReading 返回结构

```python
class CardReading(BaseModel):
    card_id: str
    position: str
    interpretation: str
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| `card_id` | `str` | 卡牌唯一标识 |
| `position` | `str` | Agent 生成的语义化位置 |
| `interpretation` | `str` | 完整单牌解读 |

---

## 17. 正常返回示例

```json
{
  "status": "success",
  "summary": "当前的停滞并非终点，而是在提醒你重新校准方向。",
  "card_readings": [
    {
      "card_id": "major_07",
      "position": "当前工作状态",
      "interpretation": "战车逆位呈现出力量尚未汇聚到同一方向的画面……"
    },
    {
      "card_id": "major_17",
      "position": "潜在挑战",
      "interpretation": "星星的水流与夜空提示你仍保有希望，但需要避免把希望停留在想象中……"
    },
    {
      "card_id": "major_19",
      "position": "发展方向",
      "interpretation": "太阳带来的光亮表明，当目标重新清晰后，行动将更坦然有力……"
    }
  ],
  "synthesis": "三张牌共同讲述了从方向混乱、重新找回信念，到走向清晰行动的过程。",
  "advice": [
    "先明确当前最重要的一个职业目标。",
    "把长期愿景拆成可以在两周内完成的行动。",
    "结合现实信息判断，不要只依靠塔罗作出重要决定。"
  ]
}
```

---

## 18. clarify 返回规则

clarify 路径也返回 `ReadingResponse`：

```json
{
  "status": "success",
  "summary": "这个问题还比较宽泛。下次抽牌前，可以试着说明你最想解决的具体困惑。",
  "card_readings": [],
  "synthesis": null,
  "advice": []
}
```

---

## 19. redirect 返回规则

redirect 路径也返回 `ReadingResponse`：

```json
{
  "status": "success",
  "summary": "这个问题更适合使用专业工具处理。塔罗更适合帮助你探索感受、选择和行动方向。",
  "card_readings": [],
  "synthesis": null,
  "advice": []
}
```

---

## 20. Backend 职责

Backend 负责：

- FastAPI 接口；
- 接收前端请求；
- 参数基础校验；
- 抽牌；
- 构造 Agent 的 `ReadingRequest`；
- 调用 `TarotAgent.generate_reading()`；
- 把 Agent 数据模型转换为 Backend 响应模型；
- 数据库存储；
- 历史记录；
- CORS；
- HTTP 和 WebSocket 错误转换；
- Mock / Real Agent 模式切换。

---

## 21. Agent 职责

Agent 负责：

- 用户意图分析；
- 问题类型判断；
- 动态牌阵规划；
- 路由决策；
- 牌义和牌面画面查询；
- 单牌或多牌解读；
- 多牌并行调用；
- 自我反思；
- 解读修正；
- 综合叙事；
- 建议生成；
- 摘要生成；
- 敏感内容教育式降级；
- LLM 异常回退。

---

## 22. Backend Adapter 要求

真实 Agent 模式下，Backend 必须使用 Agent 自己的数据模型：

```python
from agent.tarot_agent import (
    TarotAgent,
    ReadingRequest as AgentReadingRequest,
    DrawnCard as AgentDrawnCard,
)
```

Backend 需要将自己的请求模型转换为 Agent 模型：

```python
agent_cards = [
    AgentDrawnCard(
        card_id=card.card_id,
        name_zh=card.name_zh,
        position=card.position,
        orientation=card.orientation,
    )
    for card in request.cards
]

agent_request = AgentReadingRequest(
    question=request.question,
    spread_type=request.spread_type,
    cards=agent_cards,
    user_history=request.user_history,
)

result = agent.generate_reading(agent_request)
```

Backend 不直接把普通字典传给真实 Agent。

---

## 23. 错误处理

Agent 请求模型校验失败：

```text
ValueError
```

Backend 转换为：

```json
{
  "detail": {
    "error_code": "INVALID_AGENT_REQUEST",
    "message": "具体校验错误"
  }
}
```

建议 HTTP 状态码：

```text
400
```

Agent 模块无法导入、初始化失败或返回格式错误：

```json
{
  "detail": {
    "error_code": "AGENT_UNAVAILABLE",
    "message": "Agent 暂时不可用"
  }
}
```

建议 HTTP 状态码：

```text
503
```

Agent 内部普通 LLM 异常由 Agent 自身回退，不应导致 Backend 崩溃。

---

## 24. 最终数据流

```text
Frontend
  ↓
Backend API
  ↓
抽取塔罗牌
  ↓
构造 AgentReadingRequest
  ↓
TarotAgent.generate_reading()
  ↓
AgentReadingResponse
  ↓
Backend 保存数据库
  ↓
返回 Frontend
```

---

## 25. 最终约束

Backend 与 Agent 的稳定接口字段为：

```text
question
spread_type
cards
user_history
```

每张牌字段为：

```text
card_id
name_zh
position
orientation
```

Agent 返回字段为：

```text
status
summary
card_readings
synthesis
advice
```

除非 Backend 和 Agent 双方同时确认，不再单方面修改这些字段。
