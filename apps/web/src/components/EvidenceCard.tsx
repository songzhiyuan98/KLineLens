/**
 * 证据列表卡片
 *
 * 显示支持行为判断的证据。
 */

import Card from './Card';
import { Evidence } from '../lib/api';

interface EvidenceCardProps {
  evidence: Evidence[];
}

const NOTE_LABELS: Record<string, string> = {
  volume_increase: 'Volume increasing',
  price_compression: 'Price compressing',
  support_hold: 'Holding support',
  resistance_hold: 'Holding resistance',
  sweep_recovery: 'Sweep and recovery',
  breakout_volume: 'Breakout with volume',
  momentum_strong: 'Strong momentum',
  range_bound: 'Range bound action',
};

export default function EvidenceCard({ evidence }: EvidenceCardProps) {
  if (evidence.length === 0) {
    return (
      <Card title="Evidence">
        <div style={{ color: '#999', fontSize: '0.875rem' }}>
          No significant evidence detected
        </div>
      </Card>
    );
  }

  return (
    <Card title="Evidence">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {evidence.slice(0, 5).map((item, index) => (
          <div
            key={index}
            style={{
              padding: '0.5rem 0.75rem',
              backgroundColor: '#f8f9fa',
              borderRadius: '4px',
              borderLeft: '3px solid #26a69a',
            }}
          >
            {/* 证据说明 */}
            <div style={{
              fontSize: '0.8rem',
              fontWeight: 500,
              color: '#333',
              marginBottom: '0.25rem',
            }}>
              {NOTE_LABELS[item.note] || item.note}
            </div>

            {/* 指标数值 */}
            <div style={{
              fontSize: '0.75rem',
              color: '#999',
              display: 'flex',
              gap: '0.75rem',
              flexWrap: 'wrap',
            }}>
              {Object.entries(item.metrics).map(([key, value]) => (
                <span key={key}>
                  {key}: {typeof value === 'number' ? value.toFixed(2) : value}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
