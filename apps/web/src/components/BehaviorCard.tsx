/**
 * 行为概率卡片
 *
 * 显示 5 种 Wyckoff 行为的概率分布。
 */

import Card from './Card';
import { Behavior } from '../lib/api';

interface BehaviorCardProps {
  behavior: Behavior;
}

const BEHAVIOR_LABELS: Record<string, string> = {
  accumulation: 'Accumulation',
  shakeout: 'Shakeout',
  markup: 'Markup',
  distribution: 'Distribution',
  markdown: 'Markdown',
};

const BEHAVIOR_COLORS: Record<string, string> = {
  accumulation: '#4caf50',
  shakeout: '#ff9800',
  markup: '#26a69a',
  distribution: '#f44336',
  markdown: '#ef5350',
};

export default function BehaviorCard({ behavior }: BehaviorCardProps) {
  // 按概率排序
  const sortedBehaviors = Object.entries(behavior.probabilities)
    .sort(([, a], [, b]) => b - a);

  return (
    <Card title="Behavior Probabilities">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {sortedBehaviors.map(([name, probability]) => {
          const percent = Math.round(probability * 100);
          const isDominant = name === behavior.dominant;
          const color = BEHAVIOR_COLORS[name] || '#666';
          const label = BEHAVIOR_LABELS[name] || name;

          return (
            <div key={name}>
              {/* 标签和百分比 */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: '0.25rem',
              }}>
                <span style={{
                  fontSize: '0.8rem',
                  fontWeight: isDominant ? 600 : 400,
                  color: isDominant ? color : '#666',
                }}>
                  {label}
                  {isDominant && ' ★'}
                </span>
                <span style={{
                  fontSize: '0.8rem',
                  fontWeight: isDominant ? 600 : 400,
                  color: isDominant ? color : '#999',
                }}>
                  {percent}%
                </span>
              </div>

              {/* 进度条 */}
              <div style={{
                height: '6px',
                backgroundColor: '#f0f0f0',
                borderRadius: '3px',
                overflow: 'hidden',
              }}>
                <div style={{
                  width: `${percent}%`,
                  height: '100%',
                  backgroundColor: isDominant ? color : '#ccc',
                  transition: 'width 0.3s ease',
                }} />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
