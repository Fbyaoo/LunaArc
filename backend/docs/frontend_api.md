# LunaArc 前后端联调协议（课程展示版）

> 最后更新：2026-07-22<br>
> 文档版本：v2（Reading Library、Saved Readings、AI Tarot Guide）

## 联调环境

- 最新后端联调地址：`http://118.31.173.218:8001`
- 最新 Swagger：`http://118.31.173.218:8001/docs`
- 旧版兼容服务：`http://118.31.173.218:8000`
- 本地开发地址：`http://127.0.0.1:8000`

前端新增功能应使用 `8001`。服务器拉取本次最新代码并重新部署后，Swagger 才会显示新增接口。

## 展示范围

课程展示采用系统随机抽牌，不需要上传图片或识别实体卡牌。标准流程为：

```text
注册或登录
  → 选择日签、单牌或三牌
  → 输入问题
  → POST /api/draw-and-read
  → 展示卡牌和解读
  → 查看今日额度与历史记录
```

`/api/detect` 是兼容保留接口，不属于课程展示主链路。

## 认证约定

注册或登录成功后，把响应中的 Access Token 放入后续请求：

```http
Authorization: Bearer <access_token>
```

Refresh Token 由后端写入 HttpOnly Cookie，前端不要读取。Access Token 过期时调用：

```http
POST /api/auth/refresh
```

跨域请求需要携带 Cookie：

```javascript
fetch(url, {
  method: "POST",
  credentials: "include"
});
```

## 接口总览

| 方法 | 路径 | 认证 | 用途 |
|---|---|---:|---|
| GET | `/api/health` | 否 | 健康检查 |
| POST | `/api/auth/register` | 否 | 注册并登录 |
| POST | `/api/auth/login` | 否 | 登录 |
| POST | `/api/auth/refresh` | Cookie | 刷新登录状态 |
| POST | `/api/auth/logout` | Cookie | 退出登录 |
| GET | `/api/users/me` | 是 | 当前用户信息 |
| GET | `/api/cards` | 否 | 获取牌库 |
| POST | `/api/draw` | 否 | 只抽牌，不生成解读 |
| POST | `/api/draw-and-read` | 是 | 抽牌、解读并保存 |
| POST | `/api/readings/clarify` | 是 | 回答三牌追问 |
| GET | `/api/readings/recent?limit=3` | 是 | 最近解读 |
| GET | `/api/readings` | 是 | 分页历史/收藏列表 |
| GET | `/api/readings/{reading_id}` | 是 | 解读详情 |
| PATCH | `/api/readings/{reading_id}` | 是 | 收藏或取消收藏 |
| POST | `/api/guide/sessions` | 是 | 创建 AI 向导会话 |
| GET | `/api/guide/sessions` | 是 | 向导会话列表 |
| GET/POST | `/api/guide/sessions/{session_id}/messages` | 是 | 获取/发送消息 |
| GET | `/api/usage/me` | 是 | 今日额度 |
| GET | `/api/history` | 是 | 当前用户历史 |
| GET | `/api/subscriptions/me` | 是 | 当前套餐 |
| WS | `/ws/gesture` | 否 | 可选手势展示 |

## 1. 注册

```http
POST /api/auth/register
Content-Type: application/json
```

```json
{
  "email": "student@example.com",
  "password": "CourseDemo123",
  "display_name": "演示用户"
}
```

成功响应：

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "student@example.com",
    "display_name": "演示用户",
    "plan": "free"
  }
}
```

## 2. 登录

```http
POST /api/auth/login
Content-Type: application/json
```

```json
{
  "email": "student@example.com",
  "password": "CourseDemo123"
}
```

响应结构与注册相同。

## 3. 抽牌并解读

课程展示优先使用聚合接口：

```http
POST /api/draw-and-read
Authorization: Bearer <access_token>
Content-Type: application/json
```

三牌请求：

```json
{
  "question": "我应该如何规划接下来的学习？",
  "spread_type": "three_card"
}
```

支持的牌阵：

| `spread_type` | 牌数 | 问题要求 |
|---|---:|---|
| `daily_card` | 1 | 可以为空 |
| `single_card` | 1 | 必填 |
| `three_card` | 3 | 必填 |

成功响应：

```json
{
  "cards": [
    {
      "card_id": "major_00",
      "name_zh": "愚者",
      "name_en": "The Fool",
      "position": "1",
      "orientation": "upright"
    }
  ],
  "reading": {
    "status": "success",
    "summary": "...",
    "card_readings": [],
    "synthesis": "...",
    "advice": ["..."],
    "reading_id": 1,
    "saved": false,
    "created_at": "2026-07-22T15:00:00"
  }
}
```

当 `reading.status` 为 `awaiting_clarify` 时，展示 `summary` 里的追问，并保留响应中的 `session_id`。

## 4. 回答追问

```http
POST /api/readings/clarify
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "session_id": "上一步返回的 session_id",
  "user_supplement": "我主要想了解学习和实习如何平衡"
}
```

## 5. 用量与历史

```http
GET /api/usage/me
Authorization: Bearer <access_token>
```

免费用户每日可完成 3 次解读，Plus 用户不限制。

```http
GET /api/history
Authorization: Bearer <access_token>
```

历史接口只返回当前用户的数据，并按时间倒序排列。

## 6. 解读历史、详情与收藏

```http
GET /api/readings/recent?limit=3
GET /api/readings?page=1&page_size=12&sort=-created_at
GET /api/readings?saved=true&page=1&page_size=30&sort=-created_at
GET /api/readings/{reading_id}
PATCH /api/readings/{reading_id}
```

收藏请求体为 `{"saved": true}`，取消收藏改为 `false`。详情会返回问题、牌面、正逆位、牌位、单牌解释、综合解释、建议和追问信息。访问其他用户的记录统一返回 `404`。

## 7. AI Tarot Guide

创建普通会话传 `{"reading_id": null}`，从某次解读进入则传对应数字 ID：

```http
POST /api/guide/sessions
```

返回 `session_id`。发送消息使用普通 HTTP：

```http
POST /api/guide/sessions/{session_id}/messages
Content-Type: application/json

{"content": "我今天可以先做什么？"}
```

返回一条 `role=assistant` 的消息；后端会同时保存用户消息和 Agent 回复。单条消息最多 2000 字，模型上下文读取最近 12 条消息，并自动加载关联 Reading。生产部署使用 `AGENT_MODE=real` 时会调用真实大模型。

## 8. 刷新与退出

```http
POST /api/auth/refresh
```

刷新成功后替换内存中的 Access Token。Refresh Token 会自动轮换。

```http
POST /api/auth/logout
```

退出后清除本地保存的 Access Token，并跳转登录页。

## 统一错误处理

业务错误通常位于：

```json
{
  "detail": {
    "error_code": "READING_LIMIT_REACHED",
    "message": "今日免费解读次数已用完。"
  }
}
```

前端至少处理：

| 状态码 | 含义 |
|---:|---|
| 400 | 问题或牌阵参数错误 |
| 401/403 | 登录失效或额度不足 |
| 409 | 邮箱已经注册 |
| 410 | 追问会话过期 |
| 422 | 请求字段校验失败 |
| 503 | Real Agent 暂时不可用 |

## 展示建议

正式联调和课程展示配置 `AGENT_MODE=real`、`OPENAI_API_KEY`、`OPENAI_BASE_URL` 和 `OPENAI_MODEL`，Reading 与 Guide 都会接入真实 AI。`mock` 仅供自动测试和断网应急演示。
