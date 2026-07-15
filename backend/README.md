# LunaArc Backend

LunaArc 塔罗项目后端，基于 FastAPI 开发。

## 当前功能

- `GET /api/health`：健康检查
- `GET /api/cards`：获取塔罗牌基础数据
- `POST /api/detect`：上传图片并识别塔罗牌
- `POST /api/readings`：根据问题、牌阵和卡牌生成解读
- CORS 支持本地前端开发
- pytest 自动化接口测试

目前视觉识别和 Agent 均为 Mock 实现，后续替换为真实模块。

## 环境要求

- Python 3.10+
- macOS、Linux 或 Windows

## 本地启动

进入后端目录：

```bash
cd backend