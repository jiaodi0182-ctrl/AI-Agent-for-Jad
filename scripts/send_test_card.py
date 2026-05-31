#!/usr/bin/env python3
"""
Send a Feishu interactive test card with a button.

Use this to verify the card-callback link end-to-end:
clicking the button should hit POST /feishu/card/callback and return a toast.

Usage:
    python scripts/send_test_card.py --chat-id oc_xxxxxxxx
    python scripts/send_test_card.py --open-id ou_xxxxxxxx

Requires env vars (see .env.example):
    FEISHU_APP_ID
    FEISHU_APP_SECRET
"""
import argparse
import os
import sys

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE = "https://open.feishu.cn/open-apis"


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    resp = requests.post(
        f"{BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=10,
    )
    data = resp.json()
    if data.get("code") != 0:
        raise SystemExit(f"获取 tenant_access_token 失败: {data}")
    return data["tenant_access_token"]


def build_test_card() -> dict:
    """An interactive card with one button that triggers the 'ping' action."""
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "Hermes 升级后按钮回归测试"},
            "template": "blue",
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "自动测试卡：用于验证升级后的飞书交互卡片按钮链路。",
                },
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "升级后按钮测试"},
                        "type": "primary",
                        # This value is what /feishu/card/callback dispatches on
                        "value": {"action": "ping"},
                    }
                ],
            },
        ],
    }


def send_card(token: str, receive_id: str, receive_id_type: str) -> None:
    import json

    resp = requests.post(
        f"{BASE}/im/v1/messages",
        params={"receive_id_type": receive_id_type},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={
            "receive_id": receive_id,
            "msg_type": "interactive",
            "content": json.dumps(build_test_card(), ensure_ascii=False),
        },
        timeout=10,
    )
    data = resp.json()
    if data.get("code") != 0:
        raise SystemExit(f"发送卡片失败: {data}")
    print("测试卡片已发送 ✅  请在飞书中点击按钮，应弹出「pong — 按钮回调正常！」")


def main() -> None:
    parser = argparse.ArgumentParser(description="发送飞书测试按钮卡片")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--chat-id", help="群 chat_id (oc_...)")
    group.add_argument("--open-id", help="用户 open_id (ou_...)")
    args = parser.parse_args()

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        sys.exit("请先在 .env 中设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")

    token = get_tenant_access_token(app_id, app_secret)

    if args.chat_id:
        send_card(token, args.chat_id, "chat_id")
    else:
        send_card(token, args.open_id, "open_id")


if __name__ == "__main__":
    main()
