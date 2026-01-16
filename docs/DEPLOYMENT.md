# KLineLens Deployment Guide

> Local deployment guide: One-click startup using Docker Compose

---

## 1. Requirements

### 1.1 Required Software
| Software | Version | Notes |
|----------|---------|-------|
| Docker Desktop | 4.0+ | For macOS/Windows users |
| Docker Engine | 20.0+ | For Linux users |
| Docker Compose | V2 | Usually installed with Docker Desktop |

### 1.2 System Resources
| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| Memory | 2 GB | 4 GB |
| Disk | 2 GB | 5 GB |

---

## 2. Quick Start

```bash
# 1. Clone repository
git clone https://github.com/songzhiyuan98/KLineLens.git
cd KLineLens

# 2. Copy environment config
cp .env.example .env

# 3. Start services (first run builds images, takes a few minutes)
docker compose up --build

# 4. Access application
# Web UI: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 3. Environment Configuration

### 3.1 Configuration File (.env)

Copy `.env.example` to `.env` and modify as needed:

```bash
# ============ Provider Configuration ============
# Data source: yahoo (default, free) | twelvedata | alpaca | alphavantage
PROVIDER=yahoo

# ============ Cache Configuration ============
# K-line data cache duration (seconds)
CACHE_TTL=60

# ============ Port Configuration ============
# API port (default 8000)
API_PORT=8000
# Web port (default 3000)
WEB_PORT=3000

# ============ Refresh Frequency ============
# Frontend auto-refresh interval (seconds)
REFRESH_SECONDS=60

# ============ Log Level ============
# DEBUG | INFO | WARNING | ERROR
LOG_LEVEL=INFO

# ============ Optional: Provider API Keys ============
# If using TwelveData
# TWELVEDATA_API_KEY=your_key_here

# If using Alpaca
# ALPACA_API_KEY=your_key_here
# ALPACA_API_SECRET=your_secret_here

# If using Alpha Vantage
# ALPHAVANTAGE_API_KEY=your_key_here
```

### 3.2 Default Values
| Variable | Default | Description |
|----------|---------|-------------|
| PROVIDER | yahoo | Free data source, no API key needed |
| CACHE_TTL | 60 | Reduces request frequency to data source |
| API_PORT | 8000 | FastAPI backend port |
| WEB_PORT | 3000 | Next.js frontend port |
| REFRESH_SECONDS | 60 | Frontend auto-refresh interval |

---

## 4. Docker Commands

### 4.1 Common Commands
```bash
# Start (background)
docker compose up -d

# Start (foreground, shows logs)
docker compose up

# Rebuild and start
docker compose up --build

# Stop services
docker compose down

# View logs
docker compose logs -f

# View API logs only
docker compose logs -f api

# View Web logs only
docker compose logs -f web
```

### 4.2 Cleanup Commands
```bash
# Stop and remove containers
docker compose down

# Stop and remove containers, networks, volumes
docker compose down -v

# Remove all unused images
docker image prune -a
```

---

## 5. Switching Providers

### 5.1 Yahoo Finance (Default)
- **Pros**: Free, no API key needed
- **Cons**: Daily request limit (~2000), 15-20 minute data delay
- **Configuration**:
```bash
PROVIDER=yahoo
```

### 5.2 TwelveData (Recommended)
- **Pros**: Near real-time data, reliable volume, global coverage
- **Cons**: 800 free requests/day
- **Configuration**:
```bash
PROVIDER=twelvedata
TWELVEDATA_API_KEY=your_api_key
```

### 5.3 Alpaca
- **Pros**: Free, unlimited requests, professional API
- **Cons**: US stocks only
- **Configuration**:
```bash
PROVIDER=alpaca
ALPACA_API_KEY=your_key
ALPACA_API_SECRET=your_secret
```

### 5.4 Alpha Vantage
- **Pros**: High-quality volume data
- **Cons**: 25 free requests/day
- **Configuration**:
```bash
PROVIDER=alphavantage
ALPHAVANTAGE_API_KEY=your_api_key
```

---

## 6. Troubleshooting

### 6.1 Port Already in Use
**Problem**: `Error: port 8000 is already in use`

**Solutions**:
```bash
# Method 1: Change port
# Edit .env file
API_PORT=8001
WEB_PORT=3001

# Method 2: Kill process using the port
lsof -i :8000
kill -9 <PID>
```

### 6.2 Docker Permission Issues
**Problem**: `permission denied while trying to connect to Docker`

**Solution** (Linux):
```bash
sudo usermod -aG docker $USER
# Re-login to terminal
```

### 6.3 No Data Returned
**Problem**: API returns 404 NO_DATA

**Possible Causes**:
1. Yahoo Finance rate limited → Wait a few minutes and retry
2. Invalid ticker → Check ticker spelling
3. Outside trading hours → 1m data only valid during trading sessions

**Debugging**:
```bash
# Check API health
curl http://localhost:8000/

# Test data fetch
curl "http://localhost:8000/v1/bars?ticker=AAPL&tf=1d"
```

### 6.4 Build Failure
**Problem**: Docker image build fails

**Solutions**:
```bash
# Clean cache and rebuild
docker compose build --no-cache

# Check Docker resource limits
docker system df
docker system prune
```

### 6.5 Web Cannot Connect to API
**Problem**: Frontend shows "Failed to fetch"

**Debugging**:
```bash
# Check if API is running
curl http://localhost:8000/

# Check network
docker network ls
docker network inspect klinelens-network
```

---

## 7. Development Mode

### 7.1 Local Development (Without Docker)
```bash
# Terminal 1: Start API
cd apps/api
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Terminal 2: Start Web
cd apps/web
npm install
npm run dev
```

### 7.2 Hybrid Mode
```bash
# Start only API (Docker)
docker compose up api

# Start Web locally (dev mode)
cd apps/web
npm run dev
```

---

## 8. Health Checks

### 8.1 API Health Check
```bash
curl http://localhost:8000/
# Expected: {"status": "ok", "service": "klinelens-api", "provider": "yfinance"}
```

### 8.2 Service Status
```bash
docker compose ps
# All services should show "running" or "healthy"
```

---

## 9. Updates

### 9.1 Update to Latest Version
```bash
# Pull latest code
git pull origin main

# Rebuild and start
docker compose up --build -d
```

### 9.2 Rollback
```bash
# Rollback to specific version
git checkout <commit-hash>
docker compose up --build -d
```
