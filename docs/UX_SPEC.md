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
- 页面居中：大搜索框 + 副标题
- 输入框下方：热门股票快捷入口
- Enter 或按钮触发搜索

### 4.2 交互
- 输入：ticker（大小写不敏感）
- 校验：空/非法格式提示
- 成功：跳转 `/t/{ticker}`

---

## 5. Detail（/t/{ticker}）

### 5.1 Layout（左图右面板）
- Left 70%：Chart + Volume
- Right 30%：Analysis Panel（无边框卡片堆叠）

### 5.2 Header
- Ticker 名称（大字）
- 当前价格 + 涨跌幅（灰色，不用红绿）
- 市场状态标签（灰边框）
- 量比标签（灰边框）

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

### 5.5 Analysis Panel（卡片顺序固定，无边框）

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
- 可点击定位到图表对应 K 线
- ● 图标表示可定位
- 点击高亮显示

**5) 行为推断 (Behavior Inference)**
- 5 类行为概率条
- 最高概率加粗显示

**6) 交易剧本 (Playbook)**
- Plan A（推荐）+ Plan B（备选）
- 每个：条件 / 入场 / 目标 / 止损 / 盈亏比

**7) 时间线 (Timeline)**
- 最多 5 条
- 格式：● 事件名称 + 时间
- 灰色圆点（不用彩色）

### 5.6 错误态
- 无数据："暂无数据"
- 限流："请稍后刷新"
- ticker 无效：提示 + 返回按钮

---

## 6. Settings（/settings）

### 6.1 Layout
- 居中窄版布局
- 分组：通用 / 关于

### 6.2 通用设置
- 语言切换：中文 / English
- 切换后立即生效
- localStorage 持久化

### 6.3 关于
- 应用名称 + 版本号
- 免责声明

### 6.4 默认值
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

## 8. 响应式（MVP 可选）
- 优先支持桌面端（>= 1024px）
- 移动端：简化布局，图表全宽，面板下移
