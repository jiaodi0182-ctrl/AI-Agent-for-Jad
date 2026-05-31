"""
Feishu (Lark) card callback handler.

Feishu sends a POST to this endpoint when a user clicks a card button.
The server must respond within 3 seconds with HTTP 200 and valid JSON,
otherwise Feishu shows error code 200340.

Configure in Feishu Open Platform:
  Card callback URL → https://<your-host>/feishu/card/callback

Required env vars:
  FEISHU_APP_ID         - App ID from Feishu Open Platform
  FEISHU_APP_SECRET     - App Secret
  FEISHU_VERIFICATION_TOKEN - Card verification token (for legacy verification)
  FEISHU_ENCRYPT_KEY    - Encrypt key (if encryption is enabled, optional)
"""
import hashlib
import hmac
import json
import logging
import os
import time

from fastapi import APIRouter, HTTPException, Request, Response

from agent import Agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feishu", tags=["feishu"])

_VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
_ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")


def _verify_signature(timestamp: str, nonce: str, body: bytes, signature: str) -> bool:
    """Verify Feishu request signature (token-based card callback verification)."""
    if not _ENCRYPT_KEY:
        return True
    content = (timestamp + nonce + _ENCRYPT_KEY).encode("utf-8") + body
    expected = hashlib.sha256(content).hexdigest()
    return hmac.compare_digest(expected, signature)


def _build_text_card(content: str) -> dict:
    """Build a simple Feishu card that updates in place after button click."""
    return {
        "toast": {
            "type": "info",
            "content": content,
        }
    }


@router.post("/card/callback")
async def card_callback(request: Request):
    """
    Handle Feishu interactive card button callbacks.

    Feishu protocol:
    - Must return HTTP 200 within 3 seconds
    - Body must be valid JSON
    - Return {} to do nothing, or a card/toast object to update the card
    """
    body_bytes = await request.body()

    # Signature verification (only when FEISHU_ENCRYPT_KEY is set)
    if _ENCRYPT_KEY:
        timestamp = request.headers.get("X-Lark-Request-Timestamp", "")
        nonce = request.headers.get("X-Lark-Request-Nonce", "")
        signature = request.headers.get("X-Lark-Signature", "")
        if not _verify_signature(timestamp, nonce, body_bytes, signature):
            raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = json.loads(body_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    logger.info("Feishu card callback received: %s", json.dumps(payload, ensure_ascii=False))

    # Feishu URL verification challenge (sent once when you first configure the callback URL)
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge", "")}

    # Legacy token verification
    if _VERIFICATION_TOKEN and payload.get("token") != _VERIFICATION_TOKEN:
        raise HTTPException(status_code=403, detail="Token mismatch")

    action = payload.get("action", {})
    action_value = action.get("value", {})
    action_tag = action.get("tag", "")

    logger.info(
        "Card action — tag: %s, value: %s",
        action_tag,
        json.dumps(action_value, ensure_ascii=False),
    )

    # Dispatch based on the action value set on the button
    handler_name = action_value.get("action") if isinstance(action_value, dict) else None

    try:
        reply_text = _dispatch(handler_name, action_value, payload)
    except Exception as exc:
        logger.exception("Card action handler failed: %s", exc)
        return Response(
            content=json.dumps(
                _build_text_card("处理失败，请稍后重试"), ensure_ascii=False
            ),
            media_type="application/json",
        )

    if reply_text is None:
        # No update needed — acknowledge silently
        return Response(content="{}", media_type="application/json")

    return Response(
        content=json.dumps(_build_text_card(reply_text), ensure_ascii=False),
        media_type="application/json",
    )


def _dispatch(action: str | None, value: dict, payload: dict) -> str | None:
    """
    Route card button actions to the appropriate handler.

    To add a new button: set its value to {"action": "my_action", ...},
    then add a branch here.
    """
    if action == "chat":
        message = value.get("message", "")
        agent = Agent()
        return agent.chat(message)

    if action == "ping":
        return "pong — 按钮回调正常！"

    # Unknown / unhandled action — acknowledge without updating the card
    logger.warning("Unhandled card action: %s, value: %s", action, value)
    return None
