-- 此文件仅作为参考，实际通过SQLAlchemy创建表
-- 如需手动迁移到MySQL，可参考以下SQL

-- 会话历史表
CREATE TABLE conversation_history (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL COMMENT '角色：user/assistant',
    content TEXT NOT NULL COMMENT '对话内容',
    emotion VARCHAR(50) COMMENT '情绪标签',
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_session_id (session_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_session_timestamp (session_id, timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话历史记录';

-- 人设配置表
CREATE TABLE personas (
    session_id VARCHAR(100) PRIMARY KEY COMMENT '会话ID（主键）',
    name VARCHAR(50) NOT NULL DEFAULT '小椿' COMMENT 'AI名称',
    gender VARCHAR(10) NOT NULL DEFAULT 'female' COMMENT '性别',
    personality TEXT COMMENT '性格描述',
    address_as VARCHAR(50) NOT NULL DEFAULT '您' COMMENT '称呼方式',
    style VARCHAR(50) NOT NULL DEFAULT '温柔体贴' COMMENT '对话风格',
    custom_instructions TEXT COMMENT '自定义指令',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人设配置';

-- 记忆存储表
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL COMMENT '记忆内容',
    type VARCHAR(20) NOT NULL DEFAULT 'general' COMMENT '记忆类型：preference/event/general',
    importance INTEGER NOT NULL DEFAULT 5 COMMENT '重要性(1-10)',
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_session_id (session_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_memory_session_type (session_id, type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='记忆存储';

-- 提醒事项表
CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL COMMENT '提醒内容',
    remind_date DATETIME NOT NULL COMMENT '提醒时间',
    type VARCHAR(20) NOT NULL DEFAULT 'once' COMMENT '提醒类型：once/daily/weekly',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/completed/cancelled',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_session_id (session_id),
    INDEX idx_remind_date (remind_date),
    INDEX idx_reminder_date_status (remind_date, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='提醒事项';
