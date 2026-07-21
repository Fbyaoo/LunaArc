# LunaArc 前后端联调协议（课程展示版）

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

本地 Base URL：`http://127.0.0.1:8000`

Swagger：`http://127.0.0.1:8000/docs`

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
    "advice": ["..."]
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

## 6. 刷新与退出

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

课程现场使用默认 `AGENT_MODE=mock`，由内置牌义规则生成离线解读，不依赖外网或第三方模型。若要展示真实 AI 解读，再配置 `AGENT_MODE=real` 和 `OPENAI_API_KEY`。
