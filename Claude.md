# CLAUDE.md — KLineLens Collaboration Guide

This file tells Claude (and any collaborator) how to work in this repo.

---

## 0. Ground Rules (Must Follow)

1. **Explain before coding**: Before starting any task, explain what will be done, what files will be created/modified, and what the expected outcome is.
2. **Ask for requirements first**: If a task requires API keys, external services, deployment setup, or user decisions, ask the user BEFORE writing any code.
3. **Docs-first**: Implementation must match docs in `docs/`. Read docs before coding.
4. **Update docs before significant changes**: New algorithm/signal/behavior → update docs first.
5. **No silent breaking changes**: If schema changes, update `docs/API.md` and add migration notes.
6. **MVP is English-only**: No i18n complexity for MVP. Multi-language is post-MVP.
7. **Deterministic engine**: `packages/core/` must be pure and testable. Same input → same output.

---

## 1. Documentation Index (Read Order)

Before coding, read these in order:

| Order | Document | Purpose |
|-------|----------|---------|
| 1 | `MASTER_SPEC.md` | Project constitution, scope, principles |
| 2 | `docs/PRD.md` | Product requirements, user scenarios |
| 3 | `docs/UX_SPEC.md` | Page layout, UI rules |
| 4 | `docs/API.md` | REST endpoints, request/response schema |
| 5 | `docs/ENGINE_SPEC.md` | Algorithm logic, formulas, parameters |
| 6 | `docs/ARCHITECTURE.md` | System architecture, data flow |
| 7 | `docs/PROVIDER.md` | Data provider integration |
| 8 | `docs/CONFIG.md` | Environment variables |
| 9 | `docs/PLAN.md` | Development milestones |
| 10 | `docs/TODO.md` | Current task tracking |
| 11 | `docs/COMMIT_LOG.md` | Detailed commit history |

If any ambiguity exists, **update the Docs** before implementing.

---

## 2. Development Workflow

### Step A: Explain the Task First
Before writing any code, always:
1. **Describe what this step does** - What is the goal? What problem does it solve?
2. **List files to be created/modified** - So user knows what to expect
3. **Identify prerequisites** - API keys, environment setup, dependencies
4. **Ask user confirmation** - If any setup or decision is needed, ask first

Example:
```
"Next step: Initialize the FastAPI backend.

 I will create:
 - apps/api/src/main.py (FastAPI app entry)
 - apps/api/requirements.txt (dependencies)

 Prerequisites needed:
 - Python 3.11+ installed
 - No API keys required for this step

 Ready to proceed?"
```

### Step B: Pick a Milestone
Use `docs/PLAN.md` milestones. Implement in order:
1. Core engine functions first
2. Then API endpoints
3. Then web UI

### Step C: Keep Engine Deterministic
- `packages/core/` should be pure Python, no I/O
- Same input bars → same output report
- Do not mix provider/network logic into core

### Step D: Follow Schema
- API must return `AnalysisReport` as documented in `docs/API.md`
- All fields required unless marked optional

### Step E: Update TODO
- Mark tasks in `docs/TODO.md` as you work
- Add new tasks if scope changes

### Step F: Test Before Next Milestone (Required)
**每个 Milestone 完成后，必须先测试再继续下一个 Milestone！**

测试流程：
1. **启动服务** - 确保服务能正常运行
2. **手动测试** - 用 curl/浏览器验证核心功能
3. **自动化测试** - 运行 pytest 确保无回归
4. **记录问题** - 发现的 bug 记录到 `docs/BUGS.md`
5. **修复后再继续** - 所有测试通过后才能进入下一个 Milestone

---

## 3. Documentation Update Rules

### 3.1 When Adding Algorithm/Signal
- Update `docs/ENGINE_SPEC.md`:
  - Feature definitions and formulas
  - Parameters and defaults
  - Evidence rules

### 3.2 When Changing Architecture
- Update `docs/ARCHITECTURE.md`:
  - Data flow changes
  - New services/components
  - Caching/storage changes

### 3.3 When Changing API
- Update `docs/API.md`:
  - Endpoint params
  - Response fields
  - Error codes
- If breaking: add "Breaking Changes" section

### 3.4 When Changing UX
- Update `docs/UX_SPEC.md`:
  - Page layout
  - Card order
  - Error states

---

## 4. Task Tracking

### 4.1 TODO List
- File: `docs/TODO.md`
- Update status as you work
- Add new tasks when discovered

### 4.2 Bug Log
- File: `docs/BUGS.md`
- Format: ID, Date, Symptom, Root cause, Fix, Test added

### 4.3 Changelog
- File: `docs/CHANGELOG.md`
- Update for every significant change
- Follow Keep-a-Changelog format

### 4.4 Commit Log
- File: `docs/COMMIT_LOG.md`
- Record EVERY git commit with detailed context
- Format for each commit:
  ```
  ## [commit_hash] - YYYY-MM-DD
  **Message:** `commit message`
  **Milestone:** X - Name
  **Changes:**
  | Type | File | Description |
  | Add/Modify/Delete | path | what changed |
  **Result:** Summary of outcome
  ```
- Update IMMEDIATELY after each `git push`

---

## 5. Code Quality Rules

### 5.1 Chinese Comments (Required)
All code files MUST include:
- **File header comment**: Chinese description of what this file does
- **Function/class comments**: Chinese explanation of purpose
- **Complex logic comments**: Chinese inline comments for non-obvious code

Example for Python:
```python
"""
缓存管理模块

提供内存缓存功能，支持 TTL（生存时间）过期机制。
用于缓存 K 线数据，减少对数据提供商的请求频率。
"""

class MemoryCache:
    """
    内存缓存类

    使用字典存储缓存数据，支持自动过期清理。
    """

    def get(self, key: str):
        """获取缓存值，如果已过期则返回 None"""
        pass
```

Example for TypeScript:
```typescript
/**
 * 详情页面组件
 *
 * 显示股票的 K 线图和分析面板，包括：
 * - 市场状态卡片
 * - 行为概率卡片
 * - 证据卡片
 * - 时间线卡片
 * - 交易剧本卡片
 */
export default function TickerDetail() {
  // ...
}
```

### 5.2 Python (Core + API)
- Type hints required
- Docstrings for public functions (in Chinese)
- Unit tests for core logic

### 5.3 TypeScript (Web)
- TypeScript strict mode
- Types for API responses
- Component props typed
- JSDoc comments in Chinese

### 5.4 Testing (Required)

**测试是每个 Milestone 的必须步骤，不可跳过！**

#### 5.4.1 API 测试

启动命令:
```bash
cd apps/api
pip install -r requirements.txt  # 首次运行
uvicorn src.main:app --reload --port 8000
```

手动测试检查点:
```bash
# 健康检查
curl http://localhost:8000/

# 获取 K 线数据 - 正常情况
curl "http://localhost:8000/v1/bars?ticker=TSLA&tf=1m"

# 错误处理 - 无效 ticker
curl "http://localhost:8000/v1/bars?ticker=INVALIDXYZ&tf=1m"

# 错误处理 - 无效 timeframe
curl "http://localhost:8000/v1/bars?ticker=TSLA&tf=invalid"
```

预期结果:
| 测试 | 预期状态码 | 预期响应 |
|------|-----------|---------|
| 健康检查 | 200 | `{"status": "ok", ...}` |
| 正常获取 | 200 | 包含 bars 数组 |
| 无效 ticker | 404 | `{"code": "NO_DATA", ...}` |
| 无效 timeframe | 400 | `{"code": "TIMEFRAME_INVALID", ...}` |

#### 5.4.2 自动化测试

```bash
# API 测试
cd apps/api
pytest tests/ -v

# Core 测试
cd packages/core
pytest tests/ -v
```

#### 5.4.3 测试文件命名规范

- `tests/test_*.py` - 测试文件
- `test_<module>_<function>.py` - 具体测试
- 每个公开函数至少一个测试用例

#### 5.4.4 Milestone 验收标准

Milestone 验收前必须满足:
- [ ] 所有手动测试通过
- [ ] 所有自动化测试通过
- [ ] 无 P0/P1 级别 bug
- [ ] 文档已更新

---

## 6. What NOT to Do

- Do not invent providers or claim "live data" works without implementation
- Do not add features outside MVP scope without updating PRD
- Do not output final trading advice; keep playbooks conditional
- Do not commit secrets or API keys
- Do not skip docs updates for significant changes

---

## 7. Quick Start

```bash
# Read docs first
cat MASTER_SPEC.md
cat docs/TODO.md

# Check current milestone
# Implement tasks in order
# Update TODO as you go
# Update docs if schema changes
```
