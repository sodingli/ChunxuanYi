"""
初始化数据库脚本
创建所有表结构
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import engine, Base
from backend.database.models import ConversationHistory, PersonaModel, Memory, Reminder


def init_database():
    """创建所有数据库表"""
    # 确保data目录存在
    os.makedirs("data", exist_ok=True)

    print("开始创建数据库表...")

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    print("✓ 数据库表创建完成")
    print(f"✓ 数据库位置: {os.path.abspath('data/yidemo.db')}")
    print("\n已创建的表:")
    print("  - conversation_history (对话历史)")
    print("  - personas (人设配置)")
    print("  - memories (记忆存储)")
    print("  - reminders (提醒事项)")
    print("  - config (配置管理，已存在)")


if __name__ == "__main__":
    init_database()
