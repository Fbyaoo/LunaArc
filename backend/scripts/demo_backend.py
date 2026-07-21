#!/usr/bin/env python3
"""Run the complete LunaArc course-demo flow against a running backend."""

from __future__ import annotations

import argparse
import json
import time

import httpx


def show(label: str, payload: object) -> None:
    print(f"\n[{label}]")
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    email = f"course-demo-{int(time.time())}@example.com"
    password = "CourseDemo123"

    with httpx.Client(
        base_url=args.base_url,
        timeout=60,
        trust_env=False,
    ) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        show("1. 服务健康检查", health.json())

        registered = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": password,
                "display_name": "课程演示用户",
            },
        )
        registered.raise_for_status()
        auth = registered.json()
        show("2. 注册并登录", auth["user"])

        headers = {"Authorization": f"Bearer {auth['access_token']}"}

        cards = client.get("/api/cards")
        cards.raise_for_status()
        show("3. 读取牌库", {"card_count": len(cards.json())})

        result = client.post(
            "/api/draw-and-read",
            headers=headers,
            json={
                "question": "我应该如何规划接下来的学习？",
                "spread_type": "three_card",
            },
        )
        result.raise_for_status()
        show("4. 三牌抽取与解读", result.json())

        usage = client.get("/api/usage/me", headers=headers)
        usage.raise_for_status()
        show("5. 查询今日额度", usage.json())

        history = client.get("/api/history", headers=headers)
        history.raise_for_status()
        show("6. 查询用户历史", history.json())

        refreshed = client.post("/api/auth/refresh")
        refreshed.raise_for_status()
        show("7. 刷新登录状态", {"status": "success"})

        refreshed_headers = {
            "Authorization": f"Bearer {refreshed.json()['access_token']}"
        }
        logged_out = client.post("/api/auth/logout", headers=refreshed_headers)
        logged_out.raise_for_status()
        show("8. 安全退出", logged_out.json())

    print("\n课程展示主链路执行成功。")


if __name__ == "__main__":
    main()
