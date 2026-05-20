import json
from backend.services.llm import call_qwen


async def analyze_text_emotion(text: str) -> dict:
    prompt = f"""分析情绪，返回JSON：
用户输入：「{text}」

返回格式：
{{
  "emotion": "happy/sad/anxious/calm/angry/neutral",
  "emotion_cn": "开心/悲伤/焦虑/平静/愤怒/中性",
  "suggested_response": "建议回复（30字内，温暖，适合老人）"
}}

只返回JSON："""
    result = await call_qwen(prompt, max_tokens=150)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"emotion": "neutral", "emotion_cn": "中性", "suggested_response": result[:30]}