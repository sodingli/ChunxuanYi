# 情绪检测与对话系统架构重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构情绪检测和对话系统，实现模块解耦、事件驱动架构、抽象接口设计

**Architecture:** 将emotion_agent.py拆分为7个独立模块，引入EventBus事件总线，实现检测器和LLM Provider抽象接口，建立对话管理器统一调度，SQLite持久化对话历史

**Tech Stack:** Python FastAPI, SQLAlchemy, asyncio, Node.js Express (API Gateway), SQLite

---

## 文件结构规划

### 新增目录和文件

```
backend/
  core/
    __init__.py
    event_bus.py                    # 事件总线（内存实现）
  
  emotion/
    __init__.py
    events.py                       # 事件定义
    service.py                      # 情绪检测服务编排层
    
    detector/
      __init__.py
      base.py                       # 检测器抽象接口
      emo_affectnet.py              # EMO实现（迁移自emo_detector.py）
      manager.py                    # 检测器管理器
    
    analyzer/
      __init__.py
      window.py                     # 滑动窗口分析器
      pattern.py                    # 情绪模式检测
      models.py                     # 数据模型
    
    strategy/
      __init__.py
      selector.py                   # 策略选择器
      types.py                      # 策略类型定义
    
    decision/
      __init__.py
      trigger.py                    # 触发决策引擎
      state_machine.py              # 情绪状态机
      cooldown.py                   # 冷却管理
    
    response/
      __init__.py
      generator.py                  # 话术生成器
      templates.py                  # 模板管理
  
  conversation/
    __init__.py
    manager.py                      # 对话管理器
    session.py                      # 会话状态管理
    context.py                      # 上下文构建器
    history.py                      # 对话历史持久化
    models.py                       # 数据模型
  
  llm/
    __init__.py
    base.py                         # LLM Provider抽象接口
    dashscope.py                    # DashScope实现（迁移自services/llm.py）
    factory.py                      # Provider工厂
  
  persona/
    __init__.py
    service.py                      # Persona服务
    models.py                       # Persona数据模型
  
  database/
    __init__.py
    connection.py                   # 数据库连接管理
    models.py                       # SQLAlchemy模型
    migrations.sql                  # 数据库迁移SQL
```

### 修改文件

```
backend/routers/emo.py              # 简化为调用EmotionService
backend/routers/chat.py             # 简化为调用ConversationManager
backend/config.py                   # 清理，移除部分配置到模块内
backend/database.py                 # 扩展，添加新表
server.js                           # 调整为纯API网关
package.json                        # 添加http-proxy-middleware依赖
requirements.txt                    # 添加sqlalchemy, alembic
```

### 废弃文件

```
modules/llm.js                      # LLM调用迁移到Python
backend/services/emotion_agent.py   # 拆分到emotion/模块
backend/services/emo_detector.py    # 迁移到emotion/detector/
backend/services/llm.py             # 迁移到llm/dashscope.py
```

---

## 阶段1: 基础设施搭建

### Task 1: 创建事件总线

**Files:**
- Create: `backend/core/__init__.py`
- Create: `backend/core/event_bus.py`
- Create: `tests/test_event_bus.py`

- [ ] **Step 1.1: 编写事件总线测试**

```python
# tests/test_event_bus.py
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
```

- [ ] **Step 1.2: 运行测试确认失败**

```bash
pytest tests/test_event_bus.py -v
```

Expected: FAIL - ModuleNotFoundError: No module named 'backend.core'

- [ ] **Step 1.3: 实现事件总线**

```python
# backend/core/__init__.py
from .event_bus import EventBus

__all__ = ["EventBus"]
```

```python
# backend/core/event_bus.py
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
```

- [ ] **Step 1.4: 运行测试确认通过**

```bash
pytest tests/test_event_bus.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 1.5: 提交**

```bash
git add backend/core/ tests/test_event_bus.py
git commit -m "feat: add in-memory event bus (TODO: Redis migration)"
```

---

### Task 2: 创建数据库表结构

**Files:**
- Modify: `backend/database.py`
- Create: `backend/database/connection.py`
- Create: `backend/database/models.py`
- Create: `backend/database/migrations.sql`

- [ ] **Step 2.1: 添加SQLAlchemy依赖**

```bash
echo "sqlalchemy>=2.0.0" >> requirements.txt
echo "alembic>=1.13.0" >> requirements.txt
pip install -r requirements.txt
```

- [ ] **Step 2.2: 创建数据库连接管理**

```python
# backend/database/__init__.py
from .connection import engine, SessionLocal, Base, get_db
from .models import ConversationHistory, PersonaModel, Memory, Reminder

__all__ = [
    "engine", "SessionLocal", "Base", "get_db",
    "ConversationHistory", "PersonaModel", "Memory", "Reminder"
]
```

```python
# backend/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 支持SQLite和MySQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/yidemo.db"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2.3: 定义数据库模型**

```python
# backend/database/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from .connection import Base

class ConversationHistory(Base):
    """对话历史表"""
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    emotion = Column(String(32))
    timestamp = Column(DateTime, server_default=func.now())

class PersonaModel(Base):
    """Persona配置表"""
    __tablename__ = "personas"
    
    session_id = Column(String(64), primary_key=True)
    name = Column(String(64), nullable=False)
    gender = Column(String(16))
    personality = Column(Text)
    address_as = Column(String(16))
    style = Column(Text)
    custom_instructions = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Memory(Base):
    """记忆表"""
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    content = Column(Text, nullable=False)
    type = Column(String(32))  # 'conversation' | 'fact' | 'preference'
    importance = Column(Integer, default=1)  # 1-5
    timestamp = Column(DateTime, server_default=func.now())

class Reminder(Base):
    """提醒表"""
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    content = Column(Text, nullable=False)
    remind_date = Column(String(20))
    type = Column(String(32))  # 'general' | 'health'
    status = Column(String(16), default='active')  # 'active' | 'completed' | 'cancelled'
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 2.4: 创建数据库表**

```python
# backend/database/migrations.sql
-- 此文件仅作为参考，实际通过SQLAlchemy创建

-- 对话历史表
CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(64) NOT NULL,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    emotion VARCHAR(32),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_session_time ON conversation_history(session_id, timestamp);

-- Persona配置表
CREATE TABLE IF NOT EXISTS personas (
    session_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    gender VARCHAR(16),
    personality TEXT,
    address_as VARCHAR(16),
    style TEXT,
    custom_instructions TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 记忆表
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(32),
    importance INTEGER DEFAULT 1,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id);

-- 提醒表
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    remind_date VARCHAR(20),
    type VARCHAR(32),
    status VARCHAR(16) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_reminders_session_date ON reminders(session_id, remind_date);
```

- [ ] **Step 2.5: 执行数据库初始化脚本**

```python
# 创建临时脚本 backend/init_db.py
from backend.database.connection import engine, Base
from backend.database.models import ConversationHistory, PersonaModel, Memory, Reminder

def init_database():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

if __name__ == "__main__":
    init_database()
```

```bash
python -m backend.init_db
```

Expected: "Database tables created successfully"

- [ ] **Step 2.6: 验证表创建**

```bash
sqlite3 data/yidemo.db ".tables"
```

Expected: conversation_history  memories  personas  reminders  config

- [ ] **Step 2.7: 提交**

```bash
git add backend/database/ requirements.txt
git commit -m "feat: add SQLAlchemy models and database schema

- ConversationHistory: 对话历史
- PersonaModel: Persona配置
- Memory: 记忆
- Reminder: 提醒

TODO: MySQL migration"
```

---

## 阶段2: 情绪检测系统重构

### Task 3: 创建情绪事件定义

**Files:**
- Create: `backend/emotion/__init__.py`
- Create: `backend/emotion/events.py`
- Create: `tests/test_emotion_events.py`

- [ ] **Step 3.1: 编写事件数据类测试**

```python
# tests/test_emotion_events.py
from backend.emotion.events import EmotionDetectedEvent, EmotionStateChangedEvent, AgentTriggeredEvent
import time

def test_emotion_detected_event():
    event = EmotionDetectedEvent(
        session_id="test_session",
        emotion="Happiness",
        score=0.85,
        category="POSITIVE",
        timestamp=time.time()
    )
    
    assert event.session_id == "test_session"
    assert event.emotion == "Happiness"
    assert event.score == 0.85
    assert event.category == "POSITIVE"
    assert event.timestamp > 0

def test_emotion_state_changed_event():
    event = EmotionStateChangedEvent(
        session_id="test_session",
        old_emotion="Neutral",
        new_emotion="Happiness",
        stability=0.8,
        duration=5.0
    )
    
    assert event.old_emotion == "Neutral"
    assert event.new_emotion == "Happiness"
    assert event.stability == 0.8
    assert event.duration == 5.0

def test_agent_triggered_event():
    event = AgentTriggeredEvent(
        session_id="test_session",
        strategy="POSITIVE_EMPATHY",
        message="看到您笑得这么开心，我也跟着高兴了",
        emotion_context={"emotion": "Happiness", "score": 0.9}
    )
    
    assert event.strategy == "POSITIVE_EMPATHY"
    assert "开心" in event.message
    assert event.emotion_context["emotion"] == "Happiness"
```

- [ ] **Step 3.2: 运行测试确认失败**

```bash
pytest tests/test_emotion_events.py -v
```

Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3.3: 实现事件定义**

```python
# backend/emotion/__init__.py
from .events import EmotionDetectedEvent, EmotionStateChangedEvent, AgentTriggeredEvent

__all__ = [
    "EmotionDetectedEvent",
    "EmotionStateChangedEvent", 
    "AgentTriggeredEvent"
]
```

```python
# backend/emotion/events.py
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class EmotionDetectedEvent:
    """单帧情绪检测完成事件"""
    session_id: str
    emotion: str          # 情绪名称（如 "Happiness"）
    score: float          # 置信度 0-1
    category: str         # 情绪类别（POSITIVE/NEGATIVE/NEUTRAL）
    timestamp: float      # unix timestamp

@dataclass
class EmotionStateChangedEvent:
    """主导情绪状态变化事件"""
    session_id: str
    old_emotion: Optional[str]  # 上一个主导情绪
    new_emotion: str            # 新的主导情绪
    stability: float            # 稳定性 0-1
    duration: float             # 持续时间（秒）

@dataclass
class AgentTriggeredEvent:
    """Agent响应触发事件"""
    session_id: str
    strategy: str               # 策略类型
    message: str                # 生成的话术
    emotion_context: Dict       # 情绪上下文信息
```

- [ ] **Step 3.4: 运行测试确认通过**

```bash
pytest tests/test_emotion_events.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 3.5: 提交**

```bash
git add backend/emotion/ tests/test_emotion_events.py
git commit -m "feat: add emotion event definitions"
```

---

### Task 4: 实现检测器抽象接口

**Files:**
- Create: `backend/emotion/detector/__init__.py`
- Create: `backend/emotion/detector/base.py`
- Create: `backend/emotion/detector/emo_affectnet.py` (迁移自 services/emo_detector.py)
- Create: `backend/emotion/detector/manager.py`

- [ ] **Step 4.1: 实现检测器抽象基类**

```python
# backend/emotion/detector/__init__.py
from .base import EmotionDetector, DetectionResult
from .emo_affectnet import EmoAffectNetDetector
from .manager import DetectorManager

__all__ = [
    "EmotionDetector",
    "DetectionResult",
    "EmoAffectNetDetector",
    "DetectorManager"
]
```

```python
# backend/emotion/detector/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class DetectionResult:
    """检测结果"""
    faces: List[Dict]  # [{"box": [x,y,w,h], "emotions": {...}}]
    timestamp: float

class EmotionDetector(ABC):
    """情绪检测器抽象基类"""
    
    @abstractmethod
    async def detect(self, frame: np.ndarray) -> Optional[DetectionResult]:
        """
        检测情绪
        
        Args:
            frame: 输入图像 (BGR格式)
        
        Returns:
            检测结果，失败返回None
        """
        pass
    
    @abstractmethod
    def get_supported_emotions(self) -> List[str]:
        """获取支持的情绪列表"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        pass
```

- [ ] **Step 4.2: 迁移EMO检测器实现**

```python
# backend/emotion/detector/emo_affectnet.py
import torch
import cv2
import numpy as np
from PIL import Image
from torchvision import transforms
from typing import Dict, List, Optional
import time
import os
from .base import EmotionDetector, DetectionResult

class EmoAffectNetDetector(EmotionDetector):
    """EMO-AffectNet情绪检测器实现"""
    
    # 7种基础情绪
    EMOTION_NAMES = [
        "Neutral", "Happiness", "Sadness", "Surprise",
        "Fear", "Disgust", "Anger"
    ]
    
    def __init__(self, model_path: str, device: str = "auto"):
        self.model_path = model_path
        
        # 设备选择
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # 加载模型
        self.model = None
        self._load_model()
        
        # 人脸检测 (Haar Cascade)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # 图像预处理
        self.transform = transforms.Compose([
            transforms.PILToTensor(),
            transforms.Lambda(self._preprocess_input)
        ])
    
    def _load_model(self):
        """加载PyTorch模型"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        try:
            self.model = torch.jit.load(self.model_path, map_location=self.device)
            self.model.eval()
            print(f"[EMO] Model loaded on {self.device}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
    
    def _preprocess_input(self, x: torch.Tensor) -> torch.Tensor:
        """预处理输入图像"""
        x = x.to(torch.float32)
        x = torch.flip(x, dims=(0,))  # RGB -> BGR
        x[0, :, :] -= 91.4953
        x[1, :, :] -= 103.8827
        x[2, :, :] -= 131.0912
        return x
    
    def _detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """检测人脸"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces_detected = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        faces = []
        for (x, y, w, h) in faces_detected:
            img_h, img_w = frame.shape[:2]
            x = max(0, x)
            y = max(0, y)
            w = min(img_w - x, w)
            h = min(img_h - y, h)
            
            faces.append({
                "box": [x, y, w, h],
                "confidence": 0.9
            })
        
        return faces
    
    def _predict_emotion(self, face_img: np.ndarray) -> Dict[str, float]:
        """预测情绪"""
        pil_img = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
        pil_img = pil_img.resize((224, 224), Image.Resampling.NEAREST)
        
        img_tensor = self.transform(pil_img)
        img_tensor = torch.unsqueeze(img_tensor, 0).to(self.device)
        
        with torch.no_grad():
            output = self.model(img_tensor)
            probabilities = torch.nn.functional.softmax(output, dim=1)
            probs = probabilities.cpu().numpy()[0]
        
        return {name: float(prob) for name, prob in zip(self.EMOTION_NAMES, probs)}
    
    async def detect(self, frame: np.ndarray) -> Optional[DetectionResult]:
        """检测情绪"""
        try:
            faces = self._detect_faces(frame)
            
            result_faces = []
            for face in faces:
                x, y, w, h = face["box"]
                face_img = frame[y:y+h, x:x+w]
                
                if face_img.size == 0:
                    continue
                
                emotions = self._predict_emotion(face_img)
                
                result_faces.append({
                    "box": face["box"],
                    "emotions": emotions
                })
            
            return DetectionResult(
                faces=result_faces,
                timestamp=time.time()
            )
        
        except Exception as e:
            print(f"[EMO] Detection error: {e}")
            return None
    
    def get_supported_emotions(self) -> List[str]:
        """获取支持的情绪列表"""
        return self.EMOTION_NAMES.copy()
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            "model_path": self.model_path,
            "device": self.device,
            "loaded": self.model is not None,
            "emotions": self.EMOTION_NAMES
        }
```

- [ ] **Step 4.3: 实现检测器管理器（单例）**

```python
# backend/emotion/detector/manager.py
from typing import Optional
from .base import EmotionDetector
from .emo_affectnet import EmoAffectNetDetector
from backend.config import EMO_MODEL_CONFIG

class DetectorManager:
    """检测器管理器（单例模式）"""
    
    _instance: Optional[EmotionDetector] = None
    
    @classmethod
    def get_instance(cls) -> EmotionDetector:
        """获取检测器单例"""
        if cls._instance is None:
            cls._instance = EmoAffectNetDetector(
                model_path=EMO_MODEL_CONFIG["model_path"],
                device=EMO_MODEL_CONFIG["device"]
            )
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """重置单例（用于测试）"""
        cls._instance = None
```

- [ ] **Step 4.4: 提交**

```bash
git add backend/emotion/detector/
git commit -m "feat: implement emotion detector abstraction and EMO migration

- Abstract EmotionDetector interface
- Migrate EmoDetector to EmoAffectNetDetector
- Add DetectorManager singleton"
```


### Task 5: 实现情绪分析器

**Files:**
- Create: `backend/emotion/analyzer/__init__.py`
- Create: `backend/emotion/analyzer/models.py`
- Create: `backend/emotion/analyzer/window.py`
- Create: `backend/emotion/analyzer/pattern.py`

- [ ] **Step 5.1: 定义分析器数据模型**

```python
# backend/emotion/analyzer/__init__.py
from .window import EmotionWindowAnalyzer
from .pattern import PatternDetector
from .models import EmotionData, DominantEmotion

__all__ = ["EmotionWindowAnalyzer", "PatternDetector", "EmotionData", "DominantEmotion"]
```

```python
# backend/emotion/analyzer/models.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class EmotionData:
    """单次情绪数据"""
    primary: str
    score: float
    category: str
    timestamp: float

@dataclass
class DominantEmotion:
    """主导情绪"""
    emotion: str
    category: str
    ratio: float          # 占比 0-1
    avg_score: float      # 平均置信度
    duration: float       # 持续时间（秒）
```

- [ ] **Step 5.2: 实现滑动窗口分析器（迁移自emotion_agent.py）**

```python
# backend/emotion/analyzer/window.py
from collections import deque
from typing import Optional
from .models import EmotionData, DominantEmotion
from backend.config import EMOTION_AGENT_CONFIG, EMOTION_CATEGORIES

class EmotionWindowAnalyzer:
    """滑动窗口情绪分析器"""
    
    def __init__(self, window_size: int = None):
        self.window_size = window_size or EMOTION_AGENT_CONFIG["window_size"]
        self.emotion_history = deque(maxlen=self.window_size)
    
    def add_emotion(self, emotion_data: EmotionData) -> None:
        """添加情绪数据到窗口"""
        self.emotion_history.append(emotion_data)
    
    def get_dominant_emotion(self) -> Optional[DominantEmotion]:
        """获取主导情绪"""
        if not self.emotion_history:
            return None
        
        # 统计情绪出现次数和分数
        emotion_counts = {}
        emotion_scores = {}
        
        for data in self.emotion_history:
            emotion = data.primary
            score = data.score
            
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            if emotion not in emotion_scores:
                emotion_scores[emotion] = []
            emotion_scores[emotion].append(score)
        
        # 找出最频繁的情绪
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        count = emotion_counts[dominant_emotion]
        ratio = count / len(self.emotion_history)
        avg_score = sum(emotion_scores[dominant_emotion]) / len(emotion_scores[dominant_emotion])
        
        # 确定类别
        category = self._get_emotion_category(dominant_emotion)
        
        # 计算持续时间
        duration = self.get_duration()
        
        return DominantEmotion(
            emotion=dominant_emotion,
            category=category,
            ratio=ratio,
            avg_score=avg_score,
            duration=duration
        )
    
    def get_duration(self) -> float:
        """获取窗口时间跨度"""
        if len(self.emotion_history) < 2:
            return 0.0
        
        first_time = self.emotion_history[0].timestamp
        last_time = self.emotion_history[-1].timestamp
        return last_time - first_time
    
    def calculate_stability(self) -> float:
        """计算稳定性（主导情绪占比）"""
        dominant = self.get_dominant_emotion()
        return dominant.ratio if dominant else 0.0
    
    def _get_emotion_category(self, emotion: str) -> str:
        """获取情绪类别"""
        for category, emotions in EMOTION_CATEGORIES.items():
            if emotion in emotions:
                return category
        return "NEUTRAL"
    
    def clear(self) -> None:
        """清空窗口"""
        self.emotion_history.clear()
```

- [ ] **Step 5.3: 实现情绪模式检测**

```python
# backend/emotion/analyzer/pattern.py
from .window import EmotionWindowAnalyzer

class PatternDetector:
    """情绪变化模式检测"""
    
    @staticmethod
    def detect_change_pattern(analyzer: EmotionWindowAnalyzer) -> str:
        """
        检测变化模式
        
        Returns:
            "STABLE" | "GRADUAL" | "RAPID"
        """
        stability = analyzer.calculate_stability()
        
        if stability >= 0.8:
            return "STABLE"
        elif stability >= 0.5:
            return "GRADUAL"
        else:
            return "RAPID"
```

- [ ] **Step 5.4: 提交**

```bash
git add backend/emotion/analyzer/
git commit -m "feat: implement emotion window analyzer and pattern detector

Migrated from emotion_agent.py:
- EmotionWindowAnalyzer: sliding window analysis
- PatternDetector: emotion change pattern detection"
```

---

### Task 6: 实现策略选择器和决策引擎

**Files:**
- Create: `backend/emotion/strategy/__init__.py`
- Create: `backend/emotion/strategy/types.py`
- Create: `backend/emotion/strategy/selector.py`
- Create: `backend/emotion/decision/__init__.py`
- Create: `backend/emotion/decision/state_machine.py`
- Create: `backend/emotion/decision/trigger.py`
- Create: `backend/emotion/decision/cooldown.py`

- [ ] **Step 6.1: 定义策略类型**

```python
# backend/emotion/strategy/__init__.py
from .types import StrategyType
from .selector import StrategySelector

__all__ = ["StrategyType", "StrategySelector"]
```

```python
# backend/emotion/strategy/types.py
from enum import Enum

class StrategyType(str, Enum):
    """交互策略类型"""
    POSITIVE_EMPATHY = "POSITIVE_EMPATHY"          # 积极共情
    NEGATIVE_CARE = "NEGATIVE_CARE"                # 消极关怀
    EMOTION_TRANSITION = "EMOTION_TRANSITION"      # 情绪转换引导
    MIXED_EMOTION = "MIXED_EMOTION"                # 混合情绪探索
    SILENT_PRESENCE = "SILENT_PRESENCE"            # 沉默陪伴
```

- [ ] **Step 6.2: 实现策略选择器（迁移自emotion_agent.py）**

```python
# backend/emotion/strategy/selector.py
from .types import StrategyType
from backend.emotion.analyzer.models import DominantEmotion

class StrategySelector:
    """策略选择器"""
    
    def select_strategy(self, dominant: DominantEmotion) -> StrategyType:
        """
        根据情绪状态选择策略
        
        Args:
            dominant: 主导情绪
        
        Returns:
            策略类型
        """
        category = dominant.category
        ratio = dominant.ratio
        avg_score = dominant.avg_score
        
        # 情绪不够稳定，使用混合情绪策略
        if ratio < 0.7:
            return StrategyType.MIXED_EMOTION
        
        # 根据类别选择策略
        if category == "POSITIVE":
            return StrategyType.POSITIVE_EMPATHY
        elif category == "NEGATIVE":
            # 消极情绪根据强度选择
            if avg_score > 0.7:
                return StrategyType.NEGATIVE_CARE
            else:
                return StrategyType.SILENT_PRESENCE
        else:
            return StrategyType.MIXED_EMOTION
```

- [ ] **Step 6.3: 实现情绪状态机**

```python
# backend/emotion/decision/__init__.py
from .state_machine import EmotionState, EmotionStateMachine
from .trigger import TriggerDecision
from .cooldown import CooldownManager

__all__ = ["EmotionState", "EmotionStateMachine", "TriggerDecision", "CooldownManager"]
```

```python
# backend/emotion/decision/state_machine.py
from enum import Enum
import time

class EmotionState(str, Enum):
    """情绪状态"""
    IDLE = "idle"                  # 空闲
    DETECTING = "detecting"        # 检测中
    STABLE = "stable"              # 情绪稳定
    TRIGGERED = "triggered"        # 已触发响应
    COOLDOWN = "cooldown"          # 冷却期

class EmotionStateMachine:
    """情绪状态机"""
    
    def __init__(self):
        self.state = EmotionState.IDLE
        self.last_transition_time = time.time()
    
    def transition(self, new_state: EmotionState) -> bool:
        """
        状态转换
        
        Returns:
            是否转换成功
        """
        # 定义允许的转换
        allowed_transitions = {
            EmotionState.IDLE: [EmotionState.DETECTING],
            EmotionState.DETECTING: [EmotionState.STABLE, EmotionState.IDLE],
            EmotionState.STABLE: [EmotionState.TRIGGERED, EmotionState.DETECTING, EmotionState.IDLE],
            EmotionState.TRIGGERED: [EmotionState.COOLDOWN],
            EmotionState.COOLDOWN: [EmotionState.IDLE, EmotionState.DETECTING]
        }
        
        if new_state in allowed_transitions.get(self.state, []):
            self.state = new_state
            self.last_transition_time = time.time()
            return True
        
        return False
    
    def can_trigger(self) -> bool:
        """是否可以触发Agent"""
        return self.state == EmotionState.STABLE
    
    def reset(self) -> None:
        """重置状态"""
        self.state = EmotionState.IDLE
        self.last_transition_time = time.time()
```

- [ ] **Step 6.4: 实现冷却管理器**

```python
# backend/emotion/decision/cooldown.py
import time
from typing import Optional
from backend.config import EMOTION_AGENT_CONFIG

class CooldownManager:
    """冷却管理器"""
    
    def __init__(self):
        self.config = EMOTION_AGENT_CONFIG["cooldown"]
        self.last_trigger_time: float = 0
        self.last_category: Optional[str] = None
    
    def can_trigger(self, current_category: str, intensity: float) -> bool:
        """
        检查是否可以触发（基于冷却时间）
        
        Args:
            current_category: 当前情绪类别
            intensity: 情绪强度
        
        Returns:
            是否可以触发
        """
        if self.last_trigger_time == 0:
            return True
        
        elapsed = time.time() - self.last_trigger_time
        required_cooldown = self.calculate_cooldown(current_category, intensity)
        
        return elapsed >= required_cooldown
    
    def calculate_cooldown(self, current_category: str, intensity: float) -> float:
        """
        计算所需冷却时间
        
        Args:
            current_category: 当前情绪类别
            intensity: 情绪强度
        
        Returns:
            冷却时间（秒）
        """
        # 强烈情绪缩短冷却时间
        if intensity > 0.7:
            return self.config["high_intensity"]
        
        # 同类情绪
        if self.last_category == current_category:
            return self.config["same_category"]
        
        # 异类情绪（情绪转换）
        return self.config["different_category"]
    
    def record_trigger(self, category: str) -> None:
        """记录触发"""
        self.last_trigger_time = time.time()
        self.last_category = category
    
    def reset(self) -> None:
        """重置冷却"""
        self.last_trigger_time = 0
        self.last_category = None
```

- [ ] **Step 6.5: 实现触发决策引擎（迁移自emotion_agent.py）**

```python
# backend/emotion/decision/trigger.py
from backend.emotion.analyzer.models import DominantEmotion
from backend.config import EMOTION_AGENT_CONFIG
from .cooldown import CooldownManager
from .state_machine import EmotionStateMachine

class TriggerDecision:
    """触发决策引擎"""
    
    def __init__(self):
        self.config = EMOTION_AGENT_CONFIG["trigger_threshold"]
        self.cooldown = CooldownManager()
        self.state_machine = EmotionStateMachine()
    
    def should_trigger(
        self,
        dominant: DominantEmotion,
        user_speaking: bool = False
    ) -> bool:
        """
        判断是否应该触发Agent
        
        Args:
            dominant: 主导情绪
            user_speaking: 用户是否正在说话
        
        Returns:
            是否触发
        """
        # 用户正在说话时不打断
        if user_speaking:
            return False
        
        # 检查状态机是否允许触发
        if not self.state_machine.can_trigger():
            return False
        
        # 检查置信度阈值
        if dominant.avg_score < self.config["min_confidence"]:
            return False
        
        # 检查持续时间
        if dominant.duration < self.config["min_duration"]:
            return False
        
        # 检查稳定性
        if dominant.ratio < self.config["stability_ratio"]:
            return False
        
        # 检查冷却时间
        if not self.cooldown.can_trigger(dominant.category, dominant.avg_score):
            return False
        
        return True
    
    def record_trigger(self, category: str) -> None:
        """记录触发"""
        self.cooldown.record_trigger(category)
        self.state_machine.transition(self.state_machine.state.TRIGGERED)
```

- [ ] **Step 6.6: 提交**

```bash
git add backend/emotion/strategy/ backend/emotion/decision/
git commit -m "feat: implement strategy selector and decision engine

- StrategySelector: choose interaction strategy
- EmotionStateMachine: manage emotion states
- CooldownManager: handle trigger cooldown
- TriggerDecision: decide when to trigger agent"
```

---

### Task 7: 实现响应生成器

**Files:**
- Create: `backend/emotion/response/__init__.py`
- Create: `backend/emotion/response/templates.py`
- Create: `backend/emotion/response/generator.py`

- [ ] **Step 7.1: 定义模板管理器（迁移自emotion_agent.py）**

```python
# backend/emotion/response/__init__.py
from .generator import ResponseGenerator
from .templates import TemplateManager

__all__ = ["ResponseGenerator", "TemplateManager"]
```

```python
# backend/emotion/response/templates.py
import random
from typing import Dict, List, Optional

class TemplateManager:
    """模板管理器"""
    
    # 积极共情模板库
    POSITIVE_TEMPLATES: Dict[str, List[str]] = {
        "Happiness": [
            "看到{address_as}笑得这么开心，我也跟着高兴了",
            "{address_as}今天心情真好，有什么喜事吗",
            "您这笑容真暖人心"
        ],
        "Surprise": [
            "{address_as}您看起来很兴奋啊",
            "是有什么好消息吗",
            "您这么开心，跟我分享分享"
        ]
    }
    
    # 消极关怀模板库
    NEGATIVE_TEMPLATES: Dict[str, List[str]] = {
        "Sadness": [
            "{address_as}，我在这儿陪着您",
            "您是不是有点不开心",
            "有什么心事跟我说说"
        ],
        "Fear": [
            "{address_as}，别怕，我一直在",
            "没事的，您别紧张",
            "我陪着您，不用怕"
        ],
        "Anger": [
            "{address_as}，别生气，对身体不好",
            "您是不是遇到什么不顺心的事了",
            "消消气，跟我说说怎么回事"
        ],
        "Disgust": [
            "{address_as}，有什么不舒服的吗",
            "是不是哪里不对劲",
            "跟我说说，看看能不能帮上忙"
        ]
    }
    
    def get_template(self, emotion: str, strategy: str) -> Optional[str]:
        """
        获取模板
        
        Args:
            emotion: 情绪名称
            strategy: 策略类型
        
        Returns:
            模板字符串，无合适模板返回None
        """
        if strategy == "POSITIVE_EMPATHY":
            templates = self.POSITIVE_TEMPLATES.get(emotion, [])
        elif strategy == "NEGATIVE_CARE":
            templates = self.NEGATIVE_TEMPLATES.get(emotion, [])
        else:
            return None
        
        if not templates:
            return None
        
        return random.choice(templates)
```

- [ ] **Step 7.2: 实现响应生成器（迁移自emotion_agent.py）**

```python
# backend/emotion/response/generator.py
from typing import Dict, Optional
from .templates import TemplateManager
from backend.persona.models import Persona

class ResponseGenerator:
    """话术生成器"""
    
    def __init__(self):
        self.template_manager = TemplateManager()
    
    async def generate_response(
        self,
        emotion: str,
        strategy: str,
        persona: Persona,
        context: Dict
    ) -> str:
        """
        生成回复话术
        
        Args:
            emotion: 情绪名称
            strategy: 策略名称
            persona: Persona对象
            context: 上下文信息
        
        Returns:
            生成的话术
        """
        # 先尝试从模板生成
        template = self.template_manager.get_template(emotion, strategy)
        
        if template:
            return template.format(
                name=persona.name,
                address_as=persona.address_as
            )
        
        # 如果没有合适的模板，调用LLM生成
        return await self._generate_from_llm(
            emotion, strategy, persona, context
        )
    
    async def _generate_from_llm(
        self,
        emotion: str,
        strategy: str,
        persona: Persona,
        context: Dict
    ) -> str:
        """使用LLM生成话术"""
        from backend.llm.factory import LLMFactory
        
        llm = LLMFactory.create()
        
        # 构建prompt
        prompt = f"""你是「{persona.name}」，用简短温暖的话回应{persona.address_as}的{context.get('emotion_cn', emotion)}情绪。

要求：
- 语气：{persona.style}
- 性格：{persona.personality}
- 情绪强度：{context.get('intensity', '中等')}
- 持续时间：{context.get('duration', 0):.1f}秒

请生成一句话（不超过30字）："""
        
        try:
            response = await llm.generate(prompt, max_tokens=100)
            return response.strip()
        except Exception as e:
            print(f"[Agent] LLM generation failed: {e}")
            # LLM失败时返回兜底话术
            return f"我在这儿陪着{persona.address_as}"
```

- [ ] **Step 7.3: 提交**

```bash
git add backend/emotion/response/
git commit -m "feat: implement response generator with template fallback

- TemplateManager: manage positive/negative templates
- ResponseGenerator: generate responses with LLM fallback"
```

---

### Task 8: 实现情绪服务编排层

**Files:**
- Create: `backend/emotion/service.py`
- Modify: `backend/routers/emo.py`

- [ ] **Step 8.1: 实现情绪服务统一接口**

```python
# backend/emotion/service.py
from typing import Optional
import numpy as np
from backend.core.event_bus import EventBus
from .detector.manager import DetectorManager
from .analyzer.window import EmotionWindowAnalyzer
from .analyzer.pattern import PatternDetector
from .analyzer.models import EmotionData
from .strategy.selector import StrategySelector
from .decision.trigger import TriggerDecision
from .response.generator import ResponseGenerator
from .events import EmotionDetectedEvent, EmotionStateChangedEvent, AgentTriggeredEvent
from backend.persona.service import PersonaService
from backend.config import EMOTION_CN_MAP

class EmotionService:
    """情绪检测服务 - 统一编排层"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        
        # 初始化各组件
        self.detector = DetectorManager.get_instance()
        self.analyzer = EmotionWindowAnalyzer()
        self.pattern_detector = PatternDetector()
        self.strategy_selector = StrategySelector()
        self.decision = TriggerDecision()
        self.response_generator = ResponseGenerator()
        self.persona_service = PersonaService()
        
        # 订阅事件
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """设置事件处理器"""
        self.event_bus.subscribe("emotion.detected", self._on_emotion_detected)
        self.event_bus.subscribe("emotion.state_changed", self._on_state_changed)
    
    async def detect_and_respond(
        self,
        session_id: str,
        frame: np.ndarray,
        user_speaking: bool = False
    ) -> dict:
        """
        检测情绪并可能触发响应
        
        Args:
            session_id: 会话ID
            frame: 输入图像
            user_speaking: 用户是否在说话
        
        Returns:
            检测结果字典
        """
        # 1. 检测
        result = await self.detector.detect(frame)
        
        if not result or not result.faces:
            return {"faces": [], "timestamp": result.timestamp if result else 0}
        
        # 2. 处理第一个人脸（简化处理）
        face_data = result.faces[0]
        emotions_full = face_data["emotions"]
        primary_emotion = max(emotions_full, key=emotions_full.get)
        primary_score = emotions_full[primary_emotion]
        
        # 确定类别
        category = self._get_emotion_category(primary_emotion)
        
        # 3. 添加到分析器
        emotion_data = EmotionData(
            primary=primary_emotion,
            score=primary_score,
            category=category,
            timestamp=result.timestamp
        )
        self.analyzer.add_emotion(emotion_data)
        
        # 4. 发布检测事件
        await self.event_bus.publish(
            "emotion.detected",
            EmotionDetectedEvent(
                session_id=session_id,
                emotion=primary_emotion,
                score=primary_score,
                category=category,
                timestamp=result.timestamp
            )
        )
        
        # 5. 检查是否需要触发Agent
        dominant = self.analyzer.get_dominant_emotion()
        agent_message = None
        
        if dominant and self.decision.should_trigger(dominant, user_speaking):
            agent_message = await self._trigger_agent(session_id, dominant)
        
        # 6. 构建响应
        return {
            "faces": [{
                "box": face_data["box"],
                "emotions_full": emotions_full,
                "primary_emotion": primary_emotion,
                "emotion_cn": EMOTION_CN_MAP.get(primary_emotion, primary_emotion),
                "category": category,
                "intensity": self._calculate_intensity(primary_score),
                "trend": self.pattern_detector.detect_change_pattern(self.analyzer)
            }],
            "timestamp": result.timestamp,
            "agent_message": agent_message
        }
    
    async def _trigger_agent(self, session_id: str, dominant) -> str:
        """触发Agent生成响应"""
        # 选择策略
        strategy = self.strategy_selector.select_strategy(dominant)
        
        # 获取Persona
        persona = self.persona_service.get(session_id)
        
        # 构建上下文
        context = {
            "emotion": dominant.emotion,
            "emotion_cn": EMOTION_CN_MAP.get(dominant.emotion, dominant.emotion),
            "intensity": "强烈" if dominant.avg_score > 0.7 else "中等",
            "duration": dominant.duration
        }
        
        # 生成话术
        message = await self.response_generator.generate_response(
            emotion=dominant.emotion,
            strategy=strategy,
            persona=persona,
            context=context
        )
        
        # 记录触发
        self.decision.record_trigger(dominant.category)
        
        # 发布触发事件
        await self.event_bus.publish(
            "agent.triggered",
            AgentTriggeredEvent(
                session_id=session_id,
                strategy=strategy,
                message=message,
                emotion_context=context
            )
        )
        
        print(f"[Agent] Triggered: {strategy} -> {message}")
        return message
    
    def _get_emotion_category(self, emotion: str) -> str:
        """获取情绪类别"""
        from backend.config import EMOTION_CATEGORIES
        for category, emotions in EMOTION_CATEGORIES.items():
            if emotion in emotions:
                return category
        return "NEUTRAL"
    
    def _calculate_intensity(self, score: float) -> str:
        """计算强度"""
        if score > 0.7:
            return "强烈"
        elif score > 0.5:
            return "中等"
        else:
            return "轻微"
    
    async def _on_emotion_detected(self, event: EmotionDetectedEvent):
        """处理情绪检测事件"""
        # 可以在这里添加日志、统计等逻辑
        pass
    
    async def _on_state_changed(self, event: EmotionStateChangedEvent):
        """处理情绪状态变化事件"""
        # 可以在这里添加通知、记录等逻辑
        pass
```

- [ ] **Step 8.2: 简化Router层**

```python
# 修改 backend/routers/emo.py
from fastapi import APIRouter, HTTPException
from backend.models_schemas.emo import EmoDetectRequest, EmoDetectionResult
from backend.core.event_bus import EventBus
from backend.emotion.service import EmotionService
import base64
import cv2
import numpy as np

router = APIRouter()

# 全局实例
_event_bus = EventBus()
_emotion_service = EmotionService(_event_bus)

@router.post("/detect", response_model=EmoDetectionResult)
async def detect_emotion(req: EmoDetectRequest):
    """单帧情绪检测"""
    try:
        # 解码base64图像
        img_data = base64.b64decode(req.frame.split(",")[-1] if "," in req.frame else req.frame)
        arr = np.frombuffer(img_data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        # 调用服务
        result = await _emotion_service.detect_and_respond(
            session_id=req.session_id,
            frame=frame,
            user_speaking=False
        )
        
        return EmoDetectionResult(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@router.get("/model-info")
async def get_model_info():
    """获取模型信息"""
    return _emotion_service.detector.get_model_info()
```

- [ ] **Step 8.3: 运行测试（手动）**

```bash
# 启动后端
cd backend
uvicorn main:app --reload --port 8000
```

访问: http://localhost:8000/api/emo/model-info

Expected: 返回模型信息JSON

- [ ] **Step 8.4: 提交**

```bash
git add backend/emotion/service.py backend/routers/emo.py
git commit -m "feat: implement emotion service orchestration layer

- EmotionService: unified emotion detection workflow
- Simplified emo router to delegate to service
- Event-driven architecture integrated"
```

---

## 阶段3: 对话系统重构

### Task 9: 实现LLM Provider抽象

**Files:**
- Create: `backend/llm/__init__.py`
- Create: `backend/llm/base.py`
- Create: `backend/llm/dashscope.py` (迁移自 services/llm.py)
- Create: `backend/llm/factory.py`

- [ ] **Step 9.1: 定义LLM Provider抽象接口**

```python
# backend/llm/__init__.py
from .base import LLMProvider
from .dashscope import DashScopeProvider
from .factory import LLMFactory

__all__ = ["LLMProvider", "DashScopeProvider", "LLMFactory"]
```

```python
# backend/llm/base.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """LLM提供商抽象接口"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 输入提示词
            max_tokens: 最大token数
            temperature: 温度参数
        
        Returns:
            生成的文本
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """检查是否已配置"""
        pass
```

- [ ] **Step 9.2: 迁移DashScope实现**

```python
# backend/llm/dashscope.py
import aiohttp
import re
from .base import LLMProvider
from backend.config import DASHSCOPE_API_KEY, DASHSCOPE_API_URL, LLM_MODEL

class DashScopeProvider(LLMProvider):
    """通义千问LLM实现"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.api_url = DASHSCOPE_API_URL
        self.model = LLM_MODEL
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """生成文本"""
        if not self.is_configured():
            raise RuntimeError("DashScope API Key not configured")
        
        payload = {
            "model": self.model,
            "input": {"prompt": prompt},
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": temperature
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                
                if "output" in data and "text" in data["output"]:
                    return data["output"]["text"]
                
                if "code" in data:
                    raise RuntimeError(f"{data.get('code')}: {data.get('message')}")
                
                raise RuntimeError(f"Unknown response: {await resp.text()[:200]}")
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.api_key and not self.api_key.startswith("sk-YOUR"))
    
    def sanitize_input(self, text: str, max_len: int = 500) -> str:
        """清理输入"""
        if not isinstance(text, str):
            return ""
        text = re.sub(r'[<>]', '', text)
        text = text.replace('\n', ' ').replace('\r', ' ')
        return text.strip()[:max_len]
```

- [ ] **Step 9.3: 实现Provider工厂**

```python
# backend/llm/factory.py
from .base import LLMProvider
from .dashscope import DashScopeProvider

class LLMFactory:
    """LLM Provider工厂"""
    
    _instance: LLMProvider = None
    
    @classmethod
    def create(cls, provider_name: str = "dashscope") -> LLMProvider:
        """
        创建Provider实例
        
        Args:
            provider_name: 提供商名称
        
        Returns:
            Provider实例
        """
        if provider_name == "dashscope":
            if cls._instance is None:
                cls._instance = DashScopeProvider()
            return cls._instance
        # elif provider_name == "openai":
        #     return OpenAIProvider()
        
        raise ValueError(f"Unknown provider: {provider_name}")
    
    @classmethod
    def reset(cls):
        """重置单例（用于测试）"""
        cls._instance = None
```

- [ ] **Step 9.4: 提交**

```bash
git add backend/llm/
git commit -m "feat: implement LLM provider abstraction

- LLMProvider: abstract interface
- DashScopeProvider: migrated from services/llm.py
- LLMFactory: provider factory pattern

TODO: Add OpenAI provider support"
```

---

### Task 10: 实现Persona服务

**Files:**
- Create: `backend/persona/__init__.py`
- Create: `backend/persona/models.py`
- Create: `backend/persona/service.py`

- [ ] **Step 10.1: 定义Persona数据模型**

```python
# backend/persona/__init__.py
from .models import Persona
from .service import PersonaService

__all__ = ["Persona", "PersonaService"]
```

```python
# backend/persona/models.py
from pydantic import BaseModel
from typing import Optional

class Persona(BaseModel):
    """Persona数据模型"""
    name: str = "颐"
    gender: str = "neutral"
    personality: str = "温暖、耐心、有同理心"
    address_as: str = "爷爷"
    style: str = "句子短，不用网络用语，50字内"
    custom_instructions: str = "主动关心身体和饮食"
    
    class Config:
        from_attributes = True
```

- [ ] **Step 10.2: 实现Persona服务（迁移自services/memory.py）**

```python
# backend/persona/service.py
from typing import Dict
from sqlalchemy.orm import Session
from .models import Persona
from backend.database.models import PersonaModel
from backend.database.connection import SessionLocal
from backend.config import DEFAULT_PERSONA

class PersonaService:
    """Persona管理服务"""
    
    def get(self, session_id: str = "default") -> Persona:
        """
        获取Persona
        
        Args:
            session_id: 会话ID
        
        Returns:
            Persona对象
        """
        db = SessionLocal()
        try:
            persona_model = db.query(PersonaModel).filter(
                PersonaModel.session_id == session_id
            ).first()
            
            if persona_model:
                return Persona(
                    name=persona_model.name,
                    gender=persona_model.gender,
                    personality=persona_model.personality,
                    address_as=persona_model.address_as,
                    style=persona_model.style,
                    custom_instructions=persona_model.custom_instructions
                )
            else:
                # 返回默认Persona
                return Persona(**DEFAULT_PERSONA)
        finally:
            db.close()
    
    def update(self, session_id: str, updates: Dict) -> Persona:
        """
        更新Persona
        
        Args:
            session_id: 会话ID
            updates: 更新字段
        
        Returns:
            更新后的Persona
        """
        db = SessionLocal()
        try:
            persona_model = db.query(PersonaModel).filter(
                PersonaModel.session_id == session_id
            ).first()
            
            if not persona_model:
                # 创建新Persona
                persona_data = {**DEFAULT_PERSONA, **updates}
                persona_model = PersonaModel(
                    session_id=session_id,
                    **persona_data
                )
                db.add(persona_model)
            else:
                # 更新现有Persona
                for key, value in updates.items():
                    if hasattr(persona_model, key):
                        setattr(persona_model, key, value)
            
            db.commit()
            db.refresh(persona_model)
            
            return Persona(
                name=persona_model.name,
                gender=persona_model.gender,
                personality=persona_model.personality,
                address_as=persona_model.address_as,
                style=persona_model.style,
                custom_instructions=persona_model.custom_instructions
            )
        finally:
            db.close()
    
    def reset(self, session_id: str) -> Persona:
        """
        重置为默认Persona
        
        Args:
            session_id: 会话ID
        
        Returns:
            默认Persona
        """
        db = SessionLocal()
        try:
            # 删除现有Persona
            db.query(PersonaModel).filter(
                PersonaModel.session_id == session_id
            ).delete()
            db.commit()
            
            return Persona(**DEFAULT_PERSONA)
        finally:
            db.close()
```

- [ ] **Step 10.3: 提交**

```bash
git add backend/persona/
git commit -m "feat: implement persona service with SQLite persistence

- Persona: pydantic data model
- PersonaService: CRUD operations with database
- Migrated from services/memory.py"
```

---

### Task 11: 实现对话历史持久化

**Files:**
- Create: `backend/conversation/__init__.py`
- Create: `backend/conversation/models.py`
- Create: `backend/conversation/history.py`

- [ ] **Step 11.1: 定义对话数据模型**

```python
# backend/conversation/__init__.py
from .models import Message, ChatContext
from .history import HistoryStore
from .manager import ConversationManager

__all__ = ["Message", "ChatContext", "HistoryStore", "ConversationManager"]
```

```python
# backend/conversation/models.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Message(BaseModel):
    """对话消息"""
    role: str  # 'user' | 'assistant'
    content: str
    emotion: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ChatContext(BaseModel):
    """对话上下文"""
    session_id: str
    persona: dict
    recent_history: List[Message]
    memories: List[str]
```

- [ ] **Step 11.2: 实现历史存储**

```python
# backend/conversation/history.py
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from .models import Message
from backend.database.models import ConversationHistory
from backend.database.connection import SessionLocal

class HistoryStore:
    """对话历史存储"""
    
    def save(
        self,
        session_id: str,
        user_input: str,
        assistant_reply: str,
        emotion: str = None
    ) -> None:
        """
        保存对话
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
            assistant_reply: 助手回复
            emotion: 情绪标签
        """
        db = SessionLocal()
        try:
            # 保存用户消息
            user_msg = ConversationHistory(
                session_id=session_id,
                role="user",
                content=user_input,
                emotion=emotion
            )
            db.add(user_msg)
            
            # 保存助手回复
            assistant_msg = ConversationHistory(
                session_id=session_id,
                role="assistant",
                content=assistant_reply
            )
            db.add(assistant_msg)
            
            db.commit()
        finally:
            db.close()
    
    def get_recent(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Message]:
        """
        获取最近对话
        
        Args:
            session_id: 会话ID
            limit: 最大条数
        
        Returns:
            消息列表
        """
        db = SessionLocal()
        try:
            records = db.query(ConversationHistory).filter(
                ConversationHistory.session_id == session_id
            ).order_by(
                ConversationHistory.timestamp.desc()
            ).limit(limit).all()
            
            # 反转顺序（从旧到新）
            records.reverse()
            
            return [
                Message(
                    role=record.role,
                    content=record.content,
                    emotion=record.emotion,
                    timestamp=record.timestamp
                )
                for record in records
            ]
        finally:
            db.close()
    
    def get_by_date_range(
        self,
        session_id: str,
        start: datetime,
        end: datetime
    ) -> List[Message]:
        """按时间范围查询"""
        db = SessionLocal()
        try:
            records = db.query(ConversationHistory).filter(
                ConversationHistory.session_id == session_id,
                ConversationHistory.timestamp >= start,
                ConversationHistory.timestamp <= end
            ).order_by(
                ConversationHistory.timestamp.asc()
            ).all()
            
            return [
                Message(
                    role=record.role,
                    content=record.content,
                    emotion=record.emotion,
                    timestamp=record.timestamp
                )
                for record in records
            ]
        finally:
            db.close()
    
    def clear_session(self, session_id: str) -> None:
        """清空会话历史"""
        db = SessionLocal()
        try:
            db.query(ConversationHistory).filter(
                ConversationHistory.session_id == session_id
            ).delete()
            db.commit()
        finally:
            db.close()
```

- [ ] **Step 11.3: 提交**

```bash
git add backend/conversation/models.py backend/conversation/history.py
git commit -m "feat: implement conversation history persistence

- Message: conversation message model
- HistoryStore: SQLite-backed history storage
- Support recent query and date range query"
```

---

### Task 12: 实现对话管理器

**Files:**
- Create: `backend/conversation/context.py`
- Create: `backend/conversation/manager.py`
- Modify: `backend/routers/chat.py`

- [ ] **Step 12.1: 实现上下文构建器**

```python
# backend/conversation/context.py
from typing import Dict, List
from .models import ChatContext, Message
from .history import HistoryStore
from backend.persona.service import PersonaService
from datetime import datetime

class ContextBuilder:
    """上下文构建器"""
    
    def __init__(self):
        self.history_store = HistoryStore()
        self.persona_service = PersonaService()
    
    async def build(self, session_id: str) -> ChatContext:
        """
        构建对话上下文
        
        Args:
            session_id: 会话ID
        
        Returns:
            ChatContext对象
        """
        # 获取Persona
        persona = self.persona_service.get(session_id)
        
        # 获取最近对话历史
        recent_history = self.history_store.get_recent(session_id, limit=10)
        
        # 获取记忆（TODO: 从Memory表查询）
        memories = []
        
        return ChatContext(
            session_id=session_id,
            persona=persona.model_dump(),
            recent_history=recent_history,
            memories=memories
        )
    
    def get_time_context(self) -> str:
        """获取时间上下文"""
        now = datetime.now()
        hour = now.hour
        
        if hour < 6:
            time_of_day = "深夜"
        elif hour < 9:
            time_of_day = "早晨"
        elif hour < 12:
            time_of_day = "上午"
        elif hour < 14:
            time_of_day = "中午"
        elif hour < 18:
            time_of_day = "下午"
        elif hour < 21:
            time_of_day = "傍晚"
        else:
            time_of_day = "晚上"
        
        return f"当前时间：{time_of_day}（{hour}点），根据时间调整问候和关心内容。"
```

- [ ] **Step 12.2: 实现对话管理器**

```python
# backend/conversation/manager.py
from .context import ContextBuilder
from .history import HistoryStore
from .models import ChatContext
from backend.llm.factory import LLMFactory
from backend.llm.base import LLMProvider
import os

class ConversationManager:
    """对话管理器 - 核心调度"""
    
    def __init__(self):
        self.llm: LLMProvider = LLMFactory.create()
        self.context_builder = ContextBuilder()
        self.history_store = HistoryStore()
    
    async def chat(self, session_id: str, user_input: str) -> dict:
        """
        处理对话
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
        
        Returns:
            包含reply和emotion的字典
        """
        # 1. 构建上下文
        context = await self.context_builder.build(session_id)
        
        # 2. 构建prompt
        prompt = self._build_prompt(user_input, context)
        
        # 3. 调用LLM
        reply = await self.llm.generate(prompt, max_tokens=200)
        
        # 4. 保存历史
        self.history_store.save(session_id, user_input, reply)
        
        # 5. 分析情绪（简单处理，实际可调用emotion analyzer）
        emotion = "neutral"
        
        return {
            "reply": reply,
            "emotion": emotion
        }
    
    def _build_prompt(self, user_input: str, context: ChatContext) -> str:
        """构建prompt"""
        persona = context.persona
        
        # 加载模板
        template_path = os.path.join(
            os.path.dirname(__file__),
            "../prompts/persona_template.txt"
        )
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            # 兜底模板
            template = """你是「{name}」，一个专门为独居老人设计的AI陪伴助手。

【角色限定】：
1. 身份：{personality}，像子女一样关心老人
2. 称呼：{address_as}
3. 语言风格：{style}
4. 行为准则：{custom_instructions}

{time_context}

{memory_context}

【当前对话】：
老人说：「{user_input}」

请回复："""
        
        # 构建记忆上下文
        memory_context = ""
        if context.recent_history:
            memory_context = "\n\n【最近对话】：\n"
            for msg in context.recent_history[-5:]:
                role_name = "老人" if msg.role == "user" else persona["name"]
                memory_context += f"{role_name}: {msg.content}\n"
        
        # 填充模板
        prompt = template.format(
            name=persona["name"],
            personality=persona["personality"],
            address_as=persona["address_as"],
            style=persona["style"],
            custom_instructions=persona["custom_instructions"],
            time_context=self.context_builder.get_time_context(),
            memory_context=memory_context,
            user_input=user_input
        )
        
        return prompt
```

- [ ] **Step 12.3: 简化Chat Router**

```python
# 修改 backend/routers/chat.py
from fastapi import APIRouter, HTTPException
from backend.models import ChatRequest, ChatResponse
from backend.conversation.manager import ConversationManager

router = APIRouter()

# 全局管理器
_conversation_manager = ConversationManager()

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """对话接口"""
    try:
        result = await _conversation_manager.chat(
            session_id=req.session_id,
            user_input=req.user_input
        )
        
        return ChatResponse(
            reply=result["reply"],
            emotion=result["emotion"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
```

- [ ] **Step 12.4: 提交**

```bash
git add backend/conversation/ backend/routers/chat.py
git commit -m "feat: implement conversation manager

- ContextBuilder: build chat context with persona and history
- ConversationManager: orchestrate chat workflow
- Simplified chat router to delegate to manager"
```

---

## 阶段4: 集成测试与Node.js网关调整

### Task 13: 调整Node.js为纯API网关

**Files:**
- Modify: `server.js`
- Modify: `package.json`
- Remove: `modules/llm.js`

- [ ] **Step 13.1: 安装http-proxy-middleware**

```bash
cd /Users/lidashuai5/Documents/LLM/yidemo项目包/yidemo
npm install http-proxy-middleware --save
```

- [ ] **Step 13.2: 修改server.js为纯代理**

```javascript
// server.js
#!/usr/bin/env node
const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3000;
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

app.use(express.json());

// 静态文件服务
app.use(express.static(path.join(__dirname, 'public')));

// API代理到FastAPI后端
app.use('/api', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  onProxyReq: (proxyReq, req, res) => {
    console.log(`[Proxy] ${req.method} ${req.url} -> ${BACKEND_URL}${req.url}`);
  },
  onError: (err, req, res) => {
    console.error('[Proxy Error]', err);
    res.status(500).json({ error: 'Backend proxy error' });
  }
}));

// 前端路由
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend/index.html'));
});

app.listen(PORT, () => {
  console.log(`椿萱·颐 API网关已启动: http://localhost:${PORT}`);
  console.log(`代理后端: ${BACKEND_URL}`);
});
```

- [ ] **Step 13.3: 删除废弃的LLM模块**

```bash
rm modules/llm.js
```

- [ ] **Step 13.4: 更新package.json**

```json
{
  "name": "yidemo",
  "version": "2.0.0",
  "description": "椿萱·颐 - AI陪伴设备模拟器（API网关）",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "node --watch server.js"
  },
  "dependencies": {
    "express": "^4.18.0",
    "http-proxy-middleware": "^2.0.0"
  }
}
```

- [ ] **Step 13.5: 测试API代理**

```bash
# 终端1: 启动FastAPI后端
cd backend
uvicorn main:app --reload --port 8000

# 终端2: 启动Node.js网关
npm start
```

访问: http://localhost:3000/api/config/status

Expected: 返回配置状态JSON（代理成功）

- [ ] **Step 13.6: 提交**

```bash
git add server.js package.json
git rm modules/llm.js
git commit -m "refactor: convert Node.js server to pure API gateway

- Proxy all /api requests to FastAPI backend
- Remove LLM logic from Node.js
- Keep static file serving"
```

---

### Task 14: 端到端测试

**Files:**
- Create: `tests/integration/test_emotion_flow.py`
- Create: `tests/integration/test_chat_flow.py`

- [ ] **Step 14.1: 编写情绪检测集成测试**

```python
# tests/integration/test_emotion_flow.py
import pytest
import numpy as np
import cv2
from backend.core.event_bus import EventBus
from backend.emotion.service import EmotionService

@pytest.mark.asyncio
async def test_emotion_detection_flow():
    """测试情绪检测完整流程"""
    # 创建事件总线和服务
    event_bus = EventBus()
    service = EmotionService(event_bus)
    
    # 创建测试图像（白色背景）
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # 执行检测
    result = await service.detect_and_respond(
        session_id="test_session",
        frame=frame,
        user_speaking=False
    )
    
    # 验证结果结构
    assert "faces" in result
    assert "timestamp" in result
    assert isinstance(result["faces"], list)

@pytest.mark.asyncio
async def test_agent_trigger():
    """测试Agent触发逻辑"""
    event_bus = EventBus()
    service = EmotionService(event_bus)
    
    # 创建happy表情图像（需要真实图像或mock）
    # 这里简化处理，实际需要准备测试数据
    pass
```

- [ ] **Step 14.2: 编写对话管理集成测试**

```python
# tests/integration/test_chat_flow.py
import pytest
from backend.conversation.manager import ConversationManager

@pytest.mark.asyncio
async def test_chat_flow():
    """测试对话完整流程"""
    manager = ConversationManager()
    
    # 执行对话
    result = await manager.chat(
        session_id="test_session",
        user_input="今天天气不错"
    )
    
    # 验证结果
    assert "reply" in result
    assert "emotion" in result
    assert isinstance(result["reply"], str)
    assert len(result["reply"]) > 0

@pytest.mark.asyncio
async def test_history_persistence():
    """测试历史持久化"""
    manager = ConversationManager()
    
    # 发送多条消息
    await manager.chat("test_session", "你好")
    await manager.chat("test_session", "我今天很开心")
    
    # 验证历史保存
    history = manager.history_store.get_recent("test_session", limit=10)
    assert len(history) >= 4  # 至少2轮对话（4条消息）
```

- [ ] **Step 14.3: 运行集成测试**

```bash
pytest tests/integration/ -v
```

Expected: 部分测试PASS（需要真实数据的测试可能SKIP）

- [ ] **Step 14.4: 提交**

```bash
git add tests/integration/
git commit -m "test: add integration tests for emotion and chat flows"
```

---

### Task 15: 文档更新和清理

**Files:**
- Create: `docs/refactor-summary.md`
- Update: `README.md`
- Remove: `backend/services/emotion_agent.py`
- Remove: `backend/services/emo_detector.py`
- Remove: `backend/services/llm.py`

- [ ] **Step 15.1: 编写重构总结文档**

```markdown
# docs/refactor-summary.md

# 情绪检测与对话系统重构总结

## 完成时间
2026-06-09

## 重构内容

### 情绪检测系统
- ✅ 拆分 `emotion_agent.py` (430行) 为7个独立模块
- ✅ 实现检测器抽象接口
- ✅ 引入情绪状态机
- ✅ 事件驱动架构

### 对话系统
- ✅ LLM Provider抽象
- ✅ 对话管理器
- ✅ 历史持久化到SQLite
- ✅ Persona服务独立

### 基础设施
- ✅ 事件总线（内存实现）
- ✅ 数据库表扩展（4张新表）
- ✅ Node.js转为纯API网关

## 架构对比

**重构前**:
- 单体文件，紧耦合
- 全局变量管理状态
- 代码重复

**重构后**:
- 模块解耦，职责清晰
- 事件驱动，异步处理
- 抽象接口，易扩展

## 待办事项
- [ ] 事件总线迁移到Redis
- [ ] 数据库迁移到MySQL
- [ ] 添加OpenAI Provider支持
- [ ] 完善集成测试
```

- [ ] **Step 15.2: 更新README**

在README.md中添加架构说明章节（略）

- [ ] **Step 15.3: 删除废弃文件**

```bash
git rm backend/services/emotion_agent.py
git rm backend/services/emo_detector.py
git rm backend/services/llm.py
```

- [ ] **Step 15.4: 最终提交**

```bash
git add docs/refactor-summary.md README.md
git commit -m "docs: add refactor summary and cleanup deprecated files

Refactor complete:
- Emotion detection system modularized
- Conversation system with history persistence
- Event-driven architecture
- Node.js as pure API gateway

Removed deprecated files:
- backend/services/emotion_agent.py
- backend/services/emo_detector.py
- backend/services/llm.py"
```

---

## 执行方案选择

计划完成并保存到 `docs/superpowers/plans/2026-06-09-emotion-chat-refactor.md`。

**两种执行方式：**

**1. Subagent-Driven (推荐)** - 每个Task派发一个新的子agent执行，主agent在task之间进行审查，快速迭代

**2. Inline Execution** - 在当前会话中按顺序执行所有task，批量执行并在检查点处暂停审查

**选择哪种方式？**
