# 正式部署指南（Docker Compose + Caddy 自动 HTTPS）

这套方案能跑在**任何装了 Docker 的 Linux 机器**上，Caddy 会自动申请并续期
Let's Encrypt 证书，无需手动配证书。飞书回调要求 HTTPS，这里一步到位。

## 前置条件

1. 一台有公网 IP 的 Linux 机器，装好 Docker 和 Docker Compose
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
2. 一个域名，把它的 **DNS A 记录指向这台机器的公网 IP**
   （例如 `agent.your-domain.com → 1.2.3.4`）
3. 安全组 / 防火墙放行 **80 和 443** 端口（80 用于证书签发校验）

## 部署步骤

```bash
# 1. 拉代码
git clone <你的仓库地址> && cd AI-Agent-for-Jad
git checkout claude/zealous-fermi-5qTt7

# 2. 配置环境变量
cp .env.example .env
nano .env     # 填写下面的值

# 3. 启动（首次会自动构建镜像 + 申请证书）
docker compose up -d --build

# 4. 查看日志确认证书签发成功、服务正常
docker compose logs -f
```

`.env` 需要填写：

```env
ANTHROPIC_API_KEY=你的_anthropic_key
DOMAIN=agent.your-domain.com          # 必须与 DNS 指向一致

FEISHU_APP_ID=cli_xxxxxxxx
FEISHU_APP_SECRET=你的_app_secret
FEISHU_VERIFICATION_TOKEN=你的_verification_token
# FEISHU_ENCRYPT_KEY=  开了加密才填
```

## 验证

```bash
# 健康检查
curl https://agent.your-domain.com/health
# 期望: {"status":"ok","version":"0.2.0"}
```

然后在飞书开放平台 → **卡片请求网址**，填：

```
https://agent.your-domain.com/feishu/card/callback
```

保存时飞书发 challenge，端点自动回应，显示「校验通过」。
最后发测试按钮验证整条链路：

```bash
docker compose exec app python scripts/send_test_card.py --chat-id oc_xxxx
```

点按钮弹出「pong — 按钮回调正常！」即部署成功。

## 常用运维命令

```bash
docker compose ps              # 查看状态
docker compose logs -f app     # 看应用日志
docker compose logs -f caddy   # 看证书 / 反代日志
docker compose pull && docker compose up -d --build   # 更新代码后重新部署
docker compose down            # 停止
```

## 常见问题

- **证书申请失败**：确认域名 DNS 已生效（`dig agent.your-domain.com` 指向本机），
  且 80/443 端口对公网开放。Caddy 会自动重试。
- **回调还是 200340**：确认 `.env` 里的 `FEISHU_VERIFICATION_TOKEN` 与开放平台一致；
  用 `docker compose logs -f app` 看是否收到了回调请求。
- **开了加密策略**：把 `FEISHU_ENCRYPT_KEY` 填进 `.env`，端点会自动校验签名。
