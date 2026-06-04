from fastapi import APIRouter, HTTPException
from backend.models import ChatRequest, ChatResponse, EmotionRequest, EmotionResponse, PersonaUpdate, Persona
from backend.services.llm import call_qwen, sanitize_input
from backend.services.emotion import analyze_text_emotion
from backend.services.memory import get_persona, update_persona, add_memory, get_memory_context
from backend.config import PERSONA_TEMPLATE_PATH
import os

router = APIRouter()


def _load_prompt_template(template_path: str) -> str:
    """加载提示词模板文件"""
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    sanitized_input = sanitize_input(req.user_input)
    persona = get_persona(req.session_id)
    memory_ctx = get_memory_context(req.session_id)

    # 从模板文件加载提示词
    template = _load_prompt_template(PERSONA_TEMPLATE_PATH)
    if not template:
        # 兜底：使用硬编码模板
        template = """你是「{name}」，一个专门为独居老人设计的AI陪伴助手。

【角色限定】：
1. 身份：{personality}，像子女一样关心老人
2. 称呼：对男性用「爷爷」，对女性用「奶奶」，通用「您」。当前用户称呼：{address_as}
3. 语言风格：{style}
4. 行为准则：
   - 主动关心老人的身体、情绪、饮食
   - 记住老人说过的话（系统会提供记忆）
   - 在合适的时候，主动提起过去的话题
   - 如果发现老人情绪异常，要特别关注
   - {custom_instructions}

{memory_context}

【当前对话】：
老人说：「{user_input}」

请回复："""

    prompt = template.format(
        name=persona.name,
        personality=persona.personality,
        address_as=persona.address_as,
        style=persona.style,
        custom_instructions=persona.custom_instructions,
        memory_context=memory_ctx,
        user_input=sanitized_input
    )

    try:
        reply = await call_qwen(prompt)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM调用失败: {e}")

    # 保存记忆
    add_memory(req.session_id, f"用户说: {sanitized_input}", "conversation")
    add_memory(req.session_id, f"{persona.name}回复: {reply}", "conversation")

    # 分析情绪
    try:
        emotion_result = await analyze_text_emotion(sanitized_input)
        emotion = emotion_result.get("emotion", "neutral")
    except Exception:
        emotion = "neutral"

    return ChatResponse(reply=reply, emotion=emotion)


@router.post("/emotion", response_model=EmotionResponse)
async def analyze_emotion(req: EmotionRequest):
    sanitized_text = sanitize_input(req.text)
    try:
        result = await analyze_text_emotion(sanitized_text)
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