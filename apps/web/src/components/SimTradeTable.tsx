/**
 * SimTradeTable 组件
 *
 * 0DTE 交易计划表格，显示当前交易状态和建议。
 * 支持状态：WAIT, WATCH, ARMED, ENTER, HOLD, TRIM, EXIT
 */

import React from 'react';

// 类型定义
export interface TradePlan {
  status: 'WAIT' | 'WATCH' | 'ARMED' | 'ENTER' | 'HOLD' | 'TRIM' | 'EXIT';
  direction: 'CALL' | 'PUT' | 'NONE';
  entryZone: string | null;
  entryUnderlying: string | null;
  targetUnderlying: string | null;
  invalidation: string | null;
  risk: 'LOW' | 'MED' | 'HIGH';
  watchlistHint: string | null;
  reasons: string[];
  barsSinceEntry: number;
  targetAttempts: number;
}

export interface SimTradeData {
  ticker: string;
  ts: string;
  plan: TradePlan;
  history: Array<{
    ts: string;
    status: string;
    direction: string;
  }>;
  stats: {
    tradesToday: number;
    maxTradesPerDay: number;
  };
}

interface Props {
  data: SimTradeData | null;
  loading: boolean;
  error: string | null;
  lang: 'zh' | 'en';
  onRefresh?: () => void;
}

// 颜色常量
const C = {
  bg: '#ffffff',
  text: '#0a0a0a',
  textSecondary: '#525252',
  textMuted: '#a3a3a3',
  divider: '#e5e5e5',
  dividerLight: '#f5f5f5',
  bullish: '#16a34a',
  bearish: '#dc2626',
  accent: '#2563eb',
  warn: '#d97706',
};

// 状态颜色
const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  WAIT: { bg: '#f5f5f5', text: '#737373' },
  WATCH: { bg: '#fef3c7', text: '#92400e' },
  ARMED: { bg: '#fed7aa', text: '#c2410c' },
  ENTER: { bg: '#bbf7d0', text: '#15803d' },
  HOLD: { bg: '#bfdbfe', text: '#1d4ed8' },
  TRIM: { bg: '#e9d5ff', text: '#7c3aed' },
  EXIT: { bg: '#e5e5e5', text: '#525252' },
};

// 多语言
const translations = {
  zh: {
    title: '0DTE 交易计划',
    time: '时间',
    status: '状态',
    direction: '方向',
    entry: '入场',
    target: '目标',
    invalidation: '失效',
    risk: '风险',
    watch: '合约提示',
    reasons: '原因',
    noData: '无数据',
    loading: '加载中...',
    outsideHours: '非交易时段',
    todayTrades: '今日交易',
    refresh: '刷新',
    CALL: '做多',
    PUT: '做空',
    NONE: '-',
    LOW: '低',
    MED: '中',
    HIGH: '高',
    history: '状态历史',
  },
  en: {
    title: '0DTE Trade Plan',
    time: 'Time',
    status: 'Status',
    direction: 'Dir',
    entry: 'Entry',
    target: 'Target',
    invalidation: 'Invalid',
    risk: 'Risk',
    watch: 'Watch',
    reasons: 'Reasons',
    noData: 'No data',
    loading: 'Loading...',
    outsideHours: 'Outside trading hours',
    todayTrades: 'Today',
    refresh: 'Refresh',
    CALL: 'CALL',
    PUT: 'PUT',
    NONE: '-',
    LOW: 'Low',
    MED: 'Med',
    HIGH: 'High',
    history: 'History',
  },
};

export const SimTradeTable: React.FC<Props> = ({
  data,
  loading,
  error,
  lang,
  onRefresh,
}) => {
  const t = translations[lang];

  // 样式
  const styles: Record<string, React.CSSProperties> = {
    container: {
      fontSize: 'clamp(0.6875rem, 0.6rem + 0.2vw, 0.8125rem)',
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '0.75rem',
    },
    title: {
      fontSize: 'clamp(0.75rem, 0.65rem + 0.25vw, 0.875rem)',
      fontWeight: 600,
      color: C.text,
    },
    stats: {
      fontSize: 'clamp(0.625rem, 0.55rem + 0.2vw, 0.75rem)',
      color: C.textMuted,
    },
    table: {
      width: '100%',
      borderCollapse: 'collapse',
      fontSize: 'inherit',
    },
    th: {
      textAlign: 'left' as const,
      padding: '0.5rem 0.375rem',
      borderBottom: `1px solid ${C.divider}`,
      color: C.textSecondary,
      fontWeight: 500,
      fontSize: 'clamp(0.625rem, 0.55rem + 0.2vw, 0.75rem)',
    },
    td: {
      padding: '0.625rem 0.375rem',
      borderBottom: `1px solid ${C.dividerLight}`,
      verticalAlign: 'top' as const,
    },
    statusBadge: {
      display: 'inline-block',
      padding: '0.125rem 0.5rem',
      borderRadius: '4px',
      fontWeight: 600,
      fontSize: 'clamp(0.625rem, 0.55rem + 0.15vw, 0.6875rem)',
    },
    directionBadge: {
      display: 'inline-block',
      padding: '0.125rem 0.375rem',
      borderRadius: '3px',
      fontWeight: 500,
      fontSize: 'clamp(0.5625rem, 0.5rem + 0.15vw, 0.625rem)',
    },
    riskBadge: {
      display: 'inline-block',
      padding: '0.125rem 0.375rem',
      borderRadius: '3px',
      fontSize: 'clamp(0.5625rem, 0.5rem + 0.15vw, 0.625rem)',
    },
    reasons: {
      marginTop: '0.5rem',
      padding: '0.5rem',
      backgroundColor: C.dividerLight,
      borderRadius: '4px',
    },
    reasonItem: {
      fontSize: 'clamp(0.5625rem, 0.5rem + 0.15vw, 0.6875rem)',
      color: C.textSecondary,
      marginBottom: '0.25rem',
    },
    historySection: {
      marginTop: '0.75rem',
      paddingTop: '0.75rem',
      borderTop: `1px solid ${C.dividerLight}`,
    },
    historyTitle: {
      fontSize: 'clamp(0.625rem, 0.55rem + 0.2vw, 0.75rem)',
      fontWeight: 500,
      color: C.textMuted,
      marginBottom: '0.5rem',
    },
    historyItem: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.25rem',
      marginRight: '0.75rem',
      fontSize: 'clamp(0.5625rem, 0.5rem + 0.15vw, 0.625rem)',
      color: C.textSecondary,
    },
    refreshBtn: {
      padding: '0.25rem 0.5rem',
      fontSize: 'clamp(0.5625rem, 0.5rem + 0.15vw, 0.625rem)',
      color: C.accent,
      background: 'none',
      border: `1px solid ${C.accent}`,
      borderRadius: '3px',
      cursor: 'pointer',
    },
    empty: {
      textAlign: 'center' as const,
      padding: '2rem',
      color: C.textMuted,
    },
    watchHint: {
      fontSize: 'clamp(0.5625rem, 0.5rem + 0.15vw, 0.6875rem)',
      color: C.accent,
      fontStyle: 'italic',
    },
  };

  // 获取状态样式
  const getStatusStyle = (status: string): React.CSSProperties => {
    const colors = STATUS_COLORS[status] || STATUS_COLORS.WAIT;
    return {
      ...styles.statusBadge,
      backgroundColor: colors.bg,
      color: colors.text,
    };
  };

  // 获取方向样式
  const getDirectionStyle = (direction: string): React.CSSProperties => {
    if (direction === 'CALL') {
      return {
        ...styles.directionBadge,
        backgroundColor: '#dcfce7',
        color: C.bullish,
      };
    } else if (direction === 'PUT') {
      return {
        ...styles.directionBadge,
        backgroundColor: '#fee2e2',
        color: C.bearish,
      };
    }
    return {
      ...styles.directionBadge,
      backgroundColor: C.dividerLight,
      color: C.textMuted,
    };
  };

  // 获取风险样式
  const getRiskStyle = (risk: string): React.CSSProperties => {
    if (risk === 'HIGH') {
      return {
        ...styles.riskBadge,
        backgroundColor: '#fee2e2',
        color: C.bearish,
      };
    } else if (risk === 'LOW') {
      return {
        ...styles.riskBadge,
        backgroundColor: '#dcfce7',
        color: C.bullish,
      };
    }
    return {
      ...styles.riskBadge,
      backgroundColor: '#fef3c7',
      color: '#92400e',
    };
  };

  // 渲染加载状态
  if (loading && !data) {
    return (
      <div style={styles.container}>
        <div style={styles.empty}>{t.loading}</div>
      </div>
    );
  }

  // 渲染错误状态
  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.empty}>{error}</div>
      </div>
    );
  }

  // 渲染空状态
  if (!data) {
    return (
      <div style={styles.container}>
        <div style={styles.empty}>{t.noData}</div>
      </div>
    );
  }

  const { plan, history, stats } = data;

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <span style={styles.title}>{t.title}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={styles.stats}>
            {t.todayTrades}: {stats.tradesToday}/{stats.maxTradesPerDay}
          </span>
          {onRefresh && (
            <button style={styles.refreshBtn} onClick={onRefresh}>
              {t.refresh}
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>{t.time}</th>
            <th style={styles.th}>{t.status}</th>
            <th style={styles.th}>{t.direction}</th>
            <th style={styles.th}>{t.entry}</th>
            <th style={styles.th}>{t.target}</th>
            <th style={styles.th}>{t.invalidation}</th>
            <th style={styles.th}>{t.risk}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={styles.td}>
              {data.ts ? data.ts.split(' ')[1] || data.ts.slice(-8, -3) : '-'}
            </td>
            <td style={styles.td}>
              <span style={getStatusStyle(plan.status)}>{plan.status}</span>
            </td>
            <td style={styles.td}>
              <span style={getDirectionStyle(plan.direction)}>
                {t[plan.direction as keyof typeof t] || plan.direction}
              </span>
            </td>
            <td style={styles.td}>
              {plan.entryUnderlying || '-'}
            </td>
            <td style={styles.td}>
              {plan.targetUnderlying || '-'}
            </td>
            <td style={styles.td}>
              {plan.invalidation || '-'}
            </td>
            <td style={styles.td}>
              <span style={getRiskStyle(plan.risk)}>
                {t[plan.risk as keyof typeof t] || plan.risk}
              </span>
            </td>
          </tr>
        </tbody>
      </table>

      {/* Watch Hint */}
      {plan.watchlistHint && (
        <div style={{ marginTop: '0.5rem' }}>
          <span style={styles.watchHint}>{plan.watchlistHint}</span>
        </div>
      )}

      {/* Reasons */}
      {plan.reasons && plan.reasons.length > 0 && (
        <div style={styles.reasons}>
          {plan.reasons.map((reason, i) => (
            <div key={i} style={styles.reasonItem}>
              • {reason}
            </div>
          ))}
        </div>
      )}

      {/* History */}
      {history && history.length > 0 && (
        <div style={styles.historySection}>
          <div style={styles.historyTitle}>{t.history}</div>
          <div>
            {history.map((item, i) => (
              <span key={i} style={styles.historyItem}>
                <span style={getStatusStyle(item.status)}>{item.status}</span>
                <span>{item.ts}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SimTradeTable;
