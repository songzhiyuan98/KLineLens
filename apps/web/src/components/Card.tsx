/**
 * 通用卡片组件
 */

import { ReactNode } from 'react';

interface CardProps {
  title: string;
  children: ReactNode;
  action?: ReactNode;
}

export default function Card({ title, children, action }: CardProps) {
  return (
    <div style={{
      backgroundColor: '#fff',
      border: '1px solid #eaeaea',
      borderRadius: '8px',
      overflow: 'hidden',
    }}>
      {/* 卡片头部 */}
      <div style={{
        padding: '0.75rem 1rem',
        borderBottom: '1px solid #eaeaea',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#fafafa',
      }}>
        <h3 style={{
          margin: 0,
          fontSize: '0.8rem',
          fontWeight: 600,
          color: '#666',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}>
          {title}
        </h3>
        {action}
      </div>

      {/* 卡片内容 */}
      <div style={{ padding: '1rem' }}>
        {children}
      </div>
    </div>
  );
}
