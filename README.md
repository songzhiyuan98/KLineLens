# KLineLens

An open-source local market structure analysis terminal for OHLCV-based trading analysis.

> **Self-hosted**: Run entirely on your local machine via Docker. You control your data.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

---

## What It Does

Type a ticker → Get **structure + behavior probabilities + evidence + timeline + conditional playbook**, updated periodically.

| Feature | Description |
|---------|-------------|
| **Market Structure** | Regime detection (trend/range), support/resistance zones |
| **Behavior Inference** | Probability distribution (accumulation/shakeout/markup/distribution/markdown) |
| **Evidence Pack** | Traceable metrics for each inference |
| **Stateful Timeline** | Records structural changes over time |
| **Conditional Playbook** | Plan A/B with entry, target, invalidation |

> ⚠️ **Disclaimer**: Not financial advice. This tool provides rule-based analysis and probability interpretations. See [docs/DISCLAIMER.md](docs/DISCLAIMER.md).

---

## Quick Start (Docker)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (macOS/Windows) or Docker Engine (Linux)

### One-Command Setup

```bash
# 1. Clone the repository
git clone https://github.com/user/klinelens.git
cd klinelens

# 2. Copy environment template
cp .env.example .env

# 3. Start services
docker compose up --build

# 4. Open your browser
# Web UI: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

Or use Make:

```bash
cp .env.example .env
make up
```

### Stopping Services

```bash
docker compose down
# or
make down
```

---

## Configuration

Edit `.env` to customize:

```bash
# Data provider (yahoo is free, no API key needed)
PROVIDER=yahoo

# Cache TTL (seconds)
CACHE_TTL=60

# Ports
API_PORT=8000
WEB_PORT=3000

# Auto-refresh interval (seconds)
REFRESH_SECONDS=60
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed configuration options.

---

## Project Structure

```
klinelens/
├── apps/
│   ├── web/                 # Next.js frontend
│   └── api/                 # FastAPI backend
├── packages/
│   └── core/                # Python analysis engine
├── docs/                    # Documentation
├── docker-compose.yml       # Docker orchestration
├── .env.example             # Environment template
├── Makefile                 # Common commands
└── README.md
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [MASTER_SPEC.md](MASTER_SPEC.md) | Project constitution |
| [docs/PRD.md](docs/PRD.md) | Product requirements |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Docker setup guide |
| [docs/API.md](docs/API.md) | REST API reference |
| [docs/ENGINE_SPEC.md](docs/ENGINE_SPEC.md) | Algorithm specification |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [docs/PROVIDER.md](docs/PROVIDER.md) | Data provider guide |

---

## Development

### Local Development (without Docker)

```bash
# 1. Install Python dependencies at root level
pip install -r requirements.txt

# 2. Install Node dependencies
npm install

# Terminal 1: API (port 8000)
cd apps/api
uvicorn src.main:app --reload --port 8000

# Terminal 2: Web (port 3000)
cd apps/web
npm run dev
```

### Build for Production

```bash
# Build web app
cd apps/web && npm run build

# Or build all
npm run build
```

### Running Tests

```bash
# Core engine tests
cd packages/core && python3 -m pytest tests/ -v

# API tests
cd apps/api && python3 -m pytest tests/ -v

# Or use Make
make test
```

### Supported Tickers

The application supports any US stock ticker symbol available through Yahoo Finance:
- Individual stocks: `AAPL`, `TSLA`, `NVDA`, `GOOGL`, `MSFT`
- ETFs: `SPY`, `QQQ`, `IWM`, `DIA`
- Cryptocurrencies: `BTC-USD`, `ETH-USD`

### Language Support

The app supports Chinese and English. Toggle the language in the Settings page. Language preference is persisted in localStorage.

---

## Roadmap

- [x] **MVP**: Yahoo Finance provider, in-memory cache, basic UI
- [ ] **V1**: SQLite persistence, Polygon/TwelveData providers, WebSocket streaming
- [ ] **V2**: LLM narration layer, multi-timeframe alignment

---

## Contributing

1. Read [CLAUDE.md](CLAUDE.md) for collaboration guidelines
2. Check [docs/TODO.md](docs/TODO.md) for current tasks
3. Follow docs-first approach: update docs before implementing

---

## License

[MIT License](LICENSE)

---

## Disclaimer

This software is for educational and informational purposes only. It does not constitute financial advice. See [docs/DISCLAIMER.md](docs/DISCLAIMER.md) for full disclaimer.
