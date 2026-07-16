# 视觉识别模块对接协议

## 1. 调用方式

第一版视觉模型与后端运行在同一个 Python 项目或 Docker 环境中。

视觉模块对后端只暴露一个统一入口：

```python
class TarotCardDetector:
    def detect_cards(
        self,
        image_bytes: bytes,
        filename: str | None = None,
    ) -> list[RawDetection]:
        ...
```

后端负责接收上传文件、校验文件类型、过滤低置信度结果和生成 HTTP 响应。

视觉模块只负责识别图片中的塔罗牌。

## 2. 输入要求

### `image_bytes`

- 类型：`bytes`
- 内容：完整图片二进制数据
- 支持格式：JPG、PNG、WebP
- 图片最大体积由后端限制，当前为 10 MB

### `filename`

- 类型：`str | None`
- 仅用于日志和调试
- 视觉模块不得依赖固定文件名完成识别

如果模型内部必须使用文件路径，应由视觉模块自行创建和清理临时文件，不要求 FastAPI 路由处理。

## 3. 原始识别结果

```python
from typing import Literal

from pydantic import BaseModel, Field


class RawDetection(BaseModel):
    class_id: int
    confidence: float = Field(ge=0, le=1)
    orientation: Literal["upright", "reversed"]
    bbox: list[float] | None = None
```

返回示例：

```json
[
  {
    "class_id": 0,
    "confidence": 0.95,
    "orientation": "upright",
    "bbox": [120.5, 80.2, 460.8, 690.1]
  }
]
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| `class_id` | `int` | 模型类别编号 |
| `confidence` | `float` | 置信度，范围为 0 到 1 |
| `orientation` | `str` | `upright` 正位或 `reversed` 逆位 |
| `bbox` | `list[float] \| None` | 可选，顺序为 `x1, y1, x2, y2` |

## 4. 数据映射职责

视觉模型只需要返回：

```text
class_id
confidence
orientation
bbox
```

后端负责完成：

```text
class_id
→ card_id
→ 中文名
→ 英文名
→ 卡牌基础数据
```

视觉模块不要自行维护另一份中文名、英文名或卡牌含义数据，避免多套映射不一致。

双方必须统一类别映射，例如：

```text
0 → major_00 → 愚者
1 → major_01 → 魔术师
2 → major_02 → 女祭司
```

视觉同学交付时必须同时提供完整的类别编号表。

## 5. 多张牌规则

接口必须支持一张图片识别零张、一张或多张牌。

没有识别到塔罗牌时返回：

```python
[]
```

不要返回 `None`，也不要返回虚构的默认卡牌。

识别到多张牌时，返回多个 `RawDetection`：

```json
[
  {
    "class_id": 0,
    "confidence": 0.95,
    "orientation": "upright",
    "bbox": [10, 20, 200, 400]
  },
  {
    "class_id": 1,
    "confidence": 0.91,
    "orientation": "reversed",
    "bbox": [220, 20, 410, 400]
  }
]
```

## 6. 正逆位规则

视觉模块负责判断正位或逆位，并统一返回：

```text
upright
reversed
```

不得返回：

```text
正位
逆位
up
down
normal
```

如果当前模型无法可靠判断正逆位，必须提前告知后端，不得固定返回 `upright` 伪装成识别结果。

届时后端和前端将增加用户手动确认流程。

## 7. 置信度规则

视觉模块返回原始置信度，不自行删除低置信度结果。

后端根据配置：

```env
MIN_CONFIDENCE=0.60
```

统一进行过滤。

置信度必须是 0 到 1 之间的浮点数，例如：

```text
0.95
```

不要返回百分数字符串，例如：

```text
95%
```

## 8. 异常处理

推荐视觉模块提供以下异常：

```python
class VisionError(Exception):
    pass


class InvalidImageError(VisionError):
    pass


class VisionInferenceError(VisionError):
    pass
```

使用场景：

- 图片无法解析：`InvalidImageError`
- 模型加载或推理失败：`VisionInferenceError`

视觉模块不要返回 FastAPI 的 `HTTPException`，HTTP 状态码由后端转换。

## 9. 职责边界

视觉模块负责：

- 加载模型；
- 解析图片；
- 检测塔罗牌；
- 返回类别编号；
- 返回置信度；
- 判断正逆位；
- 可选返回边界框。

视觉模块不负责：

- FastAPI 路由；
- CORS；
- 用户登录；
- 数据库；
- 卡牌中文名和含义；
- Agent 解读；
- 前端展示。

## 10. 交付结构

视觉同学交付时建议提供：

```text
vision/
├── __init__.py
├── detector.py
├── exceptions.py
├── requirements.txt
└── README.md
```

其中必须可以这样调用：

```python
from vision.detector import TarotCardDetector

detector = TarotCardDetector()

results = detector.detect_cards(
    image_bytes=image_bytes,
    filename=filename,
)
```

如果模型权重文件不上传 GitHub，必须在 `README.md` 中说明：

- 权重文件名称；
- 下载或获取方式；
- 放置目录；
- 模型初始化方式；
- 所需 Python 版本和依赖。

视觉模块内部可以使用 YOLO 或其他模型，但对后端只暴露一个统一入口。
