# Developer Quick Start Guide

> Get KLineLens running locally in 5 minutes for development and contribution.

---

## Prerequisites

| Software | Version | Check Command |
|----------|---------|---------------|
| Node.js | 18+ | `node --version` |
| pnpm | 8+ | `pnpm --version` |
| Python | 3.11+ | `python --version` |
| Git | 2.0+ | `git --version` |

### Install Prerequisites

```bash
# macOS (using Homebrew)
brew install node pnpm python@3.11

# Windows (using Chocolatey)
choco install nodejs pnpm python311

# Ubuntu/Debian
sudo apt update
sudo apt install nodejs python3.11 python3.11-venv
npm install -g pnpm
```

---

## Quick Start (Local Development)

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/songzhiyuan98/KLineLens.git
cd KLineLens

# Copy environment config
cp .env.example .env
```

### 2. Start Backend (Terminal 1)

```bash
cd apps/api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server with hot reload
uvicorn src.main:app --reload --port 8000
```

**Verify:** Open http://localhost:8000/docs to see API documentation.

### 3. Start Frontend (Terminal 2)

```bash
cd apps/web

# Install dependencies
pnpm install

# Start dev server
pnpm dev
```

**Verify:** Open http://localhost:3000 to see the app.

---

## Project Structure

```
KLineLens/
├── apps/
│   ├── api/                 # FastAPI backend
│   │   ├── src/
│   │   │   ├── main.py      # Entry point
│   │   │   ├── providers/   # Data providers (Yahoo, TwelveData, etc.)
│   │   │   └── services/    # Business logic
│   │   └── requirements.txt
│   │
│   └── web/                 # Next.js frontend
│       ├── src/
│       │   ├── pages/       # Routes
│       │   ├── components/  # React components
│       │   └── lib/         # Utilities
│       └── package.json
│
├── packages/
│   └── core/                # Pure Python analysis engine
│       ├── src/
│       │   ├── analysis.py  # Main analysis logic
│       │   ├── features.py  # Feature extraction
│       │   └── zones.py     # S/R zone calculation
│       └── tests/
│
├── docs/                    # Documentation
├── docker-compose.yml       # Docker configuration
└── .env.example             # Environment template
```

---

## Key Entry Points

| Component | File | Purpose |
|-----------|------|---------|
| **API Entry** | `apps/api/src/main.py` | FastAPI app, routes |
| **Analysis Engine** | `packages/core/src/analysis.py` | Core algorithms |
| **Frontend Entry** | `apps/web/src/pages/_app.tsx` | Next.js app |
| **Detail Page** | `apps/web/src/pages/t/[ticker].tsx` | Main analysis page |

---

## Common Development Tasks

### Run Tests

```bash
# Backend tests
cd apps/api
pytest tests/ -v

# Core engine tests
cd packages/core
pytest tests/ -v
```

### Format Code

```bash
# Python (backend + core)
pip install black isort
black apps/api packages/core
isort apps/api packages/core

# TypeScript (frontend)
cd apps/web
pnpm lint --fix
```

### Add a New Data Provider

1. Create `apps/api/src/providers/newprovider_provider.py`
2. Implement `MarketDataProvider` interface
3. Register in `apps/api/src/providers/__init__.py`
4. Update docs: `docs/PROVIDER.md`

### Add a New Strategy

1. Create `packages/core/src/strategies/my_strategy.py`
2. Implement strategy logic
3. Register in strategy factory
4. See `docs/CUSTOM_STRATEGY.md` for full guide

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROVIDER` | No | yahoo | Data provider |
| `TWELVEDATA_API_KEY` | If using TwelveData | - | TwelveData API key |
| `CACHE_TTL` | No | 60 | Cache duration (seconds) |
| `API_PORT` | No | 8000 | Backend port |
| `WEB_PORT` | No | 3000 | Frontend port |

---

## Debugging Tips

### API Issues

```bash
# Check API health
curl http://localhost:8000/

# Test specific endpoint
curl "http://localhost:8000/v1/bars?ticker=AAPL&tf=1m" | jq

# Check logs
docker compose logs -f api
```

### Frontend Issues

```bash
# Check build
cd apps/web && pnpm build

# Check for TypeScript errors
pnpm tsc --noEmit
```

### Core Engine Issues

```bash
# Run specific test
cd packages/core
pytest tests/test_analysis.py -v -s

# Debug with print statements
python -c "from src.analysis import analyze; print(analyze(...))"
```

---

## Docker Development

If you prefer Docker for development:

```bash
# Start with hot reload
docker compose up

# Rebuild after dependency changes
docker compose up --build

# View logs
docker compose logs -f api
docker compose logs -f web
```

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat: add my feature"

# Push and create PR
git push -u origin feature/my-feature
```

### Commit Message Format

```
<type>: <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- refactor: Code refactoring
- test: Adding tests
- chore: Maintenance
```

---

## Getting Help

- **Documentation**: Check `docs/` folder
- **Issues**: [GitHub Issues](https://github.com/songzhiyuan98/KLineLens/issues)
- **Discussions**: [GitHub Discussions](https://github.com/songzhiyuan98/KLineLens/discussions)

---

## Next Steps

1. Read [ENGINE_SPEC.md](ENGINE_SPEC.md) to understand the analysis algorithm
2. Read [API.md](API.md) to understand the API structure
3. Read [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines
4. Pick an issue labeled `good first issue` to start contributing!
