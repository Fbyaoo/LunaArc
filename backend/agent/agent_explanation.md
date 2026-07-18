# 塔罗解读 Agent

基于 LLM 的塔罗牌解读智能体，对后端暴露唯一入口 `TarotAgent.generate_reading()`。

## 目录结构

```
agent/
├── __init__.py             # 包入口，重导出 TarotAgent 与数据模型
├── llm.py                  # 环境配置 + LLM 实例工厂 + 常量映射
├── models.py               # 数据模型（DrawnCard / ReadingRequest / ReadingResponse 等）
├── knowledge.py            # 塔罗知识库（22张大阿卡那的牌义关键词 + 画面描述）
├── safety.py               # 敏感内容检测 is_sensitive()
├── interpreter.py          # 解读引擎（牌面解读、综合叙事、摘要生成、行动建议）
├── tarot_agent.py          # Agent 编排核心（状态图 + 牌阵规划 + 意图分析 + 路由决策 + 反思修正）
├── requirements.txt        # Python 依赖
└── .env.example            # 环境变量模板
```

## 环境配置

### 1. 创建 `.env` 文件

复制模板并填入实际的 API Key：

```bash
cp .env.example .env
```

编辑 `.env`：

```
OPENAI_API_KEY=你的API密钥
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | LLM API 密钥（必填） | — |
| `OPENAI_BASE_URL` | API 端点地址 | `https://api.deepseek.com/v1` |
| `OPENAI_MODEL` | 模型名称 | `deepseek-chat` |

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

依赖列表：`pydantic>=2.5.0`、`openai>=1.6.1`、`python-dotenv>=1.0.0`、`langchain>=0.3.0`、`langchain-openai>=0.3.0`、`langgraph>=0.2.0`。

## 接入方式

```python
from agent.tarot_agent import TarotAgent, ReadingRequest, DrawnCard

agent = TarotAgent()

request = ReadingRequest(
    question="最近工作发展如何？",
    spread_type="single_card",
    cards=[
        DrawnCard(
            card_id="major_07",
            name_zh="战车",
            position="1",
            orientation="reversed",
        ),
    ],
)

result = agent.generate_reading(request)
print(result.model_dump_json(indent=2))
```

Agent 不负责 HTTP、数据库等基础设施层。牌数与位置合法性由 `ReadingRequest.model_validator` 在构造阶段校验；后端只需构造请求对象并调用 `generate_reading()` 即可，非法参数会在调用前抛出 `ValueError`。

## Agent 工作流

Agent 基于 LangGraph 状态图驱动，整体流程如下：

```
用户请求
  │
  ▼
┌─────────────────┐
│ ① 意图分析       │  LLM 一句话提炼用户真实诉求
│   analyze_intent│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ② 牌阵规划       │  根据 spread_type 分配语义化位置标签
│   plan_spread   │  单牌用固定映射，三牌按意图动态生成
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│ ③ 路由决策        │  LLM 自主判断问题类型，分派到三条路径之一
│   route_dispatch │
└───┬───┬───┬──────┘
    │   │   │
    │   │   └── redirect ──► 婉拒：问题与塔罗无关（如"帮我写代码"）
    │   │                    → 返回温柔婉拒消息 → END
    │   │
    │   └──── clarify ───► 追问：问题过于模糊（如"我怎么办"）
    │                      → 生成一句追问引导用户下次抽牌前提出更具体的问题 → END
    │
    └──── research ──► 正常解读路径（继续）
                        │
                        ▼
              ┌──────────────────┐
              │ ④ 查询知识库      │  查牌义关键词 + 牌面画面描述
              │   research_cards │  注入到后续 LLM prompt 中
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ ⑤ 并行解读        │  单牌同步调用，多牌线程池并行
              │   interpret      │  LLM 先描绘画面，再给出启示
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ ⑥ 自我反思        │  审核解读质量（画面描绘/启示相关性/牌义融合）
              │   self_reflect   │
              └───┬───┬───┬──────┘
                  │   │   │
                  │   │   └── refine_* ──► 专项修正后回到 ⑥（最多 2 轮）
                  │   │
                  │   └──── force ──────► 超轮次放弃修正，直接推进
                  │
                  └──── pass ──► 质量合格
                                  │
                                  ▼
                        ┌──────────────────┐
                        │ ⑦ 综合叙事        │  仅 three_card：串联多张牌
                        │   synthesize     │  编织成有起承转合的故事
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ ⑧ 生成建议        │  LLM 输出1-2条行动建议
                        │   gen_advice     │  
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ ⑨ 生成摘要        │  LLM 一句话凝练核心启示
                        │   gen_summary    │  → END
                        └──────────────────┘
```

### 关键节点说明

#### ① 意图分析（`analyze_intent`）

始终执行，不依赖路由。LLM 读取用户问题，用一句话提炼背后真实诉求（如"用户担忧职业发展瓶颈"），同时调用 `classify_intent` 将问题归类为五大意图之一。单牌场景（`daily_card` / `single_card`）的意图分类结果不会影响牌阵规划（牌阵规划直接使用固定映射），但仍会注入到解读 prompt 中作为参考上下文。

| 意图类别 | 触发场景 |
|----------|----------|
| `relationship` | 恋爱、婚姻、伴侣、感情、人际、家庭关系、友谊 |
| `career` | 工作、事业、职场、学业、面试、项目、创业 |
| `self_growth` | 自我探索、内在成长、情绪困扰、人生意义、性格 |
| `trend` | 运势、趋势、未来发展、时间线预测 |
| `general` | 不属以上类别的通用问题 |

#### ② 牌阵规划（`plan_spread`）

根据 `spread_type` 为每张牌生成语义化的位置标签。后端传入的 `position`（`"1"`/`"2"`/`"3"`）仅作牌序标识，Agent 内部将其映射为对应语义：

**单牌场景**：不经过 LLM 意图分析，直接使用固定语义映射：

| spread_type | 位置语义 |
|---|---|
| `daily_card` | 当日主题 |
| `single_card` | 关键指引 |

**三牌场景**：LLM 先分析意图类别，再根据意图选择对应的三位置语义：

| 意图 | "1" 位置 | "2" 位置 | "3" 位置 |
|------|----------|----------|----------|
| 关系 | 当前关系状态 | 关系阻碍因素 | 未来发展方向 |
| 事业 | 当前工作状态 | 潜在挑战 | 发展方向 |
| 自我成长 | 当前内心状态 | 成长阻碍 | 蜕变方向 |
| 运势/通用 | 过去 | 现在 | 未来 |

> 语义化标签会写入 `CardReading.position` 返回给前端，可直接展示给用户。

#### ③ 路由决策（`route_dispatch`）

LLM 自主判断用户问题该走哪条路径，三种可能：

- **research**（正常解读）：问题在塔罗范围内，继续后续流程。敏感内容（医疗/法律/投资）强制走此路径，由下游 safety 模块做教育引导。
- **clarify**（追问）：问题过于模糊或宽泛（如仅说"我怎么办""帮帮我"），生成一句温和追问引导用户**下次抽牌前提出更具体的问题**。由于前后端未实现允许用户在原有问题上追加细节的逻辑，追问中不会提及本次已抽到的牌面信息，也不会让用户补充细节，只引导用户下次更具体地提问。**直接结束**，不消耗后续解读资源。
- **redirect**（婉拒）：问题属于纯工具性请求（如"帮我写代码""翻译这段英文""给我做饭谱""解这道数学题"），返回温柔婉拒消息，**直接结束**。

#### ④ 查询知识库（`research_cards`）

从 `knowledge.py` 查询每张牌的两类知识：
1. **牌义关键词**：正位/逆位的核心含义（如愚人正位："新的开始、冒险精神、天真无畏、无限可能"）
2. **牌面画面描述**：22张韦特塔罗的详细画面文字描述（人物姿态、服饰色彩、背景环境、象征符号、整体氛围），约 150-250 字/张

两类知识均注入到后续 LLM 解读 prompt 中。LLM 被明确要求参考提供的画面描述来描绘牌面，不要自己编造画面细节，从而避免幻觉。

#### ⑤ 并行解读（`interpret`）

对每张牌调用 LLM 生成解读。单牌场景直接同步调用；多牌场景（`three_card`）使用线程池并行请求以降低延迟。解读 prompt 中包含：
- 牌的语义化位置标签（由 ② 生成）
- 用户核心诉求（由 ① 生成）
- 牌义关键词 + 画面描述（由 ④ 注入）
- 用户原始问题（如有）

LLM 被要求先用诗意的语言描绘牌面画面，再自然过渡到该位置下的启示。

#### ⑥ 自我反思（`self_reflect`）

解读完成后 LLM 从三个维度审核质量（1-5分）：

| 维度 | 评估内容 |
|------|----------|
| 画面描绘力 | 是否生动描绘了牌面细节（人物、动作、色彩、氛围） |
| 启示相关性 | 是否紧密结合用户问题与牌的位置含义 |
| 牌义融合度 | 是否巧妙融入了牌的传统含义 |

- 三项均 ≥4 分 → **pass**，进入综合叙事
- 某项最低 → 进入对应专项修正（`refine_visual` / `refine_relevance` / `refine_symbolism`），修正后回到反思重审
- 已修正 2 轮仍不达标 → **force**，放弃修正直接推进

#### ⑦ 综合叙事（`synthesize`）

仅 `three_card` 执行。LLM 将多张牌的解读串联成一段有起承转合的叙事，揭示牌面之间的内在呼应。`daily_card` 和 `single_card` 跳过此节点，`synthesis` 返回 `null`。

#### ⑧ 生成建议（`gen_advice`）

LLM 输出 1-2 条行动建议。敏感内容场景下引导用户关注内心感受而非寻求专业结论。

#### ⑨ 生成摘要（`gen_summary`）

LLM 用一句话凝练整体启示。敏感内容场景下摘要前自动添加免责前缀 `"塔罗映照内心，但无法替代专业判断。"`。

## 接口概要

### 请求结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `question` | `str \| None` | 用户问题，可为空（`daily_card` 场景通常为空） |
| `spread_type` | `"daily_card"` / `"single_card"` / `"three_card"` | 牌阵类型 |
| `cards` | `list[DrawnCard]` | 已抽牌列表 |
| `user_history` | `list[dict] \| None` | 用户历史（可选） |

> `ReadingRequest` 内置 `model_validator` 校验牌数与位置匹配关系，非法参数在构造阶段即抛出 `ValueError`。

`DrawnCard` 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `card_id` | `str` | 牌唯一标识（如 `"major_07"`） |
| `name_zh` | `str` | 牌中文名（如 `"战车"`） |
| `position` | `str` | 后端传入的牌序标识，`"1"`/`"2"`/`"3"`，仅作区分用 |
| `orientation` | `"upright"` / `"reversed"` | 正位 / 逆位 |

### 牌阵规则

| spread_type | 牌数 | position（必须） | 位置语义映射 |
|------|------|------|------|
| `daily_card` | 1 | `"1"` | "当日主题" |
| `single_card` | 1 | `"1"` | "关键指引" |
| `three_card` | 3 | `"1"`、`"2"`、`"3"` | 由意图分析动态决定（见上文②） |

> **`position` 字段说明**：后端仅需传入 `"1"` / `"2"` / `"3"` 作为牌序标识。具体语义（如"当前工作状态""关系阻碍因素""当日主题"等）完全由 Agent 内部根据 `spread_type` 和意图分析自动生成，降低了后端与 Agent 的耦合度。语义化标签会写入 `CardReading.position` 返回给前端展示。

### 返回结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | `"success"` | 固定值，不暴露错误码 |
| `summary` | `str` | 一句话摘要（追问/婉拒路径下即为对应消息） |
| `card_readings` | `list[CardReading]` | 每张牌的解读（追问/婉拒路径下为空列表） |
| `synthesis` | `str \| None` | 综合叙事，仅 `three_card` 有值，`daily_card`/`single_card` 为 `null` |
| `advice` | `list[str]` | 行动建议列表（追问/婉拒路径下为空列表） |

`CardReading` 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `card_id` | `str` | 牌唯一标识，与请求中的 `card_id` 对应 |
| `position` | `str` | 语义化位置标签（如"当日主题""关键指引""当前工作状态"等），可直接展示给用户 |
| `interpretation` | `str` | 该牌的完整解读文本（约 200 字） |

### 返回示例

**正常解读（single_card）**：
```json
{
  "status": "success",
  "summary": "逆位的战车提醒你，有时放慢脚步比强行突破更有智慧。",
  "card_readings": [
    {
      "card_id": "major_07",
      "position": "关键指引",
      "interpretation": "战车上的勇士紧握缰绳，黑白双兽朝不同方向拉扯……（完整解读）"
    }
  ],
  "synthesis": null,
  "advice": ["审视当前工作的真正瓶颈，而非一味向前冲。", "给自己留出反思和调整的空间。"]
}
```

**追问（clarify）**：
```json
{
  "status": "success",
  "summary": "下次抽牌前可以试着把你的困惑说得更具体一些，这样塔罗才能给你更有针对性的指引。",
  "card_readings": [],
  "synthesis": null,
  "advice": []
}
```

**婉拒（redirect）**：
```json
{
  "status": "success",
  "summary": "塔罗更擅长探索内心和人生方向，这个问题我可能帮不上忙。",
  "card_readings": [],
  "synthesis": null,
  "advice": []
}
```

### 敏感内容处理

采用**教育引导**策略而非硬拦截：LLM 检测到敏感问题（医疗/法律/投资等专业领域的实质性建议请求）后，仍会正常解读牌面（牌面本身对内心探索仍有价值），但会在摘要中加入免责提示、在综合解读和建议中引导用户关注内心感受而非寻求专业结论。`status` 始终为 `"success"`，不暴露错误码。

## 注意事项

- Agent 内部对多牌解读使用线程池并行调用 LLM（见 `interpreter.py` 的 `interpret_cards()`），`three_card` 场景下 3 张牌会并发请求以降低延迟；单牌场景直接同步调用，不启用线程池。
- 每次 LLM 调用均通过 `llm.py` 的 `make_llm()` 创建独立 `ChatOpenAI` 实例，保证线程安全。
- 所有 LLM 输出均有异常回退逻辑：解读失败时返回友好提示；摘要 / 综合 / 建议失败时均有默认回退文案，不会因 API 故障导致调用方崩溃。
- 敏感内容检测（`safety.py` 的 `is_sensitive()`）内部也调用 LLM 做语义分类（而非关键词匹配），LLM 失败时默认判定为敏感（宁严勿松），但不拦截请求——仅通过摘要前缀免责声明和建议引导进行教育式降级。
- 牌数与位置校验在 `models.py` 的 `ReadingRequest.model_validator` 中完成，调用 `generate_reading()` 前即可发现参数错误。
- 追问（clarify）和婉拒（redirect）路径会提前结束流程，不执行解读、反思、综合、建议等后续节点，节省 LLM 调用成本。
- `CardReading.position` 返回的是语义化标签（如"当日主题""关键指引"），而非后端传入的原始序号 `"1"`/`"2"`/`"3"`。
