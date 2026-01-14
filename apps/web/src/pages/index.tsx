/**
 * 首页 - 股票代码搜索页面
 *
 * KLineLens 的主入口页面。
 * 用户在此输入股票代码（如 TSLA, AAPL）开始分析。
 *
 * 功能:
 * - 显示应用标题和简介
 * - 提供股票代码输入框
 * - 跳转到详情分析页面
 */

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/router';

/**
 * 首页组件
 *
 * 提供简洁的搜索界面，用户输入股票代码后跳转到分析页面。
 *
 * @returns 首页 JSX
 */
export default function Home() {
  // 股票代码输入状态
  const [ticker, setTicker] = useState('');
  const router = useRouter();

  /**
   * 处理表单提交
   *
   * 清理用户输入并跳转到分析页面。
   *
   * @param e - 表单事件
   */
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    // 清理输入: 去除空格并转大写
    const sanitized = ticker.trim().toUpperCase();
    if (sanitized) {
      router.push(`/t/${sanitized}`);
    }
  };

  return (
    <main style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      fontFamily: 'system-ui, sans-serif',
    }}>
      {/* 应用标题 */}
      <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>KLineLens</h1>
      {/* 应用简介 */}
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Market structure analysis terminal
      </p>

      {/* 搜索表单 */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
        {/* 股票代码输入框 */}
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="Enter ticker (e.g., TSLA)"
          style={{
            padding: '0.75rem 1rem',
            fontSize: '1rem',
            border: '1px solid #ccc',
            borderRadius: '4px',
            width: '250px',
          }}
        />
        {/* 分析按钮 */}
        <button
          type="submit"
          style={{
            padding: '0.75rem 1.5rem',
            fontSize: '1rem',
            backgroundColor: '#000',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Analyze
        </button>
      </form>
    </main>
  );
}
