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
    'category_stocks': '热门美股',
    'category_etfs': 'ETF 基金',
    'category_crypto': '加密货币',

    // AI 解读
    'ai_interpretation': 'AI 解读',
    'evidence_chain': '证据链',
    'key_levels': '关键位',
    'scenarios': '剧本',
    'next_candle_focus': '下根K线关注',

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
    'disclaimer_text': '本工具仅用于技术分析学习，不构成任何投资建议。市场有风险，投资需谨慎。',

    // Evidence 提示
    'click_to_locate': '点击定位到图表',

    // 新增：专业终端 UI
    'data_source': '数据',
    'data_updated': '更新于',
    'data_delay': '延迟',
    'chart': '图表',
    'zones_key': '关键',
    'zones_all': '全部',

    // Verdict 卡片
    'verdict_bullish': '偏多',
    'verdict_bearish': '偏空',
    'verdict_neutral': '中性',
    'action_buy_dip': '逢低买入',
    'action_sell_rally': '逢高卖出',
    'action_wait': '等待',
    'action_fade': '反向操作',
    'action_trade_range': '区间交易',

    // Confirmation 区块
    'vol_ratio_label': '量比',
    'vol_ratio_need': '需要',
    'vol_unavailable': '延迟数据暂无',
    'closes_label': '确认K线',

    // Timeline 软事件
    'zone_tested': '测试区域',
    'zone_approached': '接近区域',
    'wick_rejection': '影线拒绝',
    'volume_notable': '成交量异常',
    'volume_low': '成交量偏低',
    'swing_formed': '新摆动点',
    'timeline_empty_title': '最近30根K线无重大变化',
    'timeline_empty_desc': '持续监控区域与成交量...',

    // Timeline badges (user-friendly)
    'badge_regime': '趋势',
    'badge_break': '突破',
    'badge_behav': '行为',
    'badge_prob': '概率',
    'badge_zone': '区域',
    'badge_wick': '影线',
    'badge_vol': '成交量',
    'badge_swing': '结构',
    'badge_info': '系统',

    // Timeline event descriptions (user-friendly)
    'timeline_init': '开始分析',
    'timeline_zone_update': '更新关键区域',
    'timeline_zone_test': '测试区域边界',
    'timeline_breakout_attempt': '识别突破结构',
    'timeline_breakout_confirmed': '突破确认',
    'timeline_fakeout': '假突破回落',
    'timeline_regime_change': '趋势状态变化',
    'timeline_behavior_shift': '行为模式切换',
    'timeline_volume_spike': '成交量异动',
    'timeline_swing_formed': '新摆动点形成',

    // Playbook 触发与失效
    'trigger': '触发',
    'risk': '风险',
    'trigger.pullback_support': '回调至支撑区 + 多头趋势',
    'trigger.breakout_resistance': '收盘突破阻力 + 量比≥1.8x',
    'trigger.rally_resistance': '反弹至阻力区 + 空头趋势',
    'trigger.breakdown_support': '收盘跌破支撑 + 量比≥1.8x',
    'trigger.touch_support': '触及支撑区 + 阳线形态',
    'trigger.touch_resistance': '触及阻力区 + 阴线形态',
    'risk.below_support': '收盘低于支撑 - 0.5 ATR',
    'risk.back_inside_zone': '3根K线内收回区域内',
    'risk.above_resistance': '收盘高于阻力 + 0.5 ATR',
    'risk.range_breakout': '放量突破区间',
    'risk.trend_continuation': '趋势延续失败风险',
    'risk.false_breakout': '假突破风险',
    'risk.reversal': '趋势反转风险',
    'risk.false_breakdown': '假跌破风险',
    'risk.range_break': '区间突破风险',

    // Decision Line (Action/Trigger/Risk)
    'decision_action': '操作',
    'decision_trigger': '触发条件',
    'decision_risk': '风险',
    'decision_wait': '等待',
    'decision_watch': '关注',
    'decision_confirm': '确认',
    'decision_avoid': '回避',
    'trigger_fakeout_detected': '检测到假突破',
    'trigger_wait_structure_reset': '等待结构重置',
    'trigger_breakout_confirmed': '3因素突破确认',
    'trigger_low_regime_confidence': '置信度偏低',
    'trigger_need_rvol': '需要 RVOL ≥ 1.8（当前 {rvol}×）',
    'trigger_low_confidence': '置信度偏低',
    'trigger_need_2nd_close': '等待第2根确认K线',
    'trigger_need_2nd_close_level': '等待第2根K线收于 {level} {direction}',
    'trigger_at_resistance': '触及阻力位，关注拒绝信号',
    'trigger_at_support': '触及支撑位，关注反弹信号',
    'trigger_monitor_structure': '监控结构等待机会',

    // Event 文本
    'event.analysis_started': '开始分析',
    'event.regime_changed': '趋势转变',
    'event.behavior_shifted': '行为切换',
    'event.at_resistance': '触及阻力',
    'event.at_support': '触及支撑',
    'event.uptrend_detected': '检测到上升趋势',
    'event.downtrend_detected': '检测到下降趋势',
    'event.range_bound': '进入震荡区间',

    // 新增：详情页 v2
    'bars': 'K线',
    'updated': '更新于',
    'behavior': '行为',
    'tab_volume': '成交量',
    'tab_effort_result': 'Effort vs Result',
    'effort_vs_result': 'VSA: Effort vs Result',
    'quadrant_absorption': '吸收',
    'quadrant_true_push': '真突破',
    'quadrant_dryup': '量缩',
    'quadrant_easy_move': '轻松推动',
    'interpretation_absorption': '吸收信号（机构吸筹/派发）',
    'interpretation_true_push': '真实推动（趋势延续）',
    'no_vsa_data': '无 VSA 数据',

    // Volume Quality
    'volume_ok': 'Volume OK',
    'volume_partial': 'Volume 部分',
    'volume_na': 'Volume N/A',
    'vq_reliable': '可靠',
    'vq_partial': '部分',
    'vq_unavailable': '不可用',
    'vol_quality': '成交量质量',

    // Breakout Quality Card
    'breakout_quality': '突破质量',
    'factor_closes': '确认K线',
    'factor_result': 'Result',
    'factor_closes_missing': '确认K线不足',
    'factor_volume_missing': '成交量未确认',
    'factor_result_missing': '推进力度不足',
    'breakout_all_confirmed': '三因子全部确认',

    // Verdict Tags
    'tag_volume_unconfirmed': '成交量未确认',
    'tag_at_resistance': '接近阻力',
    'tag_at_support': '接近支撑',
    'tag_absorption_risk': '吸收风险',
    'regime_conf': '趋势置信度',

    // Key Zones Card
    'key_zones': '关键区域',
    'resistance': '阻力',
    'support': '支撑',
    'tests': '测试',
    'rej': '拒绝',

    // Playbook
    'invalidation': '失效价位',

    // Behavior Card
    'show_probabilities': '展开概率分布',
    'hide_probabilities': '收起概率分布',

    // Timeline Filters
    'filter_all': '全部',
    'filter_structure': '结构',
    'filter_volume': '成交量',
    'filter_breakout': '突破',

    // Soft Events (new)
    'spring': 'Spring（扫止损反弹）',
    'upthrust': 'Upthrust（假突破回落）',
    'absorption_clue': '吸收信号',
    'zone_rejected': '区域拒绝',
    'zone_accepted': '突破区域',
    'new_swing_high': '新高点',
    'new_swing_low': '新低点',

    // v4 Terminal UI
    'summary': '摘要',
    'provider': '数据源',
    'delay': '延迟',
    'volume_quality_ok': 'OK',
    'volume_quality_partial': '部分',
    'volume_quality_na': 'N/A',

    // Summary Actions
    'action_wait_rvol': '等待 RVOL ≥ 1.8',
    'action_watch_confirm': '关注确认信号',
    'action_breakout_confirmed': '突破已确认',
    'action_caution_fakeout': '注意：近期假突破',
    'action_at_resistance': '阻力位观察拒绝信号',
    'action_at_support': '支撑位观察反弹信号',
    'action_monitor': '监控结构',

    // Breakout States
    'idle': '观望',
    'attempt': '尝试',
    'confirmed': '确认',

    // Bottom Panel Tabs
    'tab_timeline': '时间线',
    'tab_playbook': '交易剧本',
    'tab_evidence': '证据',

    // Evidence Table
    'time': '时间',
    'type': '类型',
    'severity': '强度',
    'note': '说明',
    'event': '事件',
    'low': '低',
    'med': '中',
    'high': '高',

    // Volume Tab
    'effort_result': 'Effort vs Result',
    'current_metrics': '当前指标',
    'rvol': 'RVOL',
    'effort': 'Effort',
    'result': 'Result',
    'quality': '质量',
    'reliable': '可靠',
    'partial': '部分',

    // VSA Quadrants
    'absorption': '吸收',
    'true_push': '真突破',
    'dryup': '量缩',
    'easy_move': '轻松推进',

    // Evidence Types
    'VOLUME_SPIKE': '量能放大',
    'REJECTION': '拒绝信号',
    'SWEEP': '扫盘',
    'ABSORPTION': '吸收',
    'BREAKOUT': '突破',

    // Confidence
    'low_conf': '低置信',

    // Timeline
    'no_significant_events': '无显著事件，持续监控中...',

    // Zones
    'level': '价位',
    'label': '标签',
    'dist': '距离',
    'no_zones': '无区域',

    // Playbook
    'plan_a': '计划 A',
    'plan_b': '计划 B',
    'plan': '计划',
    'direction': '方向',
    'condition': '条件',
    'stop': '止损',
    'no_executable_plans': '无可执行计划',

    // v4 Labels (for detail page)
    'label_regime': '趋势',
    'label_breakout': '突破',
    'label_behavior': '行为',
    'label_zones': '区域',
    'label_tf': '周期',
    'label_confidence': '置信度',
    'label_volume': '成交量',
    'bullish': '看涨',
    'bearish': '看跌',
    'neutral': '中性',
    'fakeout_state': '假突破',

    // 3-Factor Breakout
    'factor_close_x2': '收盘确认 ×2',
    'factor_rvol_threshold': 'RVOL ≥ 1.8',
    'factor_result_threshold': 'Result ≥ 0.6',

    // Zone Types
    'zone_type_r': '阻',
    'zone_type_s': '支',

    // Short timeframe warnings
    'noise_warning': '短周期噪音较高',
    'noise_warning_behavior': '行为推断仅供参考',
    'noise_warning_playbook': '仅用于入场确认',

    // Narrative (LLM)
    'narrative': 'AI 解读',
    'generate_report': '生成报告',
    'quick_update': '快速更新',
    'generating': '生成中...',
    'narrative_action': '行动建议',
    'narrative_why': '依据',
    'narrative_playbook': '策略',
    'narrative_risks': '风险提示',
    'narrative_quality_high': '高置信度',
    'narrative_quality_limited': '数据受限',
    'narrative_not_configured': 'LLM 服务未配置',
    'narrative_error': '生成失败',
    'expand_details': '展开详情',
    'collapse_details': '收起详情',

    // Signal Evaluation
    'tab_signal_eval': '信号评估',
    'signal_evaluation': '信号评估',
    'accuracy_rate': '准确率',
    'total_predictions': '总预测',
    'correct_count': '正确',
    'incorrect_count': '错误',
    'pending_count': '待评估',
    'signal_type_col': '信号类型',
    'direction_col': '方向',
    'prices_col': '价格',
    'status_col': '状态',
    'result_col': '结果',
    'notes_col': '备注',
    'status_pending': '待评估',
    'status_correct': '正确',
    'status_incorrect': '错误',
    'result_target_hit': '达到目标',
    'result_invalidation_hit': '触及止损',
    'result_partial_correct': '部分正确',
    'result_direction_wrong': '方向错误',
    'result_timeout': '超时',
    'no_evaluations': '暂无评估记录',
    'mark_correct': '标记正确',
    'mark_incorrect': '标记错误',
    'record_prediction': '记录预测',
    'up': '上涨',
    'down': '下跌',
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
    'category_stocks': 'US Stocks',
    'category_etfs': 'ETFs',
    'category_crypto': 'Crypto',

    // AI Interpretation
    'ai_interpretation': 'AI Interpretation',
    'evidence_chain': 'Evidence',
    'key_levels': 'Key Levels',
    'scenarios': 'Scenarios',
    'next_candle_focus': 'Next Candle Focus',

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
    'disclaimer_text': 'For educational purposes only. Not financial advice. Trade at your own risk.',

    // Evidence hint
    'click_to_locate': 'Click to locate on chart',

    // New: Professional Terminal UI
    'data_source': 'Data',
    'data_updated': 'Updated',
    'data_delay': 'Delay',
    'chart': 'Chart',
    'zones_key': 'Key',
    'zones_all': 'All',

    // Verdict card
    'verdict_bullish': 'Bullish',
    'verdict_bearish': 'Bearish',
    'verdict_neutral': 'Neutral',
    'action_buy_dip': 'Buy Dip',
    'action_sell_rally': 'Sell Rally',
    'action_wait': 'Wait',
    'action_fade': 'Fade',
    'action_trade_range': 'Trade Range',

    // Confirmation box
    'vol_ratio_label': 'volRatio',
    'vol_ratio_need': 'need',
    'vol_unavailable': 'delayed data',
    'closes_label': 'closes',

    // Timeline soft events
    'zone_tested': 'Zone Tested',
    'zone_approached': 'Approaching Zone',
    'wick_rejection': 'Wick Rejection',
    'volume_notable': 'Notable Volume',
    'volume_low': 'Low Volume',
    'swing_formed': 'New Swing Point',
    'timeline_empty_title': 'No regime change in last 30 bars',
    'timeline_empty_desc': 'Tracking zones & volume...',

    // Timeline badges (user-friendly)
    'badge_regime': 'Trend',
    'badge_break': 'Break',
    'badge_behav': 'Behavior',
    'badge_prob': 'Prob',
    'badge_zone': 'Zones',
    'badge_wick': 'Wick',
    'badge_vol': 'Volume',
    'badge_swing': 'Structure',
    'badge_info': 'System',

    // Timeline event descriptions (user-friendly)
    'timeline_init': 'Analysis started',
    'timeline_zone_update': 'Zones refreshed',
    'timeline_zone_test': 'Testing zone boundary',
    'timeline_breakout_attempt': 'Breakout structure detected',
    'timeline_breakout_confirmed': 'Breakout confirmed',
    'timeline_fakeout': 'Fakeout detected',
    'timeline_regime_change': 'Trend state changed',
    'timeline_behavior_shift': 'Behavior pattern shifted',
    'timeline_volume_spike': 'Volume anomaly',
    'timeline_swing_formed': 'New swing point formed',

    // Playbook trigger & invalidation
    'trigger': 'Trigger',
    'risk': 'Risk',
    'trigger.pullback_support': 'Pullback to support zone + bullish regime',
    'trigger.breakout_resistance': 'Close above resistance with volume ≥1.8x',
    'trigger.rally_resistance': 'Rally into resistance + bearish regime',
    'trigger.breakdown_support': 'Close below support with volume ≥1.8x',
    'trigger.touch_support': 'Touch support zone + bullish candle',
    'trigger.touch_resistance': 'Touch resistance zone + bearish candle',
    'risk.below_support': 'Close below support - 0.5 ATR',
    'risk.back_inside_zone': 'Close back inside zone within 3 bars',
    'risk.above_resistance': 'Close above resistance + 0.5 ATR',
    'risk.range_breakout': 'Break outside range with volume confirmation',
    'risk.trend_continuation': 'Trend continuation failure risk',
    'risk.false_breakout': 'False breakout risk',
    'risk.reversal': 'Trend reversal risk',
    'risk.false_breakdown': 'False breakdown risk',
    'risk.range_break': 'Range breakout risk',

    // Decision Line (Action/Trigger/Risk)
    'decision_action': 'Action',
    'decision_trigger': 'Trigger',
    'decision_risk': 'Risk',
    'decision_wait': 'WAIT',
    'decision_watch': 'WATCH',
    'decision_confirm': 'CONFIRM',
    'decision_avoid': 'AVOID',
    'trigger_fakeout_detected': 'Fakeout detected',
    'trigger_wait_structure_reset': 'Wait for structure reset',
    'trigger_breakout_confirmed': '3-factor breakout confirmed',
    'trigger_low_regime_confidence': 'Low confidence',
    'trigger_need_rvol': 'Need RVOL ≥ 1.8 (now {rvol}×)',
    'trigger_low_confidence': 'Low confidence',
    'trigger_need_2nd_close': 'Need 2nd close for confirmation',
    'trigger_need_2nd_close_level': 'Need 2nd close {direction} {level}',
    'trigger_at_resistance': 'At resistance, watch for rejection',
    'trigger_at_support': 'At support, watch for bounce',
    'trigger_monitor_structure': 'Monitor structure for setup',

    // Event text
    'event.analysis_started': 'Analysis Started',
    'event.regime_changed': 'Regime Changed',
    'event.behavior_shifted': 'Behavior Shifted',
    'event.at_resistance': 'At Resistance',
    'event.at_support': 'At Support',
    'event.uptrend_detected': 'Uptrend Detected',
    'event.downtrend_detected': 'Downtrend Detected',
    'event.range_bound': 'Range Bound',

    // New: Detail Page v2
    'bars': 'Bars',
    'updated': 'Updated',
    'behavior': 'Behavior',
    'tab_volume': 'Volume',
    'tab_effort_result': 'Effort vs Result',
    'effort_vs_result': 'VSA: Effort vs Result',
    'quadrant_absorption': 'Absorption',
    'quadrant_true_push': 'True Push',
    'quadrant_dryup': 'Dry-up',
    'quadrant_easy_move': 'Easy Move',
    'interpretation_absorption': 'Absorption (institutional activity)',
    'interpretation_true_push': 'True push (trend continuation)',
    'no_vsa_data': 'No VSA data',

    // Volume Quality
    'volume_ok': 'Volume OK',
    'volume_partial': 'Volume Partial',
    'volume_na': 'Volume N/A',
    'vq_reliable': 'Reliable',
    'vq_partial': 'Partial',
    'vq_unavailable': 'Unavailable',
    'vol_quality': 'Volume Quality',

    // Breakout Quality Card
    'breakout_quality': 'Breakout Quality',
    'factor_closes': 'Confirm Closes',
    'factor_result': 'Result',
    'factor_closes_missing': 'Closes not confirmed',
    'factor_volume_missing': 'Volume not confirmed',
    'factor_result_missing': 'Result below threshold',
    'breakout_all_confirmed': 'All 3 factors confirmed',

    // Verdict Tags
    'tag_volume_unconfirmed': 'Volume unconfirmed',
    'tag_at_resistance': 'At resistance',
    'tag_at_support': 'At support',
    'tag_absorption_risk': 'Absorption risk',
    'regime_conf': 'Regime Conf',

    // Key Zones Card
    'key_zones': 'Key Zones',
    'resistance': 'Resistance',
    'support': 'Support',
    'tests': 'Tests',
    'rej': 'Rej',

    // Playbook
    'invalidation': 'Invalidation',

    // Behavior Card
    'show_probabilities': 'Show probabilities',
    'hide_probabilities': 'Hide probabilities',

    // Timeline Filters
    'filter_all': 'All',
    'filter_structure': 'Structure',
    'filter_volume': 'Volume',
    'filter_breakout': 'Breakout',

    // Soft Events (new)
    'spring': 'Spring (sweep & reclaim)',
    'upthrust': 'Upthrust (fake breakout)',
    'absorption_clue': 'Absorption clue',
    'zone_rejected': 'Zone rejected',
    'zone_accepted': 'Zone accepted',
    'new_swing_high': 'New swing high',
    'new_swing_low': 'New swing low',

    // v4 Terminal UI
    'summary': 'Summary',
    'provider': 'Provider',
    'delay': 'Delay',
    'volume_quality_ok': 'OK',
    'volume_quality_partial': 'Partial',
    'volume_quality_na': 'N/A',

    // Summary Actions
    'action_wait_rvol': 'Wait for RVOL ≥ 1.8',
    'action_watch_confirm': 'Watch for confirmation',
    'action_breakout_confirmed': 'Breakout confirmed',
    'action_caution_fakeout': 'Caution: Recent fakeout',
    'action_at_resistance': 'At resistance, watch for rejection',
    'action_at_support': 'At support, watch for bounce',
    'action_monitor': 'Monitor structure',

    // Breakout States
    'idle': 'Idle',
    'attempt': 'Attempt',
    'confirmed': 'Confirmed',

    // Bottom Panel Tabs
    'tab_timeline': 'Timeline',
    'tab_playbook': 'Playbook',
    'tab_evidence': 'Evidence',

    // Evidence Table
    'time': 'Time',
    'type': 'Type',
    'severity': 'Severity',
    'note': 'Note',
    'event': 'Event',
    'low': 'Low',
    'med': 'Med',
    'high': 'High',

    // Volume Tab
    'effort_result': 'Effort vs Result',
    'current_metrics': 'Current Metrics',
    'rvol': 'RVOL',
    'effort': 'Effort',
    'result': 'Result',
    'quality': 'Quality',
    'reliable': 'Reliable',
    'partial': 'Partial',

    // VSA Quadrants
    'absorption': 'Absorption',
    'true_push': 'True Push',
    'dryup': 'Dry-up',
    'easy_move': 'Easy Move',

    // Evidence Types
    'VOLUME_SPIKE': 'Volume Spike',
    'REJECTION': 'Rejection',
    'SWEEP': 'Sweep',
    'ABSORPTION': 'Absorption',
    'BREAKOUT': 'Breakout',

    // Confidence
    'low_conf': 'low conf',

    // Timeline
    'no_significant_events': 'No significant events. Monitoring...',

    // Zones
    'level': 'Level',
    'label': 'Label',
    'dist': 'Dist',
    'no_zones': 'No zones',

    // Playbook
    'plan_a': 'Plan A',
    'plan_b': 'Plan B',
    'plan': 'Plan',
    'direction': 'Dir',
    'condition': 'Condition',
    'stop': 'Stop',
    'no_executable_plans': 'No executable plans',

    // v4 Labels (for detail page)
    'label_regime': 'Regime',
    'label_breakout': 'Breakout',
    'label_behavior': 'Behavior',
    'label_zones': 'Zones',
    'label_tf': 'TF',
    'label_confidence': 'confidence',
    'label_volume': 'Volume',
    'bullish': 'Bullish',
    'bearish': 'Bearish',
    'neutral': 'Neutral',
    'fakeout_state': 'Fakeout',

    // 3-Factor Breakout
    'factor_close_x2': 'Close ×2',
    'factor_rvol_threshold': 'RVOL ≥ 1.8',
    'factor_result_threshold': 'Result ≥ 0.6',

    // Zone Types
    'zone_type_r': 'R',
    'zone_type_s': 'S',

    // Short timeframe warnings
    'noise_warning': 'Short TF high noise',
    'noise_warning_behavior': 'Behavior inference for reference only',
    'noise_warning_playbook': 'Entry confirmation only',

    // Narrative (LLM)
    'narrative': 'AI Analysis',
    'generate_report': 'Full Report',
    'quick_update': 'Quick Update',
    'generating': 'Generating...',
    'narrative_action': 'Action',
    'narrative_why': 'Why',
    'narrative_playbook': 'Playbook',
    'narrative_risks': 'Risks',
    'narrative_quality_high': 'High Confidence',
    'narrative_quality_limited': 'Limited Data',
    'narrative_not_configured': 'LLM service not configured',
    'narrative_error': 'Generation failed',
    'expand_details': 'Expand details',
    'collapse_details': 'Collapse details',

    // Signal Evaluation
    'tab_signal_eval': 'Evaluation',
    'signal_evaluation': 'Signal Evaluation',
    'accuracy_rate': 'Accuracy',
    'total_predictions': 'Total',
    'correct_count': 'Correct',
    'incorrect_count': 'Incorrect',
    'pending_count': 'Pending',
    'signal_type_col': 'Signal',
    'direction_col': 'Dir',
    'prices_col': 'Prices',
    'status_col': 'Status',
    'result_col': 'Result',
    'notes_col': 'Notes',
    'status_pending': 'Pending',
    'status_correct': 'Correct',
    'status_incorrect': 'Incorrect',
    'result_target_hit': 'Target Hit',
    'result_invalidation_hit': 'Stop Hit',
    'result_partial_correct': 'Partial',
    'result_direction_wrong': 'Wrong Dir',
    'result_timeout': 'Timeout',
    'no_evaluations': 'No evaluations yet',
    'mark_correct': 'Mark Correct',
    'mark_incorrect': 'Mark Incorrect',
    'record_prediction': 'Record Prediction',
    'up': 'Up',
    'down': 'Down',
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
