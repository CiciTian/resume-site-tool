# 让所有人访问这个网页工具

本地地址：

```text
http://127.0.0.1:8000
```

只能在你自己的电脑访问。要让别人也能用，需要部署到公网平台，例如 Render、Railway、Fly.io、Cloud Run，或者临时使用 Cloudflare Tunnel / ngrok。

## 推荐方案：Render

Render 官方 FastAPI 部署方式使用：

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn backend.app:app --host 0.0.0.0 --port $PORT
```

本项目已经提供：

```text
render.yaml
runtime.txt
```

### 步骤

1. 新建一个 GitHub 仓库，例如：

```text
resume-site-tool
```

2. 把 `resume-site-tool` 目录里的文件推送到这个仓库根目录。

3. 打开 Render：

```text
https://render.com
```

4. New -> Web Service。

5. 选择你的 GitHub 仓库。

6. 设置环境变量：

```text
OPENAI_API_KEY=你的 OpenAI key
```

或者：

```text
ANTHROPIC_API_KEY=你的 Anthropic key
```

7. 部署完成后，Render 会给你一个公网地址，例如：

```text
https://resume-site-tool.onrender.com
```

别人打开这个地址就可以上传简历、选择模板、生成网站。

## 备选方案：Railway

本项目已经提供：

```text
railway.json
```

部署流程：

1. 把 `resume-site-tool` 推到 GitHub。
2. 打开 Railway：

```text
https://railway.com
```

3. New Project -> Deploy from GitHub repo。
4. 选择仓库。
5. 添加环境变量 `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY`。
6. Railway 会生成一个公网域名。

## 临时演示方案：Cloudflare Tunnel

适合只想临时给朋友试用。

先在本地启动工具：

```bash
./run.sh
```

然后另开一个终端：

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Cloudflare 会给一个临时公网链接。

## 生产环境必须注意

这个 MVP 页面里有 GitHub Token 输入框。正式给真实用户使用前，建议改成 GitHub OAuth。

原因：

- 不应该让用户长期手动粘贴 token。
- 后端不能记录 token。
- GitHub OAuth 可以更安全地申请 `public_repo` 权限。

更正式的产品流程应该是：

```text
用户上传简历
  -> 选择模板
  -> 预览网站
  -> 点击 Connect GitHub
  -> OAuth 授权
  -> 自动创建 username.github.io
  -> 发布网站
```

## 最短可执行路线

如果你现在就想让别人访问：

```text
1. 把 resume-site-tool 目录推到一个新的 GitHub 仓库
2. 用 Render 创建 Web Service
3. 设置 OPENAI_API_KEY
4. 复制 Render 给你的公网 URL 发给别人
```

