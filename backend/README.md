# LunaArc Backend

LunaArc 塔罗应用后端，基于 FastAPI、SQLAlchemy 和 Pydantic。

## 已实现能力

- JWT Access Token 与可撤销、可轮换的 Refresh Token
- 用户注册、登录、退出、账户资料、订阅状态
- 每日免费解读额度和 Plus 无限额度
- 日签、单牌、三牌抽牌与解读
- 用户隔离的占卜历史
- Mock/Real Agent 适配层及三牌追问流程
- 图片上传校验和视觉模块适配层
- 手势识别 WebSocket
- Alembic 数据库迁移、Docker 启动和自动化测试

卡牌图片识别目前仍使用 Mock 实现；手势识别使用 `vision/` 下的 YOLO 模型。

## 环境要求

- Python 3.12（CI 和 Docker 使用的版本）
- SQLite（本地默认）或 PostgreSQL（生产推荐）

## 本地启动

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
fastapi dev app/main.py
```

服务地址为 `http://127.0.0.1:8000`，Swagger 文档位于 `/docs`。

若本地已有通过旧版 `create_all` 创建的数据库，应先备份数据，再执行一次：

```bash
alembic stamp head
```

之后所有结构变更均通过 `alembic upgrade head` 应用。

## 测试

```bash
python -m pytest -q
python -m unittest -q vision.test.test_gesture_contract
python -m compileall -q app agent vision
```

## 关键配置

完整示例见 `.env.example`。

| 环境变量 | 说明 |
|---|---|
| `ENVIRONMENT` | `development`、`test` 或 `production` |
| `DATABASE_URL` | SQLAlchemy 数据库连接地址 |
| `JWT_SECRET_KEY` | JWT 密钥；生产环境至少 32 位 |
| `REFRESH_COOKIE_SECURE` | HTTPS 生产环境必须为 `true` |
| `DEFAULT_DAILY_READING_LIMIT` | 免费用户每日解读次数 |
| `AGENT_MODE` | `mock` 或 `real` |
| `OPENAI_API_KEY` | Real Agent 模式必填 |
| `VISION_MODEL_PATH` | 手势模型路径；空值使用仓库内默认模型 |

生产环境启动时会拒绝默认 JWT 密钥或不安全的 Refresh Cookie 配置。

## 主要接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| POST | `/api/auth/register` | 注册并登录 |
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/refresh` | 轮换 Refresh Token |
| POST | `/api/auth/logout` | 注销 Refresh Token |
| GET | `/api/users/me` | 当前用户资料和剩余额度 |
| GET | `/api/subscriptions/me` | 当前订阅 |
| GET | `/api/usage/me` | 当日使用量 |
| GET | `/api/cards` | 塔罗牌数据 |
| POST | `/api/draw` | 随机抽牌 |
| POST | `/api/readings` | 解读已有牌面 |
| POST | `/api/draw-and-read` | 抽牌并解读 |
| POST | `/api/readings/clarify` | 补充三牌追问信息 |
| GET | `/api/history` | 当前用户历史 |
| POST | `/api/detect` | 上传卡牌图片 |
| WS | `/ws/gesture` | 手势识别事件流 |

除健康检查、卡牌数据、抽牌、图片识别和认证入口外，用户相关接口均要求 Bearer Access Token。

## Docker

```bash
docker build -t lunaarc-backend .
docker run --env-file .env -p 8000:8000 lunaarc-backend
```

容器启动时会先执行数据库迁移，再启动 API。

默认镜像包含真实 Agent 依赖。需要手势推理时构建完整视觉镜像：

```bash
docker build --build-arg INSTALL_VISION=true -t lunaarc-backend-vision .
```

卡牌视觉的 Real 模式遵循 `docs/vision_contract.md`，并要求视觉模块提供 `vision.detector.TarotCardDetector`；仓库当前模型只用于手势识别。
