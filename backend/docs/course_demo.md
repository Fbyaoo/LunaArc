# LunaArc 后端课程展示清单

## 展示前

```bash
cd backend
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env  # 仅首次执行
alembic upgrade head
python -m pytest -q
```

确认 `.env` 使用：

```env
ENVIRONMENT=development
AGENT_MODE=mock
```

离线规则解读无需 API Key，现场断网也能使用。

## 启动

终端一：

```bash
fastapi dev app/main.py
```

终端二：

```bash
python scripts/demo_backend.py
```

## 建议讲解顺序（5 分钟）

1. 打开 `/docs`，说明 FastAPI 自动接口文档。
2. 展示注册和 JWT 登录状态。
3. 展示 22 张大阿卡那牌库。
4. 提交三牌问题，展示随机抽牌、正逆位和逐牌解读。
5. 展示结果已写入个人历史。
6. 展示免费用户每日 3 次额度。
7. 展示 Refresh Token 轮换和退出。
8. 可选展示手势 WebSocket，不把它作为主流程依赖。

## 推荐讲解重点

- 每个用户只能看到自己的历史记录。
- 免费额度使用数据库原子扣减，避免并发绕过。
- Refresh Token 只能使用一次，旧 Token 重放会被拒绝。
- 数据库结构由 Alembic 管理。
- 默认离线解读保证课程现场稳定，也可以切换到真实 Agent。

## 现场故障预案

- 端口占用：使用 `fastapi dev app/main.py --port 8001`，演示脚本追加 `--base-url http://127.0.0.1:8001`。
- 演示账号额度已用完：演示脚本每次自动注册新账号。
- 外网不可用：保持 `AGENT_MODE=mock`。
- 数据库结构报错：备份旧数据库后运行 `alembic stamp head`；全新演示库直接运行 `alembic upgrade head`。

## 不属于课程展示范围

- 实体卡牌图片识别
- 正式支付和订阅回调
- Redis 多实例部署
- 生产监控、告警和邮件服务
