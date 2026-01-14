"""
KLineLens 核心引擎包

纯 Python 实现的市场结构分析库。
设计原则: 确定性 - 相同的输入 K 线数据产生相同的分析报告。

核心功能（将在 Milestone 2-3 实现）:
- analyze_market: 完整市场分析入口
- calculate_features: 技术指标计算
- find_swing_points: 波段高低点识别
- classify_regime: 市场状态分类（趋势/震荡）
- cluster_zones: 支撑阻力区聚类
- infer_behavior: 行为概率推断
- TimelineManager: 时间线事件管理
- generate_playbook: 条件剧本生成

版本: 0.1.0
"""

__version__ = "0.1.0"

# 将在实现后导出主要函数:
# from .analyze import analyze_market
# from .features import calculate_features
# from .structure import find_swing_points, classify_regime, cluster_zones
# from .behavior import infer_behavior
# from .timeline import TimelineManager
# from .playbook import generate_playbook
