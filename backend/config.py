import os

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
LLM_MODEL = "qwen-turbo"
LLM_MAX_TOKENS = 200
LLM_TEMPERATURE = 0.7

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PERSONAS_DIR = os.path.join(DATA_DIR, "personas")
MEMORIES_DIR = os.path.join(DATA_DIR, "memories")
EMOTIONS_DIR = os.path.join(DATA_DIR, "emotions")
REMINDERS_FILE = os.path.join(DATA_DIR, "reminders.json")

# 提示词模板目录
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
PERSONA_TEMPLATE_PATH = os.path.join(PROMPTS_DIR, "persona_template.txt")
PROACTIVE_CARE_TEMPLATE_PATH = os.path.join(PROMPTS_DIR, "proactive_care_template.txt")

DEFAULT_PERSONA = {
    "name": "颐",
    "gender": "neutral",
    "personality": "温暖、耐心、有同理心",
    "address_as": "爷爷",
    "style": "句子短，不用网络用语，50字内",
    "custom_instructions": "主动关心身体和饮食",
}

# TTS语音配置
TTS_CONFIG = {
    "rate": 0.85,  # 语速：0.85倍速（稍慢，适合老人）
    "pitch": 1.1,  # 音调：1.1倍（稍温柔）
    "volume": 1.0,  # 音量：正常
    "voice_name": "zh-CN",  # 语音名称
}

# EMO模型配置
EMO_MODEL_CONFIG = {
    "model_path": os.path.join(os.path.dirname(__file__), "models/emo_affectnet/torchscript_model_0_66_37_wo_gl.pth"),
    "device": os.environ.get("EMO_DEVICE", "auto"),  # auto/cpu/cuda
    "input_size": (224, 224),
    "batch_size": 1
}

# Emotion Agent配置
EMOTION_AGENT_CONFIG = {
    # 检测参数
    "window_size": 10,
    "detection_fps": 5,

    # 触发阈值
    "trigger_threshold": {
        "min_confidence": 0.5,
        "min_duration": 2.0,
        "stability_ratio": 0.7
    },

    # 冷却时间（秒）
    "cooldown": {
        "same_category": 60,
        "different_category": 30,
        "high_intensity": 30
    },

    # 优先级
    "priority": {
        "NEGATIVE_CARE": 10,
        "EMOTION_TRANSITION": 8,
        "POSITIVE_EMPATHY": 6,
        "MIXED_EMOTION": 5,
        "SILENT_PRESENCE": 3
    }
}

# 20种情绪中文映射
EMOTION_CN_MAP = {
    "Neutral": "中性",
    "Happiness": "快乐",
    "Sadness": "悲伤",
    "Surprise": "惊讶",
    "Fear": "恐惧",
    "Disgust": "厌恶",
    "Anger": "愤怒",
    "Contempt": "轻蔑",
    "Confusion": "困惑",
    "Embarrassment": "尴尬",
    "Pride": "骄傲",
    "Shame": "羞愧",
    "Relief": "解脱",
    "Interest": "兴趣",
    "Boredom": "无聊",
    "Anxiety": "焦虑",
    "Calm": "平静",
    "Excitement": "兴奋",
    "Disappointment": "失望",
    "Satisfaction": "满足"
}

# 情绪分类
EMOTION_CATEGORIES = {
    "POSITIVE": ["Happiness", "Pride", "Relief", "Interest", "Calm", "Excitement", "Satisfaction"],
    "NEGATIVE": ["Sadness", "Fear", "Disgust", "Anger", "Contempt", "Embarrassment", "Shame", "Anxiety", "Disappointment", "Boredom"],
    "NEUTRAL": ["Neutral", "Surprise", "Confusion"]
}

# 提示词模板路径
EMOTION_EMPATHY_TEMPLATE_PATH = os.path.join(PROMPTS_DIR, "emotion_empathy_template.txt")
EMOTION_CARE_TEMPLATE_PATH = os.path.join(PROMPTS_DIR, "emotion_care_template.txt")