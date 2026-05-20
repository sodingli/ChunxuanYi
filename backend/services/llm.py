import httpx
import json
from backend.config import DASHSCOPE_API_KEY, DASHSCOPE_API_URL, LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE


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
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(DASHSCOPE_API_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if "output" in data and "text" in data["output"]:
            return data["output"]["text"]
        if "code" in data:
            raise RuntimeError(f"{data.get('code')}: {data.get('message')}")
        raise RuntimeError(f"未知响应: {resp.text[:200]}")