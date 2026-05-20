# backend/services/tts.py
from fastapi.responses import StreamingResponse
import io


async def synthesize_speech(text: str) -> StreamingResponse:
    """文字转语音。

    MVP阶段：返回空音频，前端降级使用浏览器 SpeechSynthesis。
    后续接入阿里云TTS API。
    """
    # MVP: 返回空WAV头
    # 真实实现将调用 TTS API 生成音频
    wav_header = b'RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    return StreamingResponse(io.BytesIO(wav_header), media_type="audio/wav")