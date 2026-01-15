"""
TwelveData WebSocket 实时数据管理器

管理与 TwelveData WebSocket API 的连接，提供实时价格推送。

特点:
- 自动重连
- 心跳保活
- 多 symbol 订阅
- 价格缓存（最新价格）

使用示例:
    manager = TwelveDataWebSocket(api_key="your_key")
    await manager.connect()
    await manager.subscribe("QQQ")

    # 获取最新价格
    price = manager.get_latest_price("QQQ")
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Set, Callable, Any
from dataclasses import dataclass

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)

# TwelveData WebSocket URL
WS_URL = "wss://ws.twelvedata.com/v1/quotes/price"


@dataclass
class RealtimePrice:
    """实时价格数据"""
    symbol: str
    price: float
    timestamp: datetime
    day_change: Optional[float] = None
    day_change_pct: Optional[float] = None


class TwelveDataWebSocket:
    """
    TwelveData WebSocket 管理器

    维护与 TwelveData 的 WebSocket 连接，
    提供实时价格订阅和获取功能。
    """

    def __init__(self, api_key: str):
        """
        初始化 WebSocket 管理器

        参数:
            api_key: TwelveData API Key
        """
        self._api_key = api_key
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._subscribed_symbols: Set[str] = set()
        self._latest_prices: Dict[str, RealtimePrice] = {}
        self._running = False
        self._reconnect_delay = 5  # 重连延迟（秒）
        self._heartbeat_interval = 10  # 心跳间隔（秒）
        self._callbacks: list[Callable[[RealtimePrice], None]] = []
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """检查 WebSocket 是否已连接"""
        if self._ws is None:
            return False
        # websockets 12+ uses state attribute instead of open
        try:
            from websockets.protocol import State
            return self._ws.state == State.OPEN
        except (ImportError, AttributeError):
            # Fallback: check if ws object exists and connection loop is running
            return self._running and self._ws is not None

    @property
    def subscribed_symbols(self) -> Set[str]:
        """获取已订阅的 symbol 列表"""
        return self._subscribed_symbols.copy()

    def add_callback(self, callback: Callable[[RealtimePrice], None]):
        """添加价格更新回调"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[RealtimePrice], None]):
        """移除价格更新回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def connect(self):
        """
        连接到 TwelveData WebSocket

        建立连接并启动消息处理和心跳任务。
        """
        if self._running:
            logger.warning("WebSocket 已在运行中")
            return

        self._running = True

        # 启动连接管理任务
        asyncio.create_task(self._connection_manager())
        logger.info("WebSocket 连接管理器已启动")

    async def disconnect(self):
        """断开 WebSocket 连接"""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None
        logger.info("WebSocket 已断开")

    async def subscribe(self, symbol: str) -> bool:
        """
        订阅 symbol 的实时价格

        参数:
            symbol: 股票代码（如 QQQ, AAPL）

        返回:
            是否订阅成功
        """
        symbol = symbol.upper()

        if symbol in self._subscribed_symbols:
            logger.debug(f"已订阅 {symbol}，跳过")
            return True

        if not self.is_connected:
            # 保存待订阅，连接后自动订阅
            self._subscribed_symbols.add(symbol)
            logger.info(f"WebSocket 未连接，{symbol} 将在连接后订阅")
            return True

        try:
            subscribe_msg = {
                "action": "subscribe",
                "params": {
                    "symbols": symbol
                }
            }
            await self._ws.send(json.dumps(subscribe_msg))
            self._subscribed_symbols.add(symbol)
            logger.info(f"已订阅实时价格: {symbol}")
            return True
        except Exception as e:
            logger.error(f"订阅 {symbol} 失败: {e}")
            return False

    async def unsubscribe(self, symbol: str) -> bool:
        """
        取消订阅 symbol

        参数:
            symbol: 股票代码

        返回:
            是否取消成功
        """
        symbol = symbol.upper()

        if symbol not in self._subscribed_symbols:
            return True

        if not self.is_connected:
            self._subscribed_symbols.discard(symbol)
            return True

        try:
            unsubscribe_msg = {
                "action": "unsubscribe",
                "params": {
                    "symbols": symbol
                }
            }
            await self._ws.send(json.dumps(unsubscribe_msg))
            self._subscribed_symbols.discard(symbol)
            self._latest_prices.pop(symbol, None)
            logger.info(f"已取消订阅: {symbol}")
            return True
        except Exception as e:
            logger.error(f"取消订阅 {symbol} 失败: {e}")
            return False

    def get_latest_price(self, symbol: str) -> Optional[RealtimePrice]:
        """
        获取 symbol 的最新价格

        参数:
            symbol: 股票代码

        返回:
            最新价格数据，如果没有则返回 None
        """
        return self._latest_prices.get(symbol.upper())

    def get_all_prices(self) -> Dict[str, RealtimePrice]:
        """获取所有已订阅 symbol 的最新价格"""
        return self._latest_prices.copy()

    async def _connection_manager(self):
        """
        连接管理器

        负责建立连接、处理消息、自动重连。
        """
        while self._running:
            try:
                # 建立连接
                url = f"{WS_URL}?apikey={self._api_key}"
                logger.info("正在连接 TwelveData WebSocket...")

                async with websockets.connect(url) as ws:
                    self._ws = ws
                    logger.info("WebSocket 连接成功")

                    # 重新订阅之前的 symbols
                    if self._subscribed_symbols:
                        symbols = ",".join(self._subscribed_symbols)
                        subscribe_msg = {
                            "action": "subscribe",
                            "params": {
                                "symbols": symbols
                            }
                        }
                        await ws.send(json.dumps(subscribe_msg))
                        logger.info(f"已重新订阅: {symbols}")

                    # 启动心跳任务
                    heartbeat_task = asyncio.create_task(self._heartbeat())

                    try:
                        # 消息处理循环
                        async for message in ws:
                            await self._handle_message(message)
                    finally:
                        heartbeat_task.cancel()

            except ConnectionClosed as e:
                logger.warning(f"WebSocket 连接关闭: {e}")
            except Exception as e:
                logger.error(f"WebSocket 错误: {e}")

            self._ws = None

            if self._running:
                logger.info(f"将在 {self._reconnect_delay} 秒后重连...")
                await asyncio.sleep(self._reconnect_delay)

    async def _heartbeat(self):
        """
        心跳任务

        定期发送心跳保持连接活跃。
        """
        while self.is_connected:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                if self._ws:
                    await self._ws.send(json.dumps({"action": "heartbeat"}))
                    logger.debug("心跳已发送")
            except Exception as e:
                logger.warning(f"心跳发送失败: {e}")
                break

    async def _handle_message(self, message: str):
        """
        处理 WebSocket 消息

        参数:
            message: JSON 格式的消息字符串
        """
        try:
            data = json.loads(message)

            # 处理不同类型的消息
            event_type = data.get("event")

            if event_type == "price":
                # 价格更新
                symbol = data.get("symbol", "").upper()
                price = float(data.get("price", 0))
                ts = data.get("timestamp", 0)  # UNIX timestamp in seconds
                day_change = data.get("day_change")
                day_change_pct = data.get("dp")  # day_change_pct

                if symbol and price > 0:
                    # TwelveData returns timestamp in seconds (UNIX timestamp)
                    realtime_price = RealtimePrice(
                        symbol=symbol,
                        price=price,
                        timestamp=datetime.fromtimestamp(ts) if ts else datetime.now(),
                        day_change=float(day_change) if day_change else None,
                        day_change_pct=float(day_change_pct) if day_change_pct else None,
                    )
                    self._latest_prices[symbol] = realtime_price

                    # 触发回调
                    for callback in self._callbacks:
                        try:
                            callback(realtime_price)
                        except Exception as e:
                            logger.error(f"回调执行失败: {e}")

                    logger.debug(f"价格更新: {symbol} = ${price:.2f}")

            elif event_type == "subscribe-status":
                # 订阅状态
                status = data.get("status")
                if status == "ok":
                    logger.info(f"订阅确认: {data.get('success', [])}")
                else:
                    logger.warning(f"订阅失败: {data}")

            elif event_type == "heartbeat":
                # 心跳响应
                logger.debug("收到心跳响应")

            else:
                # 其他消息
                logger.debug(f"收到消息: {data}")

        except json.JSONDecodeError:
            logger.warning(f"无法解析消息: {message}")
        except Exception as e:
            logger.error(f"处理消息失败: {e}")


# 全局 WebSocket 管理器实例
_ws_manager: Optional[TwelveDataWebSocket] = None


def get_websocket_manager(api_key: str = None) -> Optional[TwelveDataWebSocket]:
    """
    获取全局 WebSocket 管理器实例

    参数:
        api_key: TwelveData API Key（首次调用必须提供）

    返回:
        WebSocket 管理器实例
    """
    global _ws_manager

    if _ws_manager is None and api_key:
        _ws_manager = TwelveDataWebSocket(api_key)

    return _ws_manager


async def init_websocket(api_key: str) -> TwelveDataWebSocket:
    """
    初始化并启动 WebSocket 管理器

    参数:
        api_key: TwelveData API Key

    返回:
        已连接的 WebSocket 管理器
    """
    global _ws_manager

    if _ws_manager is None:
        _ws_manager = TwelveDataWebSocket(api_key)

    if not _ws_manager.is_connected:
        await _ws_manager.connect()

    return _ws_manager
