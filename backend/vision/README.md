# Tarot YOLO 手势识别模块

本项目是塔罗牌交互系统中的视觉识别模块，负责用 YOLO 识别前端摄像头画面中的静态手势，并向后端返回统一的 `gesture_event`。

视觉模块只回答一件事：

```text
当前图片帧里是否出现了有效手势？
```

不负责塔罗牌识别、抽牌逻辑、Agent 调用、数据库存储或前端摄像头开启。

## 1. 当前有效手势

当前模型可以识别多个手势类别，但本项目只把下面 4 个手势作为有效业务手势输出：

| gesture | 含义 | 后端业务动作 |
|---|---|---|
| `fist` | 握拳 | 洗牌 `shuffle` |
| `one` | 食指向上 | 切换排阵 `switch_spread` |
| `like` | 点赞 | 请求解读 `request_reading` |
| `peace` | Peace 手势 | 重置 `reset` |

其他类别，例如 `ok`、`palm`、`stop`、`rock` 等，会被忽略，不会输出事件。

没有有效稳定手势时返回：

```json
[]
```

## 2. 交付结构

本模块可以作为一个完整的 `vision/` 文件夹交付给后端同学。

后端项目中推荐放置方式：

```text
backend_project/
└── vision/
    ├── __init__.py
    ├── vision_service.py
    ├── detector_gesture.py
    ├── event_engine.py
    ├── mappings.py
    ├── schemas.py
    ├── yolo_utils.py
    ├── model/
    │   └── best_gesture.pt
    ├── test/
    │   ├── test_gesture_contract.py
    │   ├── test_vision_image.py
    │   └── test_images/
    ├── docs/
    │   └── vision_integration.md
    ├── requirements.txt
    ├── vision_gesture_contract.md
    ├── README.md
    └── .gitignore
```

## 3. 安装依赖

请在包含 `vision/` 文件夹的项目根目录运行命令。

```powershell
pip install -r vision\requirements.txt
```

依赖包括：

```text
ultralytics
pillow
pydantic
opencv-python
```

## 4. 后端调用方式

后端从包含 `vision/` 的项目根目录启动时，可以直接 import：

```python
from vision import VisionService

vision_service = VisionService()

events = vision_service.process_frame(image_bytes)
```

`image_bytes` 是前端通过 WebSocket 上传的图片帧二进制数据。

默认情况下，`VisionService()` 会自动加载：

```text
vision/model/best_gesture.pt
```

注意：不要进入 `vision/` 文件夹内部再运行：

```powershell
cd vision
python -c "from vision import VisionService; s=VisionService(); print('ok')"
```

这样会报：

```text
ModuleNotFoundError: No module named 'vision'
```

正确做法是在包含 `vision/` 的父目录运行：

```powershell
cd C:\Users\CJT\Desktop\tarot_yolo
python -c "from vision import VisionService; s=VisionService(); print('ok')"
```

后端项目里也是同理：从后端项目根目录启动，让 Python 能看到旁边的 `vision/` 文件夹。

## 5. 代码文件说明

| 文件 | 作用 |
|---|---|
| `__init__.py` | 暴露 `VisionService`，让后端可以 `from vision import VisionService` |
| `vision_service.py` | 后端统一入口，提供 `process_frame(image_bytes)` |
| `detector_gesture.py` | 加载 YOLO 模型并识别图片中的有效手势 |
| `event_engine.py` | 做稳定帧判断、冷却时间、防重复触发，支持同一帧多个有效手势 |
| `mappings.py` | YOLO `class_id` 到有效手势名的映射，只保留 `fist/one/like/peace` |
| `schemas.py` | 定义 `GestureDetection` 和 `VisualEvent` 数据结构 |
| `yolo_utils.py` | 图片 bytes 解码、模型路径检查、bbox 转换等工具函数 |
| `model/best_gesture.pt` | 训练好的 YOLO 手势模型 |
| `test/test_gesture_contract.py` | 协议测试，确认输出字段和有效手势符合后端约定 |
| `test/test_vision_image.py` | 单张图片测试脚本 |
| `test/test_camera_realtime.py` | 本地摄像头实时测试脚本 |
| `vision_gesture_contract.md` | 后端同学写的对接协议，当前代码按它实现 |
| `docs/vision_integration.md` | 更详细的视觉集成说明 |

## 6. 返回格式

识别到稳定有效手势时返回。若同一帧中有多个有效手势，稳定后会返回多个事件：

```json
[
  {
    "type": "gesture_event",
    "source": "gesture",
    "detector": "yolo",
    "gesture": "like",
    "confidence": 0.91,
    "timestamp": 1712345678.123,
    "bbox": [120.5, 80.2, 460.8, 690.1],
    "payload": {
      "class_id": 2,
      "gesture": "like",
      "description": "点赞手势",
      "confidence": 0.91,
      "bbox": [120.5, 80.2, 460.8, 690.1]
    }
  },
  {
    "type": "gesture_event",
    "source": "gesture",
    "detector": "yolo",
    "gesture": "fist",
    "confidence": 0.89,
    "timestamp": 1712345678.123,
    "bbox": [500.0, 80.0, 820.0, 690.0],
    "payload": {
      "class_id": 0,
      "gesture": "fist",
      "description": "握拳",
      "confidence": 0.89,
      "bbox": [500.0, 80.0, 820.0, 690.0]
    }
  }
]
```

视觉模块不会输出业务 `action`。例如 `like -> request_reading` 的映射由后端负责。

## 7. 防抖逻辑

摄像头会连续发送图片帧，为了避免重复触发，模块内置防抖：

| 参数 | 默认值 | 说明 |
|---|---:|---|
| 原始检测阈值 | `0.25` | 过滤 YOLO 低置信度检测框 |
| 事件触发阈值 | `0.75` | 低于该值不触发最终事件 |
| 稳定帧数 | `5` | 连续 5 帧同一手势才触发 |
| 冷却时间 | `1.5s` | 同一手势触发后短时间内不重复触发 |

因此 `process_frame()` 经常返回 `[]` 是正常现象。

## 8. 本地测试

检查代码和协议测试：

```powershell
python -m unittest discover -s vision\test -p "test_*.py"
```

检查语法：

```powershell
python -m compileall vision
```

检查模型能否加载：

```powershell
python -c "from vision import VisionService; s=VisionService(); print('ok')"
```

测试单张图片：

```powershell
python vision\test\test_vision_image.py vision\test\test_images\like.jpg
```

如果图片里是有效手势并且识别稳定，会输出 `gesture_event`。

如果一张图片里有多个有效手势，例如 `fist` 和 `like`，稳定后会输出两个事件。

如果图片里是无效手势或没有检测到稳定手势，会输出：

```json
[]
```

## 9. 摄像头实时测试

这个脚本只用于本地验证模型效果，不是后端正式接口。

请在包含 `vision/` 的项目根目录运行：

```powershell
python vision\test\test_camera_realtime.py
```

运行后会打开电脑默认摄像头：

- 画面窗口会显示实时摄像头；
- 控制台会打印稳定识别到的 `gesture_event`；
- 按 `q` 退出。

如果打不开摄像头，通常是：

- 摄像头权限没开；
- 摄像头被微信、会议软件、浏览器等占用；
- 默认摄像头编号不是 `0`。

正式项目里，摄像头仍然建议由前端开启，然后通过 WebSocket 把图片帧发给后端；这个脚本只是为了你自己验收 YOLO 是否实时可用。

## 10. 和后端协议

后端对接协议见：

```text
vision_gesture_contract.md
```

当前接口符合该协议：

- 提供 `from vision import VisionService`
- 提供 `VisionService.process_frame(image_bytes)`
- 返回 `list[dict]`
- 输出 `gesture_event`
- 不输出业务 `action`
- 无有效稳定手势返回 `[]`
- 只输出 `fist / one / like / peace`

## 11. 提交 GitHub 建议

建议提交：

```text
vision/
```

不要提交：

```text
__pycache__/
*.pyc
.venv/
.pytest_cache/
```
