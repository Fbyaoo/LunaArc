from __future__ import annotations


# YOLO class_id -> 手势语义映射。
# 注意：这里不直接绑定洗牌、重置等业务动作，避免视觉模块和后端业务强耦合。
# 业务动作由后端根据 gesture 再做映射。
GESTURE_MAP: dict[int, dict[str, str]] = {
    0: {"gesture": "fist", "description": "握拳"},
    1: {"gesture": "one", "description": "食指向上"},
    2: {"gesture": "ok", "description": "OK 手势"},
    3: {"gesture": "peace", "description": "Peace 手势"},
}
