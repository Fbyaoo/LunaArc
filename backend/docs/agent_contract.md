# Agent 对接协议

## 1. 调用方式

第一版 Agent 与后端在同一个 Python 项目中运行。

Agent 对后端只暴露一个统一入口：

```python
class TarotAgent:
    def generate_reading(
        self,
        request: ReadingRequest,
    ) -> ReadingResponse:
        ...
```

后端负责 HTTP、参数校验和错误响应；Agent 只负责生成解读。

## 2. 请求结构

```python
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
```

请求示例：

```json
{
  "question": "我是否适合接受这份实习？",
  "spread_type": "three_card",
  "cards": [
    {
      "card_id": "major_00",
      "name_zh": "愚者",
      "position": "past",
      "orientation": "upright"
    },
    {
      "card_id": "major_01",
      "name_zh": "魔术师",
      "position": "present",
      "orientation": "reversed"
    },
    {
      "card_id": "major_02",
      "name_zh": "女祭司",
      "position": "future",
      "orientation": "upright"
    }
  ],
  "user_history": null
}
```

## 3. 返回结构

```python
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
```

返回示例：

```json
{
  "status": "success",
  "summary": "整体趋势积极，但当前需要谨慎判断。",
  "card_readings": [
    {
      "card_id": "major_00",
      "position": "past",
      "interpretation": "过去存在新的尝试。"
    }
  ],
  "synthesis": "三张牌共同反映了从尝试到重新判断的过程。",
  "advice": [
    "确认岗位职责和成长空间。",
    "结合现实信息作出决定。"
  ]
}
```

## 4. 牌阵规则

| spread_type | 牌数 | position |
|---|---:|---|
| `daily_card` | 1 | `daily_guidance` |
| `single_card` | 1 | `core` |
| `three_card` | 3 | `past`、`present`、`future` |

## 5. 职责边界

Agent 负责：

- 理解用户问题；
- 解读每张牌；
- 综合多张牌之间的关系；
- 返回结构化结果；
- 对不适合确定回答的问题进行安全降级。

Agent 不负责：

- FastAPI 路由；
- HTTP 状态码；
- 图片上传；
- 数据库；
- CORS；
- 前端展示。

## 6. 接入要求

Agent 同学交付时应提供：

```text
agent/
├── __init__.py
├── tarot_agent.py
└── requirements.txt
```

其中必须可以这样调用：

```python
from agent.tarot_agent import TarotAgent

agent = TarotAgent()
result = agent.generate_reading(request)
```

不得要求后端直接调用多个子 Agent。Agent 内部可以自行编排，但对后端只暴露一个入口。
