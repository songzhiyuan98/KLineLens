# KLineLens Makefile
#
# 常用命令简化，使用方法：
#   make help    - 显示帮助
#   make up      - 启动服务
#   make down    - 停止服务
#   make test    - 运行测试

.PHONY: help up down build logs test clean dev

# 默认目标：显示帮助
help:
	@echo "KLineLens 常用命令："
	@echo ""
	@echo "  make up        启动所有服务（后台）"
	@echo "  make up-fg     启动所有服务（前台，显示日志）"
	@echo "  make down      停止所有服务"
	@echo "  make build     重新构建镜像"
	@echo "  make logs      查看实时日志"
	@echo "  make test      运行测试"
	@echo "  make clean     清理 Docker 资源"
	@echo "  make dev       启动开发模式（本地）"
	@echo ""
	@echo "首次使用："
	@echo "  1. cp .env.example .env"
	@echo "  2. make up"
	@echo "  3. 访问 http://localhost:3000"

# 启动服务（后台）
up:
	docker compose up -d

# 启动服务（前台）
up-fg:
	docker compose up

# 停止服务
down:
	docker compose down

# 重新构建
build:
	docker compose build --no-cache

# 查看日志
logs:
	docker compose logs -f

# 仅查看 API 日志
logs-api:
	docker compose logs -f api

# 仅查看 Web 日志
logs-web:
	docker compose logs -f web

# 运行测试
test:
	@echo "运行 API 测试..."
	cd apps/api && python3 -m pytest tests/ -v
	@echo ""
	@echo "运行 Core 测试..."
	cd packages/core && python3 -m pytest tests/ -v

# 清理 Docker 资源
clean:
	docker compose down -v
	docker image prune -f

# 开发模式：本地启动（不使用 Docker）
dev:
	@echo "请在两个终端分别运行："
	@echo ""
	@echo "Terminal 1 (API):"
	@echo "  cd apps/api && uvicorn src.main:app --reload --port 8000"
	@echo ""
	@echo "Terminal 2 (Web):"
	@echo "  cd apps/web && npm run dev"

# 检查服务状态
status:
	docker compose ps

# 健康检查
health:
	@echo "API 健康检查："
	@curl -s http://localhost:8000/ | python3 -m json.tool || echo "API 未运行"
	@echo ""
	@echo "服务状态："
	@docker compose ps
