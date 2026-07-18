# 塔罗解读 Agent

基于 LLM 的塔罗牌解读智能体，对后端暴露唯一入口 `TarotAgent.generate_reading()`。采用诗意画面叙事风格，先描绘牌面细节再将画面转化为启示，温柔而坚定。

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
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_MODEL=deepseek-ai/DeepSeek-V3
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | LLM API 密钥（必填） | — |
| `OPENAI_BASE_URL` | API 端点地址 | `https://api.siliconflow.cn/v1` |
| `OPENAI_MODEL` | 模型名称 | `deepseek-ai/DeepSeek-V3` |

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
│ ① 意图分析       |  LLM 一句话提炼用户真实诉求
│   analyze_intent│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ② 牌阵规划       │  根据意图类别（关系/事业/成长/运势/通用）
│   plan_spread   │  动态生成三张牌的位置语义标签
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
                        │ ⑦ 综合叙事        │  仅 three_card：串联三张牌
                        │   synthesize     │  编织成有起承转合的故事
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ ⑧ 生成建议        │  LLM 输出 2-5 条行动建议
                        │   gen_advice     │  JSON 数组格式
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

始终执行，不依赖路由。LLM 读取用户问题，用一句话提炼背后真实诉求（如"用户担忧职业发展瓶颈"），同时调用 `classify_intent` 将问题归类为五大意图之一：

| 意图类别 | 触发场景 |
|----------|----------|
| `relationship` | 恋爱、婚姻、伴侣、感情、人际、家庭关系、友谊 |
| `career` | 工作、事业、职场、学业、面试、项目、创业 |
| `self_growth` | 自我探索、内在成长、情绪困扰、人生意义、性格 |
| `trend` | 运势、趋势、未来发展、时间线预测 |
| `general` | 不属以上类别的通用问题 |

#### ② 牌阵规划（`plan_spread`）

根据意图类别为三张牌动态生成语义化的位置标签，替代固定的"过去/现在/未来"：

| 意图 | past 位置 | present 位置 | future 位置 |
|------|-----------|-------------|-------------|
| 关系 | 当前关系状态 | 关系阻碍因素 | 未来发展方向 |
| 事业 | 当前工作状态 | 潜在挑战 | 发展方向 |
| 自我成长 | 当前内心状态 | 成长阻碍 | 蜕变方向 |
| 运势/通用 | 过去 | 现在 | 未来 |

#### ③ 路由决策（`route_dispatch`）

LLM 自主判断用户问题该走哪条路径，三种可能：

- **research**（正常解读）：问题在塔罗范围内，继续后续流程。敏感内容（医疗/法律/投资）强制走此路径，由下游 safety 模块做教育引导。
- **clarify**（追问）：问题过于模糊或宽泛（如仅说"我怎么办""帮帮我"），生成一句温和追问引导用户**下次抽牌前提出更具体的问题**。由于前后端未实现允许用户在原有问题上追加细节的逻辑，追问中不会提及本次已抽到的牌面信息，也不会让用户补充细节，只引导用户下次更具体地提问。**直接结束**，不消耗后续解读资源。
- **redirect**（婉拒）：问题属于纯工具性请求（如"帮我写代码""翻译这段英文""给我做饭谱""解这道数学题"），返回温柔婉拒消息，**直接结束**。

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

### 知识库注入

解读时 LLM 的 prompt 中会注入两类知识（来自 `knowledge.py`）：

1. **牌义关键词**：正位/逆位的核心含义（如愚人正位："新的开始、冒险精神、天真无畏、无限可能"）
2. **牌面画面描述**：22张韦特塔罗的详细画面文字描述（人物姿态、服饰色彩、背景环境、象征符号、整体氛围），约 150-250 字/张

LLM 被明确要求参考提供的画面描述来描绘牌面，不要自己编造画面细节，从而避免幻觉。

## 接口概要

### 请求结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `question` | `str \| None` | 用户问题，可为空 |
| `spread_type` | `"daily_card"` / `"single_card"` / `"three_card"` | 牌阵类型 |
| `cards` | `list[DrawnCard]` | 已抽牌列表 |
| `user_history` | `list[dict] \| None` | 用户历史（可选） |

> `ReadingRequest` 内置 `model_validator` 校验牌数与位置匹配关系，非法参数在构造阶段即抛出 `ValueError`。

`DrawnCard` 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `card_id` | `str` | 牌唯一标识 |
| `name_zh` | `str` | 牌中文名 |
| `position` | `str` | 后端传入的牌位标识 |
| `orientation` | `"upright"` / `"reversed"` | 正位 / 逆位 |

> **关于 `position` 字段**：由于 Agent 内部会通过牌阵规划（Spread Planner）根据用户意图动态生成语义化的位置标签，后端传入的 `past`/`present`/`future` 实际上仅作为位置区分标识使用，不会直接暴露给用户。**建议后端传入 `"1"`、`"2"`、`"3"` 等简单序号即可**，降低后端与 Agent 的耦合度。

### 牌阵规则

| spread_type | 牌数 | position（建议） |
|------|------|------|
| `daily_card` | 1 | `"1"` 或 `"daily_guidance"` |
| `single_card` | 1 | `"1"` 或 `"core"` |
| `three_card` | 3 | `"1"`、`"2"`、`"3"`（任意简单标识均可） |

### 返回结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | `"success"` | 固定值 |
| `summary` | `str` | 一句话摘要（追问/婉拒路径下即为对应消息） |
| `card_readings` | `list[CardReading]` | 每张牌的解读（追问/婉拒路径下为空列表） |
| `synthesis` | `str \| None` | 综合解读（仅 three_card） |
| `advice` | `list[str]` | 行动建议列表（追问/婉拒路径下为空列表） |

`CardReading` 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `card_id` | `str` | 牌唯一标识 |
| `position` | `str` | 映射后的语义化位置标签（如"当前关系状态""成长阻碍"等），可直接展示给用户 |
| `interpretation` | `str` | 该牌的完整解读文本 |

### 敏感内容处理

采用**教育引导**策略而非硬拦截：LLM 检测到敏感问题后，仍会正常解读牌面（牌面本身对内心探索仍有价值），但会在摘要中加入免责提示、在综合解读和建议中引导用户关注内心感受而非寻求专业结论。`status` 始终为 `"success"`，不暴露错误码。

## 注意事项

- Agent 内部对多牌解读使用线程池并行调用 LLM（见 `interpreter.py` 的 `interpret_cards()`），`three_card` 场景下 3 张牌会并发请求以降低延迟；单牌场景直接同步调用，不启用线程池。
- 每次 LLM 调用均通过 `llm.py` 的 `make_llm()` 创建独立 `ChatOpenAI` 实例，保证线程安全。
- 所有 LLM 输出均有异常回退逻辑：解读失败时返回友好提示；摘要 / 综合 / 建议失败时均有默认回退文案，不会因 API 故障导致调用方崩溃。
- 敏感内容检测（`safety.py` 的 `is_sensitive()`）内部也调用 LLM 做语义分类（而非关键词匹配），LLM 失败时默认判定为敏感（宁严勿松），但不拦截请求——仅通过摘要前缀免责声明和建议引导进行教育式降级。
- 牌数与位置校验在 `models.py` 的 `ReadingRequest.model_validator` 中完成，调用 `generate_reading()` 前即可发现参数错误。
- 追问（clarify）和婉拒（redirect）路径会提前结束流程，不执行解读、反思、综合、建议等后续节点，节省 LLM 调用成本。
