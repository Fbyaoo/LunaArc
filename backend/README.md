# LunaArc Backend

LunaArc 塔罗项目后端，基于 FastAPI 开发。

## 当前功能

- `GET /api/health`：健康检查
- `GET /api/cards`：获取塔罗牌基础数据
- `POST /api/detect`：上传图片并返回 Mock 识别结果
- `POST /api/readings`：根据问题、牌阵和卡牌生成 Mock 解读
- 支持本地前端 CORS
- 提供 pytest 自动化接口测试

目前视觉识别和 Agent 均为 Mock 实现，后续只替换 `services` 层，不修改前端 API。

## 环境要求

- Python 3.10+

## 本地启动

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
fastapi dev app/main.py
```

服务地址：`http://127.0.0.1:8000`

Swagger 文档：`http://127.0.0.1:8000/docs`

## 运行测试

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## 主要接口

### `GET /api/cards`

返回塔罗牌基础数据。

### `POST /api/detect`

使用 `multipart/form-data` 上传字段名为 `file` 的 JPG、PNG 或 WebP 图片。

### `POST /api/readings`

请求示例：

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

支持的牌阵：

| spread_type | 牌数 | 说明 |
|---|---:|---|
| `daily_card` | 1 | 每日塔罗，不强制填写问题 |
| `single_card` | 1 | 单牌问答 |
| `three_card` | 3 | 过去、现在、未来 |

## 项目结构

```text
backend/
├── app/
│   ├── api/          # FastAPI 路由
│   ├── data/         # 塔罗牌基础数据
│   ├── schemas/      # Pydantic 请求和响应模型
│   ├── services/     # Agent 与视觉模块适配层
│   └── main.py
├── tests/
├── requirements.txt
└── requirements-dev.txt
```

## 模块对接

Agent 对后端暴露统一入口：

```python
TarotAgent.generate_reading(request)
```

视觉模块对后端暴露统一入口：

```python
VisionService.detect_cards(image_bytes, filename)
```

真实模块接入后，仅替换对应服务层实现，保持现有 HTTP API 不变。