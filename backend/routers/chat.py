from fastapi import APIRouter, HTTPException
from backend.models import ChatRequest, ChatResponse, EmotionRequest, EmotionResponse, PersonaUpdate, Persona
from backend.services.llm import call_qwen
from backend.services.emotion import analyze_text_emotion
from backend.services.memory import get_persona, update_persona, add_memory, get_memory_context

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    persona = get_persona(req.session_id)
    memory_ctx = get_memory_context(req.session_id)

    prompt = f"""你是「{persona.name}」，一个专门为独居老人设计的AI陪伴助手。

【角色限定】：
1. 身份：{persona.personality}，像子女一样关心老人
2. 称呼：对男性用「爷爷」，对女性用「奶奶」，通用「您」
3. 语言风格：{persona.style}
4. 行为准则：
   - 主动关心老人的身体、情绪、饮食
   - 记住老人说过的话（系统会提供记忆）
   - 在合适的时候，主动提起过去的话题
   - 如果发现老人情绪异常，要特别关注
   - {persona.custom_instructions}{memory_ctx}

【当前对话】：
老人说：「{req.user_input}」

请回复："""

    try:
        reply = await call_qwen(prompt)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM调用失败: {e}")

    # 保存记忆
    add_memory(req.session_id, f"用户说: {req.user_input}", "conversation")
    add_memory(req.session_id, f"{persona.name}回复: {reply}", "conversation")

    # 分析情绪
    try:
        emotion_result = await analyze_text_emotion(req.user_input)
        emotion = emotion_result.get("emotion", "neutral")
    except Exception:
        emotion = "neutral"

    return ChatResponse(reply=reply, emotion=emotion)


@router.post("/emotion", response_model=EmotionResponse)
async def analyze_emotion(req: EmotionRequest):
    try:
        result = await analyze_text_emotion(req.text)
        return EmotionResponse(
            emotion=result.get("emotion", "neutral"),
            emotion_cn=result.get("emotion_cn", "中性"),
            suggested_response=result.get("suggested_response", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"情绪分析失败: {e}")


@router.get("/persona", response_model=Persona)
async def get_persona_endpoint(session_id: str = "default"):
    return get_persona(session_id)


@router.put("/persona", response_model=Persona)
async def update_persona_endpoint(session_id: str = "default", updates: PersonaUpdate = None):
    if updates is None:
        return get_persona(session_id)
    return update_persona(session_id, updates.model_dump(exclude_none=True))