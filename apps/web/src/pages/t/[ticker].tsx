/**
 * 股票详情分析页面
 *
 * 显示指定股票的完整市场分析结果。
 * 路由: /t/[ticker] (如 /t/TSLA)
 *
 * 页面布局:
 * - 左侧: K 线图表（占 2/3 宽度）
 * - 右侧: 分析面板（占 1/3 宽度）
 *   - Market State: 市场状态
 *   - Behavior: 行为概率
 *   - Evidence: 证据列表
 *   - Timeline: 时间线事件
 *   - Playbook: 条件剧本
 *
 * 当前状态: 占位实现，将在 Milestone 4 中完成
 */

import { useRouter } from 'next/router';

/**
 * 股票详情页组件
 *
 * 从 URL 获取股票代码并显示分析结果。
 *
 * @returns 详情页 JSX
 */
export default function TickerDetail() {
  const router = useRouter();
  // 从路由获取股票代码
  const { ticker } = router.query;

  return (
    <main style={{
      padding: '2rem',
      fontFamily: 'system-ui, sans-serif',
    }}>
      {/* 页面头部 */}
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem',
      }}>
        {/* 面包屑导航 */}
        <h1 style={{ fontSize: '1.5rem' }}>
          <a href="/" style={{ textDecoration: 'none', color: 'inherit' }}>KLineLens</a>
          {' / '}
          <span style={{ color: '#0070f3' }}>{ticker}</span>
        </h1>
      </header>

      {/* 主要内容区域: 左右两栏布局 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '2fr 1fr',
        gap: '2rem',
      }}>
        {/* 左侧: K 线图表区域（占位） */}
        <div style={{
          backgroundColor: '#f5f5f5',
          borderRadius: '8px',
          padding: '2rem',
          minHeight: '400px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <p style={{ color: '#999' }}>Chart will be rendered here</p>
        </div>

        {/* 右侧: 分析面板区域 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* 市场状态卡片 */}
          <Card title="Market State">Regime and confidence will appear here</Card>
          {/* 行为概率卡片 */}
          <Card title="Behavior">Probabilities will appear here</Card>
          {/* 证据列表卡片 */}
          <Card title="Evidence">Evidence items will appear here</Card>
          {/* 时间线卡片 */}
          <Card title="Timeline">Recent events will appear here</Card>
          {/* 条件剧本卡片 */}
          <Card title="Playbook">Plan A/B will appear here</Card>
        </div>
      </div>
    </main>
  );
}

/**
 * 信息卡片组件
 *
 * 用于展示各类分析信息的通用卡片。
 *
 * @param title - 卡片标题
 * @param children - 卡片内容
 * @returns 卡片 JSX
 */
function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      backgroundColor: '#fff',
      border: '1px solid #eee',
      borderRadius: '8px',
      padding: '1rem',
    }}>
      {/* 卡片标题 */}
      <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.875rem', color: '#666' }}>
        {title}
      </h3>
      {/* 卡片内容 */}
      <div style={{ color: '#999', fontSize: '0.875rem' }}>{children}</div>
    </div>
  );
}
