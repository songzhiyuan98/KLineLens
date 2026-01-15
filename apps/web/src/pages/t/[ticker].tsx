/**
 * 股票详情分析页面 - Terminal Style v4 (Information Architecture v1.0)
 *
 * 布局结构:
 * - Status Strip: Provider/Latency/Updated/Bars/Volume Quality
 * - Header: Ticker/Price/Change/TF切换
 * - Main Grid:
 *   - Left: Chart Header + K线图
 *   - Right: Summary → Breakout → Behavior → Zones → Playbook
 * - Bottom Panel: Tabs (Timeline/Evidence/Volume)
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/router';
import dynamic from 'next/dynamic';
import Head from 'next/head';
import { Layout, DetailPageSkeleton } from '../../components';
import { useAnalysis, useBars } from '../../lib/hooks';
import { useI18n, Language } from '../../lib/i18n';
import {
  Evidence,
  TimelineEvent,
  Zone,
  fetchNarrative,
  SignalEvaluation,
  SignalEvaluationsResponse,
  fetchSignalEvaluations,
  updateSignalEvaluation,
} from '../../lib/api';
import {
  loadCachedEvidence,
  saveCachedEvidence,
  mergeEvidence,
  loadCachedTimeline,
  saveCachedTimeline,
  mergeTimeline,
} from '../../lib/cache';

const CandlestickChart = dynamic(
  () => import('../../components/CandlestickChart'),
  { ssr: false }
);

type Timeframe = '1m' | '5m' | '1d';
type BottomTab = 'playbook' | 'signal_eval' | 'evidence' | 'volume';
type TimelineFilter = 'all' | 'structure' | 'volume' | 'breakout';

const VOLUME_THRESHOLD = 1.8;
const RESULT_THRESHOLD = 0.6;

// Terminal mono font
const MONO = '"SF Mono", "Roboto Mono", "Fira Code", Menlo, Monaco, monospace';

// Terminal color palette (90% gray, 10% accent)
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

// ============ Fluid Typography Scale ============
// Using clamp() for responsive fonts: clamp(min, preferred, max)
// Scales up on larger viewports (fullscreen), stays readable on smaller ones
const F = {
  // Tiny: status strip, labels
  tiny: 'clamp(0.5625rem, 0.5rem + 0.15vw, 0.6875rem)',
  // Small: secondary text, meta
  small: 'clamp(0.625rem, 0.55rem + 0.2vw, 0.8125rem)',
  // Body: main text
  body: 'clamp(0.6875rem, 0.6rem + 0.2vw, 0.875rem)',
  // Medium: section content
  medium: 'clamp(0.75rem, 0.65rem + 0.25vw, 0.9375rem)',
  // Large: emphasis, values
  large: 'clamp(0.875rem, 0.75rem + 0.3vw, 1.125rem)',
  // Heading: ticker, price
  heading: 'clamp(1.375rem, 1.1rem + 0.6vw, 1.875rem)',
};

// ============ Styles ============
const s: Record<string, React.CSSProperties> = {
  page: {
    backgroundColor: C.bg,
    color: C.text,
    minHeight: '100vh',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },

  // Status Strip - more subtle, product-level
  statusStrip: {
    backgroundColor: '#fafafa',
    borderBottom: `1px solid ${C.dividerLight}`,
    padding: '0.375rem 0',
    fontSize: F.tiny,
    fontFamily: MONO,
    color: '#b0b0b0',
  },
  statusInner: {
    padding: '0 3rem',
    display: 'grid',
    gridTemplateColumns: '7fr 3fr',
    gap: '2.5rem',
    alignItems: 'center',
  },
  statusLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '1.5rem',
  },
  statusItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.25rem',
  },
  statusLabel: {
    color: '#b0b0b0',
  },
  statusValue: {
    color: '#888888',
    fontWeight: 500,
  },
  statusDot: {
    width: '5px',
    height: '5px',
    borderRadius: '50%',
    backgroundColor: C.bullish,
  },
  statusVolumeDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    marginLeft: '0.125rem',
  },

  // Header
  header: {
    borderBottom: `1px solid ${C.divider}`,
    padding: '1rem 0',
  },
  headerInner: {
    padding: '0 3rem',
    display: 'grid',
    gridTemplateColumns: '7fr 3fr',
    gap: '2.5rem',
    alignItems: 'center',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '1rem',
  },
  ticker: {
    fontSize: F.heading,
    fontWeight: 700,
    letterSpacing: '-0.02em',
    color: C.text,
  },
  price: {
    fontSize: F.heading,
    fontWeight: 600,
    fontFamily: MONO,
    fontVariantNumeric: 'tabular-nums',
    color: C.text,
  },
  change: {
    fontSize: F.large,
    fontFamily: MONO,
    fontVariantNumeric: 'tabular-nums',
    fontWeight: 500,
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-start',
    gap: '1rem',
  },
  tfGroup: {
    display: 'flex',
    gap: '1px',
    backgroundColor: C.divider,
    borderRadius: '4px',
    overflow: 'hidden',
  },
  tfBtn: {
    padding: '0.375rem 0.75rem',
    fontSize: F.body,
    fontWeight: 500,
    fontFamily: MONO,
    border: 'none',
    background: C.bg,
    color: C.textMuted,
    cursor: 'pointer',
    transition: 'all 0.15s',
  },
  tfBtnActive: {
    backgroundColor: C.text,
    color: C.bg,
  },
  tfLabel: {
    fontSize: F.tiny,
    color: C.textMuted,
    marginRight: '0.25rem',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },

  // Main layout - 固定边距，比例自适应
  main: {
    padding: '1.5rem 3rem',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '7fr 3fr',  // 70% chart, 30% panel, proportional scaling
    gap: '2.5rem',
    alignItems: 'start',
    minHeight: 0,
  },

  // Chart section
  chartSection: {
    display: 'flex',
    flexDirection: 'column' as const,
  },
  chartHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '1.5rem',
    marginBottom: '1rem',
    paddingBottom: '0.75rem',
    borderBottom: `1px solid ${C.dividerLight}`,
  },
  chartStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.375rem',
    fontSize: F.medium,
  },
  chartStatusLabel: {
    color: C.textMuted,
  },
  chartStatusValue: {
    fontWeight: 600,
    fontFamily: MONO,
  },
  chartContainer: {
    borderRadius: '4px',
    overflow: 'hidden',
    border: `1px solid ${C.dividerLight}`,
  },

  // Right panel - proportional with constraints
  panel: {
    display: 'flex',
    flexDirection: 'column' as const,
    minWidth: '280px',
    maxWidth: '420px',
  },

  // Section style - tighter, more terminal-like
  section: {
    paddingBottom: '1rem',
    marginBottom: '1rem',
    borderBottom: '1px solid rgba(0,0,0,0.04)',
  },
  sectionLast: {
    paddingBottom: 0,
    marginBottom: 0,
    borderBottom: 'none',
  },
  sectionTitle: {
    fontSize: F.tiny,
    fontWeight: 500,
    color: '#b0b0b0',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.1em',
    marginBottom: '0.5rem',
  },

  // Summary Card - Vertical List Style
  summaryList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.375rem',
  },
  summaryItem: {
    display: 'flex',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    gap: '0.5rem',
  },
  summaryLabel: {
    fontSize: F.body,
    color: '#888',
  },
  summaryValueSmall: {
    fontSize: F.body,
    fontFamily: MONO,
    color: C.text,
  },
  summaryValueLarge: {
    fontSize: F.large,
    fontFamily: MONO,
    fontWeight: 600,
  },
  summaryMuted: {
    fontSize: F.small,
    color: '#999',
    marginLeft: '0.25rem',
  },
  decisionValue: {
    fontFamily: MONO,
    fontWeight: 600,
  },
  decisionTrigger: {
    fontSize: F.body,
    color: C.textSecondary,
  },
  summaryAction: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.375rem',
    marginTop: '0.5rem',
    padding: '0.375rem 0.625rem',
    backgroundColor: C.dividerLight,
    borderRadius: '3px',
    fontSize: F.medium,
    fontWeight: 500,
    color: C.text,
  },

  // Timeline - Terminal style (minimal)
  timelineContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.25rem',
  },
  timelineItem: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '1rem',
    padding: '0.125rem 0',
    cursor: 'pointer',
    borderRadius: '2px',
    transition: 'background-color 0.1s',
  },
  timelineTime: {
    fontSize: F.body,
    fontFamily: MONO,
    color: C.textMuted,
    fontVariantNumeric: 'tabular-nums',
    flexShrink: 0,
  },
  timelineText: {
    fontSize: F.body,
    color: C.textSecondary,
    lineHeight: 1.4,
    textAlign: 'right' as const,
  },

  // Breakout section
  breakoutState: {
    fontSize: F.large,
    fontWeight: 600,
    marginBottom: '0.625rem',
  },
  breakoutFactors: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.375rem',
  },
  factorRow: {
    display: 'flex',
    alignItems: 'center',
    fontSize: F.medium,
    fontFamily: MONO,
    fontVariantNumeric: 'tabular-nums',
  },
  factorCheck: {
    width: '14px',
    height: '14px',
    marginRight: '0.5rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: F.small,
    borderRadius: '2px',
    border: `1px solid ${C.divider}`,
    color: C.textMuted,
  },
  factorCheckDone: {
    backgroundColor: '#dcfce7',
    borderColor: C.bullish,
    color: C.bullish,
  },
  factorLabel: {
    flex: 1,
    color: C.textSecondary,
  },
  factorValue: {
    color: C.text,
    fontWeight: 500,
  },

  // Behavior section
  behaviorDominant: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '0.5rem',
    marginBottom: '0.5rem',
  },
  behaviorName: {
    fontSize: F.large,
    fontWeight: 600,
    color: C.text,
  },
  behaviorProb: {
    fontSize: F.medium,
    fontFamily: MONO,
    fontVariantNumeric: 'tabular-nums',
    color: C.textMuted,
  },
  behaviorSecondary: {
    fontSize: F.medium,
    color: C.textMuted,
    marginBottom: '0.625rem',
  },
  evidenceList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.25rem',
  },
  evidenceItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '0.375rem',
    fontSize: F.medium,
    color: C.textSecondary,
    padding: '0.25rem 0',
    cursor: 'pointer',
    borderRadius: '2px',
  },
  evidenceItemHover: {
    backgroundColor: C.dividerLight,
  },
  evidenceBullet: {
    color: C.textMuted,
    marginTop: '0.0625rem',
    fontSize: F.small,
  },

  // Zones section (table)
  zonesTable: {
    width: '100%',
    fontSize: F.medium,
    fontFamily: MONO,
    fontVariantNumeric: 'tabular-nums',
  },
  zonesHeader: {
    display: 'grid',
    gridTemplateColumns: '1fr 36px 1fr',
    gap: '0.5rem',
    fontSize: F.tiny,
    fontWeight: 500,
    color: C.textMuted,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
    paddingBottom: '0.375rem',
    borderBottom: `1px solid ${C.dividerLight}`,
    marginBottom: '0.375rem',
  },
  zonesRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 36px 1fr',
    gap: '0.5rem',
    padding: '0.25rem 0',
    alignItems: 'center',
  },
  zonePrice: {
    fontWeight: 600,
  },
  zoneValue: {
    color: C.textSecondary,
    textAlign: 'right' as const,
  },

  // Playbook section
  playbookItem: {
    marginBottom: '1rem',
  },
  playbookItemLast: {
    marginBottom: 0,
  },
  planHeader: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '0.375rem',
    marginBottom: '0.375rem',
  },
  planLabel: {
    fontSize: F.small,
    fontWeight: 600,
    color: C.textMuted,
  },
  planName: {
    fontSize: F.medium,
    color: C.textSecondary,
  },
  planLevels: {
    display: 'grid',
    gridTemplateColumns: 'auto 1fr',
    gap: '0.125rem 0.75rem',
    fontSize: F.medium,
    fontFamily: MONO,
    fontVariantNumeric: 'tabular-nums',
  },
  planKey: {
    color: C.textMuted,
  },
  planValue: {
    fontWeight: 500,
    color: C.text,
  },
  planInvalidation: {
    fontWeight: 600,
    color: C.bearish,
  },

  // Bottom Panel (now inside left column)
  bottomPanel: {
    marginTop: '1.25rem',
  },
  bottomTabs: {
    display: 'flex',
    gap: '0',
    borderBottom: `1px solid ${C.divider}`,
  },
  bottomTab: {
    padding: '0.75rem 1.25rem',
    fontSize: F.body,
    fontWeight: 500,
    color: C.textMuted,
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    borderBottom: '2px solid transparent',
    marginBottom: '-1px',
    transition: 'all 0.15s',
  },
  bottomTabActive: {
    color: C.text,
    borderBottomColor: C.text,
  },
  bottomContent: {
    padding: '1rem 0',
    minHeight: '280px',
    maxHeight: '360px',
    overflowY: 'auto' as const,
  },

  // Timeline
  timelineHeader: {
    display: 'flex',
    justifyContent: 'flex-end',
    alignItems: 'center',
    marginBottom: '0.75rem',
  },
  timelineFilters: {
    display: 'flex',
    gap: '0.25rem',
  },
  filterBtn: {
    padding: '0.25rem 0.5rem',
    fontSize: F.small,
    fontWeight: 500,
    border: 'none',
    background: 'transparent',
    color: C.textMuted,
    cursor: 'pointer',
    borderRadius: '2px',
    transition: 'all 0.15s',
  },
  filterBtnActive: {
    backgroundColor: C.text,
    color: C.bg,
  },
  // Old timeline styles removed - using new vertical dot timeline

  // Evidence Tab
  evidenceTable: {
    width: '100%',
  },
  evidenceTableHeader: {
    display: 'grid',
    gridTemplateColumns: '80px 80px 60px 1fr',
    gap: '1rem',
    fontSize: F.tiny,
    fontWeight: 500,
    color: C.textMuted,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
    paddingBottom: '0.5rem',
    borderBottom: `1px solid ${C.dividerLight}`,
    marginBottom: '0.5rem',
  },
  evidenceTableRow: {
    display: 'grid',
    gridTemplateColumns: '80px 80px 60px 1fr',
    gap: '1rem',
    padding: '0.5rem 0',
    fontSize: F.medium,
    borderBottom: `1px solid ${C.dividerLight}`,
    cursor: 'pointer',
  },
  evidenceType: {
    fontWeight: 500,
    fontFamily: MONO,
    fontSize: F.body,
  },
  evidenceSeverity: {
    fontFamily: MONO,
    fontSize: F.body,
  },
  evidenceMetrics: {
    fontFamily: MONO,
    fontVariantNumeric: 'tabular-nums',
    fontSize: F.body,
    color: C.textMuted,
  },

  // Volume Tab
  volumeGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '2rem',
  },
  volumeSection: {},
  volumeSectionTitle: {
    fontSize: F.small,
    fontWeight: 600,
    color: C.textMuted,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
    marginBottom: '0.75rem',
  },
  quadrant: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gridTemplateRows: '64px 64px',
    gap: '1px',
    backgroundColor: C.divider,
    position: 'relative' as const,
  },
  quadrantCell: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: F.small,
    color: C.textMuted,
    backgroundColor: C.bg,
  },
  quadrantDot: {
    position: 'absolute' as const,
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: C.text,
    transform: 'translate(-50%, -50%)',
    boxShadow: '0 0 0 2px white',
  },
  volumeStats: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.5rem',
  },
  volumeStat: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: F.medium,
    fontFamily: MONO,
    fontVariantNumeric: 'tabular-nums',
  },
  volumeStatLabel: {
    color: C.textMuted,
  },
  volumeStatValue: {
    fontWeight: 500,
    color: C.text,
  },

  // Error
  error: {
    textAlign: 'center' as const,
    padding: '3rem',
  },
  errorText: {
    color: C.bearish,
    marginBottom: '0.5rem',
    fontWeight: 500,
  },
  errorMsg: {
    color: C.textMuted,
    fontSize: F.large,
    marginBottom: '1rem',
  },
  retryBtn: {
    padding: '0.5rem 1.5rem',
    backgroundColor: C.text,
    border: 'none',
    borderRadius: '4px',
    color: C.bg,
    cursor: 'pointer',
    fontSize: F.large,
    fontWeight: 500,
  },

  // Narrative Section
  narrativeSection: {
    marginTop: '1.5rem',
    padding: '1rem',
    backgroundColor: '#fafafa',
    borderRadius: '6px',
    border: `1px solid ${C.dividerLight}`,
  },
  narrativeHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '0.75rem',
  },
  narrativeTitle: {
    fontSize: F.small,
    fontWeight: 500,
    color: '#888',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.1em',
  },
  narrativeQuality: {
    fontSize: F.tiny,
    padding: '0.125rem 0.375rem',
    borderRadius: '3px',
    fontWeight: 500,
  },
  narrativeQualityHigh: {
    backgroundColor: '#dcfce7',
    color: C.bullish,
  },
  narrativeQualityLimited: {
    backgroundColor: '#fef3c7',
    color: C.warn,
  },
  generateBtn: {
    padding: '0.375rem 0.75rem',
    fontSize: F.body,
    fontWeight: 500,
    backgroundColor: C.text,
    color: C.bg,
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'opacity 0.15s',
  },
  generateBtnLoading: {
    opacity: 0.6,
    cursor: 'not-allowed',
  },
  narrativeContent: {
    fontSize: F.large,
    lineHeight: 1.6,
    color: C.text,
  },
  narrativeSummary: {
    marginBottom: '0.75rem',
  },
  narrativeAction: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.375rem',
    padding: '0.375rem 0.625rem',
    backgroundColor: C.dividerLight,
    borderRadius: '4px',
    fontSize: F.medium,
    fontWeight: 600,
    marginBottom: '0.75rem',
  },
  narrativeActionWait: { color: C.textMuted },
  narrativeActionWatch: { color: C.accent },
  narrativeActionTriggered: { color: C.bullish },
  narrativeWhyList: {
    margin: 0,
    padding: '0 0 0 1rem',
    fontSize: F.medium,
    color: C.textSecondary,
    marginBottom: '0.75rem',
  },
  narrativeWhyItem: {
    marginBottom: '0.25rem',
  },
  narrativePlaybook: {
    fontSize: F.medium,
    color: C.textSecondary,
    whiteSpace: 'pre-wrap' as const,
    marginBottom: '0.75rem',
    padding: '0.5rem',
    backgroundColor: '#fff',
    borderRadius: '4px',
    border: `1px solid ${C.dividerLight}`,
  },
  narrativeRisks: {
    fontSize: F.body,
    color: C.warn,
    padding: '0.5rem',
    backgroundColor: '#fffbeb',
    borderRadius: '4px',
    border: '1px solid #fef3c7',
  },
  narrativeRiskItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '0.375rem',
    marginBottom: '0.25rem',
  },
  narrativeEmpty: {
    fontSize: F.medium,
    color: C.textMuted,
    textAlign: 'center' as const,
    padding: '1rem 0',
  },
  narrativeError: {
    fontSize: F.medium,
    color: C.bearish,
    textAlign: 'center' as const,
    padding: '0.5rem',
    backgroundColor: '#fef2f2',
    borderRadius: '4px',
    border: '1px solid #fecaca',
  },
};

// ============ Helper Functions ============

/** Safe format time - returns "—" on invalid */
const formatTime = (ts: string | undefined): string => {
  if (!ts) return '—';
  try {
    const d = new Date(ts);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
  } catch {
    return '—';
  }
};

/** Safe format date time */
const formatDateTime = (ts: string | Date | undefined): string => {
  if (!ts) return '—';
  try {
    const d = ts instanceof Date ? ts : new Date(ts);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  } catch {
    return '—';
  }
};

/** Safe format number - returns "—" on NaN */
const formatNum = (n: number | undefined | null, decimals: number = 2): string => {
  if (n === undefined || n === null || isNaN(n)) return '—';
  return n.toFixed(decimals);
};

/** Safe format price */
const formatPrice = (n: number | undefined | null): string => {
  if (n === undefined || n === null || isNaN(n)) return '—';
  return `$${n.toFixed(2)}`;
};

/** Safe format percent */
const formatPercent = (n: number | undefined | null, showSign: boolean = true): string => {
  if (n === undefined || n === null || isNaN(n)) return '—';
  const sign = showSign && n >= 0 ? '+' : '';
  return `${sign}${n.toFixed(2)}%`;
};

// ============ Main Component ============
export default function TickerDetail() {
  const router = useRouter();
  const { ticker } = router.query;
  const { t, lang } = useI18n();

  const [timeframe, setTimeframe] = useState<Timeframe>('5m');
  const [bottomTab, setBottomTab] = useState<BottomTab>('playbook');
  const [timelineFilter, setTimelineFilter] = useState<TimelineFilter>('all');
  const [showAllZones, setShowAllZones] = useState(false);
  const [highlightedBarTime, setHighlightedBarTime] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [chartHeight, setChartHeight] = useState(380);

  // Daily cached evidence and timeline
  const [cachedEvidence, setCachedEvidence] = useState<Evidence[]>([]);
  const [cachedTimeline, setCachedTimeline] = useState<TimelineEvent[]>([]);

  // Signal evaluations
  const [signalEvaluations, setSignalEvaluations] = useState<SignalEvaluationsResponse | null>(null);
  const [evalLoading, setEvalLoading] = useState(false);

  const { bars, error: barsError, isLoading: barsLoading } = useBars(
    ticker as string, timeframe, { refreshInterval: 60000 }
  );
  const { analysis, error: analysisError, isLoading: analysisLoading, refresh } = useAnalysis(
    ticker as string, timeframe, { refreshInterval: 60000 }
  );

  // Narrative 缓存（三个周期各自缓存）
  const [narrativeCache, setNarrativeCache] = useState<{
    '1m'?: { content: string; loading: boolean };
    '5m'?: { content: string; loading: boolean };
    '1d'?: { content: string; loading: boolean };
  }>({});

  // 上一次状态（用于检测变化，按周期分开）
  const [prevStates, setPrevStates] = useState<{
    [key: string]: {
      regime?: string;
      breakoutState?: string;
      dominant?: string;
      dominantProb?: number;
    };
  }>({});

  // 获取当前周期的 narrative
  const currentNarrative = narrativeCache[timeframe];

  // Dynamic chart height based on viewport
  // Min: 280px, Max: 550px, scales with viewport height
  useEffect(() => {
    const updateChartHeight = () => {
      const vh = window.innerHeight;
      // Use ~45% of viewport height, clamped between 280-550
      const height = Math.min(550, Math.max(280, Math.round(vh * 0.45)));
      setChartHeight(height);
    };

    updateChartHeight();
    window.addEventListener('resize', updateChartHeight);
    return () => window.removeEventListener('resize', updateChartHeight);
  }, []);

  // 加载单个周期的 narrative
  const loadNarrative = useCallback(async (tf: Timeframe) => {
    if (!ticker) return;

    // 标记为加载中
    setNarrativeCache(prev => ({
      ...prev,
      [tf]: { content: prev[tf]?.content || '', loading: true }
    }));

    try {
      const result = await fetchNarrative(ticker as string, tf, 'quick', lang as 'zh' | 'en');
      setNarrativeCache(prev => ({
        ...prev,
        [tf]: { content: result.narrative?.content || result.narrative?.summary || '', loading: false }
      }));
    } catch (err) {
      console.error(`Failed to load narrative for ${tf}:`, err);
      setNarrativeCache(prev => ({
        ...prev,
        [tf]: { content: prev[tf]?.content || '', loading: false }
      }));
    }
  }, [ticker, lang]);

  // 初始化：进入页面时加载所有三个周期
  useEffect(() => {
    if (!ticker) return;

    // 重置缓存
    setNarrativeCache({});
    setPrevStates({});

    // 并行加载三个周期
    const timeframes: Timeframe[] = ['1d', '5m', '1m'];
    timeframes.forEach(tf => loadNarrative(tf));
  }, [ticker]); // 只在 ticker 变化时触发

  // 触发器检测（只在 analysis 更新时检查是否需要重新加载当前周期）
  useEffect(() => {
    if (!analysis || !ticker) return;

    const tf = timeframe;
    const prev = prevStates[tf] || {};

    const currentRegime = analysis.market_state?.regime;
    const currentBreakout = (() => {
      const signals = analysis.signals || [];
      const latest = signals.find(s =>
        s.type === 'breakout_confirmed' || s.type === 'breakout_attempt' || s.type === 'fakeout'
      );
      if (latest?.type === 'breakout_confirmed') return 'confirmed';
      if (latest?.type === 'breakout_attempt') return 'attempt';
      if (latest?.type === 'fakeout') return 'fakeout';
      return 'idle';
    })();
    const currentDominant = analysis.behavior?.dominant;
    const currentDominantProb = analysis.behavior?.probabilities?.[currentDominant || ''] || 0;

    // 检测是否需要更新（只有状态真的变化了才触发）
    const hasStateChange =
      prev.regime !== undefined && (
        // Hard Trigger 1: Regime 变化
        prev.regime !== currentRegime ||
        // Hard Trigger 2: Breakout 状态变化
        prev.breakoutState !== currentBreakout ||
        // Hard Trigger 3: Dominant Behavior 变化 + Δprob ≥ 0.12
        (prev.dominant !== currentDominant &&
         Math.abs(currentDominantProb - (prev.dominantProb || 0)) >= 0.12)
      );

    if (hasStateChange) {
      loadNarrative(tf);
    }

    // 更新 prevState
    setPrevStates(prev => ({
      ...prev,
      [tf]: {
        regime: currentRegime,
        breakoutState: currentBreakout,
        dominant: currentDominant,
        dominantProb: currentDominantProb,
      }
    }));
  }, [analysis]); // 只在 analysis 变化时检查

  const isLoading = barsLoading || analysisLoading;
  const error = barsError || analysisError;

  useEffect(() => {
    if (analysis) setLastUpdated(new Date());
  }, [analysis]);

  useEffect(() => {
    setHighlightedBarTime(null);
  }, [timeframe]);

  // Load cached evidence/timeline on mount and timeframe change
  useEffect(() => {
    if (!ticker) return;
    const tickerStr = ticker as string;

    // Load from cache
    const cachedEv = loadCachedEvidence(tickerStr, timeframe);
    const cachedTl = loadCachedTimeline(tickerStr, timeframe);

    setCachedEvidence(cachedEv);
    setCachedTimeline(cachedTl);
  }, [ticker, timeframe]);

  // Merge and save evidence when analysis updates
  useEffect(() => {
    if (!ticker || !analysis?.behavior?.evidence) return;
    const tickerStr = ticker as string;
    const freshEvidence = analysis.behavior.evidence || [];

    // Merge with existing cache
    const merged = mergeEvidence(cachedEvidence, freshEvidence);
    setCachedEvidence(merged);
    saveCachedEvidence(tickerStr, timeframe, merged);
  }, [analysis?.behavior?.evidence]);

  // Merge and save timeline when analysis updates
  useEffect(() => {
    if (!ticker || !analysis?.timeline) return;
    const tickerStr = ticker as string;
    const freshTimeline = analysis.timeline || [];

    // Merge with existing cache
    const merged = mergeTimeline(cachedTimeline, freshTimeline);
    setCachedTimeline(merged);
    saveCachedTimeline(tickerStr, timeframe, merged);
  }, [analysis?.timeline]);

  // Load signal evaluations
  useEffect(() => {
    if (!ticker) return;
    const tickerStr = ticker as string;

    const loadEvaluations = async () => {
      setEvalLoading(true);
      try {
        const data = await fetchSignalEvaluations(tickerStr, timeframe, undefined, 20);
        setSignalEvaluations(data);
      } catch (error) {
        console.error('Failed to load signal evaluations:', error);
      } finally {
        setEvalLoading(false);
      }
    };

    loadEvaluations();
  }, [ticker, timeframe]);

  // Computed values
  const currentPrice = bars?.[bars.length - 1]?.c;
  const prevPrice = bars?.[bars.length - 2]?.c;
  const priceChange = currentPrice && prevPrice ? currentPrice - prevPrice : 0;
  const priceChangePercent = prevPrice ? (priceChange / prevPrice) * 100 : 0;
  const isUp = priceChange >= 0;

  const regime = analysis?.market_state?.regime || 'range';
  const regimeConf = analysis?.market_state?.confidence || 0;
  const volumeQuality = analysis?.volume_quality || 'unavailable';
  const dominantBehavior = analysis?.behavior?.dominant || '';
  const dominantProb = analysis?.behavior?.probabilities?.[dominantBehavior] || 0;

  // Get second behavior for display
  const secondBehavior = useMemo(() => {
    const probs = analysis?.behavior?.probabilities || {};
    const sorted = Object.entries(probs)
      .filter(([k]) => k !== dominantBehavior)
      .sort((a, b) => b[1] - a[1]);
    return sorted[0] ? { name: sorted[0][0], prob: sorted[0][1] } : null;
  }, [analysis, dominantBehavior]);

  const latestRvol = useMemo(() => {
    const evidence = analysis?.behavior?.evidence || [];
    for (const e of evidence) {
      if (e.metrics?.rvol !== undefined && !isNaN(e.metrics.rvol)) return e.metrics.rvol;
    }
    return null;
  }, [analysis]);

  const latestResult = useMemo(() => {
    const evidence = analysis?.behavior?.evidence || [];
    for (const e of evidence) {
      if (e.metrics?.result !== undefined && !isNaN(e.metrics.result)) return e.metrics.result;
    }
    return null;
  }, [analysis]);

  const latestEffort = useMemo(() => {
    const evidence = analysis?.behavior?.evidence || [];
    for (const e of evidence) {
      if (e.metrics?.effort !== undefined && !isNaN(e.metrics.effort)) return e.metrics.effort;
    }
    return latestRvol; // Effort often equals RVOL
  }, [analysis, latestRvol]);

  // Calculate ATR from bars (14-period)
  const estimatedATR = useMemo(() => {
    if (!bars || bars.length < 15) return null;
    const period = 14;
    let trSum = 0;
    for (let i = bars.length - period; i < bars.length; i++) {
      const high = bars[i].h;
      const low = bars[i].l;
      const prevClose = bars[i - 1]?.c || bars[i].o;
      const tr = Math.max(high - low, Math.abs(high - prevClose), Math.abs(low - prevClose));
      trSum += tr;
    }
    return trSum / period;
  }, [bars]);

  const { breakoutState, confirmCloses, breakoutLevel, breakoutDirection } = useMemo(() => {
    const signals = analysis?.signals || [];
    const latest = signals.find(s =>
      s.type === 'breakout_confirmed' || s.type === 'breakout_attempt' || s.type === 'fakeout'
    );
    if (latest) {
      if (latest.type === 'breakout_confirmed') return { breakoutState: 'confirmed', confirmCloses: 2, breakoutLevel: latest.level, breakoutDirection: latest.direction };
      if (latest.type === 'breakout_attempt') return { breakoutState: 'attempt', confirmCloses: 1, breakoutLevel: latest.level, breakoutDirection: latest.direction };
      if (latest.type === 'fakeout') return { breakoutState: 'fakeout', confirmCloses: 0, breakoutLevel: latest.level, breakoutDirection: latest.direction };
    }
    return { breakoutState: 'idle', confirmCloses: 0, breakoutLevel: null, breakoutDirection: null };
  }, [analysis]);

  const resistanceZones = useMemo(() => {
    const zones = analysis?.zones?.resistance || [];
    return showAllZones ? zones : zones.slice(0, 3);
  }, [analysis, showAllZones]);

  const supportZones = useMemo(() => {
    const zones = analysis?.zones?.support || [];
    return showAllZones ? zones : zones.slice(0, 3);
  }, [analysis, showAllZones]);

  // HOD/LOD calculation (Session High/Low)
  const sessionHL = useMemo(() => {
    if (!bars || bars.length === 0) return { hod: null, lod: null };
    // For intraday (1m, 5m), calculate today's high/low
    // For daily, use the most recent bar
    const today = new Date().toDateString();
    const todayBars = bars.filter(bar => new Date(bar.t).toDateString() === today);
    const relevantBars = todayBars.length > 0 ? todayBars : bars.slice(-1);
    if (relevantBars.length === 0) return { hod: null, lod: null };
    const hod = Math.max(...relevantBars.map(b => b.h));
    const lod = Math.min(...relevantBars.map(b => b.l));
    return { hod, lod };
  }, [bars]);

  // Structured Key Zones: R_major, R2, R1, S1, S2, S_major
  const structuredZones = useMemo(() => {
    const allResistance = analysis?.zones?.resistance || [];
    const allSupport = analysis?.zones?.support || [];
    const price = currentPrice || 0;

    // Sort resistance by distance from current price (closest first)
    const resistanceByDistance = [...allResistance]
      .filter(z => (z.low + z.high) / 2 > price)
      .sort((a, b) => ((a.low + a.high) / 2) - ((b.low + b.high) / 2));

    // Sort support by distance from current price (closest first)
    const supportByDistance = [...allSupport]
      .filter(z => (z.low + z.high) / 2 < price)
      .sort((a, b) => ((b.low + b.high) / 2) - ((a.low + a.high) / 2));

    // R_major: highest score resistance (structure ceiling)
    const rMajor = allResistance.length > 0
      ? allResistance.reduce((max, z) => (z.score || 0) > (max.score || 0) ? z : max)
      : null;

    // S_major: highest score support (structure floor)
    const sMajor = allSupport.length > 0
      ? allSupport.reduce((max, z) => (z.score || 0) > (max.score || 0) ? z : max)
      : null;

    // R1, R2: closest resistances above price
    const r1 = resistanceByDistance[0] || null;
    const r2 = resistanceByDistance[1] || null;

    // S1, S2: closest supports below price
    const s1 = supportByDistance[0] || null;
    const s2 = supportByDistance[1] || null;

    return { rMajor, r2, r1, s1, s2, sMajor };
  }, [analysis, currentPrice]);

  // Use cached timeline for display
  const filteredTimeline = useMemo(() => {
    const events = cachedTimeline.length > 0 ? cachedTimeline : (analysis?.timeline || []);
    if (timelineFilter === 'all') return events;
    return events.filter(e => {
      const et = e.event_type || '';
      if (timelineFilter === 'structure') return et.includes('regime') || et.includes('swing');
      if (timelineFilter === 'volume') return et.includes('volume') || et.includes('absorption');
      if (timelineFilter === 'breakout') return et.includes('breakout') || et.includes('fakeout') || et.includes('zone');
      return true;
    });
  }, [cachedTimeline, analysis?.timeline, timelineFilter]);

  // Parse AI narrative into structured sections
  const parsedNarrative = useMemo(() => {
    const content = currentNarrative?.content || '';
    if (!content) return null;

    // Parse conclusion
    const conclusionMatch = content.match(/结论[：:]\s*([^\n]+)/);
    const conclusion = conclusionMatch?.[1]?.trim() || '';

    // Parse evidence chain
    const evidenceMatch = content.match(/证据链[：:]?\s*([\s\S]*?)(?=关键位|两套剧本|$)/);
    const evidenceText = evidenceMatch?.[1] || '';
    const evidenceItems = evidenceText.split(/[•\-\*]/).map(s => s.trim()).filter(s => s.length > 0);

    // Parse key levels
    const levelsMatch = content.match(/关键位[：:]?\s*([\s\S]*?)(?=两套剧本|下根|$)/);
    const levelsText = levelsMatch?.[1] || '';
    const resistanceMatch = levelsText.match(/阻力[：:]\s*([\d\.,\s]+)/);
    const supportMatch = levelsText.match(/支撑[：:]\s*([\d\.,\s]+)/);
    const resistance = resistanceMatch?.[1]?.match(/[\d.]+/g)?.map(Number) || [];
    const support = supportMatch?.[1]?.match(/[\d.]+/g)?.map(Number) || [];

    // Parse scenarios
    const bullMatch = content.match(/多头[剧本场景：:]*\s*([\s\S]*?)(?=空头|下根|$)/i);
    const bearMatch = content.match(/空头[剧本场景：:]*\s*([\s\S]*?)(?=下根|$)/i);

    const parseBullBear = (text: string) => {
      const trigger = text.match(/触发[：:]\s*(.+?)(?=目标|失效|\n|$)/)?.[1]?.trim() || '';
      const target = text.match(/目标[：:]\s*(.+?)(?=失效|\n|$)/)?.[1]?.trim() || '';
      const invalidation = text.match(/失效[：:]\s*(.+?)(?=\n|$)/)?.[1]?.trim() || '';
      return { trigger, target, invalidation };
    };

    const bull = bullMatch ? parseBullBear(bullMatch[1]) : null;
    const bear = bearMatch ? parseBullBear(bearMatch[1]) : null;

    // Parse next candle focus
    const focusMatch = content.match(/下根K线关注[：:]?\s*([\s\S]*?)$/i);
    const focusText = focusMatch?.[1] || '';
    const focusItems = focusText.split(/[•\-\*□☐✓✗]/).map(s => s.trim()).filter(s => s.length > 0 && s.length < 100);

    return {
      conclusion,
      evidenceItems: evidenceItems.slice(0, 4),
      resistance: resistance.slice(0, 2),
      support: support.slice(0, 2),
      bull,
      bear,
      focusItems: focusItems.slice(0, 3),
      raw: content
    };
  }, [currentNarrative?.content]);

  // Use cached evidence for display
  const displayEvidence = useMemo(() => {
    return cachedEvidence.length > 0 ? cachedEvidence : (analysis?.behavior?.evidence || []);
  }, [cachedEvidence, analysis?.behavior?.evidence]);

  const handleEvidenceClick = useCallback((e: Evidence) => {
    if (e.bar_time) {
      setHighlightedBarTime(e.bar_time);
    }
  }, []);

  const handleTimelineClick = useCallback((e: TimelineEvent) => {
    if (e.bar_index !== undefined && e.bar_index >= 0 && bars) {
      const bar = bars[e.bar_index];
      if (bar) setHighlightedBarTime(bar.t);
    }
  }, [bars]);

  // Helpers
  const getRegimeText = () => {
    if (regime === 'uptrend') return t('bullish');
    if (regime === 'downtrend') return t('bearish');
    return t('neutral');
  };

  const getRegimeColor = () => {
    if (regime === 'uptrend') return C.bullish;
    if (regime === 'downtrend') return C.bearish;
    return C.textSecondary;
  };

  const getBreakoutStateColor = () => {
    if (breakoutState === 'confirmed') return C.bullish;
    if (breakoutState === 'fakeout') return C.bearish;
    // 'attempt' 用中性灰色，不用橙色抢眼
    if (breakoutState === 'attempt') return C.textSecondary;
    return C.textMuted;
  };

  const getBreakoutStateText = () => {
    if (breakoutState === 'confirmed') return t('confirmed');
    if (breakoutState === 'fakeout') return t('fakeout_state');
    if (breakoutState === 'attempt') return t('attempt');
    return t('idle');
  };

  // Decision Line - Bloomberg-style action/trigger/risk
  const getDecisionLine = (): {
    actionKey: string;
    actionColor: string;
    triggerKey: string;
    triggerParams?: Record<string, string>;
    riskKey?: string;
  } => {
    const nearResistance = resistanceZones[0] && currentPrice && currentPrice >= resistanceZones[0].low * 0.99;
    const nearSupport = supportZones[0] && currentPrice && currentPrice <= supportZones[0].high * 1.01;
    const lowConfidence = dominantProb < 0.3;

    if (breakoutState === 'fakeout') {
      return {
        actionKey: 'decision_avoid',
        actionColor: C.bearish,
        triggerKey: 'trigger_fakeout_detected',
        riskKey: 'trigger_wait_structure_reset'
      };
    }
    if (breakoutState === 'confirmed') {
      return {
        actionKey: 'decision_confirm',
        actionColor: C.bullish,
        triggerKey: 'trigger_breakout_confirmed',
        riskKey: lowConfidence ? 'trigger_low_regime_confidence' : undefined
      };
    }
    if (breakoutState === 'attempt') {
      if (latestRvol !== null && latestRvol < VOLUME_THRESHOLD) {
        return {
          actionKey: 'decision_wait',
          actionColor: C.textSecondary,  // 灰色，不用橙色
          triggerKey: 'trigger_need_rvol',
          triggerParams: { rvol: formatNum(latestRvol) },
          riskKey: lowConfidence ? 'trigger_low_confidence' : undefined
        };
      }
      // Include breakout level and direction in the trigger message
      const levelStr = breakoutLevel ? formatPrice(breakoutLevel) : '—';
      const dirStr = breakoutDirection === 'up' ? '↑' : breakoutDirection === 'down' ? '↓' : '';
      return {
        actionKey: 'decision_watch',
        actionColor: C.accent,
        triggerKey: 'trigger_need_2nd_close_level',
        triggerParams: { level: levelStr, direction: dirStr },
        riskKey: lowConfidence ? 'trigger_low_confidence' : undefined
      };
    }

    if (nearResistance) {
      return {
        actionKey: 'decision_watch',
        actionColor: C.accent,
        triggerKey: 'trigger_at_resistance',
        riskKey: lowConfidence ? 'trigger_low_confidence' : undefined
      };
    }
    if (nearSupport) {
      return {
        actionKey: 'decision_watch',
        actionColor: C.accent,
        triggerKey: 'trigger_at_support',
        riskKey: lowConfidence ? 'trigger_low_confidence' : undefined
      };
    }

    return {
      actionKey: 'decision_wait',
      actionColor: C.textMuted,
      triggerKey: 'trigger_monitor_structure',
      riskKey: lowConfidence ? 'trigger_low_confidence' : undefined
    };
  };

  const getSummaryAction = (): { text: string; type: 'wait' | 'watch' | 'caution' } => {
    if (breakoutState === 'fakeout') return { text: t('action_caution_fakeout'), type: 'caution' };
    if (breakoutState === 'attempt') {
      if (latestRvol !== null && latestRvol < VOLUME_THRESHOLD) {
        return { text: t('action_wait_rvol'), type: 'wait' };
      }
      return { text: t('action_watch_confirm'), type: 'watch' };
    }
    if (breakoutState === 'confirmed') return { text: t('action_breakout_confirmed'), type: 'watch' };

    // Check proximity to zones
    const nearResistance = resistanceZones[0] && currentPrice && currentPrice >= resistanceZones[0].low * 0.99;
    const nearSupport = supportZones[0] && currentPrice && currentPrice <= supportZones[0].high * 1.01;
    if (nearResistance) return { text: t('action_at_resistance'), type: 'watch' };
    if (nearSupport) return { text: t('action_at_support'), type: 'watch' };

    return { text: t('action_monitor'), type: 'wait' };
  };

  // Zone distance - primary: ATR with arrow, hover: percentage
  const formatZoneDistance = (zone: Zone): { atr: string; pct: string } => {
    if (!currentPrice) return { atr: '—', pct: '—' };
    const mid = (zone.low + zone.high) / 2;
    const diff = mid - currentPrice;
    const pct = (diff / currentPrice) * 100;

    if (estimatedATR && estimatedATR > 0) {
      const atrDist = Math.abs(diff / estimatedATR);
      // ↑ for resistance (above price), ↓ for support (below price)
      const arrow = diff >= 0 ? '↑' : '↓';
      return {
        atr: `${atrDist.toFixed(1)} ${arrow}`,
        pct: formatPercent(pct, true)
      };
    }
    return { atr: '—', pct: formatPercent(pct, true) };
  };

  const getEventBadgeStyle = (eventType: string): { bg: string; color: string } => {
    const et = eventType || '';
    if (et.includes('regime')) return { bg: '#dbeafe', color: '#1d4ed8' };
    if (et.includes('breakout') || et.includes('fakeout')) return { bg: '#fef3c7', color: '#b45309' };
    if (et.includes('zone')) return { bg: '#fce7f3', color: '#be185d' };
    if (et.includes('volume') || et.includes('absorption')) return { bg: '#cffafe', color: '#0891b2' };
    if (et.includes('spring') || et.includes('upthrust')) return { bg: '#fef9c3', color: '#a16207' };
    if (et.includes('swing')) return { bg: '#dcfce7', color: '#15803d' };
    return { bg: C.dividerLight, color: C.textSecondary };
  };

  const getEventBadgeText = (eventType: string) => {
    const et = eventType || '';
    if (et.includes('regime')) return t('badge_regime');
    if (et.includes('breakout')) return t('badge_break');
    if (et.includes('fakeout')) return t('badge_break');
    if (et.includes('zone')) return t('badge_zone');
    if (et.includes('volume')) return t('badge_vol');
    if (et.includes('absorption')) return t('badge_vol');
    if (et.includes('spring') || et.includes('upthrust')) return t('badge_behav');
    if (et.includes('swing')) return t('badge_swing');
    if (et.includes('init')) return t('badge_info');
    return t('badge_info');
  };

  const getEventText = (event: TimelineEvent) => {
    const et = event.event_type || '';
    // Map event types to user-friendly descriptions
    if (et.includes('init')) return t('timeline_init');
    if (et.includes('zone') && et.includes('test')) return t('timeline_zone_test');
    if (et.includes('zone')) return t('timeline_zone_update');
    if (et.includes('breakout_confirmed')) return t('timeline_breakout_confirmed');
    if (et.includes('breakout')) return t('timeline_breakout_attempt');
    if (et.includes('fakeout')) return t('timeline_fakeout');
    if (et.includes('regime')) return t('timeline_regime_change');
    if (et.includes('behavior')) return t('timeline_behavior_shift');
    if (et.includes('volume')) return t('timeline_volume_spike');
    if (et.includes('swing')) return t('timeline_swing_formed');
    // Fallback to translated reason or default
    const translated = t(et);
    if (translated !== et) return translated;
    return et.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  const translateEvidence = (note: string) => {
    if (!note) return '—';
    const translated = t(note);
    return translated !== note ? translated : note.replace(/^evidence\./, '').replace(/\./g, ' ').replace(/_/g, ' ');
  };

  const getEvidenceSeverityColor = (severity: string | undefined) => {
    if (severity === 'high') return C.bearish;
    if (severity === 'med') return C.warn;
    return C.textMuted;
  };

  const action = getSummaryAction();

  return (
    <Layout>
      <Head>
        <title>{ticker} - KLineLens</title>
      </Head>

      <div style={s.page}>
        {/* ===== Status Strip ===== */}
        <div style={s.statusStrip}>
          <div style={s.statusInner}>
            <div style={s.statusLeft}>
              <div style={s.statusItem}>
                <span style={s.statusDot} />
                <span style={s.statusLabel}>{t('provider')}:</span>
                <span style={s.statusValue}>TwelveData</span>
              </div>
              <div style={s.statusItem}>
                <span style={s.statusLabel}>{t('delay')}:</span>
                <span style={s.statusValue}>~15m</span>
              </div>
              <div style={s.statusItem}>
                <span style={s.statusLabel}>{t('updated')}:</span>
                <span style={s.statusValue}>{formatDateTime(lastUpdated || undefined)}</span>
              </div>
              <div style={s.statusItem}>
                <span style={s.statusLabel}>{t('bars')}:</span>
                <span style={s.statusValue}>{analysis?.bar_count || '—'}</span>
              </div>
              <div style={s.statusItem}>
                <span style={s.statusLabel}>Vol</span>
                <span style={{
                  ...s.statusVolumeDot,
                  backgroundColor: volumeQuality === 'reliable' ? C.bullish :
                         volumeQuality === 'partial' ? C.warn : C.bearish
                }} title={volumeQuality === 'reliable' ? 'Volume OK' : volumeQuality === 'partial' ? 'Volume Partial' : 'Volume N/A'} />
              </div>
            </div>
            <div />
          </div>
        </div>

        {/* ===== Header ===== */}
        <header style={s.header}>
          <div style={s.headerInner}>
            <div style={s.headerLeft}>
              <span style={s.ticker}>{ticker}</span>
              <span style={s.price}>{formatPrice(currentPrice)}</span>
              <span style={{ ...s.change, color: isUp ? C.bullish : C.bearish }}>
                {formatPercent(priceChangePercent, true)}
              </span>
            </div>

            <div style={s.headerRight}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <span style={s.tfLabel}>{t('label_tf')}</span>
                <div style={s.tfGroup}>
                  {(['1d', '5m', '1m'] as Timeframe[]).map(tf => (
                    <button
                      key={tf}
                      onClick={() => setTimeframe(tf)}
                      style={{ ...s.tfBtn, ...(timeframe === tf ? s.tfBtnActive : {}) }}
                    >
                      {tf.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <span style={s.tfLabel}>{t('label_zones')}</span>
                <div style={s.tfGroup}>
                  <button
                    onClick={() => setShowAllZones(false)}
                    style={{ ...s.tfBtn, ...(!showAllZones ? s.tfBtnActive : {}) }}
                  >
                    {t('zones_key').toUpperCase()}
                  </button>
                  <button
                    onClick={() => setShowAllZones(true)}
                    style={{ ...s.tfBtn, ...(showAllZones ? s.tfBtnActive : {}) }}
                  >
                    {t('zones_all').toUpperCase()}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* ===== Main ===== */}
        <main style={s.main}>
          {error && (
            <div style={s.error}>
              <div style={s.errorText}>{t('load_failed')}</div>
              <div style={s.errorMsg}>{error.message}</div>
              <button onClick={() => refresh()} style={s.retryBtn}>{t('retry')}</button>
            </div>
          )}

          {isLoading && !analysis && <DetailPageSkeleton />}

          {analysis && (
            <>
              <div style={s.grid}>
                {/* ===== Left: Chart ===== */}
                <div style={s.chartSection}>
                  {/* Chart Header (status line) */}
                  <div style={s.chartHeader}>
                    <div style={s.chartStatus}>
                      <span style={s.chartStatusLabel}>{t('label_regime')}:</span>
                      <span style={{ ...s.chartStatusValue, color: getRegimeColor() }}>
                        {getRegimeText()} ({Math.round(regimeConf * 100)}%)
                      </span>
                    </div>
                    <div style={s.chartStatus}>
                      <span style={s.chartStatusLabel}>{t('label_breakout')}:</span>
                      <span style={{ ...s.chartStatusValue, color: getBreakoutStateColor() }}>
                        {getBreakoutStateText()}
                      </span>
                    </div>
                    <div style={s.chartStatus}>
                      <span style={s.chartStatusLabel}>{t('label_behavior')}:</span>
                      <span style={s.chartStatusValue}>
                        {t(dominantBehavior) || '—'}
                      </span>
                    </div>
                  </div>

                  <div style={s.chartContainer}>
                    <CandlestickChart
                      bars={bars || []}
                      supportZones={supportZones}
                      resistanceZones={resistanceZones}
                      height={chartHeight}
                      showVolume={true}
                      highlightedBarTime={highlightedBarTime}
                      onClearHighlight={() => setHighlightedBarTime(null)}
                      currentPrice={currentPrice}
                      timeframe={timeframe}
                    />
                  </div>

                  {/* ===== AI 解读（纯文字，清晰排版） ===== */}
                  {(currentNarrative?.content || currentNarrative?.loading) && (
                    <div style={{
                      marginTop: '1.5rem',
                      paddingTop: '1rem',
                      borderTop: `1px solid ${C.dividerLight}`,
                    }}>
                      <div style={{
                        fontSize: '0.6875rem',
                        fontWeight: 600,
                        color: C.textMuted,
                        marginBottom: '0.75rem',
                        textTransform: 'uppercase' as const,
                        letterSpacing: '0.04em',
                      }}>
                        {t('ai_interpretation')}
                      </div>

                      {/* Loading skeleton */}
                      {currentNarrative?.loading && !currentNarrative?.content && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                          <div style={{ height: '0.875rem', width: '100%', backgroundColor: '#f3f4f6', borderRadius: '2px', animation: 'pulse 1.5s ease-in-out infinite' }} />
                          <div style={{ height: '0.875rem', width: '95%', backgroundColor: '#f3f4f6', borderRadius: '2px', animation: 'pulse 1.5s ease-in-out infinite', animationDelay: '0.1s' }} />
                          <div style={{ height: '0.875rem', width: '85%', backgroundColor: '#f3f4f6', borderRadius: '2px', animation: 'pulse 1.5s ease-in-out infinite', animationDelay: '0.2s' }} />
                          <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
                        </div>
                      )}

                      {/* Plain text */}
                      {currentNarrative?.content && (
                        <div style={{
                          fontSize: '0.8125rem',
                          lineHeight: 1.8,
                          color: C.textSecondary,
                        }}>
                          {currentNarrative.content}
                        </div>
                      )}
                    </div>
                  )}

                  {/* ===== Bottom Panel (below chart, left side) ===== */}
                  <div style={s.bottomPanel}>
                    <div style={s.bottomTabs}>
                      {(['playbook', 'signal_eval', 'evidence', 'volume'] as BottomTab[]).map(tab => (
                        <button
                          key={tab}
                          onClick={() => setBottomTab(tab)}
                          style={{ ...s.bottomTab, ...(bottomTab === tab ? s.bottomTabActive : {}) }}
                        >
                          {t(`tab_${tab}`)}
                        </button>
                      ))}
                    </div>

                    <div style={s.bottomContent}>
                      {/* Playbook Tab - Table Format */}
                      {bottomTab === 'playbook' && (
                        <div style={{ padding: '0.5rem 0' }}>
                          {analysis.playbook.length === 0 ? (
                            <div style={{ color: C.textMuted, fontSize: '0.75rem' }}>{t('no_executable_plans')}</div>
                          ) : (
                            <div style={{ overflowX: 'auto' }}>
                              {/* Table Header */}
                              <div style={{
                                display: 'grid',
                                gridTemplateColumns: '60px 60px 80px 80px 80px 50px 1fr 120px',
                                gap: '0.75rem',
                                fontSize: '0.5625rem',
                                fontWeight: 500,
                                color: C.textMuted,
                                textTransform: 'uppercase',
                                letterSpacing: '0.04em',
                                paddingBottom: '0.5rem',
                                borderBottom: `1px solid ${C.dividerLight}`,
                                marginBottom: '0.5rem',
                                minWidth: '700px',
                              }}>
                                <span>{t('plan')}</span>
                                <span>{t('direction')}</span>
                                <span style={{ textAlign: 'right' }}>{t('entry')}</span>
                                <span style={{ textAlign: 'right' }}>{t('target')}</span>
                                <span style={{ textAlign: 'right' }}>{t('stop')}</span>
                                <span style={{ textAlign: 'center' }}>R:R</span>
                                <span>{t('condition')}</span>
                                <span>{t('risk')}</span>
                              </div>
                              {/* Table Rows */}
                              {analysis.playbook.slice(0, 2).map((plan, i) => {
                                const isLong = plan.target > plan.level;
                                const direction = isLong ? 'LONG' : 'SHORT';
                                const directionColor = isLong ? C.bullish : C.bearish;
                                const riskAmt = Math.abs(plan.level - plan.invalidation);
                                const rewardAmt = Math.abs(plan.target - plan.level);
                                const rr = riskAmt > 0 ? (rewardAmt / riskAmt).toFixed(1) : '—';

                                return (
                                  <div
                                    key={i}
                                    style={{
                                      display: 'grid',
                                      gridTemplateColumns: '60px 60px 80px 80px 80px 50px 1fr 120px',
                                      gap: '0.75rem',
                                      padding: '0.625rem 0',
                                      fontSize: '0.75rem',
                                      fontFamily: MONO,
                                      fontVariantNumeric: 'tabular-nums',
                                      borderBottom: i < analysis.playbook.slice(0, 2).length - 1 ? `1px solid ${C.dividerLight}` : 'none',
                                      alignItems: 'center',
                                      minWidth: '700px',
                                    }}
                                  >
                                    <span style={{ fontWeight: 600, color: C.textSecondary }}>
                                      {i === 0 ? t('plan_a') : t('plan_b')}
                                    </span>
                                    <span style={{
                                      fontWeight: 600,
                                      color: directionColor,
                                      padding: '0.125rem 0.375rem',
                                      backgroundColor: isLong ? 'rgba(22, 163, 74, 0.1)' : 'rgba(220, 38, 38, 0.1)',
                                      borderRadius: '2px',
                                      textAlign: 'center',
                                      fontSize: '0.625rem',
                                    }}>
                                      {direction}
                                    </span>
                                    <span style={{ fontWeight: 500, textAlign: 'right' }}>{formatPrice(plan.level)}</span>
                                    <span style={{ fontWeight: 500, color: C.bullish, textAlign: 'right' }}>{formatPrice(plan.target)}</span>
                                    <span style={{ fontWeight: 600, color: C.bearish, textAlign: 'right' }}>{formatPrice(plan.invalidation)}</span>
                                    <span style={{ fontWeight: 500, textAlign: 'center' }}>{rr}</span>
                                    <span style={{
                                      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                                      fontSize: '0.6875rem',
                                      color: C.textSecondary,
                                      whiteSpace: 'nowrap',
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                    }} title={t(plan.condition) || plan.condition}>
                                      {t(plan.condition) || plan.condition}
                                    </span>
                                    <span style={{
                                      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                                      fontSize: '0.625rem',
                                      color: plan.risk ? C.warn : C.textMuted,
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '0.25rem',
                                    }}>
                                      {plan.risk && <span>⚠</span>}
                                      <span style={{
                                        whiteSpace: 'nowrap',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                      }} title={plan.risk ? (t(plan.risk) || plan.risk) : ''}>
                                        {plan.risk ? (t(plan.risk) || plan.risk) : '—'}
                                      </span>
                                    </span>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Signal Evaluation Tab */}
                      {bottomTab === 'signal_eval' && (
                        <div style={{ padding: '0.5rem 0' }}>
                          {/* Statistics Summary */}
                          {signalEvaluations && (
                            <div style={{
                              display: 'flex',
                              gap: '1.5rem',
                              marginBottom: '0.75rem',
                              padding: '0.5rem 0',
                              borderBottom: `1px solid ${C.dividerLight}`,
                            }}>
                              <div style={{ fontSize: '0.75rem' }}>
                                <span style={{ color: C.textMuted }}>{t('accuracy_rate')}: </span>
                                <span style={{
                                  fontWeight: 600,
                                  color: signalEvaluations.statistics.accuracy_rate >= 0.6 ? C.bullish : C.textSecondary,
                                }}>
                                  {Math.round(signalEvaluations.statistics.accuracy_rate * 100)}%
                                </span>
                              </div>
                              <div style={{ fontSize: '0.6875rem', color: C.textMuted }}>
                                {t('total_predictions')}: {signalEvaluations.statistics.total_predictions}
                              </div>
                              <div style={{ fontSize: '0.6875rem', color: C.bullish }}>
                                {t('correct_count')}: {signalEvaluations.statistics.correct}
                              </div>
                              <div style={{ fontSize: '0.6875rem', color: C.bearish }}>
                                {t('incorrect_count')}: {signalEvaluations.statistics.incorrect}
                              </div>
                              <div style={{ fontSize: '0.6875rem', color: C.textMuted }}>
                                {t('pending_count')}: {signalEvaluations.statistics.pending}
                              </div>
                            </div>
                          )}

                          {/* Evaluations Table */}
                          {evalLoading ? (
                            <div style={{ color: C.textMuted, fontSize: '0.75rem' }}>{t('loading')}</div>
                          ) : signalEvaluations?.records.length === 0 ? (
                            <div style={{ color: C.textMuted, fontSize: '0.75rem' }}>{t('no_evaluations')}</div>
                          ) : (
                            <div style={{ overflowX: 'auto' }}>
                              {/* Table Header */}
                              <div style={{
                                display: 'grid',
                                gridTemplateColumns: '70px 90px 50px 120px 70px 80px 1fr',
                                gap: '0.5rem',
                                fontSize: '0.5625rem',
                                fontWeight: 500,
                                color: C.textMuted,
                                textTransform: 'uppercase',
                                letterSpacing: '0.04em',
                                paddingBottom: '0.5rem',
                                marginBottom: '0.25rem',
                                minWidth: '600px',
                              }}>
                                <span>{t('time')}</span>
                                <span>{t('signal_type_col')}</span>
                                <span>{t('direction_col')}</span>
                                <span>{t('prices_col')}</span>
                                <span>{t('status_col')}</span>
                                <span>{t('result_col')}</span>
                                <span>{t('notes_col')}</span>
                              </div>
                              {/* Table Rows */}
                              {signalEvaluations?.records.map((evalRecord) => (
                                <div
                                  key={evalRecord.id}
                                  style={{
                                    display: 'grid',
                                    gridTemplateColumns: '70px 90px 50px 120px 70px 80px 1fr',
                                    gap: '0.5rem',
                                    padding: '0.5rem 0',
                                    fontSize: '0.6875rem',
                                    fontFamily: MONO,
                                    borderBottom: `1px solid ${C.dividerLight}`,
                                    alignItems: 'center',
                                    minWidth: '600px',
                                  }}
                                >
                                  <span style={{ color: C.textMuted }}>
                                    {formatTime(evalRecord.created_at)}
                                  </span>
                                  <span style={{ color: C.textSecondary }}>
                                    {t(`signal.${evalRecord.signal_type}`) || evalRecord.signal_type}
                                  </span>
                                  <span style={{
                                    color: evalRecord.direction === 'up' ? C.bullish : C.bearish,
                                    fontWeight: 600,
                                  }}>
                                    {t(evalRecord.direction)}
                                  </span>
                                  <span style={{ fontSize: '0.625rem', color: C.textSecondary }}>
                                    {formatPrice(evalRecord.entry_price)} → {formatPrice(evalRecord.target_price)}
                                  </span>
                                  <span style={{
                                    fontSize: '0.625rem',
                                    fontWeight: 500,
                                    padding: '0.125rem 0.25rem',
                                    borderRadius: '2px',
                                    backgroundColor: evalRecord.status === 'correct' ? 'rgba(22, 163, 74, 0.1)' :
                                                     evalRecord.status === 'incorrect' ? 'rgba(220, 38, 38, 0.1)' :
                                                     'rgba(163, 163, 163, 0.1)',
                                    color: evalRecord.status === 'correct' ? C.bullish :
                                           evalRecord.status === 'incorrect' ? C.bearish :
                                           C.textMuted,
                                  }}>
                                    {t(`status_${evalRecord.status}`)}
                                  </span>
                                  <span style={{ fontSize: '0.625rem', color: C.textSecondary }}>
                                    {evalRecord.result ? t(`result_${evalRecord.result}`) : '—'}
                                  </span>
                                  <span style={{
                                    fontSize: '0.625rem',
                                    color: C.textMuted,
                                    whiteSpace: 'nowrap',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                  }} title={evalRecord.notes || evalRecord.actual_outcome || ''}>
                                    {evalRecord.notes || evalRecord.actual_outcome || '—'}
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Evidence Tab */}
                      {bottomTab === 'evidence' && (
                        <div style={s.evidenceTable}>
                          <div style={{
                            ...s.evidenceTableHeader,
                            gridTemplateColumns: '60px 80px 80px 60px 1fr',
                          }}>
                            <span>{t('time')}</span>
                            <span>{t('type')}</span>
                            <span>{t('behavior')}</span>
                            <span>{t('severity')}</span>
                            <span>{t('note')}</span>
                          </div>
                          {displayEvidence.length === 0 ? (
                            <div style={s.timelineEmpty}>{t('no_evidence')}</div>
                          ) : (
                            displayEvidence.map((ev, i) => (
                              <div
                                key={i}
                                onClick={() => handleEvidenceClick(ev)}
                                style={{
                                  ...s.evidenceTableRow,
                                  gridTemplateColumns: '60px 80px 80px 60px 1fr',
                                }}
                              >
                                <span style={{ fontSize: '0.6875rem', fontFamily: MONO, color: C.textMuted }}>
                                  {formatTime(ev.bar_time)}
                                </span>
                                <span style={s.evidenceType}>{ev.type ? t(ev.type) : '—'}</span>
                                <span style={{ color: C.textSecondary }}>{ev.behavior ? t(ev.behavior) : '—'}</span>
                                <span style={{ ...s.evidenceSeverity, color: getEvidenceSeverityColor(ev.severity) }}>
                                  {ev.severity ? t(ev.severity) : '—'}
                                </span>
                                <span style={{ color: C.textSecondary }}>{translateEvidence(ev.note)}</span>
                              </div>
                            ))
                          )}
                        </div>
                      )}

                      {/* Volume Tab */}
                      {bottomTab === 'volume' && (
                        <div style={s.volumeGrid}>
                          <div style={s.volumeSection}>
                            <div style={s.volumeSectionTitle}>{t('effort_result')}</div>
                            <div style={s.quadrant}>
                              <div style={{ ...s.quadrantCell, backgroundColor: '#fffbeb' }}>
                                <span>{t('absorption')}</span>
                              </div>
                              <div style={{ ...s.quadrantCell, backgroundColor: '#ecfdf5' }}>
                                <span>{t('true_push')}</span>
                              </div>
                              <div style={s.quadrantCell}>
                                <span>{t('dryup')}</span>
                              </div>
                              <div style={{ ...s.quadrantCell, backgroundColor: '#eff6ff' }}>
                                <span>{t('easy_move')}</span>
                              </div>
                              {latestEffort !== null && latestResult !== null && (
                                <div style={{
                                  ...s.quadrantDot,
                                  left: `${Math.min(Math.max((latestResult / 1.5) * 100, 5), 95)}%`,
                                  top: `${Math.min(Math.max((1 - latestEffort / 3) * 100, 5), 95)}%`,
                                }} />
                              )}
                            </div>
                          </div>
                          <div style={s.volumeSection}>
                            <div style={s.volumeSectionTitle}>{t('current_metrics')}</div>
                            <div style={s.volumeStats}>
                              <div style={s.volumeStat}>
                                <span style={s.volumeStatLabel}>{t('rvol')}</span>
                                <span style={s.volumeStatValue}>{latestRvol !== null ? `${formatNum(latestRvol)}×` : '—'}</span>
                              </div>
                              <div style={s.volumeStat}>
                                <span style={s.volumeStatLabel}>{t('effort')}</span>
                                <span style={s.volumeStatValue}>{latestEffort !== null ? formatNum(latestEffort) : '—'}</span>
                              </div>
                              <div style={s.volumeStat}>
                                <span style={s.volumeStatLabel}>{t('result')}</span>
                                <span style={s.volumeStatValue}>{latestResult !== null ? `${formatNum(latestResult)} ATR` : '—'}</span>
                              </div>
                              <div style={s.volumeStat}>
                                <span style={s.volumeStatLabel}>{t('quality')}</span>
                                <span style={{
                                  ...s.volumeStatValue,
                                  color: volumeQuality === 'reliable' ? C.bullish :
                                         volumeQuality === 'partial' ? C.warn : C.bearish
                                }}>
                                  {volumeQuality === 'reliable' ? t('reliable') :
                                   volumeQuality === 'partial' ? t('partial') : 'N/A'}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* ===== Right: Insight Rail ===== */}
                <div style={s.panel}>
                  {/* Section: Summary - Vertical List */}
                  <div style={s.section}>
                    <div style={s.sectionTitle}>{t('summary')}</div>
                    {(() => {
                      const decision = getDecisionLine();
                      const primaryColor = getRegimeColor();
                      let triggerText = t(decision.triggerKey);
                      if (decision.triggerParams) {
                        Object.entries(decision.triggerParams).forEach(([key, value]) => {
                          triggerText = triggerText.replace(`{${key}}`, value);
                        });
                      }
                      return (
                        <div style={s.summaryList}>
                          {/* 市场状态 - 大字 */}
                          <div style={s.summaryItem}>
                            <span style={s.summaryLabel}>{t('market_state')}</span>
                            <span>
                              <span style={{ ...s.summaryValueLarge, color: primaryColor }}>{getRegimeText()}</span>
                              <span style={s.summaryMuted}>({Math.round(regimeConf * 100)}%)</span>
                            </span>
                          </div>
                          {/* 突破状态 */}
                          <div style={s.summaryItem}>
                            <span style={s.summaryLabel}>{t('label_breakout')}</span>
                            <span style={{ ...s.summaryValueSmall, color: getBreakoutStateColor() }}>{getBreakoutStateText()}</span>
                          </div>
                          {/* 行为 */}
                          <div style={s.summaryItem}>
                            <span style={s.summaryLabel}>{t('behavior')}</span>
                            <span style={s.summaryValueSmall}>{t(dominantBehavior)}</span>
                          </div>
                          {/* 操作 - 大字 */}
                          <div style={s.summaryItem}>
                            <span style={s.summaryLabel}>{t('decision_action')}</span>
                            <span style={{ ...s.summaryValueLarge, color: decision.actionColor }}>{t(decision.actionKey)}</span>
                          </div>
                          {/* 触发条件 */}
                          <div style={s.summaryItem}>
                            <span style={s.summaryLabel}>{t('decision_trigger')}</span>
                            <span style={s.summaryValueSmall}>{triggerText}</span>
                          </div>
                          {/* 风险 */}
                          {decision.riskKey && (
                            <div style={s.summaryItem}>
                              <span style={s.summaryLabel}>{t('decision_risk')}</span>
                              <span style={{ ...s.summaryValueSmall, color: C.warn }}>{t(decision.riskKey)}</span>
                            </div>
                          )}
                        </div>
                      );
                    })()}
                  </div>

                  {/* Section: Breakout Quality */}
                  <div style={s.section}>
                    <div style={s.sectionTitle}>{t('breakout_quality')}</div>
                    <div style={{ ...s.breakoutState, color: getBreakoutStateColor() }}>
                      {getBreakoutStateText()}
                    </div>
                    <div style={s.breakoutFactors}>
                      <div style={s.factorRow}>
                        <span style={{ ...s.factorCheck, ...(confirmCloses >= 2 ? s.factorCheckDone : {}) }}>
                          {confirmCloses >= 2 ? '✓' : ''}
                        </span>
                        <span style={s.factorLabel}>{t('factor_close_x2')}</span>
                        <span style={s.factorValue}>({confirmCloses}/2)</span>
                      </div>
                      <div style={s.factorRow}>
                        <span style={{ ...s.factorCheck, ...(latestRvol !== null && latestRvol >= VOLUME_THRESHOLD ? s.factorCheckDone : {}) }}>
                          {latestRvol !== null && latestRvol >= VOLUME_THRESHOLD ? '✓' : ''}
                        </span>
                        <span style={s.factorLabel}>{t('factor_rvol_threshold')}</span>
                        <span style={s.factorValue}>({latestRvol !== null ? `${formatNum(latestRvol)}×` : '—'})</span>
                      </div>
                      <div style={s.factorRow}>
                        <span style={{ ...s.factorCheck, ...(latestResult !== null && latestResult >= RESULT_THRESHOLD ? s.factorCheckDone : {}) }}>
                          {latestResult !== null && latestResult >= RESULT_THRESHOLD ? '✓' : ''}
                        </span>
                        <span style={s.factorLabel}>{t('factor_result_threshold')}</span>
                        <span style={s.factorValue}>({latestResult !== null ? `${formatNum(latestResult)} ATR` : '—'})</span>
                      </div>
                    </div>
                  </div>

                  {/* Section: Behavior (Top2 only) */}
                  <div style={s.section}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={s.sectionTitle}>{t('behavior')}</div>
                      {(timeframe === '1m' || timeframe === '5m') && (
                        <span style={{
                          fontSize: '0.5rem',
                          padding: '0.125rem 0.375rem',
                          backgroundColor: '#fef3c7',
                          color: '#b45309',
                          borderRadius: '2px',
                          fontWeight: 500,
                        }} title={t('noise_warning_behavior')}>
                          {t('noise_warning')}
                        </span>
                      )}
                    </div>
                    <div style={s.behaviorDominant}>
                      <span style={s.behaviorName}>{t(dominantBehavior) || '—'}</span>
                      <span style={s.behaviorProb}>{Math.round(dominantProb * 100)}%</span>
                      {dominantProb < 0.3 && (
                        <span
                          style={{ ...s.behaviorProb, color: C.warn, cursor: 'help', borderBottom: '1px dotted' }}
                          title={`Top1-Top2 probability gap < 15%${volumeQuality !== 'reliable' ? '\nVolume data unreliable → confidence down-weighted' : ''}`}
                        >
                          {t('low_conf')}
                        </span>
                      )}
                    </div>
                    {secondBehavior && (
                      <div style={s.behaviorSecondary}>
                        {t(secondBehavior.name)} {Math.round(secondBehavior.prob * 100)}%
                      </div>
                    )}
                    <div style={s.evidenceList}>
                      {displayEvidence.slice(0, 2).map((ev, i) => (
                        <div
                          key={i}
                          onClick={() => handleEvidenceClick(ev)}
                          style={s.evidenceItem}
                        >
                          <span style={s.evidenceBullet}>•</span>
                          <span>{translateEvidence(ev.note)}</span>
                        </div>
                      ))}
                      {displayEvidence.length === 0 && (
                        <div style={{ color: C.textMuted, fontSize: '0.75rem' }}>{t('no_evidence')}</div>
                      )}
                    </div>
                  </div>

                  {/* Section: Key Zones - Table format with explanations */}
                  <div style={s.section}>
                    <div style={s.sectionTitle}>{t('key_zones')}</div>
                    <div style={s.zonesTable}>

                      {/* HOD */}
                      {sessionHL.hod && (
                        <div style={s.zonesRow}>
                          <span style={{ ...s.zonePrice, color: C.bearish }}>{formatPrice(sessionHL.hod)}</span>
                          <span style={{ ...s.zoneValue, color: C.textMuted }}>HOD</span>
                          <span style={{ fontSize: '0.625rem', color: C.textMuted, textAlign: 'right' }}>{lang === 'zh' ? '当日最高' : 'High of Day'}</span>
                        </div>
                      )}

                      {/* R★ */}
                      {structuredZones.rMajor && structuredZones.rMajor !== structuredZones.r1 && structuredZones.rMajor !== structuredZones.r2 && (
                        <div style={s.zonesRow}>
                          <span style={{ ...s.zonePrice, color: C.bearish }}>{formatPrice((structuredZones.rMajor.low + structuredZones.rMajor.high) / 2)}</span>
                          <span style={{ ...s.zoneValue, color: C.textMuted }}>R★</span>
                          <span style={{ fontSize: '0.625rem', color: C.textMuted, textAlign: 'right' }}>{lang === 'zh' ? '结构天花板' : 'Ceiling'}</span>
                        </div>
                      )}

                      {/* R2 */}
                      {structuredZones.r2 && (
                        <div style={s.zonesRow}>
                          <span style={{ ...s.zonePrice, color: C.bearish }}>{formatPrice((structuredZones.r2.low + structuredZones.r2.high) / 2)}</span>
                          <span style={{ ...s.zoneValue, color: C.textMuted }}>R2</span>
                          <span style={{ fontSize: '0.625rem', color: C.textMuted, textAlign: 'right' }}>{lang === 'zh' ? '突破后目标' : 'Breakout Target'}</span>
                        </div>
                      )}

                      {/* R1 */}
                      {structuredZones.r1 && (
                        <div style={s.zonesRow}>
                          <span style={{ ...s.zonePrice, color: C.bearish }}>{formatPrice((structuredZones.r1.low + structuredZones.r1.high) / 2)}</span>
                          <span style={{ ...s.zoneValue, color: C.bearish, fontWeight: 600 }}>R1</span>
                          <span style={{ fontSize: '0.625rem', color: C.textSecondary, textAlign: 'right' }}>{lang === 'zh' ? '最近阻力' : 'Next Resistance'}</span>
                        </div>
                      )}

                      {/* Divider */}
                      <div style={{ borderTop: `1px dashed ${C.divider}`, margin: '0.375rem 0' }} />

                      {/* S1 */}
                      {structuredZones.s1 && (
                        <div style={s.zonesRow}>
                          <span style={{ ...s.zonePrice, color: C.bullish }}>{formatPrice((structuredZones.s1.low + structuredZones.s1.high) / 2)}</span>
                          <span style={{ ...s.zoneValue, color: C.bullish, fontWeight: 600 }}>S1</span>
                          <span style={{ fontSize: '0.625rem', color: C.textSecondary, textAlign: 'right' }}>{lang === 'zh' ? '最近支撑' : 'Next Support'}</span>
                        </div>
                      )}

                      {/* S2 */}
                      {structuredZones.s2 && (
                        <div style={s.zonesRow}>
                          <span style={{ ...s.zonePrice, color: C.bullish }}>{formatPrice((structuredZones.s2.low + structuredZones.s2.high) / 2)}</span>
                          <span style={{ ...s.zoneValue, color: C.textMuted }}>S2</span>
                          <span style={{ fontSize: '0.625rem', color: C.textMuted, textAlign: 'right' }}>{lang === 'zh' ? '跌破后目标' : 'Breakdown Target'}</span>
                        </div>
                      )}

                      {/* S★ */}
                      {structuredZones.sMajor && structuredZones.sMajor !== structuredZones.s1 && structuredZones.sMajor !== structuredZones.s2 && (
                        <div style={s.zonesRow}>
                          <span style={{ ...s.zonePrice, color: C.bullish }}>{formatPrice((structuredZones.sMajor.low + structuredZones.sMajor.high) / 2)}</span>
                          <span style={{ ...s.zoneValue, color: C.textMuted }}>S★</span>
                          <span style={{ fontSize: '0.625rem', color: C.textMuted, textAlign: 'right' }}>{lang === 'zh' ? '结构地板' : 'Floor'}</span>
                        </div>
                      )}

                      {/* LOD */}
                      {sessionHL.lod && (
                        <div style={s.zonesRow}>
                          <span style={{ ...s.zonePrice, color: C.bullish }}>{formatPrice(sessionHL.lod)}</span>
                          <span style={{ ...s.zoneValue, color: C.textMuted }}>LOD</span>
                          <span style={{ fontSize: '0.625rem', color: C.textMuted, textAlign: 'right' }}>{lang === 'zh' ? '当日最低' : 'Low of Day'}</span>
                        </div>
                      )}

                      {/* Empty state */}
                      {!structuredZones.r1 && !structuredZones.s1 && !sessionHL.hod && (
                        <div style={{ color: C.textMuted, fontSize: '0.75rem', padding: '0.5rem 0' }}>{t('no_zones')}</div>
                      )}
                    </div>
                  </div>

                  {/* Section: Timeline - Vertical with dots */}
                  <div style={{ ...s.section, ...s.sectionLast }}>
                    <div style={s.sectionTitle}>{t('timeline')}</div>
                    {filteredTimeline.length === 0 ? (
                      <div style={{ color: C.textMuted, fontSize: '0.75rem' }}>{t('no_significant_events')}</div>
                    ) : (
                      <div style={s.timelineContainer}>
                        {filteredTimeline.slice(0, 6).map((event, i) => (
                          <div
                            key={i}
                            onClick={() => handleTimelineClick(event)}
                            style={s.timelineItem}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = C.dividerLight}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                          >
                            <span style={s.timelineTime}>{formatTime(event.ts)}</span>
                            <span style={s.timelineText}>{getEventText(event)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </main>
      </div>
    </Layout>
  );
}
