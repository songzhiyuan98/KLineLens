/**
 * 国际化上下文和工具
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type Language = 'zh' | 'en';

interface I18nContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

const translations: Record<Language, Record<string, string>> = {
  zh: {
    // 通用
    'settings': '设置',
    'general': '通用',
    'about': '关于',
    'language': '语言',
    'chinese': '中文',
    'english': 'English',
    'version': '版本',
    'refresh': '刷新',
    'loading': '加载中...',
    'retry': '重试',
    'load_failed': '加载失败',

    // 首页
    'search_placeholder': '输入代码 (如 TSLA)',
    'search_hint': '支持美股代码，如 AAPL、TSLA、NVDA',
    'quick_access': '热门股票',
    'analyze': '分析',
    'subtitle': '市场结构分析终端',
    'error_empty_ticker': '请输入股票代码',
    'error_invalid_ticker': '无效的代码格式',

    // 市场状态
    'market_state': '市场状态',
    'confidence': '置信度',
    'uptrend': '上升趋势',
    'downtrend': '下降趋势',
    'range': '震荡区间',

    // 行为
    'behavior_inference': '行为推断',
    'accumulation': '吸筹',
    'shakeout': '洗盘',
    'markup': '拉升',
    'distribution': '派发',
    'markdown': '下跌',

    // 证据
    'evidence': '支撑证据',
    'no_evidence': '暂无显著证据',

    // 时间线
    'timeline': '时间线',
    'no_events': '暂无事件',
    'initialized': '开始分析',
    'regime_change': '市场状态转变',
    'behavior_shift': '行为模式切换',
    'breakout_confirmed': '突破确认',
    'breakout_attempt': '尝试突破',
    'fakeout': '假突破',
    'fakeout_detected': '假突破',
    'probability_change': '概率变化',

    // 交易剧本
    'playbook': '交易剧本',
    'no_plans': '暂无可执行计划',
    'recommended': '推荐',
    'alternative': '备选',
    'entry': '入场',
    'target': '目标',
    'stop_loss': '止损',
    'risk_reward': '盈亏比',

    // 条件
    'condition.pullback_to_support': '价格回踩支撑位',
    'condition.breakout_continuation': '突破后顺势延续',
    'condition.resistance_rejection': '阻力位受阻回落',
    'condition.breakdown_continuation': '跌破后顺势延续',
    'condition.support_bounce': '支撑位企稳反弹',
    'condition.resistance_fade': '阻力位逢高做空',

    // 证据详情
    'evidence.accumulation.near_support': '价格接近支撑区域',
    'evidence.accumulation.high_volume_at_support': '支撑位放量承接',
    'evidence.accumulation.demand_wick': '下影线显示买盘需求',
    'evidence.shakeout.sweep_and_reclaim': '跌破支撑后快速收回',
    'evidence.shakeout.long_lower_wick': '长下影线（扫盘形态）',
    'evidence.shakeout.high_volume_sweep': '放量扫盘',
    'evidence.markup.uptrend_continuation': '上升趋势延续',
    'evidence.markup.volume_confirmation': '成交量确认上涨',
    'evidence.distribution.near_resistance': '价格接近阻力区域',
    'evidence.distribution.high_volume_at_resistance': '阻力位放量出货',
    'evidence.distribution.rejection_wick': '上影线显示卖压拒绝',
    'evidence.markdown.downtrend_continuation': '下降趋势延续',
    'evidence.markdown.volume_confirmation': '成交量确认下跌',

    // 图表
    'support_zone': '支撑区域',
    'resistance_zone': '阻力区域',
    'volume_ma': '成交量均线',
    'timeframe_1m': '1分钟',
    'timeframe_5m': '5分钟',
    'timeframe_1d': '日线',

    // 市场偏向 (1m/5m)
    'bias_bullish': '偏多',
    'bias_bearish': '偏空',
    'bias_neutral': '中性',

    // 突破状态
    'breakout_status': '突破状态',
    'breakout_state': '状态',
    'state_idle': '观望中',
    'state_attempt': '尝试突破',
    'state_confirmed': '突破确认',
    'state_fakeout': '假突破',
    'volume_ratio': '量比',
    'vol_threshold': '阈值',
    'confirm_closes': '确认K线',
    'no_volume_data': '无成交量数据',

    // 信号
    'signals': '信号',
    'no_signals': '暂无信号',
    'signal_breakout': '突破',
    'signal_fakeout': '假突破',
    'signal_rejection': '拒绝',
    'signal.breakout_attempt': '尝试突破',
    'signal.breakout_confirmed': '突破确认',
    'signal.fakeout': '假突破',
    'signal.support_bounce': '支撑反弹',
    'signal.resistance_rejection': '阻力拒绝',

    // 设置页
    'settings_future': '更多设置功能将在未来版本中提供。',
    'app_description': '市场结构分析终端',
    'disclaimer': '免责声明',
    'disclaimer_text': '本工具仅供教育目的使用，不提供投资建议。在做出任何投资决策之前，请务必自行研究。',

    // Evidence 提示
    'click_to_locate': '点击定位到图表',
  },
  en: {
    // General
    'settings': 'Settings',
    'general': 'General',
    'about': 'About',
    'language': 'Language',
    'chinese': '中文',
    'english': 'English',
    'version': 'Version',
    'refresh': 'Refresh',
    'loading': 'Loading...',
    'retry': 'Retry',
    'load_failed': 'Load Failed',

    // Home
    'search_placeholder': 'Enter ticker (e.g., TSLA)',
    'search_hint': 'Supports US stocks like AAPL, TSLA, NVDA',
    'quick_access': 'Popular tickers',
    'analyze': 'Analyze',
    'subtitle': 'Market Structure Analysis Terminal',
    'error_empty_ticker': 'Please enter a ticker symbol',
    'error_invalid_ticker': 'Invalid ticker format',

    // Market state
    'market_state': 'Market State',
    'confidence': 'Confidence',
    'uptrend': 'Uptrend',
    'downtrend': 'Downtrend',
    'range': 'Range',

    // Behavior
    'behavior_inference': 'Behavior Inference',
    'accumulation': 'Accumulation',
    'shakeout': 'Shakeout',
    'markup': 'Markup',
    'distribution': 'Distribution',
    'markdown': 'Markdown',

    // Evidence
    'evidence': 'Evidence',
    'no_evidence': 'No significant evidence',

    // Timeline
    'timeline': 'Timeline',
    'no_events': 'No events',
    'initialized': 'Analysis Started',
    'regime_change': 'Regime Changed',
    'behavior_shift': 'Behavior Shifted',
    'breakout_confirmed': 'Breakout Confirmed',
    'breakout_attempt': 'Breakout Attempt',
    'fakeout': 'Fakeout',
    'fakeout_detected': 'Fakeout Detected',
    'probability_change': 'Probability Changed',

    // Playbook
    'playbook': 'Playbook',
    'no_plans': 'No executable plans',
    'recommended': 'Recommended',
    'alternative': 'Alternative',
    'entry': 'Entry',
    'target': 'Target',
    'stop_loss': 'Stop Loss',
    'risk_reward': 'R/R',

    // Conditions
    'condition.pullback_to_support': 'Price pulls back to support',
    'condition.breakout_continuation': 'Breakout continuation',
    'condition.resistance_rejection': 'Resistance rejection',
    'condition.breakdown_continuation': 'Breakdown continuation',
    'condition.support_bounce': 'Support bounce',
    'condition.resistance_fade': 'Fade at resistance',

    // Evidence details
    'evidence.accumulation.near_support': 'Price near support zone',
    'evidence.accumulation.high_volume_at_support': 'High volume at support',
    'evidence.accumulation.demand_wick': 'Lower wick shows demand',
    'evidence.shakeout.sweep_and_reclaim': 'Sweep and reclaim pattern',
    'evidence.shakeout.long_lower_wick': 'Long lower wick (sweep)',
    'evidence.shakeout.high_volume_sweep': 'High volume sweep',
    'evidence.markup.uptrend_continuation': 'Uptrend continuation',
    'evidence.markup.volume_confirmation': 'Volume confirms rally',
    'evidence.distribution.near_resistance': 'Price near resistance zone',
    'evidence.distribution.high_volume_at_resistance': 'High volume at resistance',
    'evidence.distribution.rejection_wick': 'Upper wick shows rejection',
    'evidence.markdown.downtrend_continuation': 'Downtrend continuation',
    'evidence.markdown.volume_confirmation': 'Volume confirms decline',

    // Chart
    'support_zone': 'Support Zone',
    'resistance_zone': 'Resistance Zone',
    'volume_ma': 'Volume MA',
    'timeframe_1m': '1min',
    'timeframe_5m': '5min',
    'timeframe_1d': '1D',

    // Market bias (1m/5m)
    'bias_bullish': 'Bullish',
    'bias_bearish': 'Bearish',
    'bias_neutral': 'Neutral',

    // Breakout status
    'breakout_status': 'Breakout Status',
    'breakout_state': 'State',
    'state_idle': 'Idle',
    'state_attempt': 'Attempt',
    'state_confirmed': 'Confirmed',
    'state_fakeout': 'Fakeout',
    'volume_ratio': 'Vol Ratio',
    'vol_threshold': 'Threshold',
    'confirm_closes': 'Confirm Closes',
    'no_volume_data': 'No volume data',

    // Signals
    'signals': 'Signals',
    'no_signals': 'No signals',
    'signal_breakout': 'Breakout',
    'signal_fakeout': 'Fakeout',
    'signal_rejection': 'Rejection',
    'signal.breakout_attempt': 'Breakout Attempt',
    'signal.breakout_confirmed': 'Breakout Confirmed',
    'signal.fakeout': 'Fakeout',
    'signal.support_bounce': 'Support Bounce',
    'signal.resistance_rejection': 'Resistance Rejection',

    // Settings page
    'settings_future': 'More settings will be available in future updates.',
    'app_description': 'Market Structure Analysis Terminal',
    'disclaimer': 'Disclaimer',
    'disclaimer_text': 'This tool is for educational purposes only. It does not provide financial advice. Always do your own research before making any investment decisions.',

    // Evidence hint
    'click_to_locate': 'Click to locate on chart',
  },
};

const STORAGE_KEY = 'kline_lens_lang';

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>('zh');

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Language;
    if (stored && (stored === 'zh' || stored === 'en')) {
      setLangState(stored);
    }
  }, []);

  const setLang = (newLang: Language) => {
    setLangState(newLang);
    localStorage.setItem(STORAGE_KEY, newLang);
  };

  const t = (key: string): string => {
    return translations[lang][key] || key;
  };

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
}
