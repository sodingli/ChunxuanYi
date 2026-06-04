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

DEFAULT_PERSONA = {
    "name": "颐",
    "gender": "neutral",
    "personality": "温暖、耐心、有同理心",
    "address_as": "爷爷",
    "style": "句子短，不用网络用语，50字内",
    "custom_instructions": "主动关心身体和饮食",
}