from typing import Callable, Dict, List, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """
    内存事件总线

    TODO: 迁移到Redis实现持久化和分布式支持
    """

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型（如 "emotion.detected"）
            handler: 异步处理函数
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(f"Subscribed handler to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """取消订阅"""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Unsubscribed handler from {event_type}")
            except ValueError:
                pass

    async def publish(self, event_type: str, event_data: Any) -> None:
        """
        发布事件（异步非阻塞）

        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        if event_type not in self._handlers:
            return

        handlers = self._handlers[event_type].copy()

        # 异步并发执行所有handler
        tasks = []
        for handler in handlers:
            try:
                task = asyncio.create_task(handler(event_data))
                tasks.append(task)
            except Exception as e:
                logger.error(f"Error creating task for {event_type}: {e}")

        # 不等待完成，立即返回（非阻塞）
        if tasks:
            logger.debug(f"Published {event_type} to {len(tasks)} handlers")

    def get_subscribers(self, event_type: str) -> int:
        """获取订阅者数量（用于调试）"""
        return len(self._handlers.get(event_type, []))
