import pytest
import asyncio
from backend.core.event_bus import EventBus

@pytest.mark.asyncio
async def test_publish_and_subscribe():
    bus = EventBus()
    received_events = []

    async def handler(event_data):
        received_events.append(event_data)

    bus.subscribe("test.event", handler)
    await bus.publish("test.event", {"message": "hello"})

    await asyncio.sleep(0.1)  # 等待异步处理
    assert len(received_events) == 1
    assert received_events[0]["message"] == "hello"

@pytest.mark.asyncio
async def test_multiple_subscribers():
    bus = EventBus()
    call_count = [0]

    async def handler1(data):
        call_count[0] += 1

    async def handler2(data):
        call_count[0] += 10

    bus.subscribe("test.event", handler1)
    bus.subscribe("test.event", handler2)
    await bus.publish("test.event", {})

    await asyncio.sleep(0.1)
    assert call_count[0] == 11

@pytest.mark.asyncio
async def test_unsubscribe():
    bus = EventBus()
    received = []

    async def handler(data):
        received.append(data)

    bus.subscribe("test.event", handler)
    bus.unsubscribe("test.event", handler)
    await bus.publish("test.event", {"data": 1})

    await asyncio.sleep(0.1)
    assert len(received) == 0
