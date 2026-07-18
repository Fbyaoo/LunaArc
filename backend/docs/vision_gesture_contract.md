# 手势视觉模块对接协议

## 1. 模块职责

视觉模块负责识别前端摄像头画面中的手势，并输出统一的手势事件。

当前 YOLO 模型负责以下静态手势识别：

| gesture | 含义 |
|---|---|
| `fist` | 握拳 |
| `one` | 食指向上 |
| `ok` | OK 手势 |
| `peace` | Peace 手势 |

视觉模块不负责：

- 塔罗牌牌面识别；
- `card_id` 生成；
- 洗牌、抽牌和牌阵逻辑；
- Agent 调用；
- 数据库存储；
- 用户状态管理；
- 前端摄像头开启。

视觉模块只回答：

> 当前画面中检测到了什么手势？

---

## 2. 系统调用链

```text
前端摄像头
  ↓
WebSocket 发送图片帧
  ↓
后端接收图片二进制
  ↓
VisionService.process_frame(image_bytes)
  ↓
gesture_event
  ↓
GestureAdapter
  ↓
业务动作
  ↓
Tarot Workflow
  ↓
Agent
```

---

## 3. 后端调用接口

视觉模块必须对后端提供统一入口：

```python
from vision import VisionService

vision_service = VisionService(
    model_path="models/best_gesture.pt"
)

events = vision_service.process_frame(
    image_bytes
)
```

方法签名：

```python
class VisionService:
    def process_frame(
        self,
        image_bytes: bytes,
    ) -> list[dict]:
        ...
```

参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `image_bytes` | `bytes` | 前端摄像头当前帧的图片二进制数据 |

返回值：

```python
list[dict]
```

没有稳定识别到手势时必须返回：

```json
[]
```

返回空数组是正常情况，不代表模块调用失败。

---

## 4. 手势事件协议

视觉模块输出的是手势事件，不是业务事件。

完整示例：

```json
[
  {
    "type": "gesture_event",
    "source": "gesture",
    "detector": "yolo",
    "gesture": "peace",
    "confidence": 0.94,
    "timestamp": 1712345678.123,
    "bbox": [
      120.5,
      80.2,
      460.8,
      690.1
    ],
    "payload": {
      "class_id": 3,
      "gesture": "peace",
      "description": "Peace 手势",
      "confidence": 0.94,
      "bbox": [
        120.5,
        80.2,
        460.8,
        690.1
      ]
    }
  }
]
```

---

## 5. 事件字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `type` | `string` | 固定为 `gesture_event` |
| `source` | `string` | 固定为 `gesture` |
| `detector` | `string` | 检测器来源，例如 `yolo` |
| `gesture` | `string` | 手势语义 |
| `confidence` | `float` | 模型置信度，范围为 0 到 1 |
| `timestamp` | `float` | Unix 时间戳，单位为秒 |
| `bbox` | `list[float]` 或 `null` | 检测框，顺序为 `[x1, y1, x2, y2]` |
| `payload` | `object` | 调试用原始信息，业务层不应强依赖 |

---

## 6. 手势名称要求

当前只允许输出以下静态手势名称：

```text
fist
one
ok
peace
```

不得使用其他命名方式，例如：

```text
Fist
open_fist
number_one
victory
yes
```

如果模型类别发生变化，必须先同步后端协议。

---

## 7. 手势与业务动作边界

视觉模块只输出：

```json
{
  "gesture": "peace"
}
```

视觉模块不得输出：

```json
{
  "gesture": "peace",
  "action": "reset"
}
```

业务动作由后端映射。

当前后端映射为：

| gesture | 后端 action | 含义 |
|---|---|---|
| `fist` | `shuffle` | 洗牌 |
| `one` | `switch_spread` | 切换牌阵 |
| `ok` | `request_reading` | 请求解读 |
| `peace` | `reset` | 重置流程 |

视觉模块不应依赖这份业务映射。

后续即使业务动作发生变化，也不应重新训练视觉模型。

---

## 8. 模型文件

默认模型路径：

```text
models/best_gesture.pt
```

当前模型类别映射：

```python
{
    0: "fist",
    1: "one",
    2: "ok",
    3: "peace",
}
```

如果重新训练模型导致类别顺序变化，只修改视觉模块内部映射：

```text
vision/mappings.py
```

后端不得直接依赖 YOLO 原始 `class_id`。

---

## 9. 置信度要求

`confidence` 必须来自模型实际输出，不得写死。

范围：

```text
0.0 到 1.0
```

示例：

```json
{
  "gesture": "ok",
  "confidence": 0.92
}
```

表示模型认为当前检测框属于 `ok` 手势的可信度约为 92%。

不得返回百分数字符串：

```json
{
  "confidence": "92%"
}
```

---

## 10. 置信度阈值

视觉模块当前建议使用两层阈值：

| 位置 | 默认值 | 作用 |
|---|---:|---|
| `GestureDetector.confidence_threshold` | `0.25` | 过滤 YOLO 原始低置信度检测框 |
| `GestureEventEngine.confidence_threshold` | `0.75` | 低于该值不触发最终手势事件 |

推荐处理链：

```text
YOLO 原始检测
  ↓
confidence >= 0.25
  ↓
进入稳定性判断
  ↓
confidence >= 0.75
  ↓
触发 gesture_event
```

后端只处理最终输出的 `gesture_event`。

---

## 11. 稳定识别与防抖

摄像头会连续发送大量图片帧。

为了避免同一个手势连续触发业务动作，视觉模块必须提供防抖机制。

建议默认参数：

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `stable_frames` | `5` | 连续 5 帧识别为同一手势后才触发 |
| `cooldown_seconds` | `1.5` | 同一手势触发后 1.5 秒内不重复触发 |

因此，以下返回是正常的：

```json
[]
```

只有稳定识别后才返回非空事件列表：

```json
[
  {
    "type": "gesture_event",
    "gesture": "ok",
    "confidence": 0.91
  }
]
```

后端不要把每一帧都当成一次业务动作。

---

## 12. 多手势检测

如果一帧中检测到多个有效手势，可以返回多个事件：

```json
[
  {
    "type": "gesture_event",
    "gesture": "fist",
    "confidence": 0.91
  },
  {
    "type": "gesture_event",
    "gesture": "peace",
    "confidence": 0.88
  }
]
```

视觉模块应保证每个事件字段完整。

业务层是否处理多个事件，由后端决定。

---

## 13. 前端摄像头职责

视觉模块本身不负责开启摄像头。

前端负责：

- 请求摄像头权限；
- 显示摄像头预览；
- 控制采样帧率；
- 将视频帧转换成图片；
- 通过 WebSocket 发送图片二进制。

推荐链路：

```text
navigator.mediaDevices.getUserMedia()
  ↓
video / canvas 截帧
  ↓
转换为 Blob 或 ArrayBuffer
  ↓
WebSocket 发送
  ↓
后端
  ↓
VisionService.process_frame()
```

---

## 14. WebSocket 接口

后端 WebSocket 地址：

```text
ws://127.0.0.1:8000/ws/gesture
```

前端发送内容：

```text
图片二进制数据
```

后端调用：

```python
events = vision_service.process_frame(
    image_bytes
)
```

后端返回示例：

```json
{
  "gesture": {
    "type": "gesture_event",
    "source": "gesture",
    "detector": "yolo",
    "gesture": "peace",
    "confidence": 0.94,
    "timestamp": 1712345678.123,
    "bbox": null,
    "payload": {}
  },
  "action": {
    "gesture": "peace",
    "action": "reset"
  },
  "workflow": {
    "state": "idle",
    "action": "reset",
    "message": "重置流程"
  }
}
```

其中：

- `gesture` 来自视觉模块；
- `action` 由后端映射；
- `workflow` 由后端业务状态服务生成。

视觉模块只负责第一部分。

---

## 15. YOLO 与 MediaPipe 兼容

YOLO 和 MediaPipe 可以同时存在，但必须输出统一事件结构。

推荐原则：

```text
YOLO 原始结果
MediaPipe 原始结果
其他模型原始结果
  ↓
统一转换为 gesture_event
  ↓
后端只消费 gesture_event
```

MediaPipe 示例：

```json
{
  "type": "gesture_event",
  "source": "gesture",
  "detector": "mediapipe",
  "gesture": "swipe_left",
  "confidence": 0.88,
  "timestamp": 1712345678.123,
  "bbox": null,
  "payload": {}
}
```

后端不直接消费：

- YOLO `class_id`；
- MediaPipe landmarks；
- 模型内部张量；
- 模型私有对象。

---

## 16. 异常处理

建议视觉模块定义统一异常：

```python
class VisionError(Exception):
    pass


class InvalidImageError(VisionError):
    pass


class VisionModelLoadError(VisionError):
    pass


class VisionInferenceError(VisionError):
    pass
```

使用场景：

| 异常 | 场景 |
|---|---|
| `InvalidImageError` | 图片字节无法解析 |
| `VisionModelLoadError` | 模型文件不存在或加载失败 |
| `VisionInferenceError` | 模型推理过程失败 |

视觉模块不要抛出 FastAPI 的 `HTTPException`。

HTTP 和 WebSocket 错误响应由后端处理。

---

## 17. 视觉模块交付结构

视觉同学提交时建议使用：

```text
vision/
├── __init__.py
├── service.py
├── detector.py
├── event_engine.py
├── mappings.py
├── exceptions.py
├── models/
│   └── best_gesture.pt
├── requirements.txt
└── README.md
```

必须保证后端可以执行：

```python
from vision import VisionService

vision_service = VisionService(
    model_path="models/best_gesture.pt"
)

events = vision_service.process_frame(
    image_bytes
)
```

---

## 18. 视觉模块不得提交的内容

不要提交：

```text
__pycache__/
*.pyc
.venv/
.pytest_cache/
```

不要把完整后端项目复制到：

```text
vision/backend/
```

视觉目录只应包含视觉模块自身代码、模型和测试。

视觉模块的测试文件名应避免和后端测试重名。

不建议使用：

```text
test_api.py
test_draw.py
```

建议使用：

```text
test_gesture_detector.py
test_gesture_service.py
test_gesture_event_engine.py
```

---

## 19. 本地测试要求

视觉模块至少需要提供以下测试：

### 模型加载测试

```text
确认 best_gesture.pt 可以成功加载
```

### 单张图片测试

```text
输入测试图片
输出手势识别结果
```

### 空结果测试

```text
没有检测到稳定手势时返回 []
```

### 事件结构测试

```text
输出必须符合 gesture_event 协议
```

推荐运行方式：

```bash
python tests/test_vision_image.py tests/test_images/example.jpg
```

或者：

```bash
python -m pytest vision/tests -q
```

---

## 20. 集成检查清单

视觉同学提交前必须确认：

- [ ] 模块只识别手势，不识别塔罗牌；
- [ ] 不输出 `card_id`；
- [ ] 不输出塔罗牌名称；
- [ ] 不执行抽牌；
- [ ] 不调用 Agent；
- [ ] 不修改数据库；
- [ ] 不输出业务 `action`；
- [ ] 输出统一 `gesture_event`；
- [ ] `gesture` 使用约定名称；
- [ ] `confidence` 范围为 0 到 1；
- [ ] 无稳定结果返回 `[]`；
- [ ] 已实现稳定帧判断；
- [ ] 已实现冷却时间；
- [ ] 已说明模型文件路径；
- [ ] 已提供 `requirements.txt`；
- [ ] 已提供模型初始化方式；
- [ ] 没有复制完整后端工程；
- [ ] 测试文件不会与后端测试重名。

---

## 21. 当前后端状态

后端已经完成：

- Gesture WebSocket；
- Gesture Schema；
- Gesture Adapter；
- Gesture 到业务动作映射；
- Tarot Workflow；
- 三牌抽取；
- Agent 对接；
- 数据库存储；
- 历史记录接口。

当前等待：

- 真实 `VisionService` 接入；
- 前端摄像头 WebSocket 联调；
- 模型端到端测试。

---

## 22. 最终约束

视觉模块唯一职责：

```text
图片帧
  ↓
识别手势
  ↓
返回 gesture_event
```

后端职责：

```text
gesture_event
  ↓
映射业务动作
  ↓
控制塔罗流程
  ↓
调用 Agent
  ↓
保存结果
```

视觉模块不得重新实现后端已有业务逻辑。
