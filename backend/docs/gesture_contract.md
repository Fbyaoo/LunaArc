# Gesture Integration Contract

## 1. Module Responsibility

本模块负责识别前端摄像头画面中的手势，并输出统一的手势事件。

当前 YOLO 模型只负责静态手势识别：

| 手势 | 含义 |
|---|---|
| fist | 握拳 |
| one | 食指向上 |
| ok | OK 手势 |
| peace | Peace 手势 |

本模块不负责：

- 塔罗牌牌面识别；
- 洗牌、切换牌阵、请求解读、重置等业务状态修改；
- Agent 解读调用；
- 前端摄像头开启。


推荐链路：

```
前端摄像头
  ↓
WebSocket 图片帧
  ↓
后端 WebSocket 接收
  ↓
vision_service.process_frame(image_bytes)
  ↓
gesture_event
  ↓
后端业务映射
  ↓
调用 Tarot Workflow / Agent
```

---

# 2. Model Information

默认模型路径：

```
models/best_gesture.pt
```

当前 YOLO 类别：

```python
{
    0: "fist",
    1: "one",
    2: "ok",
    3: "peace"
}
```

如果重新训练模型导致类别变化，只需要修改：

```
vision/mappings.py
```

后端不要依赖 YOLO 原始 class_id。

---

# 3. Backend Calling Interface

后端调用：

```python
from vision import VisionService


vision_service = VisionService(
    model_path="models/best_gesture.pt"
)
```

收到前端 WebSocket 图片帧：

```python
events = vision_service.process_frame(
    image_bytes
)
```

参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| image_bytes | bytes | 摄像头当前帧图片二进制 |

返回：

```python
list[dict]
```

没有稳定识别：

```json
[]
```

这是正常情况。

---

# 4. Gesture Event Protocol

视觉模块输出的是：

```
gesture_event
```

不是业务事件。


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

# 5. Event Fields

| 字段 | 类型 | 说明 |
|---|---|---|
| type | string | 固定 gesture_event |
| source | string | 固定 gesture |
| detector | string | 当前 yolo，未来可 mediaPipe |
| gesture | string | 手势语义 |
| confidence | float | 模型置信度 |
| timestamp | float | Unix 时间戳 |
| bbox | list/null | 检测框 |
| payload | object | 原始调试信息 |

---

# 6. Gesture Mapping

视觉模块只负责：

```
看到什么
```

后端负责：

```
这个手势代表什么业务
```


映射：

| gesture | action | 含义 |
|---|---|---|
| fist | shuffle | 洗牌 |
| one | switch_spread | 切换牌阵 |
| ok | request_reading | 请求解读 |
| peace | reset | 重置 |

---

# 7. Gesture Adapter

Backend 使用 Adapter 转换：

输入：

```json
{
  "gesture":"peace"
}
```

输出：

```json
{
  "gesture":"peace",
  "action":"reset"
}
```

示例：

```python
GESTURE_MAPPING = {
    "fist": "shuffle",
    "one": "switch_spread",
    "ok": "request_reading",
    "peace": "reset"
}
```

---

# 8. Confidence Handling

confidence 来源：

```
YOLO 模型输出
```

范围：

```
0.0 ~ 1.0
```

例如：

```json
{
 "gesture":"peace",
 "confidence":0.94
}
```

表示：

模型认为当前手势为 peace 的概率约为 94%。

---

## 两层阈值

|位置|默认值|作用|
|-|-|-|
|GestureDetector.confidence_threshold|0.25|过滤 YOLO 原始低置信度框|
|GestureEventEngine.confidence_threshold|0.75|过滤最终业务事件|

流程：

```
YOLO识别
 ↓
confidence > 0.25
 ↓
进入事件判断
 ↓
confidence > 0.75
 ↓
触发 gesture_event
```

---

# 9. Stability And Debounce

摄像头连续发送大量帧。

为了避免重复触发：

|参数|默认值|作用|
|-|-|-|
|stable_frames|5|连续5帧相同手势|
|cooldown_seconds|1.5|触发后冷却时间|

因此：

```python
process_frame()
```

经常返回：

```json
[]
```

是正常现象。

只有稳定识别：

```json
[
 {
  "gesture":"peace"
 }
]
```

才处理。

---

# 10. Camera Responsibility

视觉模块不开摄像头。


摄像头由前端负责：

```
navigator.mediaDevices.getUserMedia()

↓

video/canvas 截帧

↓

WebSocket发送图片bytes

↓

Backend

↓

VisionService
```

---

# 11. YOLO And MediaPipe Compatibility

YOLO / MediaPipe 不直接暴露给后端。


统一：

```
YOLO
MediaPipe
其他模型

↓

gesture_event

↓

Backend
```

Backend 不关心检测来源。

例如 MediaPipe：

```json
{
"type":"gesture_event",
"source":"gesture",
"detector":"mediapipe",
"gesture":"swipe_left",
"confidence":0.88
}
```

---

# 12. Backend Responsibility

Backend负责：

- WebSocket管理；
- 调用 VisionService；
- gesture 到 action 映射；
- 当前业务状态判断；
- 调用 Agent；
- 保存数据库。


Backend 不负责：

- 摄像头权限；
- 原始模型推理；
- 模型训练。

---

# 13. Local Testing

安装：

```bash
pip install -r requirements.txt
```

测试：

```bash
python tests/test_vision_image.py tests/test_images/example.jpg
```

稳定识别输出：

```
gesture_event
```

---

# 14. Git Submission

建议提交：

```
vision/
models/best_gesture.pt
tests/
docs/gesture_integration.md
requirements.txt
```

不要提交：

```
__pycache__
*.pyc
```

---

# 15. Current Status

| Module | Status |
|---|---|
| Gesture API | Mock |
| YOLO Gesture Model | Waiting |
| Gesture Adapter | Ready |
| Tarot Workflow | Backend |
| Agent Integration | Ready |
| Database | Ready |