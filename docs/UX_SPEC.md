# KLineLens MVP - UX Spec（极简专业页面规格）

## 1. 设计原则
- **极简**：无边框卡片、灰色系配色、减少视觉干扰
- **专业**：数据密度高、信息层级清晰
- **少层级**：三页（Dashboard / Detail / Settings）
- **进入即用**：无登录
- **双语支持**：中文/English，Settings 切换

---

## 2. 路由
- `/` Dashboard
- `/t/{ticker}` Detail
- `/settings` Settings

---

## 3. 顶部导航（全站一致）
- 左：Logo（点击回 `/`）
- 右：Settings 图标（跳转 `/settings`）

---

## 4. Dashboard（/）
### 4.1 Layout
- 页面居中：大搜索框 + "Analyze" 按钮
- 纯黑白设计（Logo 黑色，副标题灰色）
- 输入框下方：最近访问的股票（localStorage，最多 6 个）
- Enter 或按钮触发搜索

### 4.2 交互
- 输入：ticker（大小写不敏感）
- 模糊搜索：输入时显示建议列表
- 校验：空/非法格式提示
- 成功：跳转 `/t/{ticker}` 并记录到最近访问

---

## 5. Detail（/t/{ticker}）

### 5.1 Layout（左图右面板）
- Left 70%：Chart + Volume
- Right 30%：Analysis Panel（无边框卡片堆叠）

### 5.2 Header
- Ticker 名称（大字）
- 当前价格 + 涨跌幅（灰色，不用红绿）
- 量比标签（灰边框）
- 最后更新时间

> **注意**: 旧版的"趋势/突破/行为"摘要条已移除，相关信息整合到右侧面板的各个卡片中。

### 5.3 工具条
- Timeframe 切换：1分钟 / 5分钟 / 日线（圆角按钮）
- 刷新按钮
- 最后更新时间

### 5.4 Chart 区
- K 线图（OHLC）
- Volume 柱状图（占底部 20%）
- Volume MA 均线（橙色，30 周期）
- Support/Resistance Zone 线（虚线）
- 高亮标记（Evidence 点击触发）
- **EH Levels（仅 1m/5m 周期）**：
  - YC: 橙色实线 (Yesterday's Close - 磁吸位)
  - PMH/PML: 紫色虚线 (Premarket High/Low)
  - AHH/AHL: 靛蓝点线 (Afterhours High/Low)

### 5.5 Analysis Panel（卡片顺序固定，无边框）

**0) 盘前上下文 (Premarket Context)** — 仅 1m/5m 周期显示
- 位置：Summary 上方，作为首个 section
- 显示内容（单行布局）：
  - 左侧：形态（大字）- trend_continuation / gap_and_go / gap_fill_bias / range_day_setup
  - 右侧：偏向 + 置信度 + Gap
- 不显示 YC/YH/YL 等价位（这些在 Key Zones 中显示）
- 条件：仅当 `ehContext` 存在且 `timeframe` 为 1m/5m 时显示

**1) 市场状态 (Market State)**
- 状态名称 + 置信度百分比
- 置信度进度条（灰色）

**2) 突破状态 (Breakout Status)**
- 状态：观望中 / 尝试突破 / 突破确认 / 假突破
- 量比：X.XXx (≥/< 1.8)
- 确认K线：2/2 / 1/2 / -

**3) 信号 (Signals)**
- 最多 5 条
- 格式：信号名称 · $价格 · 时间
- 无滚动条

**4) 支撑证据 (Evidence)**
- 最多 5 条
- 显示时间戳（发生时间）
- 可点击定位到图表对应 K 线
- ● 图标表示可定位
- 点击高亮显示
- 每日缓存：进入自动加载当天数据

**5) 行为推断 (Behavior Inference)**
- 5 类行为概率条
- 最高概率加粗显示

**6) 交易剧本 (Playbook)** — 表格化显示
- Plan A + Plan B 并排，一行表格格式
- 列：方向 | 入场 | 目标 | 止损 | R:R | 条件 | 风险
- 方向颜色：LONG 绿色 / SHORT 红色
- 可切换到"信号评估"Tab

**7) 信号评估 (Signal Evaluation)** — 与 Playbook 切换
- 表格显示历史预测记录
- 列：时间 | 信号类型 | 方向 | 价格 | 状态 | 结果 | 原因
- 状态标签：待评估(灰) / 正确(绿) / 错误(红)
- 顶部显示准确率统计：总数 / 正确 / 错误 / 准确率
- 支持手动标记评估结果

**8) 时间线 (Timeline)**
- 最多 6 条，显示在右侧面板
- 格式：● 事件名称 + 时间
- 灰色圆点（不用彩色）
- 每日缓存：进入自动加载当天数据

### 5.6 错误态
- 无数据："暂无数据"
- 限流："请稍后刷新"
- ticker 无效：提示 + 返回按钮

---

## 6. Settings（/settings）

### 6.1 Layout
- 居中窄版布局（max-width: 560px）
- 分组：语言 / 关于 / 免责声明
- 响应式字体（clamp）

### 6.2 语言设置
- 按钮式切换：中文 / English
- 选中状态：黑底白字
- 切换后立即生效
- localStorage 持久化

### 6.3 关于
- 应用名称 + 描述 + 版本号
- 灰色背景卡片

### 6.4 免责声明
- 简洁文本，边框卡片
- 中文："本工具仅用于技术分析学习，不构成任何投资建议。市场有风险，投资需谨慎。"
- 英文："For educational purposes only. Not financial advice. Trade at your own risk."

### 6.5 默认值
- 初次访问默认：中文

---

## 7. 视觉规范

### 7.1 配色
- 背景：#f8f9fa（浅灰）
- 文字：#1a1a1a（黑）/ #666（次要）/ #999（辅助）
- 边框：#eaeaea
- 强调：#26a69a（仅用于 K 线涨色和关键操作按钮）

### 7.2 卡片样式
- 无背景色（透明）
- 无边框
- 内容分隔用细线或间距

### 7.3 字体
- 系统默认：-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto
- 标题：1rem - 2rem
- 正文：0.875rem
- 辅助：0.75rem

---

## 8. 响应式设计

### 8.1 流体排版（Fluid Typography）
- 使用 CSS `clamp()` 实现字体大小随视口缩放
- 字体层级：
  - tiny: `clamp(0.5625rem, 0.5rem + 0.15vw, 0.6875rem)` - 状态栏、标签
  - small: `clamp(0.625rem, 0.55rem + 0.2vw, 0.8125rem)` - 次要文本
  - body: `clamp(0.6875rem, 0.6rem + 0.2vw, 0.875rem)` - 主要文本
  - medium: `clamp(0.75rem, 0.65rem + 0.25vw, 0.9375rem)` - 区块内容
  - large: `clamp(0.875rem, 0.75rem + 0.3vw, 1.125rem)` - 强调文本
  - heading: `clamp(1.375rem, 1.1rem + 0.6vw, 1.875rem)` - 标题

### 8.2 动态图表高度
- 基于视口高度：~45% of vh
- 最小：280px
- 最大：550px
- 公式：`Math.min(550, Math.max(280, vh * 0.45))`

### 8.3 智能可视范围
- 1m 周期：120 bars（约 2 小时）- 执行级别
- 5m 周期：78 bars（约 1 交易日）- 结构级别
- 1d 周期：20 bars（约 1 个月）- 趋势级别

### 8.4 断点
- 桌面端优先（>= 1024px）
- 全屏模式：字体自动放大填充屏幕
- 移动端（未来）：图表全宽，面板下移
