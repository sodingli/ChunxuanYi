import json
import asyncio
import re
import aiohttp
from backend.config import DASHSCOPE_API_KEY, DASHSCOPE_API_URL, LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE


def sanitize_input(text: str, max_len: int = 500) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r'[<>]', '', text)
    text = text.replace('\n', ' ').replace('\r', ' ')
    return text.strip()[:max_len]


async def call_qwen(prompt: str, max_tokens: int = LLM_MAX_TOKENS, temperature: float = LLM_TEMPERATURE) -> str:
    payload = {
        "model": LLM_MODEL,
        "input": {"prompt": prompt},
        "parameters": {"max_tokens": max_tokens, "temperature": temperature},
    }
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(DASHSCOPE_API_URL, json=payload, headers=headers, timeout=30) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if "output" in data and "text" in data["output"]:
                return data["output"]["text"]
            if "code" in data:
                raise RuntimeError(f"{data.get('code')}: {data.get('message')}")
            raise RuntimeError(f"未知响应: {await resp.text()[:200]}")