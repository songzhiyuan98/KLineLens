# KLineLens MVP - UX Specification

## 1. Design Principles
- **Minimal**: Borderless cards, gray color scheme, reduced visual noise
- **Professional**: High data density, clear information hierarchy
- **Few Layers**: Three pages (Dashboard / Detail / Settings)
- **Instant Use**: No login required
- **Bilingual Support**: Chinese/English, switchable in Settings

---

## 2. Routes
- `/` Dashboard
- `/t/{ticker}` Detail
- `/settings` Settings

---

## 3. Top Navigation (Site-wide Consistent)
- Left: Logo (click to go to `/`)
- Right: Settings icon (navigate to `/settings`)

---

## 4. Dashboard (/)

### 4.1 Layout
- Page centered: Large search box + "Analyze" button
- Pure black and white design (Logo black, subtitle gray)
- Below input: Recently visited stocks (localStorage, max 6)
- Enter key or button triggers search

### 4.2 Interactions
- Input: ticker (case-insensitive)
- Fuzzy search: Show suggestion list while typing
- Validation: Empty/invalid format shows prompt
- Success: Navigate to `/t/{ticker}` and record to recent visits

---

## 5. Detail (/t/{ticker})

### 5.1 Layout (Left Chart, Right Panel)
- Left 70%: Chart + Volume
- Right 30%: Analysis Panel (borderless stacked cards)

### 5.2 Header
- Ticker name (large font)
- Current price + change percentage (gray, no red/green)
- Volume ratio badge (gray border)
- Last update time

> **Note**: The old "Trend/Breakout/Behavior" summary bar has been removed, related info is now integrated into the right panel cards.

### 5.3 Toolbar
- Timeframe toggle: 1 Minute / 5 Minute / Daily (rounded buttons)
- Refresh button
- Last update time

### 5.4 Chart Area
- K-line chart (OHLC)
- Volume bar chart (occupies bottom 20%)
- Volume MA line (orange, 30 periods)
- Support/Resistance Zone lines (dashed)
- Highlight markers (triggered by Evidence click)
- **EH Levels (1m/5m timeframes only)**:
  - YC: Orange solid line (Yesterday's Close - magnet level)
  - PMH/PML: Purple dashed line (Premarket High/Low)
  - AHH/AHL: Indigo dotted line (Afterhours High/Low)

### 5.5 Analysis Panel (Fixed Card Order, Borderless)

**0) Premarket Context** — Only shown for 1m/5m timeframes
- Position: Above Summary, as first section
- Display content (single-line layout):
  - Left: Regime (large font) - trend_continuation / gap_and_go / gap_fill_bias / range_day_setup
  - Right: Bias + Confidence + Gap
- Does not display YC/YH/YL prices (these are shown in Key Zones)
- Condition: Only show when `ehContext` exists and `timeframe` is 1m/5m

**1) Market State**
- State name + Confidence percentage
- Confidence progress bar (gray)

**2) Breakout Status**
- State: Watching / Breakout Attempt / Breakout Confirmed / Fakeout
- Volume Ratio: X.XXx (≥/< 1.8)
- Confirmation Candles: 2/2 / 1/2 / -

**3) Signals**
- Max 5 items
- Format: Signal name · $Price · Time
- No scrollbar

**4) Supporting Evidence**
- Max 5 items
- Shows timestamp (occurrence time)
- Clickable to locate corresponding K-line on chart
- ● icon indicates locatable
- Click to highlight
- Daily cache: Auto-loads today's data on entry

**5) Behavior Inference**
- 5 behavior probability bars
- Highest probability shown in bold

**6) Trading Playbook** — Table display
- Plan A + Plan B side by side, table row format
- Columns: Direction | Entry | Target | Stop | R:R | Condition | Risk
- Direction colors: LONG green / SHORT red
- Can toggle to "Signal Evaluation" Tab

**7) Signal Evaluation** — Toggle with Playbook
- Table showing historical prediction records
- Columns: Time | Signal Type | Direction | Price | Status | Result | Reason
- Status labels: Pending (gray) / Correct (green) / Wrong (red)
- Top shows accuracy stats: Total / Correct / Wrong / Accuracy Rate
- Supports manual evaluation result marking

**8) Timeline**
- Max 6 items, displayed in right panel
- Format: ● Event name + Time
- Gray dots (no colors)
- Daily cache: Auto-loads today's data on entry

### 5.6 Error States
- No data: "No data available"
- Rate limited: "Please refresh later"
- Invalid ticker: Prompt + Back button

---

## 6. Settings (/settings)

### 6.1 Layout
- Centered narrow layout (max-width: 560px)
- Grouped: Language / About / Disclaimer
- Responsive fonts (clamp)

### 6.2 Language Settings
- Button-style toggle: Chinese / English
- Selected state: Black background, white text
- Takes effect immediately on switch
- localStorage persistence

### 6.3 About
- App name + Description + Version number
- Gray background card

### 6.4 Disclaimer
- Concise text, bordered card
- Chinese: "This tool is for technical analysis learning only, does not constitute any investment advice. Markets carry risk, invest with caution."
- English: "For educational purposes only. Not financial advice. Trade at your own risk."

### 6.5 Defaults
- First visit defaults to: Browser language or English

---

## 7. Visual Specifications

### 7.1 Colors
- Background: #f8f9fa (light gray)
- Text: #1a1a1a (black) / #666 (secondary) / #999 (tertiary)
- Border: #eaeaea
- Accent: #26a69a (only used for K-line up color and key action buttons)

### 7.2 Card Style
- No background color (transparent)
- No border
- Content separated by thin lines or spacing

### 7.3 Fonts
- System default: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto
- Headings: 1rem - 2rem
- Body: 0.875rem
- Secondary: 0.75rem

---

## 8. Responsive Design

### 8.1 Fluid Typography
- Use CSS `clamp()` for viewport-scaling font sizes
- Font hierarchy:
  - tiny: `clamp(0.5625rem, 0.5rem + 0.15vw, 0.6875rem)` - status bar, labels
  - small: `clamp(0.625rem, 0.55rem + 0.2vw, 0.8125rem)` - secondary text
  - body: `clamp(0.6875rem, 0.6rem + 0.2vw, 0.875rem)` - main text
  - medium: `clamp(0.75rem, 0.65rem + 0.25vw, 0.9375rem)` - block content
  - large: `clamp(0.875rem, 0.75rem + 0.3vw, 1.125rem)` - emphasized text
  - heading: `clamp(1.375rem, 1.1rem + 0.6vw, 1.875rem)` - titles

### 8.2 Dynamic Chart Height
- Based on viewport height: ~45% of vh
- Minimum: 280px
- Maximum: 550px
- Formula: `Math.min(550, Math.max(280, vh * 0.45))`

### 8.3 Smart Visible Range
- 1m timeframe: 120 bars (~2 hours) - execution level
- 5m timeframe: 78 bars (~1 trading day) - structure level
- 1d timeframe: 20 bars (~1 month) - trend level

### 8.4 Breakpoints
- Desktop-first (>= 1024px)
- Fullscreen mode: Fonts auto-scale to fill screen
- Mobile (future): Chart full-width, panel moves below
