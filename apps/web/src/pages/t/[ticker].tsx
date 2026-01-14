/**
 * 股票详情分析页面
 */

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/router';
import dynamic from 'next/dynamic';
import Head from 'next/head';
import { Layout, DetailPageSkeleton } from '../../components';
import { useAnalysis, useBars } from '../../lib/hooks';
import { useI18n } from '../../lib/i18n';
import { calculateVolumeRatio } from '../../components/CandlestickChart';

const CandlestickChart = dynamic(
  () => import('../../components/CandlestickChart'),
  { ssr: false }
);

type Timeframe = '1m' | '5m' | '1d';

const VOLUME_THRESHOLD = 1.8;

// Evidence item with bar_time for chart highlighting
interface EvidenceItem {
  behavior: string;
  bar_time: string;
  metrics: Record<string, unknown>;
  note: string;
}

const styles = {
  page: {
    backgroundColor: '#f8f9fa',
    color: '#1a1a1a',
    minHeight: '100vh',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    lineHeight: 1.5,
  },
  // 专业数字字体
  numericFont: {
    fontFamily: '"SF Mono", "Roboto Mono", Menlo, monospace',
    fontVariantNumeric: 'tabular-nums',
  },
  container: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '2rem 3rem',
  },
  ticker: {
    fontSize: '2rem',
    fontWeight: 700,
    marginBottom: '0.25rem',
    color: '#1a1a1a',
  },
  priceRow: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '1rem',
    marginBottom: '1.5rem',
    flexWrap: 'wrap' as const,
  },
  price: {
    fontSize: '2.5rem',
    fontWeight: 700,
    color: '#1a1a1a',
    fontFamily: '"SF Mono", "Roboto Mono", Menlo, monospace',
    fontVariantNumeric: 'tabular-nums',
  },
  change: {
    fontSize: '1rem',
  },
  regimeTag: {
    fontSize: '0.75rem',
    padding: '0.25rem 0.75rem',
    borderRadius: '4px',
    border: '1px solid',
  },
  controls: {
    display: 'flex',
    alignItems: 'center',
    gap: '1.5rem',
    marginBottom: '2rem',
    fontSize: '0.875rem',
    color: '#999',
  },
  tfButton: {
    padding: '0.5rem 1rem',
    background: 'transparent',
    border: '1px solid #eaeaea',
    color: '#666',
    cursor: 'pointer',
    borderRadius: '20px',
    fontSize: '0.875rem',
    transition: 'all 0.2s',
  },
  tfButtonActive: {
    backgroundColor: '#26a69a',
    borderColor: '#26a69a',
    color: '#fff',
  },
  refreshBtn: {
    background: 'transparent',
    border: 'none',
    color: '#26a69a',
    cursor: 'pointer',
    fontSize: '0.875rem',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr 320px',
    gap: '3rem',
  },
  section: {
    marginBottom: '2rem',
  },
  sectionTitle: {
    fontSize: '0.875rem',
    color: '#666',
    fontWeight: 600,
    marginBottom: '1rem',
  },
  card: {
    marginBottom: '1rem',
  },
  behaviorRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    marginBottom: '0.75rem',
  },
  behaviorName: {
    width: '3rem',
    fontSize: '0.875rem',
    color: '#666',
  },
  behaviorBar: {
    flex: 1,
    height: '8px',
    backgroundColor: '#eaeaea',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  behaviorFill: {
    height: '100%',
    borderRadius: '4px',
  },
  behaviorPct: {
    width: '2.5rem',
    textAlign: 'right' as const,
    fontSize: '0.875rem',
    color: '#666',
  },
  playbookGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1rem',
  },
  planItem: {
    paddingBottom: '1rem',
    borderBottom: '1px solid #eaeaea',
  },
  planLabel: {
    fontSize: '0.75rem',
    color: '#26a69a',
    fontWeight: 600,
    marginBottom: '0.25rem',
  },
  planCondition: {
    fontSize: '0.875rem',
    color: '#666',
    marginBottom: '1rem',
  },
  planRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.875rem',
    marginBottom: '0.5rem',
    color: '#1a1a1a',
  },
  planKey: {
    color: '#999',
  },
  stateRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.75rem',
  },
  confidenceBar: {
    flex: 1,
    height: '6px',
    backgroundColor: '#eaeaea',
    borderRadius: '3px',
    overflow: 'hidden',
  },
  evidenceItem: {
    marginBottom: '0.75rem',
    paddingBottom: '0.75rem',
    borderBottom: '1px solid #f0f0f0',
  },
  evidenceTop: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.875rem',
    marginBottom: '0.25rem',
    color: '#1a1a1a',
  },
  evidenceMetrics: {
    fontSize: '0.75rem',
    color: '#999',
  },
  timelineItem: {
    display: 'flex',
    gap: '0.75rem',
    marginBottom: '0.75rem',
  },
  timelineDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    backgroundColor: '#999',
    marginTop: '0.5rem',
    flexShrink: 0,
  },
  timelineText: {
    fontSize: '0.875rem',
    color: '#1a1a1a',
  },
  timelineDate: {
    fontSize: '0.75rem',
    color: '#999',
  },
  legend: {
    display: 'flex',
    gap: '1.5rem',
    fontSize: '0.75rem',
    color: '#999',
    marginTop: '0.5rem',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.375rem',
  },
  legendBox: {
    width: '12px',
    height: '8px',
    borderRadius: '2px',
  },
  empty: {
    color: '#999',
    fontSize: '0.875rem',
  },
  error: {
    textAlign: 'center' as const,
    padding: '4rem 0',
  },
  errorText: {
    color: '#ef5350',
    marginBottom: '0.5rem',
    fontSize: '1rem',
  },
  errorMsg: {
    color: '#999',
    fontSize: '0.875rem',
    marginBottom: '1rem',
  },
  retryBtn: {
    padding: '0.5rem 1.5rem',
    backgroundColor: '#26a69a',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '0.875rem',
    fontWeight: 600,
  },
  chartContainer: {
    borderRadius: '8px',
    overflow: 'hidden',
  },
  // Verdict Card - 最终结论卡
  verdictCard: {
    backgroundColor: '#fff',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    padding: '1rem 1.25rem',
    marginBottom: '1.5rem',
  },
  verdictHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.75rem',
  },
  verdictBias: {
    fontSize: '1.125rem',
    fontWeight: 600,
  },
  verdictStatus: {
    fontSize: '0.75rem',
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    fontWeight: 500,
  },
  verdictAction: {
    fontSize: '0.875rem',
    color: '#666',
    marginBottom: '0.75rem',
    padding: '0.5rem 0',
    borderBottom: '1px solid #f0f0f0',
  },
  verdictLevels: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '0.5rem',
    fontSize: '0.8125rem',
  },
  verdictLevel: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  verdictLevelLabel: {
    color: '#999',
    fontSize: '0.75rem',
  },
  verdictLevelValue: {
    fontFamily: '"SF Mono", "Roboto Mono", Menlo, monospace',
    fontVariantNumeric: 'tabular-nums',
    fontWeight: 500,
  },
  signalItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.5rem 0',
    borderBottom: '1px solid #f0f0f0',
  },
  signalType: {
    fontSize: '0.75rem',
    padding: '0.125rem 0.5rem',
    borderRadius: '4px',
    fontWeight: 500,
  },
  breakoutRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '0.875rem',
    marginBottom: '0.5rem',
    height: '1.75rem',
  },
  breakoutLabel: {
    color: '#666',
    minWidth: '80px',
  },
  breakoutValue: {
    fontFamily: '"SF Mono", "Roboto Mono", Menlo, monospace',
    fontVariantNumeric: 'tabular-nums',
    textAlign: 'right' as const,
  },
  checkMark: {
    color: '#26a69a',
    fontWeight: 600,
  },
  crossMark: {
    color: '#ef5350',
    fontWeight: 600,
  },
};

export default function TickerDetail() {
  const router = useRouter();
  const { ticker } = router.query;
  const { t, lang } = useI18n();
  const [timeframe, setTimeframe] = useState<Timeframe>('1d');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [highlightedBarTime, setHighlightedBarTime] = useState<string | null>(null);

  const { bars, error: barsError, isLoading: barsLoading } = useBars(
    ticker as string, timeframe, { refreshInterval: 60000 }
  );
  const { analysis, error: analysisError, isLoading: analysisLoading, refresh } = useAnalysis(
    ticker as string, timeframe, { refreshInterval: 60000 }
  );

  const isLoading = barsLoading || analysisLoading;
  const error = barsError || analysisError;

  useEffect(() => {
    if (analysis) setLastUpdated(new Date());
  }, [analysis]);

  // 切换时间周期时清除高亮
  useEffect(() => {
    setHighlightedBarTime(null);
  }, [timeframe]);

  // 计算 volume ratio
  const volumeRatio = useMemo(() => {
    if (!bars || bars.length < 31) return null;
    const hasVolume = bars.some(b => b.v > 0);
    if (!hasVolume) return null;
    return calculateVolumeRatio(bars, 30);
  }, [bars]);

  // 判断 breakout 状态
  const breakoutState = useMemo(() => {
    const signals = analysis?.signals || [];
    const latestBreakout = signals.find(s =>
      s.type === 'breakout_confirmed' || s.type === 'breakout_attempt' || s.type === 'fakeout'
    );
    if (latestBreakout) {
      if (latestBreakout.type === 'breakout_confirmed') return 'confirmed';
      if (latestBreakout.type === 'breakout_attempt') return 'attempt';
      if (latestBreakout.type === 'fakeout') return 'fakeout';
    }
    return 'idle';
  }, [analysis]);

  const currentPrice = bars?.[bars.length - 1]?.c;
  const prevPrice = bars?.[bars.length - 2]?.c;
  const priceChange = currentPrice && prevPrice ? currentPrice - prevPrice : 0;
  const priceChangePercent = prevPrice ? (priceChange / prevPrice) * 100 : 0;
  const isUp = priceChange >= 0;

  const regime = analysis?.market_state?.regime || 'range';

  // 1m/5m 用 bias，1d 用 trend
  const getMarketLabel = () => {
    if (timeframe === '1d') {
      return t(regime);
    }
    // 1m/5m 用偏向
    if (regime === 'uptrend') return t('bias_bullish');
    if (regime === 'downtrend') return t('bias_bearish');
    return t('bias_neutral');
  };

  const getRegimeColor = () => {
    if (regime === 'uptrend') return '#26a69a';
    if (regime === 'downtrend') return '#ef5350';
    return '#ff9800';
  };

  return (
    <Layout>
      <Head>
        <title>{ticker} - KLineLens</title>
      </Head>

      <div style={styles.page}>
        <div style={styles.container}>
          {/* Header */}
          <div style={styles.ticker}>{ticker}</div>

          {currentPrice && (
            <div style={styles.priceRow}>
              <span style={styles.price}>${currentPrice.toFixed(2)}</span>
              <span style={{ ...styles.change, color: '#666' }}>
                {isUp ? '+' : ''}{priceChange.toFixed(2)} ({isUp ? '+' : ''}{priceChangePercent.toFixed(2)}%)
              </span>
              {analysis?.market_state && (
                <span style={{ ...styles.regimeTag, color: '#666', borderColor: '#eaeaea' }}>
                  {getMarketLabel()}
                </span>
              )}
              {volumeRatio !== null && (
                <span style={{ ...styles.regimeTag, color: '#666', borderColor: '#eaeaea' }}>
                  {t('volume_ratio')}: {volumeRatio.toFixed(2)}x
                </span>
              )}
            </div>
          )}

          <div style={styles.controls}>
            <div style={{ display: 'flex', gap: '4px' }}>
              {(['1m', '5m', '1d'] as Timeframe[]).map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  style={{
                    ...styles.tfButton,
                    ...(timeframe === tf ? styles.tfButtonActive : {}),
                  }}
                >
                  {t(`timeframe_${tf}`)}
                </button>
              ))}
            </div>
            <button
              onClick={() => refresh()}
              disabled={isLoading}
              style={{ ...styles.refreshBtn, opacity: isLoading ? 0.5 : 1 }}
            >
              {isLoading ? t('loading') : t('refresh')}
            </button>
            {lastUpdated && (
              <span style={{ color: '#999' }}>
                {lang === 'zh' ? '更新于' : 'Updated'} {lastUpdated.toLocaleTimeString(lang === 'zh' ? 'zh-CN' : 'en-US')}
              </span>
            )}
          </div>

          {/* Error */}
          {error && (
            <div style={styles.error}>
              <div style={styles.errorText}>{t('load_failed')}</div>
              <div style={styles.errorMsg}>{error.message}</div>
              <button onClick={() => refresh()} style={styles.retryBtn}>{t('retry')}</button>
            </div>
          )}

          {/* Loading */}
          {isLoading && !analysis && (
            <DetailPageSkeleton />
          )}

          {/* Main Content */}
          {analysis && (
            <div style={styles.grid}>
              {/* Left Column */}
              <div>
                {/* Chart */}
                <div style={styles.section}>
                  <div style={styles.chartContainer}>
                    <CandlestickChart
                      bars={bars || []}
                      supportZones={analysis.zones.support}
                      resistanceZones={analysis.zones.resistance}
                      height={450}
                      showVolume={true}
                      highlightedBarTime={highlightedBarTime}
                      onClearHighlight={() => setHighlightedBarTime(null)}
                    />
                  </div>
                  <div style={styles.legend}>
                    <span style={styles.legendItem}>
                      <span style={{ ...styles.legendBox, backgroundColor: 'rgba(38,166,154,0.4)' }} />
                      {t('support_zone')}
                    </span>
                    <span style={styles.legendItem}>
                      <span style={{ ...styles.legendBox, backgroundColor: 'rgba(239,83,80,0.4)' }} />
                      {t('resistance_zone')}
                    </span>
                    <span style={styles.legendItem}>
                      <span style={{ ...styles.legendBox, backgroundColor: '#ff9800' }} />
                      {t('volume_ma')}
                    </span>
                  </div>
                </div>

                {/* Behaviors */}
                <div style={styles.section}>
                  <div style={styles.sectionTitle}>{t('behavior_inference')}</div>
                  {Object.entries(analysis.behavior.probabilities)
                    .sort(([, a], [, b]) => b - a)
                    .map(([name, prob]) => {
                      const pct = Math.round(prob * 100);
                      const isDominant = name === analysis.behavior.dominant;
                      return (
                        <div key={name} style={styles.behaviorRow}>
                          <span style={{
                            ...styles.behaviorName,
                            color: isDominant ? '#1a1a1a' : '#999',
                            fontWeight: isDominant ? 500 : 400,
                          }}>
                            {t(name)}
                          </span>
                          <div style={styles.behaviorBar}>
                            <div style={{
                              ...styles.behaviorFill,
                              width: `${pct}%`,
                              backgroundColor: isDominant ? '#26a69a' : '#ccc',
                            }} />
                          </div>
                          <span style={{
                            ...styles.behaviorPct,
                            color: isDominant ? '#1a1a1a' : '#999',
                            fontWeight: isDominant ? 500 : 400,
                          }}>
                            {pct}%
                          </span>
                        </div>
                      );
                    })}
                </div>

                {/* Playbook */}
                <div style={styles.section}>
                  <div style={styles.sectionTitle}>{t('playbook')}</div>
                  {analysis.playbook.length === 0 ? (
                    <div style={styles.empty}>{t('no_plans')}</div>
                  ) : (
                    <div style={styles.playbookGrid}>
                      {analysis.playbook.slice(0, 2).map((plan, i) => {
                        const isPrimary = i === 0;
                        const rr = plan.invalidation !== plan.level
                          ? Math.abs((plan.target - plan.level) / (plan.level - plan.invalidation))
                          : 0;

                        return (
                          <div key={i} style={{
                            ...styles.planItem,
                            borderBottomColor: isPrimary ? '#26a69a' : '#eaeaea',
                          }}>
                            <div style={{
                              ...styles.planLabel,
                              color: isPrimary ? '#26a69a' : '#999',
                            }}>
                              {plan.name} · {isPrimary ? t('recommended') : t('alternative')}
                            </div>
                            <div style={styles.planCondition}>
                              {t(plan.condition) || plan.condition}
                            </div>
                            <div style={styles.planRow}>
                              <span style={styles.planKey}>{t('entry')}</span>
                              <span style={{ color: isPrimary ? '#26a69a' : '#1a1a1a' }}>${plan.level.toFixed(2)}</span>
                            </div>
                            <div style={styles.planRow}>
                              <span style={styles.planKey}>{t('target')}</span>
                              <span>${plan.target.toFixed(2)}</span>
                            </div>
                            <div style={styles.planRow}>
                              <span style={styles.planKey}>{t('stop_loss')}</span>
                              <span style={{ color: '#ef5350' }}>${plan.invalidation.toFixed(2)}</span>
                            </div>
                            <div style={{ ...styles.planRow, marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid #eaeaea' }}>
                              <span style={styles.planKey}>{t('risk_reward')}</span>
                              <span style={{ fontWeight: 600 }}>{rr.toFixed(1)}:1</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column */}
              <div>
                {/* Verdict Card - 最终结论 */}
                <div style={styles.verdictCard}>
                  <div style={styles.verdictHeader}>
                    <span style={{
                      ...styles.verdictBias,
                      color: regime === 'uptrend' ? '#26a69a' : regime === 'downtrend' ? '#ef5350' : '#666',
                    }}>
                      {regime === 'uptrend' ? (lang === 'zh' ? '偏多' : 'Bullish') :
                       regime === 'downtrend' ? (lang === 'zh' ? '偏空' : 'Bearish') :
                       (lang === 'zh' ? '中性' : 'Neutral')}
                    </span>
                    <span style={{
                      ...styles.verdictStatus,
                      backgroundColor: breakoutState === 'confirmed' ? '#e8f5e9' :
                                      breakoutState === 'attempt' ? '#fff3e0' :
                                      breakoutState === 'fakeout' ? '#ffebee' : '#f5f5f5',
                      color: breakoutState === 'confirmed' ? '#2e7d32' :
                             breakoutState === 'attempt' ? '#ef6c00' :
                             breakoutState === 'fakeout' ? '#c62828' : '#666',
                    }}>
                      {t(`state_${breakoutState}`)}
                    </span>
                  </div>
                  <div style={styles.verdictAction}>
                    {breakoutState === 'confirmed' ?
                      (lang === 'zh' ? '突破已确认，考虑顺势' : 'Breakout confirmed, consider trend follow') :
                     breakoutState === 'attempt' ?
                      (lang === 'zh' ? '等待量能确认' : 'Wait for volume confirmation') :
                     breakoutState === 'fakeout' ?
                      (lang === 'zh' ? '假突破，谨慎观望' : 'Fakeout detected, stay cautious') :
                      (lang === 'zh' ? '等待突破信号' : 'Wait for breakout signal')}
                  </div>
                  <div style={styles.verdictLevels}>
                    {analysis.zones.resistance.length > 0 && (
                      <div style={styles.verdictLevel}>
                        <span style={styles.verdictLevelLabel}>
                          {lang === 'zh' ? '阻力' : 'Resistance'}
                        </span>
                        <span style={{ ...styles.verdictLevelValue, color: '#ef5350' }}>
                          ${((analysis.zones.resistance[0].low + analysis.zones.resistance[0].high) / 2).toFixed(2)}
                        </span>
                      </div>
                    )}
                    {analysis.zones.support.length > 0 && (
                      <div style={styles.verdictLevel}>
                        <span style={styles.verdictLevelLabel}>
                          {lang === 'zh' ? '支撑' : 'Support'}
                        </span>
                        <span style={{ ...styles.verdictLevelValue, color: '#26a69a' }}>
                          ${((analysis.zones.support[0].low + analysis.zones.support[0].high) / 2).toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Market State */}
                <div style={styles.section}>
                  <div style={styles.sectionTitle}>{t('market_state')}</div>
                  <div style={styles.card}>
                    <div style={styles.stateRow}>
                      <span style={{ fontSize: '1rem', fontWeight: 500 }}>
                        {getMarketLabel()}
                      </span>
                      <span style={{ fontSize: '0.875rem', color: '#666' }}>
                        {Math.round(analysis.market_state.confidence * 100)}%
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ color: '#999', fontSize: '0.75rem' }}>{t('confidence')}</span>
                      <div style={styles.confidenceBar}>
                        <div style={{
                          height: '100%',
                          width: `${Math.round(analysis.market_state.confidence * 100)}%`,
                          backgroundColor: '#666',
                          borderRadius: '2px',
                        }} />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Breakout Status */}
                <div style={styles.section}>
                  <div style={styles.sectionTitle}>{t('breakout_status')}</div>
                  <div style={styles.card}>
                    {volumeRatio === null ? (
                      <div style={{ color: '#999', fontSize: '0.875rem' }}>{t('no_volume_data')}</div>
                    ) : (
                      <>
                        <div style={styles.breakoutRow}>
                          <span style={styles.breakoutLabel}>{t('breakout_state')}</span>
                          <span style={{ ...styles.breakoutValue, fontWeight: 500 }}>
                            {t(`state_${breakoutState}`)}
                          </span>
                        </div>
                        <div style={styles.breakoutRow}>
                          <span style={styles.breakoutLabel}>{t('volume_ratio')}</span>
                          <span style={styles.breakoutValue}>
                            <span style={{
                              color: volumeRatio >= VOLUME_THRESHOLD ? '#26a69a' : '#666',
                              fontWeight: volumeRatio >= VOLUME_THRESHOLD ? 600 : 400,
                            }}>
                              {volumeRatio.toFixed(2)}x
                            </span>
                            <span style={{ color: '#bbb', marginLeft: '0.375rem', fontSize: '0.75rem' }}>
                              {volumeRatio >= VOLUME_THRESHOLD ? '✓' : ''}
                            </span>
                          </span>
                        </div>
                        <div style={styles.breakoutRow}>
                          <span style={styles.breakoutLabel}>{t('confirm_closes')}</span>
                          <span style={styles.breakoutValue}>
                            {breakoutState === 'confirmed' ?
                              <span style={{ color: '#26a69a', fontWeight: 600 }}>2/2 ✓</span> :
                             breakoutState === 'attempt' ?
                              <span style={{ color: '#ff9800' }}>1/2</span> :
                              <span style={{ color: '#999' }}>—</span>}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Signals - 只显示最近 3 条，标准化格式 */}
                <div style={styles.section}>
                  <div style={styles.sectionTitle}>{t('signals')}</div>
                  <div style={styles.card}>
                    {analysis.signals.length === 0 ? (
                      <div style={styles.empty}>{t('no_signals')}</div>
                    ) : (
                      <div>
                        {analysis.signals.slice(0, 3).map((signal, i, arr) => {
                          const signalKey = `signal.${signal.type}`;
                          const signalText = t(signalKey) !== signalKey ? t(signalKey) : t(signal.type);
                          const isLast = i === arr.length - 1;
                          const isBullish = signal.direction === 'bullish';
                          const isConfirmed = signal.type === 'breakout_confirmed';
                          const isFakeout = signal.type === 'fakeout';
                          return (
                            <div key={i} style={{
                              ...styles.signalItem,
                              ...(isLast ? { borderBottom: 'none' } : {}),
                            }}>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.125rem' }}>
                                <span style={{
                                  fontSize: '0.8125rem',
                                  color: isConfirmed ? '#26a69a' : isFakeout ? '#ef5350' : '#1a1a1a',
                                  fontWeight: isConfirmed ? 500 : 400,
                                }}>
                                  {signalText}
                                  {isConfirmed && ' ✓'}
                                </span>
                                <span style={{
                                  fontSize: '0.6875rem',
                                  color: '#999',
                                  fontFamily: '"SF Mono", "Roboto Mono", Menlo, monospace',
                                }}>
                                  {formatDate(signal.bar_time)}
                                </span>
                              </div>
                              <span style={{
                                fontSize: '0.8125rem',
                                color: isBullish ? '#26a69a' : '#ef5350',
                                fontFamily: '"SF Mono", "Roboto Mono", Menlo, monospace',
                                fontVariantNumeric: 'tabular-nums',
                              }}>
                                ${signal.level.toFixed(2)}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>

                {/* Evidence - 只显示最近 3 条 */}
                <div style={styles.section}>
                  <div style={styles.sectionTitle}>{t('evidence')}</div>
                  <div style={styles.card}>
                    {analysis.behavior.evidence.length === 0 ? (
                      <div style={styles.empty}>{t('no_evidence')}</div>
                    ) : (
                      <div>
                        {analysis.behavior.evidence.slice(0, 3).map((item: EvidenceItem, i, arr) => {
                          const noteKey = item.note;
                          const translated = t(noteKey) !== noteKey ? t(noteKey) : noteKey;
                          const isLast = i === arr.length - 1;
                          const hasBarTime = !!item.bar_time;
                          const isHighlighted = highlightedBarTime === item.bar_time;
                          return (
                            <div
                              key={i}
                              onClick={() => hasBarTime && setHighlightedBarTime(item.bar_time)}
                              style={{
                                ...styles.evidenceItem,
                                ...(isLast ? { borderBottom: 'none', marginBottom: 0, paddingBottom: 0 } : {}),
                                cursor: hasBarTime ? 'pointer' : 'default',
                                backgroundColor: isHighlighted ? '#f0f0f0' : 'transparent',
                                marginLeft: '-0.5rem',
                                marginRight: '-0.5rem',
                                paddingLeft: '0.5rem',
                                paddingRight: '0.5rem',
                                borderRadius: '4px',
                              }}
                            >
                              <div style={styles.evidenceTop}>
                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                                  {hasBarTime && (
                                    <span style={{
                                      color: isHighlighted ? '#666' : '#ccc',
                                      fontSize: '0.625rem',
                                    }}>
                                      ●
                                    </span>
                                  )}
                                  {translated}
                                </span>
                                <span style={{ fontSize: '0.75rem', color: '#999' }}>
                                  {t(item.behavior)}
                                </span>
                              </div>
                              <div style={styles.evidenceMetrics}>
                                {formatMetrics(item.metrics)}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>

                {/* Timeline - 只显示最近 3 条 */}
                <div style={styles.section}>
                  <div style={styles.sectionTitle}>{t('timeline')}</div>
                  <div style={styles.card}>
                    {analysis.timeline.length === 0 ? (
                      <div style={styles.empty}>{t('no_events')}</div>
                    ) : (
                      <div>
                        {analysis.timeline.slice(0, 3).map((event, i) => {
                          // 只显示有意义的 reason，跳过原始 key
                          const showReason = event.reason && !event.reason.includes('.');
                          return (
                            <div key={i} style={styles.timelineItem}>
                              <div style={styles.timelineDot} />
                              <div style={{ flex: 1 }}>
                                <div style={styles.timelineText}>
                                  {t(event.event_type) !== event.event_type ? t(event.event_type) : event.event_type.replace(/_/g, ' ')}
                                </div>
                                <div style={styles.timelineDate}>
                                  {formatDate(event.ts)}
                                  {showReason && ` · ${event.reason}`}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}

function formatDate(ts: string): string {
  try {
    const date = new Date(ts);
    if (isNaN(date.getTime())) return '';
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    return `${month}/${day} ${hour}:${minute}`;
  } catch {
    return '';
  }
}

function formatMetrics(metrics: Record<string, unknown>): string {
  const parts: string[] = [];
  for (const [key, value] of Object.entries(metrics)) {
    if (typeof value === 'number') {
      if (key.includes('price') || key.includes('zone')) {
        parts.push(`$${value.toFixed(2)}`);
      } else if (key.includes('ratio')) {
        parts.push(`${value.toFixed(2)}x`);
      }
    }
  }
  return parts.join(' / ') || '';
}
