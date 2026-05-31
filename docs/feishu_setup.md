# 飞书卡片按钮配置指南

本指南帮你把飞书卡片按钮的回调链路跑通，解决点击按钮报错 `code: 200340`。

> 200340 的根因：飞书把按钮点击事件 POST 到「卡片请求网址」，但服务器没有在
> 3 秒内返回 HTTP 200 + 合法 JSON。新增的 `/feishu/card/callback` 端点已解决此问题。

---

## 推荐方案（最省事）：本地运行 + ngrok 穿透 + 不开加密

适合先把按钮跑通验证，之后再迁正式服务器只需换 URL。

### 1. 安装依赖并启动服务

```bash
pip install -r requirements.txt
cp .env.example .env        # 然后填写下面的变量
python -m uvicorn api.server:app --reload --port 8000
```

`.env` 至少要填：

```env
ANTHROPIC_API_KEY=你的_anthropic_key
FEISHU_APP_ID=cli_xxxxxxxx
FEISHU_APP_SECRET=你的_app_secret
FEISHU_VERIFICATION_TOKEN=开放平台复制的_verification_token
# FEISHU_ENCRYPT_KEY 不开加密就留空
```

> App ID / App Secret：开放平台 → 你的应用 → **凭证与基础信息**
> Verification Token：开放平台 → **事件与回调 → 加密策略**（Encrypt Key 同页）

### 2. 用 ngrok 暴露本地端口

```bash
ngrok http 8000
```

记下它给的公网地址，例如 `https://abcd-1-2-3-4.ngrok-free.app`。

### 3. 在飞书开放平台配置回调 URL

开放平台 → 你的应用 → **机器人 / 消息卡片 → 卡片请求网址**，填：

```
https://abcd-1-2-3-4.ngrok-free.app/feishu/card/callback
```

保存时飞书会发一个 `url_verification` challenge，端点会自动回应，显示「校验通过」。

### 4. 发个测试按钮验证

先拿到目标群的 `chat_id` 或你自己的 `open_id`，然后：

```bash
python scripts/send_test_card.py --chat-id oc_xxxxxxxx
```

飞书里会收到「Hermes 升级后按钮回归测试」卡片，点「升级后按钮测试」，
应弹出 toast：**pong — 按钮回调正常！** 说明链路修好了。

---

## 迁移到正式服务器

把回调 URL 换成你服务器的公网地址即可，例如：

```
https://your-domain.com/feishu/card/callback
```

服务器上同样跑：

```bash
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```

建议前面再挂一层 Nginx 做 HTTPS（飞书要求 HTTPS）。

---

## 如果开启了加密策略

在 `.env` 里填上 `FEISHU_ENCRYPT_KEY`，端点会自动校验请求签名。
（当前回调处理的是飞书的标准卡片 action 结构；若你的回调内容是整体 AES 加密，
需要再加一层解密，告诉我即可补上。）

---

## 按钮 action 怎么扩展

按钮的 `value` 字段决定服务器执行什么，在 `api/routes/feishu.py` 的 `_dispatch` 里分发：

| value 示例 | 行为 |
|---|---|
| `{"action": "ping"}` | 返回「pong — 按钮回调正常！」 |
| `{"action": "chat", "message": "你好"}` | 调用 AI Agent 回复 |
| `{}` 或未知 action | 静默确认，不更新卡片 |

新增按钮：设好 `value.action`，在 `_dispatch` 里加一个分支即可。
