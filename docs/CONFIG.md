# KLineLens — Configuration

> Environment variables and configuration strategy.

---

## 1. Overview

KLineLens uses environment variables for configuration. This allows:
- Different settings for dev/staging/prod
- Secrets management (API keys)
- Easy deployment configuration

---

## 2. Environment Variables

### 2.1 API (Backend)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROVIDER` | No | `yfinance` | Data provider name |
| `CACHE_TTL` | No | `60` | Default cache TTL in seconds |
| `CACHE_TYPE` | No | `memory` | Cache backend: `memory` or `redis` |
| `REDIS_URL` | No | - | Redis connection URL (if CACHE_TYPE=redis) |
| `LOG_LEVEL` | No | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |
| `CORS_ORIGINS` | No | `*` | Allowed CORS origins (comma-separated) |
| `PORT` | No | `8000` | Server port |

### 2.2 Web (Frontend)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | - | Backend API URL |
| `NEXT_PUBLIC_REFRESH_INTERVAL` | No | `60000` | Auto-refresh interval (ms) |

### 2.3 Provider-Specific

| Variable | Provider | Required | Description |
|----------|----------|----------|-------------|
| `ALPHAVANTAGE_API_KEY` | Alpha Vantage | Yes | API key |
| `POLYGON_API_KEY` | Polygon.io | Yes | API key |

---

## 3. Configuration Files

### 3.1 API: `.env` Example

```bash
# apps/api/.env

# Provider
PROVIDER=yfinance

# Cache
CACHE_TYPE=memory
CACHE_TTL=60
# REDIS_URL=redis://localhost:6379

# Server
PORT=8000
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000

# Provider API keys (if needed)
# ALPHAVANTAGE_API_KEY=your_key_here
# POLYGON_API_KEY=your_key_here
```

### 3.2 Web: `.env.local` Example

```bash
# apps/web/.env.local

NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_REFRESH_INTERVAL=60000
```

---

## 4. Configuration Loading

### 4.1 Python (API)

```python
# apps/api/src/config.py

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Provider
    provider: str = "yfinance"

    # Cache
    cache_type: str = "memory"
    cache_ttl: int = 60
    redis_url: Optional[str] = None

    # Server
    port: int = 8000
    log_level: str = "INFO"
    cors_origins: str = "*"

    # Provider keys
    alphavantage_api_key: Optional[str] = None
    polygon_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton
settings = Settings()
```

### 4.2 TypeScript (Web)

```typescript
// apps/web/src/lib/config.ts

export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  refreshInterval: parseInt(process.env.NEXT_PUBLIC_REFRESH_INTERVAL || '60000'),
};
```

---

## 5. Validation

### 5.1 Required Variable Check

```python
# apps/api/src/config.py

def validate_config():
    """Validate configuration at startup."""
    errors = []

    # Check provider-specific requirements
    if settings.provider == "alphavantage" and not settings.alphavantage_api_key:
        errors.append("ALPHAVANTAGE_API_KEY required for Alpha Vantage provider")

    if settings.provider == "polygon" and not settings.polygon_api_key:
        errors.append("POLYGON_API_KEY required for Polygon provider")

    if settings.cache_type == "redis" and not settings.redis_url:
        errors.append("REDIS_URL required when CACHE_TYPE=redis")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
```

### 5.2 Startup Validation

```python
# apps/api/src/main.py

from fastapi import FastAPI
from .config import settings, validate_config

app = FastAPI()

@app.on_event("startup")
async def startup():
    validate_config()
    print(f"Starting with provider: {settings.provider}")
    print(f"Cache type: {settings.cache_type}")
```

---

## 6. Secrets Management

### 6.1 Development
- Use `.env` files (gitignored)
- Never commit secrets to version control

### 6.2 Production
- Use platform secrets management:
  - Vercel: Environment Variables
  - Railway: Service Variables
  - Docker: `--env-file` or secrets

### 6.3 `.gitignore` Entries

```gitignore
# Environment files
.env
.env.local
.env.*.local
*.env

# API keys
secrets/
```

---

## 7. Default Configurations

### 7.1 Development Defaults

```python
DEFAULTS_DEV = {
    "provider": "yfinance",
    "cache_type": "memory",
    "cache_ttl": 60,
    "log_level": "DEBUG",
    "cors_origins": "*",
}
```

### 7.2 Production Recommendations

```python
DEFAULTS_PROD = {
    "provider": "yfinance",  # or paid provider
    "cache_type": "redis",
    "cache_ttl": 30,
    "log_level": "INFO",
    "cors_origins": "https://yourdomain.com",
}
```

---

## 8. Feature Flags (Future)

For MVP, no feature flags needed. Future implementation:

```python
class FeatureFlags:
    websocket_enabled: bool = False
    multi_timeframe: bool = False
    llm_narration: bool = False
    snapshots_enabled: bool = False
```

---

## 9. Quick Reference

### Development Setup

```bash
# 1. Copy example env files
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local

# 2. Edit as needed (usually defaults work)

# 3. Start services
cd apps/api && uvicorn src.main:app --reload
cd apps/web && npm run dev
```

### Minimum Required for MVP

```bash
# API - no env file needed, uses defaults

# Web
NEXT_PUBLIC_API_URL=http://localhost:8000
```
