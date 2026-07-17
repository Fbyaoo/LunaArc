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

后端负责：

- HTTP 接口；
- 参数校验；
- 数据库保存；
- 错误处理；
- 前端接口。


Agent 负责：

- 理解用户问题；
- 分析塔罗牌信息；
- 判断三张牌之间的关系；
- 生成自然语言解读。


---

# 2. 系统职责划分

整体流程：

```
Frontend

↓

Backend

↓

Draw Service
抽取三张牌

↓

Tarot Service
补充牌义信息

↓

Agent

↓

Reading Result

↓

Database
```

---

# 3. Backend 提供给 Agent 的信息

Backend 不负责决定解读方式。

Backend 只提供事实信息：

包括：

- 用户问题；
- 三牌阵类型；
- 三张牌信息；
- 每张牌基础牌义；
- 用户历史记录（可选）。


Agent 根据这些信息自主决定：

- 如何理解问题；
- 如何组织三张牌关系；
- 如何生成回答结构。

---

# 4. Request Structure

## DrawnCard

```python
class DrawnCard(BaseModel):

    card_id: str

    name_zh: str

    position_number: int

    orientation: Literal[
        "upright",
        "reversed"
    ]
```

字段说明：

|字段|说明|
|-|-|
|card_id|塔罗牌唯一 ID|
|name_zh|中文名称|
|position_number|第几张牌|
|orientation|正位/逆位|


注意：

Backend 使用：

```
position_number
```

表示：

```
第1张
第2张
第3张
```

不使用：

```
past
present
future
```

因为牌位解释由 Agent 决定。

---

## ReadingRequest

```python
class ReadingRequest(BaseModel):

    question: str

    spread_type: Literal[
        "three_card"
    ]

    cards: list[DrawnCard]

    user_history: list[dict] | None = None
```

---

# 5. Request Example

```json
{
  "question": "我是否适合接受这份实习？",

  "spread_type": "three_card",

  "cards": [
    {
      "card_id": "major_00",
      "name_zh": "愚者",
      "position_number": 1,
      "orientation": "upright"
    },
    {
      "card_id": "major_01",
      "name_zh": "魔术师",
      "position_number": 2,
      "orientation": "reversed"
    },
    {
      "card_id": "major_02",
      "name_zh": "女祭司",
      "position_number": 3,
      "orientation": "upright"
    }
  ],

  "user_history": null
}
```

---

# 6. Card Metadata

Backend 会额外提供完整牌义信息。

示例：

```json
{
  "card_id": "major_00",

  "name_zh": "愚者",

  "orientation": "upright",

  "core_symbolism": [
    "开始",
    "冒险",
    "自由",
    "未知"
  ],

  "upright_keywords": [
    "探索",
    "机会"
  ],

  "reversed_keywords": [
    "冲动",
    "准备不足"
  ]
}
```

Agent 不需要维护自己的塔罗牌库。

---

# 7. Three Card Rule

当前 MVP 固定：

```
spread_type = three_card
```

表示：

```
三张牌解读
```

Backend 保证：

- 一定返回三张牌；
- 每张牌包含完整信息。


Agent 自主决定：

例如：

## 方案 1

```
过去
现在
未来
```

或者：

## 方案 2

```
情况
挑战
建议
```

或者：

## 方案 3

```
优势
阻碍
机会
```


Backend 不限制具体解释模板。

---

# 8. Response Structure

```python
class CardReading(BaseModel):

    card_id: str

    interpretation: str



class ReadingResponse(BaseModel):

    status: Literal["success"]

    summary: str

    card_readings: list[CardReading]

    synthesis: str | None = None

    advice: list[str]
```

---

# 9. Response Example

```json
{
  "status": "success",

  "summary":
  "整体趋势显示这是一个需要谨慎评估的新机会。",

  "card_readings": [
    {
      "card_id": "major_00",
      "interpretation":
      "愚者代表新的开始和探索机会。"
    },
    {
      "card_id": "major_01",
      "interpretation":
      "魔术师逆位提示需要关注准备不足的问题。"
    },
    {
      "card_id": "major_02",
      "interpretation":
      "女祭司提醒用户相信直觉并深入思考。"
    }
  ],

  "synthesis":
  "三张牌共同反映用户面对选择时的状态变化。",

  "advice": [
    "结合现实信息评估机会。",
    "不要仅依靠塔罗作出重要决定。"
  ]
}
```

---

# 10. Agent Responsibility

Agent 负责：

- 理解用户问题；
- 分析牌面含义；
- 分析三张牌之间关系；
- 决定解读结构；
- 生成自然语言回答；
- 安全降级。


---

# 11. Backend Responsibility

Backend 负责：

- FastAPI 路由；
- HTTP 请求处理；
- 参数校验；
- 三牌抽取；
- 塔罗数据查询；
- Agent 调用；
- 数据库存储；
- CORS；
- 返回结果。


---

# 12. Agent 不负责

Agent 不负责：

- FastAPI；
- HTTP 状态码；
- 图片上传；
- 摄像头；
- 数据库；
- 前端展示；
- 抽牌逻辑。


---

# 13. Integration Requirement

Agent 同学交付：

```
agent/
├── __init__.py
├── tarot_agent.py
└── requirements.txt
```

必须支持：

```python
from agent.tarot_agent import TarotAgent


agent = TarotAgent()


result = agent.generate_reading(
    request
)
```

---

# 14. Single Entry Rule

Backend 只能调用：

```python
TarotAgent.generate_reading()
```

禁止：

Backend 直接调用多个子 Agent。


Agent 内部可以自行：

- Prompt 管理；
- 多模型调用；
- 任务拆分；

但是对 Backend 只暴露一个统一入口。

---

# 15. Current Status

当前：

|模块|状态|
|-|-|
|Backend API|Ready|
|Tarot Data|Ready|
|Database|Ready|
|Agent Adapter|Ready|
|Agent Model|Waiting|
|Gesture Integration|Ready|

真实 Agent 接入后：

Frontend API 不需要修改。