# Resume Site Tool 本地使用说明

这个工具可以在用户自己的电脑上运行，不需要公网部署。用户上传简历后，工具会生成固定模板的个人网站，并可以下载静态网站压缩包，或发布到自己的 GitHub Pages。

## 1. 运行环境

用户电脑需要：

- Python 3.10 或更高版本
- 第一次运行需要联网安装依赖
- 推荐准备一个 OpenAI API Key 或 Anthropic API Key，用于高质量解析简历

没有 API Key 也能体验，但会使用简易本地解析，效果会比 LLM 解析弱。

## 2. 解压工具包

解压后进入目录：

```bash
cd resume-site-tool
```

## 3. 启动工具

### 方式 A：终端启动

```bash
./run.sh
```

如果提示没有执行权限：

```bash
chmod +x run.sh
./run.sh
```

启动成功后，浏览器打开：

```text
http://127.0.0.1:8000
```

### 方式 B：macOS 双击启动

在 macOS 上可以双击：

```text
start-local.command
```

如果系统提示没有权限，先在终端执行：

```bash
chmod +x start-local.command
```

## 4. 配置高质量简历解析

推荐用户在启动前设置 API Key。

OpenAI：

```bash
export OPENAI_API_KEY=sk-...
./run.sh
```

Anthropic：

```bash
export ANTHROPIC_API_KEY=sk-ant-...
./run.sh
```

如果两个都设置了，工具优先使用 OpenAI。

## 5. 使用流程

打开页面后：

1. 选择固定模板。
   - Engineer Clean
   - Research Academic
   - Product Modern
2. 上传简历文件。
   - PDF
   - DOCX
   - TXT
   - Markdown
3. 检查工具解析出的 JSON。
4. 点击 Generate site。
5. 在页面中预览网站。
6. 点击 Download .zip 下载静态网站。
7. 或点击 Publish website 发布，成功后页面会直接显示可复制的网站链接。

下载的 zip 可以直接上传到 GitHub Pages、Netlify、Vercel 或任意静态网站托管平台。

## 6. 发布到 GitHub Pages

工具页面里有 Publish to GitHub Pages 功能。

用户需要准备 GitHub Token：

- Classic token：勾选 `public_repo`
- Fine-grained token：选择目标仓库，并授予 `Contents: Read and write`

仓库规则：

- 如果要生成 `https://username.github.io/` 这种主页网站，仓库名必须是 `username.github.io`。
- 仓库可以是完全空的，工具会自动创建第一次提交。
- 如果使用 Fine-grained token，通常需要用户先在 GitHub 创建这个空仓库，并把 token 授权给这个仓库。

发布后默认生成：

```text
https://username.github.io/
```

发布成功后，页面会优先显示这个网站链接，并提供 Copy website link 按钮。GitHub Pages 有时需要 30-120 秒才真正打开，如果刚点开是 404，等一会儿刷新即可。

注意：这是本地 MVP 版本。正式产品建议改成 GitHub OAuth，不建议让用户长期手动粘贴 token。

## 7. 常见问题

### 页面打不开，显示 127.0.0.1 拒绝连接

说明服务没有启动。重新运行：

```bash
./run.sh
```

### 上传简历后解析效果不好

原因通常是没有配置 LLM API Key。设置 `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY` 后重新启动。

### PDF 解析为空

可能是扫描版 PDF。当前版本不带 OCR，需要用户换成可复制文本的 PDF 或 DOCX。

### GitHub 发布失败

常见原因：

- Token 权限不够
- 主页网站的仓库名不是 `username.github.io`
- 网络无法连接 GitHub
- Fine-grained token 没选对仓库

如果看到 `name already exists on this account`，说明仓库已经存在，但当前 token 没有权限读取它。解决方法：

- Fine-grained token：编辑 token，选择这个仓库，并授予 `Contents: Read and write`
- Classic token：使用带 `public_repo` 权限的 token
- 如果仓库是 private，建议改成 public，或使用带 private repo 权限的 token

## 8. 给最终用户的最短说明

```text
1. 解压 resume-site-tool-mvp.zip
2. 进入 resume-site-tool 文件夹
3. 运行 ./run.sh
4. 打开 http://127.0.0.1:8000
5. 上传简历，选择模板，生成网站
```
