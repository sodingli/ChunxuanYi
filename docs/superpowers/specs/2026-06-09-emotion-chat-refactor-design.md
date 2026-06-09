# 情绪检测与对话系统架构重构设计文档

**日期**: 2026-06-09  
**版本**: 1.0  
**状态**: 待审核

---

## 一、概述

### 1.1 目标

对「椿萱·颐」项目的情绪检测和对话系统进行架构重构，实现：
- 解耦模块职责，提升代码可维护性
- 引入事件驱动架构，支持异步处理
- 抽象核心接口，支持未来扩展（多模型、多LLM提供商）
- 统一数据持久化方案

### 1.2 当前问题

**情绪检测系统**:
- `emotion_agent.py` 430行，4个类耦合在一起
- 全局变量管理状态（`_emotion_agent`字典）
- 情绪分类逻辑重复（`_get_emotion_category`出现3次）
- 缺乏状态管理机制

**对话系统**:
- Node.js (`modules/llm.js`) 和 Python (`backend/services/llm.py`) 重复实现
- 配置管理混乱（运行时变量 + 数据库 + 环境变量）
- 缺乏会话管理和对话历史持久化
- Persona管理分散在多处

### 1.3 设计原则

- **单一职责**: 每个模块只负责一件事
- **依赖倒置**: 依赖抽象接口而非具体实现
- **事件驱动**: 解耦检测与响应
- **可测试性**: 所有模块支持单元测试
- **向后兼容**: API路径保持不变

---

## 二、整体架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────┐
│                Frontend Layer                        │
│  (frontend/index.html, public/js/*)                 │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP
┌─────────────────▼───────────────────────────────────┐
│          Node.js API Gateway (保留)                  │
│  - Express server.js                                │
│  - 路由转发到 FastAPI                                │
│  - 静态文件服务                                       │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP Proxy
┌─────────────────▼───────────────────────────────────┐
│              FastAPI Backend (Python)                │
│  - 核心业务逻辑                                       │
│  - 情绪检测、对话管理                                 │
└─────────────────┬───────────────────────────────────┘
                  │
    ┌─────────────┼──────────────┐
    │             │              │
┌───▼────┐  ┌────▼──────┐  ┌───▼─────────┐
│ 情绪    │  │ 对话       │  │ 数据持久化   │
│ 检测    │  │ 管理       │  │ SQLite       │
│ 服务    │  │ 服务       │  │ (→MySQL)     │
└───┬────┘  └────┬──────┘  └──────────────┘
    │            │
    │    ┌───────▼──────────┐
    │    │ LLM Provider      │
    │    │ (抽象接口)         │
    │    │ - DashScope       │
    │    │ - (OpenAI...)     │
    │    └──────────────────┘
    │
┌───▼──────────────────┐
│ 事件总线 (EventBus)   │
│ - 内存实现            │
│ - TODO: Redis持久化   │
└─────────────────────┘
```

### 2.2 技术栈保持

- **前端**: HTML/JS (保持不变)
- **API网关**: Node.js Express (保留，转发到FastAPI)
- **后端**: Python FastAPI
- **数据库**: SQLite → MySQL (渐进迁移)
- **事件总线**: 内存 → Redis (待办)

---

## 三、情绪检测系统重构

### 3.1 模块拆分

**当前结构**:
```
backend/services/
  emo_detector.py          # 检测器
  emotion_agent.py         # 4个类混在一起
```

**重构后结构**:
```
backend/
  emotion/
    __init__.py
    
    # 检测器层
    detector/
      __init__.py
      base.py              # 抽象接测器接口
      emo_affectnet.py     # EMO-AffectNet实现
      manager.py           # 检测器管理器（单例）
    
    # 分析层
    analyzer/
      __init__.py
      window.py            # 滑动窗口分析器
      pattern.py           # 情绪模式检测
      models.py            # 数据模型
    
    # 策略层
    strategy/
      __init__.py
      selector.py          # 策略选择器
      types.py             # 策略类型定义
    
    # 决策层
    decision/
      __init__.py
      trigger.py           # 触发决策引擎
      state_machine.py     # 情绪状态机
      cooldown.py          # 冷却管理
    
    # 响应层
    response/
      __init__.py
      generator.py         # 话术生成器
      templates.py         # 模板管理
    
    # 事件定义
    events.py
    
    # 服务编排
    service.py             # 对外统一接口
```

### 3.2 核心组件设计

#### 3.2.1 检测器抽象接口

```python
# backend/emotion/detector/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import numpy as np

class DetectionResult:
    faces: List[Dict]
    timestamp: float

class EmotionDetector(ABC):
    """情绪检测器抽象基类"""
    
    @abstractmethod
    async def detect(self, frame: np.ndarray) -> Optional[DetectionResult]:
        """检测情绪"""
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

**Why**: 支持未来替换不同模型（如DeepFace、FER等）而不影响上层逻辑

**How to apply**: 所有检测器实现此接口，通过工厂模式创建

#### 3.2.2 情绪状态机

```python
# backend/emotion/decision/state_machine.py
from enum import Enum

class EmotionState(Enum):
    IDLE = "idle"                    # 空闲
    DETECTING = "detecting"          # 检测中
    STABLE = "stable"                # 情绪稳定
    TRIGGERED = "triggered"          # 已触发响应
    COOLDOWN = "cooldown"            # 冷却期

class EmotionStateMachine:
    """管理情绪状态转换"""
    
    def transition(self, event: str) -> bool:
        """状态转换"""
        pass
    
    def can_trigger(self) -> bool:
        """是否可以触发Agent"""
        pass
```

**Why**: 明确状态转换逻辑，避免隐式状态管理

**How to apply**: 在决策引擎中使用，确保触发逻辑清晰可追踪

#### 3.2.3 事件驱动架构

```python
# backend/emotion/events.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class EmotionDetectedEvent:
    """单帧情绪检测完成"""
    session_id: str
    emotion: str
    score: float
    category: str
    timestamp: float

@dataclass
class EmotionStateChangedEvent:
    """主导情绪状态变化"""
    session_id: str
    old_emotion: Optional[str]
    new_emotion: str
    stability: float
    duration: float

@dataclass
class AgentTriggeredEvent:
    """Agent响应触发"""
    session_id: str
    strategy: str
    message: str
    emotion_context: dict
```

```python
# backend/core/event_bus.py (新建)
from typing import Callable, Dict, List
import asyncio

class EventBus:
    """内存事件总线 (TODO: 迁移到Redis)"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        pass
    
    async def publish(self, event_type: str, event_data):
        """发布事件"""
        pass
```

**Why**: 解耦检测、分析、决策、响应各模块

**How to apply**: 
- 检测器发布 `EmotionDetectedEvent`
- 分析器订阅并发布 `EmotionStateChangedEvent`
- 决策引擎订阅并发布 `AgentTriggeredEvent`

#### 3.2.4 服务编排层

```python
# backend/emotion/service.py
class EmotionService:
    """情绪检测服务统一入口"""
    
    def __init__(self, event_bus: EventBus):
        self.detector = DetectorManager.get_instance()
        self.analyzer = EmotionAnalyzer()
        self.decision = DecisionEngine()
        self.response = ResponseGenerator()
        self.event_bus = event_bus
        
        # 订阅事件
        self._setup_event_handlers()
    
    async def detect_and_respond(
        self, 
        session_id: str, 
        frame: np.ndarray
    ) -> DetectionResponse:
        """检测并可能触发响应"""
        # 1. 检测
        result = await self.detector.detect(frame)
        
        # 2. 发布事件（后续流程通过事件驱动）
        await self.event_bus.publish(
            "emotion.detected", 
            EmotionDetectedEvent(...)
        )
        
        # 3. 返回检测结果
        return result
```

**Why**: 统一对外接口，隐藏内部复杂性

**How to apply**: Router层只调用 `EmotionService`

### 3.3 重构优势

1. **可测试性**: 每个组件独立测试
2. **可扩展性**: 添加新检测器/策略只需实现接口
3. **可维护性**: 职责清晰，代码量减少
4. **异步处理**: 事件总线支持非阻塞响应

---

## 四、对话系统重构

### 4.1 模块拆分

**当前结构**:
```
server.js                 # Node.js Express
modules/
  llm.js                  # Node.js LLM调用
  memory-store.js         # 记忆管理
backend/services/
  llm.py                  # Python LLM调用（重复）
backend/routers/
  chat.py                 # 对话路由
```

**重构后结构**:
```
server.js                 # 保留，仅做API网关
modules/                  # 废弃LLM调用，保留其他工具函数

backend/
  conversation/
    __init__.py
    manager.py            # 对话管理器
    session.py            # 会话状态管理
    context.py            # 上下文构建器
    history.py            # 对话历史持久化
    models.py             # 数据模型
  
  persona/
    __init__.py
    service.py            # Persona CRUD
    models.py             # Persona数据模型
    defaults.py           # 默认配置
  
  llm/
    __init__.py
    base.py               # LLM Provider抽象接口
    dashscope.py          # DashScope实现
    factory.py            # Provider工厂
    config.py             # LLM配置管理
  
  database/
    __init__.py
    connection.py         # 数据库连接管理
    models.py             # SQLAlchemy模型
    migrations/           # 数据库迁移
```

### 4.2 核心组件设计

#### 4.2.1 LLM Provider抽象

```python
# backend/llm/base.py
from abc import ABC, abstractmethod
from typing import Optional

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
        """生成文本"""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """检查是否已配置"""
        pass
```

```python
# backend/llm/dashscope.py
class DashScopeProvider(LLMProvider):
    """通义千问实现"""
    
    async def generate(self, prompt: str, **kwargs) -> str:
        # 从 backend/services/llm.py 迁移实现
        pass
```

```python
# backend/llm/factory.py
class LLMFactory:
    """LLM Provider工厂"""
    
    @staticmethod
    def create(provider_name: str = "dashscope") -> LLMProvider:
        if provider_name == "dashscope":
            return DashScopeProvider()
        # elif provider_name == "openai":
        #     return OpenAIProvider()
        raise ValueError(f"Unknown provider: {provider_name}")
```

**Why**: 支持未来切换LLM提供商（OpenAI、本地模型等）

**How to apply**: 所有LLM调用通过工厂创建Provider

#### 4.2.2 对话管理器

```python
# backend/conversation/manager.py
class ConversationManager:
    """对话管理器 - 核心调度"""
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        persona_service: PersonaService,
        history_store: HistoryStore
    ):
        self.llm = llm_provider
        self.persona_service = persona_service
        self.history = history_store
    
    async def chat(
        self, 
        session_id: str, 
        user_input: str
    ) -> ChatResponse:
        """处理对话"""
        # 1. 加载会话上下文
        context = await self._build_context(session_id)
        
        # 2. 构建prompt
        prompt = self._build_prompt(user_input, context)
        
        # 3. 调用LLM
        reply = await self.llm.generate(prompt)
        
        # 4. 保存历史
        await self.history.save(session_id, user_input, reply)
        
        # 5. 返回响应
        return ChatResponse(reply=reply)
    
    async def _build_context(self, session_id: str) -> dict:
        """构建上下文"""
        persona = self.persona_service.get(session_id)
        history = await self.history.get_recent(session_id, limit=10)
        memories = await self._get_memories(session_id)
        
        return {
            "persona": persona,
            "history": history,
            "memories": memories,
            "time_context": self._get_time_context()
        }
```

**Why**: 统一管理对话流程，封装复杂性

**How to apply**: Router层只调用 `ConversationManager.chat()`

#### 4.2.3 对话历史持久化

```python
# backend/conversation/history.py
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from backend.database.connection import Base

class ConversationHistory(Base):
    """对话历史表 (SQLite → MySQL)"""
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), index=True)
    role = Column(String(16))  # user/assistant
    content = Column(Text)
    timestamp = Column(DateTime)
    emotion = Column(String(32), nullable=True)

class HistoryStore:
    """历史存储接口"""
    
    async def save(
        self, 
        session_id: str, 
        user_input: str, 
        assistant_reply: str
    ):
        """保存对话"""
        pass
    
    async def get_recent(
        self, 
        session_id: str, 
        limit: int = 10
    ) -> List[dict]:
        """获取最近对话"""
        pass
    
    async def get_by_date_range(
        self, 
        session_id: str, 
        start: datetime, 
        end: datetime
    ) -> List[dict]:
        """按时间范围查询"""
        pass
```

**Why**: 
- 支持对话历史查询和分析
- 为未来的上下文压缩/摘要打基础
- 迁移到MySQL时只需修改连接配置

**How to apply**: `ConversationManager` 依赖 `HistoryStore`

#### 4.2.4 Persona服务

```python
# backend/persona/service.py
class PersonaService:
    """Persona管理服务"""
    
    def get(self, session_id: str) -> Persona:
        """获取Persona"""
        pass
    
    def update(self, session_id: str, updates: dict) -> Persona:
        """更新Persona"""
        pass
    
    def reset(self, session_id: str) -> Persona:
        """重置为默认"""
        pass
```

**Why**: 集中管理Persona逻辑，避免分散

**How to apply**: 从 `backend/services/memory.py` 迁移相关函数

### 4.3 Node.js网关层调整

```javascript
// server.js (保留，调整为纯网关)
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

// 静态文件服务
app.use(express.static('public'));

// API代理到FastAPI
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:8000',
  changeOrigin: true
}));

// 前端路由
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend/index.html'));
});

app.listen(3000);
```

**Why**: 
- 保持前端URL不变（`http://localhost:3000`）
- Node.js专注于静态服务和路由
- Python专注于业务逻辑

**How to apply**: 
- 废弃 `modules/llm.js` 中的LLM调用
- 保留其他工具函数（如需要）

### 4.4 重构优势

1. **消除重复**: 单一LLM调用实现
2. **配置统一**: 所有配置从数据库/环境变量加载
3. **历史可查**: 对话历史持久化到SQLite
4. **易于迁移**: 抽象接口支持无缝切换MySQL

---

## 五、数据持久化方案

### 5.1 数据库设计

#### 现有表（保持）
```sql
-- backend/database.py 已实现
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

#### 新增表

```sql
-- 对话历史表
CREATE TABLE conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(64) NOT NULL,
    role VARCHAR(16) NOT NULL,           -- 'user' | 'assistant'
    content TEXT NOT NULL,
    emotion VARCHAR(32),                  -- 情绪标签
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_time (session_id, timestamp)
);

-- Persona配置表
CREATE TABLE personas (
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

-- 记忆表（迁移自JSON）
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(32),                     -- 'conversation' | 'fact' | 'preference'
    importance INTEGER DEFAULT 1,         -- 1-5
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id)
);

-- 提醒表（迁移自JSON）
CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    remind_date VARCHAR(20),
    type VARCHAR(32),                     -- 'general' | 'health'
    status VARCHAR(16) DEFAULT 'active',  -- 'active' | 'completed' | 'cancelled'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_date (session_id, remind_date)
);
```

### 5.2 迁移策略

#### 阶段1: SQLite实现（本期）
- 创建上述表结构
- 实现SQLAlchemy ORM模型
- 迁移现有JSON数据（memories, reminders）

#### 阶段2: MySQL迁移（TODO）
- 使用相同的SQLAlchemy模型
- 只需修改数据库连接字符串
- 数据迁移脚本

```python
# backend/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# 支持SQLite和MySQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./data/yidemo.db"  # 默认SQLite
)
# MySQL: "mysql+pymysql://user:pass@localhost/yidemo"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
```

**Why**: 
- SQLAlchemy抽象数据库差异
- 相同代码支持SQLite/MySQL
- 生产环境迁移无需改代码

**How to apply**: 
- 开发环境用SQLite
- 生产环境设置 `DATABASE_URL` 环境变量指向MySQL

---

## 六、待办事项 (TODO)

### 6.1 高优先级
- [ ] **事件总线持久化到Redis**  
  原因: 支持分布式部署，事件不丢失
  
- [ ] **数据库迁移到MySQL**  
  原因: 生产环境性能和并发需求

### 6.2 中优先级
- [ ] **上下文窗口管理**  
  原因: 超过token限制时自动截断/摘要
  
- [ ] **对话历史摘要**  
  原因: 长对话压缩为关键信息

- [ ] **多LLM Provider支持**  
  原因: 支持OpenAI、本地模型等

### 6.3 低优先级
- [ ] **情绪检测模型热替换**  
  原因: 支持运行时切换模型
  
- [ ] **WebSocket支持**  
  原因: 实时推送情绪变化

---

## 七、实施计划

### 阶段1: 基础设施 (2天)
- [ ] 创建新目录结构
- [ ] 实现事件总线（内存版）
- [ ] 设置数据库表结构
- [ ] 迁移配置管理

**验收标准**: 
- 事件总线单元测试通过
- 数据库表创建成功
- 配置统一从数据库读取

### 阶段2: 情绪检测重构 (2天)
- [ ] 拆分 `emotion_agent.py` 为独立模块
- [ ] 实现检测器抽象接口
- [ ] 实现情绪状态机
- [ ] 集成事件总线

**验收标准**:
- 原有API `/api/emo/detect` 功能不变
- 检测准确率不下降
- 单元测试覆盖率 >80%

### 阶段3: 对话系统重构 (2天)
- [ ] 实现LLM Provider抽象
- [ ] 实现对话管理器
- [ ] 实现对话历史持久化
- [ ] 迁移Persona管理

**验收标准**:
- 原有API `/api/chat` 功能不变
- 对话历史正确保存到SQLite
- Node.js网关正常代理

### 阶段4: 集成测试与优化 (1天)
- [ ] 端到端测试
- [ ] 性能基准测试
- [ ] 前端集成验证
- [ ] 文档更新

**验收标准**:
- 所有现有功能正常
- 响应时间无明显增加
- 前端无需修改代码

---

## 八、风险与缓解

### 8.1 性能风险
**风险**: 事件驱动架构可能增加延迟

**缓解**: 
- 内存事件总线延迟<1ms
- 异步处理非阻塞
- 性能基准测试对比

### 8.2 兼容性风险
**风险**: 重构可能破坏现有功能

**缓解**:
- 保持API接口不变
- 完整的回归测试
- 灰度发布策略

### 8.3 数据迁移风险
**风险**: JSON迁移到SQLite可能丢失数据

**缓解**:
- 数据迁移脚本
- 迁移前备份
- 验证脚本对比数据

---

## 九、成功指标

### 9.1 代码质量
- [ ] 平均函数行数 <50行
- [ ] 单元测试覆盖率 >80%
- [ ] 代码重复率 <5%

### 9.2 性能
- [ ] API响应时间 <500ms (P95)
- [ ] 情绪检测延迟 <200ms
- [ ] 数据库查询 <50ms

### 9.3 可维护性
- [ ] 新增功能只需修改单一模块
- [ ] 单元测试独立运行
- [ ] 文档完整覆盖所有模块

---

## 十、附录

### 10.1 目录结构对比

**重构前**:
```
backend/
  routers/chat.py         (120行)
  routers/emo.py          (186行)
  services/llm.py         (34行)
  services/emotion_agent.py (430行)
  services/emo_detector.py  (193行)
```

**重构后**:
```
backend/
  emotion/                # 情绪检测模块
    detector/             (3个文件, ~200行)
    analyzer/             (3个文件, ~150行)
    strategy/             (2个文件, ~80行)
    decision/             (3个文件, ~200行)
    response/             (2个文件, ~150行)
    events.py             (~50行)
    service.py            (~100行)
  
  conversation/           # 对话管理模块
    manager.py            (~150行)
    session.py            (~80行)
    context.py            (~100行)
    history.py            (~120行)
  
  llm/                    # LLM抽象层
    base.py               (~40行)
    dashscope.py          (~80行)
    factory.py            (~30行)
  
  persona/                # Persona管理
    service.py            (~100行)
    models.py             (~60行)
  
  core/                   # 核心基础设施
    event_bus.py          (~80行)
  
  database/               # 数据持久化
    connection.py         (~40行)
    models.py             (~150行)
```

### 10.2 依赖清单

**新增依赖**:
```
# requirements.txt
sqlalchemy>=2.0.0        # ORM
alembic>=1.13.0          # 数据库迁移
redis>=5.0.0             # TODO: 事件总线持久化
pymysql>=1.1.0           # TODO: MySQL驱动
```

**Node.js**:
```json
{
  "dependencies": {
    "http-proxy-middleware": "^2.0.0"  // API代理
  }
}
```

---

**文档结束**
