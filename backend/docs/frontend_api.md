# LunaArc Frontend API Contract

## Overview

本文档用于前端与后端接口联调。

前端只需要调用 Backend API，不直接访问：

- Agent
- Vision Model
- Database

调用链：

```
Frontend
    |
    ↓
FastAPI Backend
    |
    ├── Vision Adapter
    |
    └── Agent Adapter
```

---

# Base URL

本地开发环境：

```
http://127.0.0.1:8000
```

Swagger API 文档：

```
http://127.0.0.1:8000/docs
```

---

# 用户完整流程

标准占卜流程：

```
1. 获取塔罗牌数据
        |
        ↓
2. 用户输入问题
        |
        ↓
3. 用户上传图片
        |
        ↓
4. 后端识别卡牌
        |
        ↓
5. 用户确认识别结果
        |
        ↓
6. 请求 AI 解读
        |
        ↓
7. 展示解读结果
```

---

# API List

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | 服务健康检查 |
| GET | `/api/cards` | 获取塔罗牌基础数据 |
| POST | `/api/detect` | 图片识别塔罗牌 |
| POST | `/api/readings` | 生成塔罗解读 |

---

# 1. Health Check

## Request

```
GET /api/health
```

## Response

```json
{
  "status": "ok"
}
```

---

# 2. 获取塔罗牌数据

## Request

```
GET /api/cards
```

## Response

```json
[
  {
    "card_id": "major_00",
    "class_id": 0,
    "name_en": "The Fool",
    "name_zh": "愚者",
    "image": "/cards/major_00.png",
    "upright_keywords": [
      "开始",
      "自由",
      "冒险"
    ],
    "reversed_keywords": [
      "冲动",
      "迟疑",
      "风险"
    ]
  }
]
```

字段说明：

| Field | Type | Description |
|---|---|---|
| card_id | string | 后端统一卡牌 ID |
| class_id | int | 模型类别编号 |
| name_zh | string | 中文名称 |
| image | string | 前端图片路径 |

---

# 3. 图片识别卡牌

## Request

```
POST /api/detect
```

Content-Type:

```
multipart/form-data
```

上传字段：

```
file
```

注意：

字段名必须为：

```
file
```

---

## Frontend Example

```javascript
const formData = new FormData();

formData.append(
    "file",
    imageFile
);


fetch(
    "http://127.0.0.1:8000/api/detect",
    {
        method: "POST",
        body: formData
    }
);
```

---

## Success Response

```json
{
  "status": "success",
  "filename": "card.jpg",
  "cards": [
    {
      "class_id": 0,
      "card_id": "major_00",
      "name_zh": "愚者",
      "orientation": "upright",
      "confidence": 0.95
    }
  ]
}
```

---

## Detection Result Fields

| Field | Type | Description |
|---|---|---|
| class_id | int | 模型类别编号 |
| card_id | string | 卡牌 ID |
| name_zh | string | 中文名称 |
| orientation | string | 正逆位 |
| confidence | float | 识别置信度 |

orientation:

```
upright
```

表示：

```
正位
```

---

# 识别结果确认流程

识别完成后：

不要直接调用 `/api/readings`。

推荐：

```
识别结果
    ↓
用户确认
    ↓
生成解读
```

用户可以：

- 确认卡牌
- 修改正逆位
- 重新上传图片

---

# 4. 请求 AI 解读

## Request

```
POST /api/readings
```

Content-Type:

```
application/json
```

---

## Request Body

```json
{
  "question": "我是否适合接受这份实习？",

  "spread_type": "single_card",

  "cards": [
    {
      "card_id": "major_00",
      "name_zh": "愚者",
      "position": "core",
      "orientation": "upright"
    }
  ],

  "user_history": null
}
```

---

# Spread Types

| spread_type | Cards | Description |
|---|---:|---|
| daily_card | 1 | 每日塔罗 |
| single_card | 1 | 单牌问答 |
| three_card | 3 | 三牌牌阵 |

---

# Card Position

## single_card

```text
core
```

---

## three_card

三个位置：

```text
past
present
future
```

示例：

```json
[
 {
  "position":"past"
 },
 {
  "position":"present"
 },
 {
  "position":"future"
 }
]
```

---

# Reading Response

## Success

```json
{
  "status": "success",

  "summary":
  "整体解读结果",

  "card_readings": [
    {
      "card_id": "major_00",
      "position": "core",
      "interpretation":
      "这张牌代表新的开始"
    }
  ],

  "synthesis":
  "综合分析",

  "advice": [
    "建议一",
    "建议二"
  ]
}
```

---

# Response Fields

| Field | Type | Description |
|---|---|---|
| summary | string | 总体结论 |
| card_readings | array | 每张牌解释 |
| synthesis | string | 多牌综合分析 |
| advice | array | 行动建议 |

---

# Error Handling

统一错误格式：

```json
{
  "detail": {
    "error_code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

---

# Error Codes

## EMPTY_QUESTION

用户没有输入问题。

HTTP:

```
400
```

---

## INCOMPLETE_DRAW

牌数量不足。

HTTP:

```
400
```

---

## UNSUPPORTED_IMAGE_TYPE

图片格式不支持。

HTTP:

```
415
```

---

## IMAGE_TOO_LARGE

图片超过大小限制。

HTTP:

```
413
```

---

# Frontend Rules

## 禁止

不要：

```
Frontend
    ↓
YOLO
```

不要：

```
Frontend
    ↓
Agent
```

---

## 正确

必须：

```
Frontend
    ↓
Backend API
    ↓
Vision / Agent
```

---

# Current Status

当前：

| Module | Status |
|---|---|
| Backend API | Ready |
| Vision | Mock |
| Agent | Mock |
| Database | Not integrated |

真实模型接入后：

前端接口保持不变。