# KLineLens Deployment Guide

> 本地部署指南：使用 Docker Compose 一键启动 KLineLens。

---

## 1. 环境要求

### 1.1 必需软件
| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Docker Desktop | 4.0+ | macOS/Windows 用户 |
| Docker Engine | 20.0+ | Linux 用户 |
| Docker Compose | V2 | 通常随 Docker Desktop 安装 |

### 1.2 系统资源
| 资源 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核 |
| 内存 | 2 GB | 4 GB |
| 磁盘 | 2 GB | 5 GB |

---

## 2. Quick Start（快速启动）

```bash
# 1. 克隆仓库
git clone https://github.com/user/klinelens.git
cd klinelens

# 2. 复制环境配置
cp .env.example .env

# 3. 启动服务（首次会构建镜像，需要几分钟）
docker compose up --build

# 4. 访问应用
# Web UI: http://localhost:3000
# API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

---

## 3. 环境配置

### 3.1 配置文件 (.env)

复制 `.env.example` 为 `.env` 并根据需要修改：

```bash
# ============ Provider 配置 ============
# 数据源选择：yahoo (默认，免费) | polygon | twelvedata
PROVIDER=yahoo

# ============ 缓存配置 ============
# K 线数据缓存时间（秒）
CACHE_TTL=60

# ============ 端口配置 ============
# API 端口（默认 8000）
API_PORT=8000
# Web 端口（默认 3000）
WEB_PORT=3000

# ============ 刷新频率 ============
# 前端自动刷新间隔（秒）
REFRESH_SECONDS=60

# ============ 日志级别 ============
# DEBUG | INFO | WARNING | ERROR
LOG_LEVEL=INFO

# ============ 可选：付费 Provider API Keys ============
# 如果使用 Polygon.io
# POLYGON_API_KEY=your_key_here

# 如果使用 TwelveData
# TWELVEDATA_API_KEY=your_key_here
```

### 3.2 默认值说明
| 变量 | 默认值 | 说明 |
|------|--------|------|
| PROVIDER | yahoo | 免费数据源，无需 API key |
| CACHE_TTL | 60 | 减少对数据源的请求频率 |
| API_PORT | 8000 | FastAPI 后端端口 |
| WEB_PORT | 3000 | Next.js 前端端口 |
| REFRESH_SECONDS | 60 | 前端自动刷新间隔 |

---

## 4. Docker 命令

### 4.1 常用命令
```bash
# 启动（后台运行）
docker compose up -d

# 启动（前台运行，显示日志）
docker compose up

# 重新构建并启动
docker compose up --build

# 停止服务
docker compose down

# 查看日志
docker compose logs -f

# 仅查看 API 日志
docker compose logs -f api

# 仅查看 Web 日志
docker compose logs -f web
```

### 4.2 清理命令
```bash
# 停止并删除容器
docker compose down

# 停止并删除容器、网络、卷
docker compose down -v

# 删除所有未使用的镜像
docker image prune -a
```

---

## 5. 切换 Provider

### 5.1 Yahoo Finance（默认）
- **优点**：免费，无需 API key
- **缺点**：有每日请求限制（约 2000 次），数据延迟 15-20 分钟
- **配置**：
```bash
PROVIDER=yahoo
```

### 5.2 Polygon.io（V1 支持）
- **优点**：实时数据，更高限额
- **缺点**：需要付费 API key
- **配置**：
```bash
PROVIDER=polygon
POLYGON_API_KEY=your_api_key
```

### 5.3 TwelveData（V1 支持）
- **优点**：全球市场覆盖
- **缺点**：需要付费 API key
- **配置**：
```bash
PROVIDER=twelvedata
TWELVEDATA_API_KEY=your_api_key
```

---

## 6. 常见问题排查

### 6.1 端口占用
**问题**：`Error: port 8000 is already in use`

**解决**：
```bash
# 方法 1：修改端口
# 编辑 .env 文件
API_PORT=8001
WEB_PORT=3001

# 方法 2：停止占用端口的进程
lsof -i :8000
kill -9 <PID>
```

### 6.2 Docker 权限问题
**问题**：`permission denied while trying to connect to Docker`

**解决**（Linux）：
```bash
sudo usermod -aG docker $USER
# 重新登录终端
```

### 6.3 拉不到数据
**问题**：API 返回 404 NO_DATA

**可能原因**：
1. Yahoo Finance 限流 → 等待几分钟后重试
2. 无效的 ticker → 检查股票代码是否正确
3. 非交易时间 → 1m 数据仅在交易时段有效

**排查**：
```bash
# 检查 API 健康状态
curl http://localhost:8000/

# 测试获取数据
curl "http://localhost:8000/v1/bars?ticker=AAPL&tf=1d"
```

### 6.4 构建失败
**问题**：Docker 镜像构建失败

**解决**：
```bash
# 清理缓存重新构建
docker compose build --no-cache

# 检查 Docker 资源限制
docker system df
docker system prune
```

### 6.5 Web 无法连接 API
**问题**：前端显示 "Failed to fetch"

**排查**：
```bash
# 检查 API 是否运行
curl http://localhost:8000/

# 检查网络
docker network ls
docker network inspect klinelens-network
```

---

## 7. 开发模式

### 7.1 本地开发（不使用 Docker）
```bash
# Terminal 1: 启动 API
cd apps/api
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Terminal 2: 启动 Web
cd apps/web
npm install
npm run dev
```

### 7.2 混合模式
```bash
# 仅启动 API（Docker）
docker compose up api

# 本地启动 Web（开发模式）
cd apps/web
npm run dev
```

---

## 8. 健康检查

### 8.1 API 健康检查
```bash
curl http://localhost:8000/
# 期望响应: {"status": "ok", "service": "klinelens-api", "provider": "yfinance"}
```

### 8.2 服务状态
```bash
docker compose ps
# 所有服务应显示 "running" 或 "healthy"
```

---

## 9. 更新

### 9.1 更新到最新版本
```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker compose up --build -d
```

### 9.2 回滚
```bash
# 回滚到指定版本
git checkout <commit-hash>
docker compose up --build -d
```
