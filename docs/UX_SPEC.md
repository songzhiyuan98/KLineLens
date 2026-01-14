# KLineLens MVP - UX Spec（极简专业页面规格）

## 1. 设计原则
- 极简、专业、少层级：三页（Dashboard / Detail / Settings）
- 进入即用：无登录
- 信息结构稳定：右侧面板固定卡片顺序
- 语言手动选择：Settings 控制全站

---

## 2. 路由
- `/` Dashboard
- `/t/{ticker}` Detail
- `/settings` Settings

---

## 3. 顶部导航（全站一致）
- 左：Logo（点击回 `/`）
- 中：Mini Search（可选，MVP可只放在 Dashboard）
- 右：Settings 图标/按钮（跳转 `/settings`）

---

## 4. Dashboard（/）
### 4.1 Layout
- 页面居中：一个“大搜索框”
- 输入框下方（可选）：最近搜索 ticker（本地存储）
- Enter 或按钮触发搜索

### 4.2 交互
- 输入：ticker（大小写不敏感）
- 校验：空/非法格式提示
- 成功：跳转 `/t/{ticker}`

---

## 5. Detail（/t/{ticker}）
### 5.1 Layout（推荐：左图右面板）
- Left 70%：Chart
- Right 30%：Analysis Panel（卡片堆叠）

### 5.2 Chart 区（必需）
- K线图（OHLC）
- 成交量柱（Volume）
- Overlays：
  - Support/Resistance Zones（矩形带）
  - Markers：breakout attempt / confirmed / fakeout（点或小旗标）

### 5.3 工具条（Chart 上方）
- Ticker（只读）
- Timeframe 切换：
  - 1m（默认）
  - 1d
  - （可选）5m
- Last Updated 时间
- Refresh 状态（loading）

### 5.4 Analysis Panel（卡片顺序固定）
1) Market State Card  
   - Regime + confidence  
   - Key zones（Top 2 支撑 + Top 2 阻力）

2) Behavior Probabilities Card  
   - 5 类概率列表（条形/百分比）
   - Dominant narrative（最高概率）

3) Evidence Card（最多 3 条）  
   - 每条：时间 + 数值 + 短说明（模板）

4) Timeline Card（最近 10 条）  
   - ts + event 文案 + delta

5) Playbook Card（Plan A / Plan B）  
   - If（条件）
   - Target（目标）
   - Invalidation（失效）
   - Risk（风险提示）

### 5.5 错误态
- 无数据：显示 “No data / 无数据”
- provider 限流：显示 “Rate limited，请稍后刷新”
- ticker 无效：提示并提供返回 Dashboard 的按钮

---

## 6. Settings（/settings）
### 6.1 内容
- Language：
  - 中文
  - English
- 保存到 localStorage/cookie
- 提示：切换后立即生效

### 6.2 默认值
- 初次访问默认：中文
