/**
 * Next.js 配置文件
 *
 * 配置说明：
 * - output: standalone 用于 Docker 部署优化
 * - reactStrictMode: 启用 React 严格模式
 *
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  reactStrictMode: true,

  // Docker 部署优化：生成独立输出目录
  output: 'standalone',

  // 环境变量（运行时可用）
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_REFRESH_SECONDS: process.env.NEXT_PUBLIC_REFRESH_SECONDS || '60',
  },
}

module.exports = nextConfig
