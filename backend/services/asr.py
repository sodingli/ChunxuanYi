# backend/services/asr.py
import json
from backend.services.llm import call_qwen


async def recognize_speech(audio_b64: str, audio_format: str = "wav") -> dict:
    """语音识别 + 语音情绪分析。

    MVP阶段：使用LLM模拟ASR（接收文字输入模拟语音识别结果）。
    后续接入阿里云/百度ASR API。
    """
    # MVP: 直接返回占位结果
    # 真实实现将调用 ASR API 将音频转为文字
    return {
        "text": "",
        "emotion": "neutral",
        "emotion_confidence": 0.5,
        "emotion_source": "voice",
    }


async def analyze_voice_emotion(text: str) -> dict:
    """基于文本内容分析语音情绪（MVP阶段用LLM替代声学分析）。"""
    prompt = f"""分析这段话的语音情绪，返回JSON：
用户说：「{text}」

返回格式：
{{
  "emotion": "happy/sad/anxious/calm/angry/neutral",
  "emotion_cn": "开心/悲伤/焦虑/平静/愤怒/中性",
  "confidence": 0.85,
  "reason": "分析理由（20字内）"
}}

只返回JSON："""
    result = await call_qwen(prompt, max_tokens=150)
    try:
        data = json.loads(result)
        return {
            "emotion": data.get("emotion", "neutral"),
            "emotion_confidence": data.get("confidence", 0.5),
        }
    except json.JSONDecodeError:
        return {"emotion": "neutral", "emotion_confidence": 0.5}