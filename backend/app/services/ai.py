import httpx
from app.core.config import get_settings

class AIService:
    async def ask(self, message: str, score: int) -> str:
        settings = get_settings()
        if not settings.openrouter_api_key:
            return f"Your current security score is {score}/100. Start by reviewing unfamiliar sign-ins and keeping device software current. For your question: prioritize evidence, avoid approving unexpected prompts, and contact a trusted person before sharing codes."
        payload = {"model": settings.openrouter_model, "messages": [{"role": "system", "content": "You are SentinelAI, a concise device-security assistant. Give practical, calm, non-alarmist advice. Do not claim to access data you were not given."}, {"role": "user", "content": f"Security score: {score}. Question: {message}"}]}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {settings.openrouter_api_key}", "HTTP-Referer": "http://localhost:5173", "X-Title": "SentinelAI"})
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
