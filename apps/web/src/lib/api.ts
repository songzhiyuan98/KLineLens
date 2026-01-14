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

/** 支撑/阻力区域 */
export interface Zone {
  low: number;
  high: number;
  score: number;
  touches: number;
}

/** 信号 */
export interface Signal {
  type: string;
  direction: string;
  level: number;
  confidence: number;
  bar_time: string;
}

/** 证据 */
export interface Evidence {
  behavior: string;
  bar_time: string;
  metrics: Record<string, number>;
  note: string;
}

/** 时间线事件 */
export interface TimelineEvent {
  ts: string;
  event_type: string;
  delta: number;
  reason: string;
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

/** 分析报告 */
export interface AnalysisReport {
  ticker: string;
  tf: string;
  generated_at: string;
  bar_count: number;
  data_gaps: boolean;
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
