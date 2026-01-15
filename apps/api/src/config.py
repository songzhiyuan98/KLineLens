"""
配置管理模块

使用 pydantic-settings 从环境变量加载应用配置。
支持 .env 文件和环境变量两种配置方式。

配置项:
- provider: 数据提供者（默认 yfinance）
- cache_type: 缓存类型（默认 memory）
- cache_ttl: 缓存生存时间（默认 60 秒）
- log_level: 日志级别（默认 INFO）
- cors_origins: 允许的跨域来源

使用示例:
    from .config import settings
    print(settings.cache_ttl)  # 60
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类

    从环境变量或 .env 文件加载配置。
    所有配置项都有默认值，可以直接使用。

    属性:
        provider: 数据提供者名称 (yfinance, alphavantage)
        cache_type: 缓存类型 (memory/redis)
        cache_ttl: 缓存生存时间（秒）
        log_level: 日志级别
        cors_origins: 允许的跨域来源，多个用逗号分隔
        alphavantage_api_key: Alpha Vantage API 密钥（使用 alphavantage 时必需）
    """

    # 数据提供者配置
    # twelvedata: 推荐！实时数据，可靠分钟成交量，Free 800次/天
    # yfinance: 免费，无需 Key，分钟成交量不可靠，15-20分钟延迟
    # alpaca: 免费，需要 Key，有分钟成交量（IEX 口径）
    # alphavantage: 25次/天，需要 Key
    provider: str = "twelvedata"  # 默认使用 Twelve Data

    # API Keys（根据选择的 provider 使用）
    twelvedata_api_key: str = ""  # Twelve Data API Key（推荐）
    alpaca_api_key: str = ""  # Alpaca API Key
    alpaca_api_secret: str = ""  # Alpaca API Secret
    alphavantage_api_key: str = ""  # Alpha Vantage API Key

    # LLM 配置（用于生成叙事报告）
    # openai: 使用 OpenAI API（支持兼容 API）
    # gemini: 使用 Google Gemini API
    llm_provider: str = "openai"  # openai 或 gemini
    llm_api_key: str = ""  # LLM API Key
    llm_model: str = ""  # 短评模型（留空使用默认: gpt-4o-mini）
    llm_model_full: str = ""  # 完整报告模型（留空使用默认: gpt-4o）
    llm_base_url: str = ""  # OpenAI 兼容 API 的 base URL（可选）

    # 缓存配置
    cache_type: str = "memory"  # memory 或 redis
    cache_ttl: int = 60  # 缓存生存时间（秒）

    # 服务器配置
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    cors_origins: str = "*"  # 允许的跨域来源，* 表示允许所有

    # Pydantic V2 配置
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


# 全局配置实例（单例）
settings = Settings()
