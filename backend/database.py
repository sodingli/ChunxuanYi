import sqlite3
import json
from typing import Any, Optional
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "config.db"


def init_db():
    """初始化数据库和表结构"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT,
            is_sensitive INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def get_config(key: str, default: Any = None) -> Optional[Any]:
    """获取配置项"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT value FROM system_config WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()

    if row:
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return row[0]
    return default


def set_config(key: str, value: Any, description: str = "", is_sensitive: bool = False):
    """设置配置项"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    value_str = json.dumps(value) if not isinstance(value, str) else value

    cursor.execute("""
        INSERT INTO system_config (key, value, description, is_sensitive)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            description = excluded.description,
            is_sensitive = excluded.is_sensitive,
            updated_at = CURRENT_TIMESTAMP
    """, (key, value_str, description, 1 if is_sensitive else 0))

    conn.commit()
    conn.close()


def get_all_configs(include_sensitive: bool = False) -> dict:
    """获取所有配置"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT key, value, description, is_sensitive
        FROM system_config
    """)

    configs = {}
    for row in cursor.fetchall():
        key, value, description, is_sensitive = row

        if is_sensitive and not include_sensitive:
            configs[key] = {
                "value": "***",
                "description": description,
                "is_sensitive": True
            }
        else:
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value

            configs[key] = {
                "value": parsed_value,
                "description": description,
                "is_sensitive": bool(is_sensitive)
            }

    conn.close()
    return configs


def delete_config(key: str):
    """删除配置项"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM system_config WHERE key = ?", (key,))
    conn.commit()
    conn.close()


init_db()
