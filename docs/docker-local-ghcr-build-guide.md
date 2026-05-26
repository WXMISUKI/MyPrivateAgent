# Docker 本地构建与 GHCR 推送指南

本文档用于本地构建 `MyPrivateAgent` 后端镜像，并推送到 GitHub Container Registry。

## 1. Docker Hub 镜像加速

Docker Desktop:

1. 打开 Docker Desktop。
2. 进入 `Settings -> Docker Engine`。
3. 在 JSON 中加入或合并：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io"
  ]
}
```

4. 点击 `Apply & restart`。

说明：

- `registry-mirrors` 是 Docker daemon 配置项，只影响 Docker Hub 这类基础镜像拉取。
- 国内公共镜像源可用性会变化，如果拉取失败，替换为你当前可用的企业镜像源或云厂商 ACR mirror。
- 该配置不会解决 GHCR 登录问题，GHCR 推送仍需要 Docker auth config 或 `docker login`。

## 2. 下载本地 wheelhouse

不要用 Windows Python 直接下载依赖包，因为正式镜像是 Linux 容器，需要 Linux wheel。

使用项目脚本通过 `python:3.11-slim` 容器下载 Linux 可用依赖：

```powershell
cd D:\AI\AIcode\MyPrivateAgent
.\scripts\docker\prepare-backend-wheelhouse.ps1 -Clear
```

默认使用清华 PyPI 源：

```text
https://pypi.tuna.tsinghua.edu.cn/simple
```

下载结果在：

```text
.docker\wheelhouse\backend
```

该目录已被 `.gitignore` 忽略，只保留 `.gitkeep`。

## 3. 构建镜像

默认模式为 `auto`：

- 如果 `.docker\wheelhouse\backend` 有 wheel 或源码包，则离线安装。
- 如果 wheelhouse 为空，则走 PyPI 镜像源在线安装。

```powershell
.\scripts\docker\build-backend-ghcr.ps1 -Tag latest
```

强制离线安装：

```powershell
.\scripts\docker\build-backend-ghcr.ps1 -Tag latest -InstallMode offline
```

强制在线安装：

```powershell
.\scripts\docker\build-backend-ghcr.ps1 -Tag latest -InstallMode online
```

镜像名默认为：

```text
ghcr.io/wxmisuki/myprivateagent-backend:latest
```

## 4. GHCR denied 的绕过方式

如果 `docker login ghcr.io` 报：

```text
denied: denied
```

但 GitHub PAT 可以通过 GHCR token endpoint 获取目标仓库 token，则创建临时 Docker config：

```powershell
$dockerConfig = "$env:TEMP\docker-ghcr-myprivateagent"
.\scripts\docker\new-ghcr-docker-config.ps1 -OutputPath $dockerConfig
```

然后构建并推送：

```powershell
.\scripts\docker\build-backend-ghcr.ps1 -Tag latest -DockerConfig $dockerConfig -Push
```

推送后删除临时凭据：

```powershell
Remove-Item $dockerConfig -Recurse -Force
```

## 5. 线上环境变量

Railway 或其它容器运行平台至少需要：

```env
PORT=8000
PROJECT_ROOT=/app
CORS_ALLOWED_ORIGINS=https://my-private-agent.vercel.app,http://localhost:5173,http://localhost:8000
CORS_ALLOWED_ORIGIN_REGEX=https://.*\.vercel\.app
```

容器启动入口已固定为：

```text
python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
```
