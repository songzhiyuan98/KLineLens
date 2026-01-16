/**
 * Extended Hours 上下文卡片
 *
 * 显示盘前/盘后的市场先验信息：
 * - 盘前形态 (Premarket Regime)
 * - 方向偏向 (Bias)
 * - 关键位 (Key Zones)
 * - 数据质量指示
 */

import { EHContextResponse, EHKeyZone } from '../lib/api';
import { useI18n } from '../lib/i18n';

interface EHContextCardProps {
  ehContext: EHContextResponse;
}

// Regime 颜色映射
const REGIME_COLORS: Record<string, string> = {
  trend_continuation: '#16a34a',
  gap_and_go: '#2563eb',
  gap_fill_bias: '#d97706',
  range_day_setup: '#6b7280',
  unavailable: '#9ca3af',
};

// Bias 配置
const BIAS_CONFIG: Record<string, { icon: string; color: string }> = {
  bullish: { icon: '↑', color: '#16a34a' },
  bearish: { icon: '↓', color: '#dc2626' },
  neutral: { icon: '↔', color: '#6b7280' },
};

// Quality 颜色映射
const QUALITY_COLORS: Record<string, string> = {
  complete: '#16a34a',
  partial: '#d97706',
  minimal: '#9ca3af',
};

// 终端风格
const MONO = '"SF Mono", "Roboto Mono", "Fira Code", Menlo, Monaco, monospace';

export default function EHContextCard({ ehContext }: EHContextCardProps) {
  const { t } = useI18n();

  const regimeKey = ehContext.premarket_regime || 'unavailable';
  const biasKey = ehContext.premarket_bias || 'neutral';
  const qualityKey = ehContext.data_quality || 'minimal';

  const regimeColor = REGIME_COLORS[regimeKey] || REGIME_COLORS.unavailable;
  const biasConfig = BIAS_CONFIG[biasKey] || BIAS_CONFIG.neutral;
  const qualityColor = QUALITY_COLORS[qualityKey] || QUALITY_COLORS.minimal;

  // 只显示前 4 个关键位
  const topZones = ehContext.key_zones.slice(0, 4);

  return (
    <div style={{
      padding: '0.75rem 0',
      fontSize: 'clamp(0.625rem, 0.55rem + 0.2vw, 0.8125rem)',
      fontFamily: MONO,
    }}>
      {/* 标题行 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '0.75rem',
        paddingBottom: '0.5rem',
        borderBottom: '1px solid #f0f0f0',
      }}>
        <span style={{ color: '#a3a3a3', fontWeight: 500 }}>
          {t('eh_context')}
        </span>
        <span style={{
          fontSize: '0.625rem',
          padding: '0.125rem 0.375rem',
          borderRadius: '2px',
          backgroundColor: `${qualityColor}15`,
          color: qualityColor,
        }}>
          {t(`eh_quality_${qualityKey}`)}
        </span>
      </div>

      {/* Regime + Bias 行 */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        marginBottom: '0.75rem',
      }}>
        {/* Regime */}
        <div style={{ flex: 1 }}>
          <div style={{ color: '#a3a3a3', fontSize: '0.5625rem', marginBottom: '0.25rem' }}>
            {t('eh_regime')}
          </div>
          <div style={{
            color: regimeColor,
            fontWeight: 600,
            fontSize: 'clamp(0.6875rem, 0.6rem + 0.2vw, 0.875rem)',
          }}>
            {t(`eh_regime_${regimeKey}`)}
          </div>
        </div>

        {/* Bias */}
        <div style={{ flex: 1 }}>
          <div style={{ color: '#a3a3a3', fontSize: '0.5625rem', marginBottom: '0.25rem' }}>
            {t('eh_bias')}
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.25rem',
            color: biasConfig.color,
            fontWeight: 600,
            fontSize: 'clamp(0.6875rem, 0.6rem + 0.2vw, 0.875rem)',
          }}>
            <span>{biasConfig.icon}</span>
            <span>{t(`eh_bias_${biasKey}`)}</span>
          </div>
        </div>

        {/* Confidence */}
        <div style={{ flex: 1 }}>
          <div style={{ color: '#a3a3a3', fontSize: '0.5625rem', marginBottom: '0.25rem' }}>
            {t('eh_confidence')}
          </div>
          <div style={{
            color: '#525252',
            fontWeight: 600,
            fontSize: 'clamp(0.6875rem, 0.6rem + 0.2vw, 0.875rem)',
          }}>
            {Math.round(ehContext.regime_confidence * 100)}%
          </div>
        </div>
      </div>

      {/* Key Zones */}
      {topZones.length > 0 && (
        <div>
          <div style={{
            color: '#a3a3a3',
            fontSize: '0.5625rem',
            marginBottom: '0.375rem',
          }}>
            {t('eh_key_levels')}
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '0.25rem 0.75rem',
          }}>
            {topZones.map((zone, idx) => (
              <div key={idx} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <span style={{
                  color: getZoneColor(zone.zone),
                  fontWeight: 500,
                }}>
                  {zone.zone}
                </span>
                <span style={{ color: '#525252' }}>
                  ${zone.price.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Gap 信息 */}
      {ehContext.levels.gap !== 0 && (
        <div style={{
          marginTop: '0.5rem',
          paddingTop: '0.5rem',
          borderTop: '1px solid #f5f5f5',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span style={{ color: '#a3a3a3' }}>
            {t('eh_gap')}
          </span>
          <span style={{
            color: ehContext.levels.gap > 0 ? '#16a34a' : '#dc2626',
            fontWeight: 600,
          }}>
            {ehContext.levels.gap > 0 ? '+' : ''}{ehContext.levels.gap.toFixed(2)}
          </span>
        </div>
      )}
    </div>
  );
}

// 根据 zone 类型返回颜色
function getZoneColor(zone: string): string {
  switch (zone) {
    case 'YC':
      return '#f59e0b';  // 橙色 - 昨收
    case 'PMH':
    case 'PML':
      return '#8b5cf6';  // 紫色 - 盘前
    case 'AHH':
    case 'AHL':
      return '#6366f1';  // 靛蓝 - 盘后
    case 'YH':
    case 'YL':
      return '#525252';  // 灰色 - 昨高低
    default:
      return '#6b7280';
  }
}
