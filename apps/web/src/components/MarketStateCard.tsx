/**
 * 市场状态卡片
 *
 * 显示当前市场趋势和置信度。
 */

import Card from './Card';
import { MarketState } from '../lib/api';

interface MarketStateCardProps {
  marketState: MarketState;
}

const REGIME_LABELS: Record<string, string> = {
  uptrend: 'Uptrend',
  downtrend: 'Downtrend',
  range: 'Range / Consolidation',
};

const REGIME_COLORS: Record<string, string> = {
  uptrend: '#26a69a',
  downtrend: '#ef5350',
  range: '#ff9800',
};

export default function MarketStateCard({ marketState }: MarketStateCardProps) {
  const color = REGIME_COLORS[marketState.regime] || '#666';
  const label = REGIME_LABELS[marketState.regime] || marketState.regime;
  const confidence = Math.round(marketState.confidence * 100);

  return (
    <Card title="Market State">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* 趋势指示器 */}
        <div style={{
          width: '48px',
          height: '48px',
          borderRadius: '50%',
          backgroundColor: `${color}20`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <span style={{ fontSize: '1.5rem' }}>
            {marketState.regime === 'uptrend' ? '↑' : marketState.regime === 'downtrend' ? '↓' : '↔'}
          </span>
        </div>

        {/* 文字信息 */}
        <div>
          <div style={{
            fontSize: '1.25rem',
            fontWeight: 600,
            color,
          }}>
            {label}
          </div>
          <div style={{
            fontSize: '0.875rem',
            color: '#999',
          }}>
            Confidence: {confidence}%
          </div>
        </div>
      </div>

      {/* 置信度进度条 */}
      <div style={{
        marginTop: '1rem',
        height: '4px',
        backgroundColor: '#f0f0f0',
        borderRadius: '2px',
        overflow: 'hidden',
      }}>
        <div style={{
          width: `${confidence}%`,
          height: '100%',
          backgroundColor: color,
          transition: 'width 0.3s ease',
        }} />
      </div>
    </Card>
  );
}
