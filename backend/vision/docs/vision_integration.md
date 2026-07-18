# 手势识别模块对接说明

## 1. 模块职责

本模块负责识别前端摄像头画面中的手势，并输出统一的手势事件。

当前 YOLO 模型只负责静态手势识别：

| 手势 | 含义 |
|---|---|
| fist | 握拳 |
| one | 食指向上 |
| like | 点赞手势 |
| peace | Peace 手势 |

本模块不负责：

- 塔罗牌牌面识别；
- 洗牌、切换牌阵、请求解读、重置等业务状态修改；
- Agent 解读调用；
- 前端摄像头开启。

推荐链路：

```text
前端摄像头
  -> 后端 WebSocket 接收图片帧
  -> 调用 vision_service.process_frame(image_bytes)
  -> 得到 gesture_event
  -> 后端把 gesture 映射成业务动作
  -> 后端通知前端 / 调用 Agent
```

## 2. 模型文件

默认模型路径：

```text
vision/model/best_gesture.pt
```

当前模型类别：

```python
{
    0: "fist",
    1: "one",
    2: "like",
    3: "peace",
    4: "call",
    5: "dislike",
    6: "four",
    7: "ok",
    8: "palm",
    9: "rock",
    10: "stop",
    11: "three",
    12: "three2",
}
```

只有 `fist`、`one`、`like`、`peace` 会输出 `gesture_event`。

其他类别会被忽略，最终返回 `[]`，不需要额外输出 `none`。

如果后续重新训练模型，类别顺序发生变化，只需要修改：

```text
vision/mappings.py
```

## 3. 后端调用方式

后端可以直接 import：

```python
from vision import VisionService

vision_service = VisionService()
```

收到前端 WebSocket 传来的图片帧后：

```python
events = vision_service.process_frame(image_bytes)
```

参数说明：

| 参数 | 类型 | 说明 |
|---|---|---|
| image_bytes | bytes | 前端摄像头当前帧的图片二进制数据 |

返回值：

```python
list[dict]
```

没有稳定识别到手势时返回：

```json
[]
```

## 4. 输出事件协议

视觉模块输出的是“手势事件”，不是业务事件。

示例：

```json
[
  {
    "type": "gesture_event",
    "source": "gesture",
    "detector": "yolo",
    "gesture": "peace",
    "confidence": 0.94,
    "timestamp": 1712345678.123,
    "bbox": [120.5, 80.2, 460.8, 690.1],
    "payload": {
      "class_id": 3,
      "gesture": "peace",
      "description": "Peace 手势",
      "confidence": 0.94,
      "bbox": [120.5, 80.2, 460.8, 690.1]
    }
  }
]
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| type | string | 固定为 `gesture_event` |
| source | string | 固定为 `gesture` |
| detector | string | 当前为 `yolo`，后续 MediaPipe 可输出 `mediapipe` |
| gesture | string | 识别出的有效手势语义，例如 `fist`、`one`、`like`、`peace` |
| confidence | float | YOLO 对该检测框的置信度，范围 0 到 1 |
| timestamp | float | 事件生成时间，Unix 时间戳，单位秒 |
| bbox | list[float] \| null | 检测框，顺序为 `[x1, y1, x2, y2]` |
| payload | object | 调试用原始信息，后端业务一般不需要依赖它 |

## 5. 后端业务映射建议

建议由后端把 `gesture` 映射成业务动作：

| gesture | 建议业务动作 | 含义 |
|---|---|---|
| fist | shuffle | 洗牌 |
| one | switch_spread | 切换牌阵 |
| like | request_reading | 请求解读 |
| peace | reset | 重置 |

这样做的好处是：视觉模块只负责“看见了什么手势”，后端负责“这个手势在当前业务状态下意味着什么”。后续如果某个页面想把 `peace` 改成别的动作，不需要重新改视觉模型。

## 6. 置信度是怎么来的

`confidence` 来自 YOLO 模型输出，不是手写固定值。

简单理解：

```text
confidence = 模型认为这个检测框属于某个手势类别的可信程度
```

范围是：

```text
0.0 ~ 1.0
```

例如：

```json
{
  "gesture": "peace",
  "confidence": 0.94
}
```

表示 YOLO 认为这个检测框是 `peace` 手势的置信度约为 94%。

当前代码里有两层阈值：

| 位置 | 默认值 | 作用 |
|---|---:|---|
| `GestureDetector.confidence_threshold` | 0.25 | 过滤 YOLO 原始低置信度检测框 |
| `GestureEventEngine.confidence_threshold` | 0.75 | 低于该置信度不触发稳定手势事件 |

也就是说，模型可能识别出一个 0.4 的手势，但它不会触发最终 `gesture_event`。

## 7. 防抖机制

摄像头会连续发送多帧图片，如果每一帧都触发事件，后端和前端会重复执行动作。

因此模块内置防抖：

| 参数 | 默认值 | 说明 |
|---|---:|---|
| stable_frames | 5 | 连续 5 帧识别为同一手势才触发 |
| cooldown_seconds | 1.5 | 同一手势触发后 1.5 秒内不重复触发 |

所以：

- `process_frame()` 经常返回 `[]` 是正常现象；
- 只有返回非空数组时，后端才需要处理；
- 后端不要把每一帧都当作一次业务动作。

## 8. 是否开启摄像头实时检测

当前 `vision/` 模块本身不开摄像头。

它只提供这个能力：

```python
events = vision_service.process_frame(image_bytes)
```

也就是说，它接收一帧图片的二进制数据，然后返回识别事件。

摄像头实时采集通常由前端负责：

```text
前端 navigator.mediaDevices.getUserMedia()
  -> canvas / video 截帧
  -> WebSocket 发送图片 bytes 给后端
  -> 后端调用 VisionService
```

这样设计更适合 Web 项目，因为摄像头权限、画面预览、帧率控制都在浏览器前端更自然。

如果后续需要本地调试，也可以单独写一个 OpenCV 脚本直接打开电脑摄像头，但这不是当前后端对接必需项。

## 9. YOLO 和 MediaPipe 是否会冲突

不会天然冲突，但需要统一事件协议。

推荐原则：

```text
YOLO / MediaPipe 原始识别结果
  -> 统一整理成 gesture_event
  -> 后端只消费 gesture_event
```

建议：

1. YOLO 负责静态有效手势：`fist`、`one`、`like`、`peace`。
2. MediaPipe 负责动态手势，例如滑动、挥动、旋转等。
3. 如果动态手势正在进行，可以暂停 YOLO 静态事件触发，避免误触。
4. 后端不要直接消费 YOLO class_id，也不要直接消费 MediaPipe 原始 landmark。
5. 后端只根据最终 `gesture_event.gesture` 做业务映射。

MediaPipe 后续也可以输出同样格式：

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

## 10. 后端 WebSocket 示例

以下仅为示意代码，后端同学可按实际项目结构调整：

```python
from fastapi import WebSocket
from vision import VisionService

vision_service = VisionService()


async def vision_ws(websocket: WebSocket):
    await websocket.accept()

    while True:
        image_bytes = await websocket.receive_bytes()
        events = vision_service.process_frame(image_bytes)

        for event in events:
            await websocket.send_json(event)
```

## 11. 本地测试

安装依赖：

```powershell
pip install -r vision\requirements.txt
```

运行测试：

```powershell
python vision\test\test_vision_image.py vision\test\test_images\你的测试图片.jpg
```

如果识别稳定，会输出 `gesture_event`。

## 12. 提交 GitHub 建议

建议提交：

```text
vision/
```

不建议提交：

```text
__pycache__/
*.pyc
```

这些是 Python 自动生成的缓存文件，已经在 `.gitignore` 中忽略。
