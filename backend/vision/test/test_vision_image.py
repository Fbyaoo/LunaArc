from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from vision import VisionService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    service = VisionService(model_path=args.model)

    image_bytes = args.image.read_bytes()

    # 事件引擎需要连续稳定帧；测试单张图片时重复喂几次，模拟摄像头稳定识别。
    events: list[dict] = []
    for _ in range(6):
        events.extend(service.process_frame(image_bytes, filename=args.image.name))

    print(json.dumps(events, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
