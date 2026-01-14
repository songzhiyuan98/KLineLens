"""
缓存管理模块

提供内存缓存功能，支持 TTL（生存时间）过期机制。
用于缓存 K 线数据，减少对数据提供商的请求频率。

主要功能:
- MemoryCache: 带 TTL 的内存缓存类
- get_cache(): 获取全局缓存实例
- cache_key(): 生成缓存键

使用示例:
    cache = get_cache(default_ttl=60)
    cache.set("key", data)
    data = cache.get("key")  # 60秒内有效
"""

import time
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

# 配置日志记录器
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """
    缓存条目

    存储缓存数据和过期时间。

    属性:
        data: 缓存的数据
        expires_at: 过期时间戳（Unix 时间）
    """
    data: Any
    expires_at: float


class MemoryCache:
    """
    内存缓存类

    使用字典存储缓存数据，支持自动过期清理。
    适用于单实例部署，多实例部署需要使用 Redis。

    属性:
        _cache: 内部缓存字典
        _default_ttl: 默认生存时间（秒）
    """

    def __init__(self, default_ttl: int = 60):
        """
        初始化缓存

        参数:
            default_ttl: 默认生存时间，单位秒，默认 60 秒
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        参数:
            key: 缓存键

        返回:
            缓存的数据，如果不存在或已过期则返回 None
        """
        entry = self._cache.get(key)
        if entry is None:
            return None

        # 检查是否过期
        if time.time() > entry.expires_at:
            del self._cache[key]
            logger.debug(f"缓存已过期: {key}")
            return None

        logger.debug(f"缓存命中: {key}")
        return entry.data

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值

        参数:
            key: 缓存键
            value: 要缓存的数据
            ttl: 生存时间（秒），不指定则使用默认值
        """
        ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.time() + ttl
        self._cache[key] = CacheEntry(data=value, expires_at=expires_at)
        logger.debug(f"缓存设置: {key} (TTL={ttl}秒)")

    def delete(self, key: str) -> None:
        """
        删除指定缓存

        参数:
            key: 要删除的缓存键
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        清理所有过期的缓存条目

        返回:
            清理的条目数量
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry.expires_at
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


# 全局缓存实例
_cache: Optional[MemoryCache] = None


def get_cache(default_ttl: int = 60) -> MemoryCache:
    """
    获取或创建全局缓存实例

    使用单例模式，确保整个应用使用同一个缓存实例。

    参数:
        default_ttl: 默认生存时间（秒）

    返回:
        全局 MemoryCache 实例
    """
    global _cache
    if _cache is None:
        _cache = MemoryCache(default_ttl=default_ttl)
    return _cache


def cache_key(ticker: str, timeframe: str, window: str) -> str:
    """
    生成 K 线数据的缓存键

    格式: bars:{TICKER}:{timeframe}:{window}

    参数:
        ticker: 股票代码
        timeframe: K线周期
        window: 回溯时间

    返回:
        格式化的缓存键字符串
    """
    return f"bars:{ticker.upper()}:{timeframe}:{window}"
