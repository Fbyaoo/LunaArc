from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from vision import VisionService


def main() -> None:
    import cv2

    service = VisionService()
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError("无法打开摄像头，请检查摄像头权限或设备编号。")

    print("摄像头已打开。按 q 退出。")

    while True:
        ok, frame = camera.read()
        if not ok:
            print("读取摄像头画面失败。")
            break

        encode_ok, buffer = cv2.imencode(".jpg", frame)
        if not encode_ok:
            continue

        events = service.process_frame(buffer.tobytes())
        for event in events:
            print(event)

        cv2.imshow("YOLO Gesture Realtime Test - press q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
