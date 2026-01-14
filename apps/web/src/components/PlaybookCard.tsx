/**
 * Playbook 卡片
 *
 * 显示条件交易计划。
 */

import Card from './Card';
import { PlaybookPlan } from '../lib/api';

interface PlaybookCardProps {
  plans: PlaybookPlan[];
}

const CONDITION_LABELS: Record<string, string> = {
  pullback_support: 'If price pulls back to support',
  breakout_resistance: 'If price breaks resistance',
  rejection_resistance: 'If price rejects at resistance',
  breakdown_support: 'If price breaks support',
  bounce_support: 'If price bounces off support',
  fade_resistance: 'If price fades at resistance',
};

const RISK_LABELS: Record<string, string> = {
  low: 'Low Risk',
  medium: 'Medium Risk',
  high: 'High Risk',
};

export default function PlaybookCard({ plans }: PlaybookCardProps) {
  if (plans.length === 0) {
    return (
      <Card title="Playbook">
        <div style={{ color: '#999', fontSize: '0.875rem' }}>
          No actionable plans available
        </div>
      </Card>
    );
  }

  return (
    <Card title="Playbook">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {plans.map((plan, index) => (
          <div
            key={index}
            style={{
              padding: '0.75rem',
              backgroundColor: index === 0 ? '#f0f9f4' : '#f8f9fa',
              borderRadius: '6px',
              border: index === 0 ? '1px solid #26a69a40' : '1px solid #eaeaea',
            }}
          >
            {/* 计划名称 */}
            <div style={{
              fontSize: '0.9rem',
              fontWeight: 600,
              color: '#333',
              marginBottom: '0.5rem',
            }}>
              {plan.name}
            </div>

            {/* 条件 */}
            <div style={{
              fontSize: '0.8rem',
              color: '#666',
              marginBottom: '0.75rem',
            }}>
              {CONDITION_LABELS[plan.condition] || plan.condition}
            </div>

            {/* 价格水平 */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '0.5rem',
              fontSize: '0.75rem',
            }}>
              <div>
                <div style={{ color: '#999' }}>Entry</div>
                <div style={{ fontWeight: 600, color: '#333' }}>
                  ${plan.level.toFixed(2)}
                </div>
              </div>
              <div>
                <div style={{ color: '#999' }}>Target</div>
                <div style={{ fontWeight: 600, color: '#26a69a' }}>
                  ${plan.target.toFixed(2)}
                </div>
              </div>
              <div>
                <div style={{ color: '#999' }}>Stop</div>
                <div style={{ fontWeight: 600, color: '#ef5350' }}>
                  ${plan.invalidation.toFixed(2)}
                </div>
              </div>
            </div>

            {/* 风险标签 */}
            <div style={{
              marginTop: '0.5rem',
              fontSize: '0.7rem',
              color: '#999',
            }}>
              {RISK_LABELS[plan.risk] || plan.risk}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
