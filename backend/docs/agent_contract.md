# Agent 对接协议

## 1. 唯一入口

后端只调用：

~~~python
from agent.tarot_agent import (
    TarotAgent,
    ReadingRequest,
    DrawnCard,
)

agent = TarotAgent()
result = agent.generate_reading(request)
~~~

Agent 不负责 HTTP、FastAPI、数据库、CORS 和前端展示。

## 2. 后端请求结构

~~~python
class DrawnCard(BaseModel):
    card_id: str
    name_zh: str
    position: str
    orientation: Literal["upright", "reversed"]


class ReadingRequest(BaseModel):
    question: str | None = None
    spread_type: Literal[
        "daily_card",
        "single_card",
        "three_card",
    ]
    cards: list[DrawnCard]
    user_history: list[dict] | None = None
~~~

## 3. 三牌请求示例

~~~json
{
  "question": "最近工作发展如何？",
  "spread_type": "three_card",
  "cards": [
    {
      "card_id": "major_07",
      "name_zh": "战车",
      "position": "past",
      "orientation": "reversed"
    },
    {
      "card_id": "major_17",
      "name_zh": "星星",
      "position": "present",
      "orientation": "upright"
    },
    {
      "card_id": "major_19",
      "name_zh": "太阳",
      "position": "future",
      "orientation": "upright"
    }
  ],
  "user_history": null
}
~~~

`position` 只是三张牌的区分标识。

当前后端可以传：

~~~text
past
present
future
~~~

Agent 内部的 Spread Planner 会根据用户意图，把这些标识转换成语义化位置，例如：

~~~text
当前工作状态
潜在挑战
发展方向
~~~

## 4. Agent 内部职责

Agent 负责：

- 意图分析；
- 问题分类；
- 动态牌阵规划；
- research / clarify / redirect 路由；
- 查询 Agent 自己的 knowledge.py；
- 单牌或多牌解读；
- 自我反思与修正；
- 综合叙事；
- 行动建议；
- 摘要生成；
- 敏感内容教育式降级。

后端不再给真实 Agent 注入：

- core_symbolism；
- upright_keywords；
- reversed_keywords。

真实 Agent 使用自己的 knowledge.py。

## 5. 返回结构

~~~python
class CardReading(BaseModel):
    card_id: str
    position: str
    interpretation: str


class ReadingResponse(BaseModel):
    status: Literal["success"]
    summary: str
    card_readings: list[CardReading]
    synthesis: str | None = None
    advice: list[str]
~~~

追问或婉拒路径下：

- status 仍为 success；
- summary 为追问或婉拒文本；
- card_readings 为空；
- synthesis 为 null；
- advice 为空。

## 6. Agent 模式

后端支持两种模式：

~~~text
AGENT_MODE=mock
AGENT_MODE=real
~~~

mock：

- 不调用 LLM；
- 用于 pytest、CI 和前端早期联调。

real：

- 调用 agent.tarot_agent.TarotAgent；
- 需要安装 Agent 依赖；
- 需要配置 OPENAI_API_KEY。

## 7. 真实 Agent 环境变量

~~~text
AGENT_MODE=real
OPENAI_API_KEY=实际密钥
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_MODEL=deepseek-ai/DeepSeek-V3
~~~

## 8. 交付要求

Agent 目录需要包含：

~~~text
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
~~~

后端只依赖唯一入口：

~~~python
TarotAgent.generate_reading()
~~~
