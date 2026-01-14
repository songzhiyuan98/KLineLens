# KLineLens Web Dockerfile
#
# Next.js 前端服务容器
# 提供市场分析可视化界面
#
# 构建：docker build -t klinelens-web .
# 运行：docker run -p 3000:3000 klinelens-web

FROM node:20-alpine AS base

# 安装依赖阶段
FROM base AS deps
WORKDIR /app

# 复制依赖文件
COPY package.json package-lock.json* ./

# 安装依赖（使用 npm install 因为是 monorepo 结构）
RUN npm install --legacy-peer-deps

# 构建阶段
FROM base AS builder
WORKDIR /app

# 复制依赖
COPY --from=deps /app/node_modules ./node_modules

# 复制源代码
COPY . .

# 设置构建时环境变量
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_REFRESH_SECONDS=60
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_REFRESH_SECONDS=$NEXT_PUBLIC_REFRESH_SECONDS

# 构建应用
RUN npm run build

# 生产阶段
FROM base AS runner
WORKDIR /app

# 设置生产环境
ENV NODE_ENV=production

# 创建非 root 用户（安全最佳实践）
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 复制构建产物
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 切换到非 root 用户
USER nextjs

# 暴露端口
EXPOSE 3000

# 设置运行时环境变量
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# 启动命令
CMD ["node", "server.js"]
