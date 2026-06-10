"""
数据库模型定义
包含：会话历史、人设、记忆、提醒事项
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, Enum as SQLEnum, Index
from sqlalchemy.sql import func
from datetime import datetime
from .connection import Base


class ConversationHistory(Base):
    """对话历史记录表"""
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True, comment="会话ID")
    role = Column(String(20), nullable=False, comment="角色：user/assistant")
    content = Column(Text, nullable=False, comment="对话内容")
    emotion = Column(String(50), nullable=True, comment="情绪标签")
    timestamp = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="创建时间"
    )

    __table_args__ = (
        Index("idx_session_timestamp", "session_id", "timestamp"),
    )

    def __repr__(self):
        return f"<ConversationHistory(id={self.id}, session_id={self.session_id}, role={self.role})>"


class PersonaModel(Base):
    """人设配置表"""
    __tablename__ = "personas"

    session_id = Column(String(100), primary_key=True, comment="会话ID（主键）")
    name = Column(String(50), nullable=False, default="小椿", comment="AI名称")
    gender = Column(String(10), nullable=False, default="female", comment="性别")
    personality = Column(Text, nullable=True, comment="性格描述")
    address_as = Column(String(50), nullable=False, default="您", comment="称呼方式")
    style = Column(String(50), nullable=False, default="温柔体贴", comment="对话风格")
    custom_instructions = Column(Text, nullable=True, comment="自定义指令")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )

    def __repr__(self):
        return f"<PersonaModel(session_id={self.session_id}, name={self.name})>"


class Memory(Base):
    """记忆存储表"""
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True, comment="会话ID")
    content = Column(Text, nullable=False, comment="记忆内容")
    type = Column(
        String(20),
        nullable=False,
        default="general",
        comment="记忆类型：preference/event/general"
    )
    importance = Column(Integer, nullable=False, default=5, comment="重要性(1-10)")
    timestamp = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="创建时间"
    )

    __table_args__ = (
        Index("idx_memory_session_type", "session_id", "type"),
    )

    def __repr__(self):
        return f"<Memory(id={self.id}, session_id={self.session_id}, type={self.type})>"


class Reminder(Base):
    """提醒事项表"""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True, comment="会话ID")
    content = Column(Text, nullable=False, comment="提醒内容")
    remind_date = Column(DateTime, nullable=False, index=True, comment="提醒时间")
    type = Column(
        String(20),
        nullable=False,
        default="once",
        comment="提醒类型：once/daily/weekly"
    )
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="状态：pending/completed/cancelled"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )

    __table_args__ = (
        Index("idx_reminder_date_status", "remind_date", "status"),
    )

    def __repr__(self):
        return f"<Reminder(id={self.id}, session_id={self.session_id}, status={self.status})>"
