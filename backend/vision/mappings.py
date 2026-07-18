from __future__ import annotations


# YOLO class_id -> 有效手势语义映射。
# 注意：这里不直接绑定洗牌、重置等业务动作，避免视觉模块和后端业务强耦合。
# 业务动作由后端根据 gesture 再做映射。
#
# 当前模型还能识别 call/dislike/four/ok/palm/rock/stop/three/three2 等类别。
# 这些类别不在本项目交互协议内，因此不写入 GESTURE_MAP；
# detector 会自动忽略它们，最终 process_frame() 返回 []，效果等同于 none。
GESTURE_MAP: dict[int, dict[str, str]] = {
    0: {"gesture": "fist", "description": "握拳"},
    1: {"gesture": "one", "description": "食指向上"},
    2: {"gesture": "like", "description": "点赞手势"},
    3: {"gesture": "peace", "description": "Peace 手势"},
}
