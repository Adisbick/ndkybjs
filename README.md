# sing-box Reality 多协议 Docker 节点模板

这个项目用于用 Docker 部署一个 sing-box 服务端，并输出订阅链接。默认包含 3 个入站：

1. `vless-tcp-reality`
2. `vless-httpupgrade-reality`
3. `anytls-reality`

默认 SNI 是 `adm.com`，UUID、REALITY 密钥、short_id、AnyTLS 密码可自动生成，也可以通过环境变量固定。请只在你有权使用的服务器和网络环境中部署。

## 项目结构

```text
.
├── Dockerfile
├── entrypoint.sh
├── sub_server.py
├── docker-compose.yml
├── .env.example
├── .dockerignore
└── README.md
```

## 重要说明

- Koyeb 这类平台部署 TCP 代理时，需要启用 TCP Proxy，并把容器端口映射成外部 TCP 入口。
- Koyeb 分配的 TCP Proxy 外部端口可能不是容器内部端口，所以需要用 `EXTERNAL_VLESS_TCP_PORT`、`EXTERNAL_VLESS_HU_PORT`、`EXTERNAL_ANYTLS_PORT` 修正订阅里的端口。
- `AnyTLS` 的分享 URI 在不同客户端里的兼容性不完全一致，建议优先使用 `/client.json` 里的 sing-box outbound 配置。
- 如果不固定环境变量，容器重启或重建后，节点身份可能变化。生产使用建议固定 `UUID`、`REALITY_PRIVATE_KEY`、`REALITY_PUBLIC_KEY`、`SHORT_ID`、`ANYTLS_PASSWORD`。

## 本地构建和运行

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env`，至少设置：

```bash
PUBLIC_HOST=你的公网IP或域名
NODE_NAME=你的节点名称
SNI=adm.com
```

启动：

```bash
docker compose up -d --build
```

查看自动生成的 UUID、REALITY 公钥、short_id、AnyTLS 密码：

```bash
docker logs singbox-reality-node
cat ./data/identity.env
```

建议把 `./data/identity.env` 里的值复制到 `.env`，以后重新部署就不会变化。

## 订阅地址

假设 `PUBLIC_HOST=example.com`，订阅端口是 `8080`：

```text
http://example.com:8080/sub
http://example.com:8080/sub.b64
http://example.com:8080/client.json
http://example.com:8080/health
```

- `/sub`：明文 URI，每行一个节点。
- `/sub.b64`：base64 形式，兼容部分订阅工具。
- `/client.json`：sing-box 客户端 outbounds 示例。
- `/health`：健康检查。

## 修改 UUID 和密钥

方式一：修改 `.env` 或云平台环境变量：

```bash
UUID=新的UUID
REALITY_PRIVATE_KEY=新的REALITY私钥
REALITY_PUBLIC_KEY=新的REALITY公钥
SHORT_ID=新的short_id
ANYTLS_PASSWORD=新的AnyTLS密码
```

然后重启容器。

方式二：删除本地 `data/identity.env`，让容器重新生成：

```bash
docker compose down
rm -f data/identity.env
docker compose up -d
```

注意：重新生成后，旧客户端配置会失效。

## 添加节点/用户

当前模板的三个协议共用同一组 UUID、REALITY 密钥和 short_id。要添加更多用户，可以修改 `sub_server.py` 中 `build_config()` 里的 `users` 数组，并同步修改订阅输出函数。

例如 VLESS 增加一个用户：

```json
"users": [
  {"name": "user1", "uuid": "第一个UUID", "flow": ""},
  {"name": "user2", "uuid": "第二个UUID", "flow": ""}
]
```

AnyTLS 增加一个用户：

```json
"users": [
  {"name": "user1", "password": "第一个密码"},
  {"name": "user2", "password": "第二个密码"}
]
```

## 推送到 GitHub

```bash
git init
git add .
git commit -m "init sing-box reality docker node"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

## 使用 GitHub Actions 自动推送到 Docker Hub

本项目已经包含 GitHub Actions 工作流文件：

```text
.github/workflows/docker-publish.yml
```

只要你把代码推送到 GitHub 的 `main` 分支，GitHub Actions 就会自动构建 Docker 镜像，并推送到 Docker Hub。

### 1. 准备 Docker Hub Access Token

1. 登录 Docker Hub。
2. 进入 `Account Settings`。
3. 找到 `Personal access tokens`。
4. 创建一个新的 Access Token。
5. 复制生成的 token，后面要放进 GitHub Secrets。

### 2. 在 GitHub 仓库添加 Secrets

进入你的 GitHub 仓库：

```text
Settings → Secrets and variables → Actions → New repository secret
```

添加这两个 Secret：

```text
DOCKERHUB_USERNAME=你的DockerHub用户名
DOCKERHUB_TOKEN=你的DockerHub Access Token
```

注意：`DOCKERHUB_TOKEN` 不建议填写 Docker Hub 登录密码，建议使用 Access Token。

### 3. 修改镜像名称

打开 `.github/workflows/docker-publish.yml`，修改：

```yaml
IMAGE_NAME: singbox-reality-node
```

例如你想推送成：

```text
你的DockerHub用户名/koyeb-singbox:latest
```

就改成：

```yaml
IMAGE_NAME: koyeb-singbox
```

### 4. 推送代码到 GitHub

```bash
git init
git add .
git commit -m "init sing-box reality docker node"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

推送后，进入 GitHub 仓库的 `Actions` 页面，可以看到自动构建和推送记录。

### 5. Docker Hub 镜像地址

默认工作流会推送两个 tag：

```text
你的DockerHub用户名/singbox-reality-node:latest
你的DockerHub用户名/singbox-reality-node:main-提交短哈希
```

Koyeb 部署时一般填写：

```text
你的DockerHub用户名/singbox-reality-node:latest
```

如果你修改了 `IMAGE_NAME`，就使用你修改后的镜像名。

### 6. 手动触发构建

这个工作流支持手动触发：

```text
GitHub 仓库 → Actions → Docker Publish → Run workflow
```

这适合你没有新提交，但想重新构建并推送镜像的情况。

## Koyeb 部署提示

1. 先把镜像推送到 Docker Hub。
2. 在 Koyeb 新建 Service，选择 Docker image。
3. 镜像填写：`你的DockerHub用户名/singbox-reality-node:latest`。
4. 配置环境变量：
   - `PUBLIC_HOST`：Koyeb TCP Proxy 分配的 host，或你的自定义域名。
   - `SNI=adm.com`
   - `NODE_NAME=你的节点名`
   - 建议固定 `UUID`、`REALITY_PRIVATE_KEY`、`REALITY_PUBLIC_KEY`、`SHORT_ID`、`ANYTLS_PASSWORD`。
5. 暴露端口：
   - `443/tcp`
   - `8443/tcp`
   - `9443/tcp`
   - `8080/http` 或 `8080/tcp`，用于订阅服务。
6. 对三个代理端口启用 TCP Proxy。
7. 如果 Koyeb 给每个 TCP 端口分配了不同外部端口，设置：
   - `EXTERNAL_VLESS_TCP_PORT`
   - `EXTERNAL_VLESS_HU_PORT`
   - `EXTERNAL_ANYTLS_PORT`

## 其他云服务部署

只要支持 Docker 和 TCP 端口映射即可，例如 VPS、Railway、Render、Fly.io、Zeabur 等。核心要求：

- 能暴露 TCP 端口。
- 能设置环境变量。
- 能查看日志，拿到首次生成的身份信息。
- 最好能挂载持久化目录到 `/data`。

本地 Docker 运行示例：

```bash
docker run -d \
  --name singbox-reality-node \
  --restart unless-stopped \
  -p 443:443/tcp \
  -p 8443:8443/tcp \
  -p 9443:9443/tcp \
  -p 8080:8080/tcp \
  -e PUBLIC_HOST=你的公网IP或域名 \
  -e SNI=adm.com \
  -e NODE_NAME=my-node \
  -v "$PWD/data:/data" \
  你的DockerHub用户名/singbox-reality-node:latest
```
