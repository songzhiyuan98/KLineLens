/**
 * 时间线卡片
 *
 * 显示最近的市场事件。
 */

import Card from './Card';
import { TimelineEvent } from '../lib/api';

interface TimelineCardProps {
  events: TimelineEvent[];
}

const EVENT_LABELS: Record<string, string> = {
  regime_change: 'Regime Change',
  behavior_shift: 'Behavior Shift',
  probability_change: 'Probability Change',
  breakout_attempt: 'Breakout Attempt',
  breakout_confirmed: 'Breakout Confirmed',
  fakeout: 'Fakeout Detected',
};

const EVENT_COLORS: Record<string, string> = {
  regime_change: '#2196f3',
  behavior_shift: '#ff9800',
  probability_change: '#9c27b0',
  breakout_attempt: '#26a69a',
  breakout_confirmed: '#4caf50',
  fakeout: '#ef5350',
};

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

export default function TimelineCard({ events }: TimelineCardProps) {
  if (events.length === 0) {
    return (
      <Card title="Timeline">
        <div style={{ color: '#999', fontSize: '0.875rem' }}>
          No events recorded
        </div>
      </Card>
    );
  }

  return (
    <Card title="Timeline">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {events.slice(0, 5).map((event, index) => {
          const color = EVENT_COLORS[event.event_type] || '#666';
          const label = EVENT_LABELS[event.event_type] || event.event_type;

          return (
            <div
              key={index}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
              }}
            >
              {/* 时间线点 */}
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: color,
                marginTop: '6px',
                flexShrink: 0,
              }} />

              {/* 事件内容 */}
              <div style={{ flex: 1 }}>
                <div style={{
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  color: '#333',
                }}>
                  {label}
                </div>
                <div style={{
                  fontSize: '0.75rem',
                  color: '#999',
                  marginTop: '0.125rem',
                }}>
                  {formatDate(event.ts)} {formatTime(event.ts)}
                  {event.delta !== 0 && ` • Δ${event.delta > 0 ? '+' : ''}${(event.delta * 100).toFixed(0)}%`}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
