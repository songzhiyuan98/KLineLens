/**
 * 布局组件
 *
 * 提供统一的页面布局，包括头部导航。
 */

import Link from 'next/link';
import { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 头部导航 */}
      <header style={{
        backgroundColor: '#fff',
        borderBottom: '1px solid #eaeaea',
        padding: '0 3rem',
        height: '56px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        {/* Logo */}
        <Link href="/" style={{
          fontSize: '1.25rem',
          fontWeight: 700,
          color: '#000',
        }}>
          KLineLens
        </Link>

        {/* 导航链接 */}
        <nav style={{ display: 'flex', gap: '1.5rem' }}>
          <Link href="/" style={{ color: '#666', fontSize: '0.875rem' }}>
            Home
          </Link>
          <Link href="/settings" style={{ color: '#666', fontSize: '0.875rem' }}>
            Settings
          </Link>
        </nav>
      </header>

      {/* 主内容区 */}
      <main style={{ flex: 1 }}>
        {children}
      </main>

      {/* 页脚 */}
      <footer style={{
        backgroundColor: '#fff',
        borderTop: '1px solid #eaeaea',
        padding: '1rem 3rem',
        textAlign: 'center',
        fontSize: '0.75rem',
        color: '#999',
      }}>
        KLineLens - Market Structure Analysis Terminal
      </footer>
    </div>
  );
}
