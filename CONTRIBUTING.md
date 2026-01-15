# Contributing to KLineLens

Thank you for your interest in contributing to KLineLens! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Adding a Data Provider](#adding-a-data-provider)

---

## Code of Conduct

Be respectful, inclusive, and professional. We're all here to build something useful for traders.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (recommended)
- Git

### Fork and Clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/KLineLens.git
cd KLineLens
git remote add upstream https://github.com/songzhiyuan98/KLineLens.git
```

---

## Development Setup

### Option 1: Docker (Recommended)

```bash
cp .env.example .env
docker compose up --build
```

### Option 2: Local Development

```bash
# Backend
cd apps/api
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Frontend (new terminal)
cd apps/web
npm install
npm run dev
```

### Running Tests

```bash
# Core engine tests
cd packages/core && python -m pytest tests/ -v

# API tests
cd apps/api && python -m pytest tests/ -v
```

---

## How to Contribute

### 1. Check Existing Issues

Before starting work, check if there's an existing issue:
- [Open Issues](https://github.com/songzhiyuan98/KLineLens/issues)
- [TODO List](docs/TODO.md)

### 2. Types of Contributions

| Type | Description |
|------|-------------|
| **Bug Fixes** | Fix bugs, improve error handling |
| **Features** | Add new functionality |
| **Providers** | Add new data providers |
| **Documentation** | Improve docs, add examples |
| **Tests** | Add test coverage |
| **UI/UX** | Improve user interface |

### 3. Create an Issue First

For significant changes, create an issue to discuss before coding:
- Describe the problem or feature
- Explain your proposed solution
- Wait for feedback

---

## Pull Request Process

### 1. Branch Naming

```
feature/short-description
fix/issue-number-description
docs/what-you-documented
```

### 2. Commit Messages

Follow conventional commits:

```
feat: add polygon provider support
fix: resolve price line duplication on timeframe switch
docs: update provider integration guide
refactor: simplify breakout state machine
test: add zone clustering edge cases
```

### 3. Before Submitting

- [ ] Code passes all tests
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated
- [ ] No console.log or print statements left
- [ ] Code follows existing style

### 4. PR Template

```markdown
## Summary
Brief description of changes.

## Type
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring

## Testing
How did you test this?

## Screenshots
(if UI changes)
```

---

## Coding Standards

### Python (Backend)

```python
# Use type hints
def calculate_atr(bars: List[Bar], period: int = 14) -> float:
    ...

# Docstrings for public functions
def analyze_market(bars: List[Bar], params: AnalysisParams) -> AnalysisReport:
    """
    Analyze market structure from OHLCV bars.

    Args:
        bars: List of OHLCV bars
        params: Analysis parameters

    Returns:
        Complete analysis report
    """
    ...
```

### TypeScript (Frontend)

```typescript
// Use explicit types
interface ChartProps {
  bars: Bar[];
  zones: Zone[];
  height?: number;
}

// Functional components
export default function Chart({ bars, zones, height = 400 }: ChartProps) {
  ...
}
```

### General Rules

1. **No magic numbers** - Use constants with descriptive names
2. **Keep functions small** - Single responsibility
3. **Handle errors** - Always handle edge cases
4. **Write tests** - For new features and bug fixes

---

## Adding a Data Provider

We welcome new data providers! Here's how:

### 1. Create Provider File

```python
# apps/api/src/providers/your_provider.py

from .base import MarketDataProvider, Bar

class YourProvider(MarketDataProvider):
    """Your data provider implementation."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key

    async def get_bars(
        self,
        ticker: str,
        timeframe: str,
        limit: int = 500
    ) -> List[Bar]:
        """Fetch OHLCV bars."""
        # Your implementation
        pass

    async def validate_ticker(self, ticker: str) -> bool:
        """Check if ticker is valid."""
        # Your implementation
        pass
```

### 2. Register Provider

```python
# apps/api/src/providers/__init__.py

from .your_provider import YourProvider

PROVIDERS = {
    'yahoo': YahooProvider,
    'twelvedata': TwelveDataProvider,
    'your_provider': YourProvider,  # Add here
}
```

### 3. Update Configuration

```bash
# .env.example
# Your Provider
# PROVIDER=your_provider
# YOUR_PROVIDER_API_KEY=xxx
```

### 4. Add Documentation

Update `docs/PROVIDER.md` with:
- Provider overview
- Rate limits
- API key setup
- Supported features

### 5. Add Tests

```python
# apps/api/tests/test_your_provider.py

def test_your_provider_get_bars():
    ...
```

---

## Questions?

- Open an issue for questions
- Check existing documentation in `docs/`
- Review `CLAUDE.md` for collaboration guidelines

---

Thank you for contributing! 🙏
