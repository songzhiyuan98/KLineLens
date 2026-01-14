"""
缓存功能测试

测试内存缓存的各种场景：
- 缓存存取
- TTL 过期
- 缓存键生成
"""

import time
import pytest

from src.cache import MemoryCache, cache_key


class TestMemoryCache:
    """内存缓存测试类"""

    def test_set_and_get(self):
        """
        测试基本的存取操作

        预期:
        - set 后能够 get 到相同的值
        """
        cache = MemoryCache(default_ttl=60)
        cache.set("test_key", {"data": "value"})

        result = cache.get("test_key")
        assert result == {"data": "value"}

    def test_get_nonexistent_key(self):
        """
        测试获取不存在的键

        预期:
        - 返回 None
        """
        cache = MemoryCache(default_ttl=60)
        result = cache.get("nonexistent_key")

        assert result is None

    def test_ttl_expiration(self):
        """
        测试 TTL 过期

        预期:
        - 设置 1 秒 TTL
        - 2 秒后获取返回 None
        """
        cache = MemoryCache(default_ttl=60)
        cache.set("expire_key", "data", ttl=1)

        # 立即获取应该成功
        assert cache.get("expire_key") == "data"

        # 等待过期
        time.sleep(1.5)

        # 过期后返回 None
        assert cache.get("expire_key") is None

    def test_delete(self):
        """
        测试删除缓存

        预期:
        - 删除后获取返回 None
        """
        cache = MemoryCache(default_ttl=60)
        cache.set("delete_key", "data")
        cache.delete("delete_key")

        assert cache.get("delete_key") is None

    def test_clear(self):
        """
        测试清空缓存

        预期:
        - 清空后所有键都返回 None
        """
        cache = MemoryCache(default_ttl=60)
        cache.set("key1", "data1")
        cache.set("key2", "data2")
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cleanup_expired(self):
        """
        测试清理过期条目

        预期:
        - cleanup_expired 返回清理的条目数
        """
        cache = MemoryCache(default_ttl=60)
        cache.set("expire1", "data", ttl=1)
        cache.set("expire2", "data", ttl=1)
        cache.set("keep", "data", ttl=60)

        time.sleep(1.5)

        cleaned = cache.cleanup_expired()
        assert cleaned == 2


class TestCacheKey:
    """缓存键生成测试类"""

    def test_cache_key_format(self):
        """
        测试缓存键格式

        预期:
        - 格式为 bars:{TICKER}:{tf}:{window}
        """
        key = cache_key("tsla", "1m", "1d")
        assert key == "bars:TSLA:1m:1d"

    def test_cache_key_uppercase(self):
        """
        测试 ticker 自动转大写

        预期:
        - 小写 ticker 转为大写
        """
        key = cache_key("aapl", "5m", "5d")
        assert "AAPL" in key

    def test_cache_key_uniqueness(self):
        """
        测试缓存键唯一性

        预期:
        - 不同参数生成不同的键
        """
        key1 = cache_key("TSLA", "1m", "1d")
        key2 = cache_key("TSLA", "5m", "1d")
        key3 = cache_key("AAPL", "1m", "1d")

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3
