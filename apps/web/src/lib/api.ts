/**
 * API 客户端
 *
 * 与后端 API 通信的封装。
 */

// API 基础地址
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============ 类型定义 ============

/** K 线数据 */
export interface Bar {
  t: string;  // ISO 时间戳
  o: number;  // 开盘价
  h: number;  // 最高价
  l: number;  // 最低价
  c: number;  // 收盘价
  v: number;  // 成交量
}

/** K 线响应 */
export interface BarsResponse {
  ticker: string;
  tf: string;
  bar_count: number;
  bars: Bar[];
}

/** 支撑/阻力区域（增强版：含 rejections, reaction, recency） */
export interface Zone {
  low: number;
  high: number;
  score: number;
  touches: number;
  rejections?: number;
  last_reaction?: number;
  last_test_time?: string;
}

/** 信号（增强版：含 bar_index, volume_quality） */
export interface Signal {
  type: string;
  direction: string;
  level: number;
  confidence: number;
  bar_time: string;
  bar_index?: number;
  volume_quality?: string;  // confirmed, pending, unavailable
}

/** 证据（增强版：含 type, severity, bar_index, VSA metrics） */
export interface Evidence {
  type?: string;      // VOLUME_SPIKE, REJECTION, SWEEP, ABSORPTION, BREAKOUT
  behavior: string;
  severity?: string;  // low, med, high
  bar_time: string;
  bar_index?: number;
  metrics: Record<string, number>;  // rvol, wick_ratio, effort, result
  note: string;
}

/** 时间线事件（增强版：含 bar_index, severity） */
export interface TimelineEvent {
  ts: string;
  event_type: string;
  delta: number;
  reason: string;
  bar_index?: number;
  severity?: string;  // info, warning, critical
}

/** 交易计划 */
export interface PlaybookPlan {
  name: string;
  condition: string;
  level: number;
  target: number;
  invalidation: number;
  risk: string;
}

/** 市场状态 */
export interface MarketState {
  regime: 'uptrend' | 'downtrend' | 'range';
  confidence: number;
}

/** 行为推断 */
export interface Behavior {
  probabilities: Record<string, number>;
  dominant: string;
  evidence: Evidence[];
}

/** 分析报告（增强版：含 volume_quality） */
export interface AnalysisReport {
  ticker: string;
  tf: string;
  generated_at: string;
  bar_count: number;
  data_gaps: boolean;
  volume_quality?: string;  // reliable, partial, unavailable
  market_state: MarketState;
  zones: {
    support: Zone[];
    resistance: Zone[];
  };
  signals: Signal[];
  behavior: Behavior;
  timeline: TimelineEvent[];
  playbook: PlaybookPlan[];
}

/** API 错误 */
export interface ApiError {
  code: string;
  message: string;
}

/** 信号评估记录 */
export interface SignalEvaluation {
  id: string;
  ticker: string;
  tf: string;
  created_at: string;
  signal_type: string;
  direction: 'up' | 'down';
  predicted_behavior: string;
  entry_price: number;
  target_price: number;
  invalidation_price: number;
  confidence: number;
  notes?: string;
  status: 'pending' | 'correct' | 'incorrect';
  result?: string;
  actual_outcome?: string;
  evaluation_notes?: string;
  evaluated_at?: string;
}

/** 评估统计 */
export interface EvaluationStatistics {
  total_predictions: number;
  correct: number;
  incorrect: number;
  pending: number;
  accuracy_rate: number;
  by_signal_type: Record<string, { total: number; correct: number; accuracy: number }>;
}

/** 信号评估列表响应 */
export interface SignalEvaluationsResponse {
  ticker: string;
  total: number;
  records: SignalEvaluation[];
  statistics: EvaluationStatistics;
}

/** 报告类型 */
export type ReportType = 'full' | 'quick' | 'confirmation' | 'context';

/** 叙事报告 v2 */
export interface NarrativeResult {
  summary: string;
  action: 'WAIT' | 'WATCH' | 'TRIGGERED';
  content: string;  // 完整格式化内容（Markdown）
  why: string[];
  risks?: string[];
  quality: 'high' | 'limited';
  triggered_by?: string;  // 触发事件类型
}

/** 叙事响应 v2 */
export interface NarrativeResponse {
  ticker: string;
  timeframe: string;
  report_type: ReportType;
  lang: string;
  narrative: NarrativeResult;
  error?: string;
}

// ============ API 函数 ============

/**
 * 获取 K 线数据
 */
export async function fetchBars(
  ticker: string,
  tf: string = '1d',
  window?: string
): Promise<BarsResponse> {
  const params = new URLSearchParams({ ticker, tf });
  if (window) params.set('window', window);

  const res = await fetch(`${API_BASE}/v1/bars?${params}`);

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail?.message || 'Failed to fetch bars');
  }

  return res.json();
}

/**
 * 获取市场分析
 */
export async function fetchAnalysis(
  ticker: string,
  tf: string = '1d',
  window?: string
): Promise<AnalysisReport> {
  const body: Record<string, string> = { ticker, tf };
  if (window) body.window = window;

  const res = await fetch(`${API_BASE}/v1/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail?.message || 'Failed to fetch analysis');
  }

  return res.json();
}

/**
 * 生成市场叙事报告 v2
 *
 * @param ticker - 股票代码
 * @param tf - 时间周期 (1m, 5m, 1d)
 * @param reportType - 报告类型
 *   - full: 完整 5m 结构分析（gpt-4o）
 *   - quick: 简短更新（gpt-4o-mini）
 *   - confirmation: 1m 执行确认
 *   - context: 1D 背景框架
 * @param lang - 输出语言
 */
export async function fetchNarrative(
  ticker: string,
  tf: string = '5m',
  reportType: ReportType = 'full',
  lang: 'zh' | 'en' = 'zh'
): Promise<NarrativeResponse> {
  const body = {
    ticker,
    tf,
    report_type: reportType,
    lang,
  };

  const res = await fetch(`${API_BASE}/v1/narrative`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail?.message || 'Failed to generate narrative');
  }

  return res.json();
}

// ============ Signal Evaluation API ============

/**
 * 创建信号评估记录
 */
export async function createSignalEvaluation(data: {
  ticker: string;
  tf: string;
  signal_type: string;
  direction: 'up' | 'down';
  predicted_behavior: string;
  entry_price: number;
  target_price: number;
  invalidation_price: number;
  confidence: number;
  notes?: string;
}): Promise<SignalEvaluation> {
  const res = await fetch(`${API_BASE}/v1/signal-evaluation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail?.message || 'Failed to create signal evaluation');
  }

  return res.json();
}

/**
 * 获取信号评估列表
 */
export async function fetchSignalEvaluations(
  ticker: string,
  tf?: string,
  status?: 'pending' | 'correct' | 'incorrect',
  limit: number = 50,
  offset: number = 0
): Promise<SignalEvaluationsResponse> {
  const params = new URLSearchParams({ ticker, limit: String(limit), offset: String(offset) });
  if (tf) params.set('tf', tf);
  if (status) params.set('status', status);

  const res = await fetch(`${API_BASE}/v1/signal-evaluations?${params}`);

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail?.message || 'Failed to fetch signal evaluations');
  }

  return res.json();
}

/**
 * 更新信号评估结果
 */
export async function updateSignalEvaluation(
  evalId: string,
  data: {
    status: 'correct' | 'incorrect';
    result: string;
    actual_outcome: string;
    evaluation_notes?: string;
  }
): Promise<SignalEvaluation> {
  const res = await fetch(`${API_BASE}/v1/signal-evaluation/${evalId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail?.message || 'Failed to update signal evaluation');
  }

  return res.json();
}

/**
 * 删除信号评估记录
 */
export async function deleteSignalEvaluation(evalId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/signal-evaluation/${evalId}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail?.message || 'Failed to delete signal evaluation');
  }
}

// ============ Watchlist (自选股) API ============

/** 自选股项目 */
export interface WatchlistItem {
  ticker: string;
  added_at: string;
  note?: string;
  realtime?: {
    price: number;
    change?: number;
    change_pct?: number;
    timestamp?: string;
  };
}

/** 自选股列表响应 */
export interface WatchlistResponse {
  count: number;
  max: number;
  items: WatchlistItem[];
}

/** 自选股状态响应 */
export interface WatchlistStatusResponse {
  ticker: string;
  is_watched: boolean;
  has_realtime: boolean;
  realtime?: {
    price: number;
    change?: number;
    change_pct?: number;
    timestamp?: string;
  };
  count: number;
  max: number;
}

/**
 * 获取自选股列表
 */
export async function fetchWatchlist(): Promise<WatchlistResponse> {
  const res = await fetch(`${API_BASE}/v1/watchlist`);

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail?.message || 'Failed to fetch watchlist');
  }

  return res.json();
}

/**
 * 添加股票到自选股
 */
export async function addToWatchlist(ticker: string, note?: string): Promise<{
  success: boolean;
  ticker: string;
  message: string;
  count: number;
  max: number;
}> {
  const res = await fetch(`${API_BASE}/v1/watchlist/${ticker}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ note }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail?.message || 'Failed to add to watchlist');
  }

  return res.json();
}

/**
 * 从自选股移除
 */
export async function removeFromWatchlist(ticker: string): Promise<{
  success: boolean;
  ticker: string;
  message: string;
  count: number;
  max: number;
}> {
  const res = await fetch(`${API_BASE}/v1/watchlist/${ticker}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail?.message || 'Failed to remove from watchlist');
  }

  return res.json();
}

/**
 * 获取股票的自选股状态
 */
export async function fetchWatchlistStatus(ticker: string): Promise<WatchlistStatusResponse> {
  const res = await fetch(`${API_BASE}/v1/watchlist/${ticker}/status`);

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail?.message || 'Failed to fetch watchlist status');
  }

  return res.json();
}


// ============ Extended Hours (EH) Types ============

/** EH 关键价位 */
export interface EHLevels {
  yc: number;              // 昨收 Yesterday Close
  yh: number;              // 昨高 Yesterday High
  yl: number;              // 昨低 Yesterday Low
  pmh: number | null;      // 盘前高 Premarket High
  pml: number | null;      // 盘前低 Premarket Low
  ahh: number | null;      // 盘后高 Afterhours High
  ahl: number | null;      // 盘后低 Afterhours Low
  gap: number;             // 缺口
}

/** EH 关键区域 */
export interface EHKeyZone {
  zone: string;    // YC, YH, YL, PMH, PML, AHH, AHL
  price: number;
  role: string;    // magnet, major_resistance, major_support, breakout_trigger, etc.
}

/** AH 风险评估 */
export interface AHRisk {
  risk: string;            // low, medium, high
  likely_behavior: string; // continuation, mean_revert, drift
  close_position: number;  // 0-1
  late_rvol: number;
  is_trend_day: boolean;
}

/** EH 上下文响应 */
export interface EHContextResponse {
  levels: EHLevels;
  premarket_regime: string;      // trend_continuation, gap_and_go, gap_fill_bias, range_day_setup, unavailable
  premarket_bias: string;        // bullish, bearish, neutral
  regime_confidence: number;
  eh_range_score: number;
  eh_rvol: number;
  key_zones: EHKeyZone[];
  pm_absorption: Record<string, unknown> | null;
  ah_risk: AHRisk | null;
  expected_behaviors: string[];
  generated_at: string;
  data_quality: string;          // complete, partial, minimal
  data_quality_note: string;
  data_source: string;           // yfinance_prepost, regular_only
}

/**
 * 获取 Extended Hours 上下文
 *
 * 提供盘前/盘后关键位（PMH/PML/YC/AHH/AHL）和市场先验信息。
 */
export async function fetchEHContext(
  ticker: string,
  tf: string = '1m',
  useEH: boolean = true
): Promise<EHContextResponse> {
  const params = new URLSearchParams({
    ticker,
    tf,
    use_eh: useEH.toString(),
  });

  const res = await fetch(`${API_BASE}/v1/eh-context?${params}`);

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail?.message || 'Failed to fetch EH context');
  }

  return res.json();
}
