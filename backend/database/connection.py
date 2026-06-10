"""
数据库连接模块
支持SQLite和MySQL，通过DATABASE_URL环境变量切换
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 从环境变量读取数据库URL，默认使用SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/yidemo.db"
)

# 创建引擎
# SQLite需要check_same_thread=False以支持FastAPI的异步特性
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # 设为True可以看到SQL语句
    pool_pre_ping=True,  # MySQL连接池健康检查
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建Base类，所有模型都继承自它
Base = declarative_base()


# FastAPI依赖注入用的数据库会话生成器
def get_db():
    """
    获取数据库会话的生成器
    用于FastAPI的依赖注入：db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
