import logging

import httpx
from app.core.config import get_settings


logger = logging.getLogger(__name__)


class AIService:
    async def ask(self, message: str, score: int) -> str:
        settings = get_settings()
        if not settings.openrouter_api_key:
            return self._local_guidance(message, score)

        payload = {
            "model": settings.openrouter_model,
            "max_tokens": 450,
            "messages": [
                {
                    "role": "system",
                    "content": "You are SentinelAI, a concise device-security assistant. Give practical, calm, non-alarmist advice. Do not claim to access data you were not given. Do not request passwords, recovery codes, or other secrets.",
                },
                {"role": "user", "content": f"Security score: {score}/100. Question: {message}"},
            ],
        }
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "HTTP-Referer": "https://sentinalai-nine.vercel.app",
            "X-Title": "SentinelAI",
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
                response = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                answer = response.json()["choices"][0]["message"]["content"].strip()
                if answer:
                    return answer
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
            logger.warning("OpenRouter free-model request failed; using local guidance: %s", error)

        return self._local_guidance(message, score)

    @staticmethod
    def _local_guidance(message: str, score: int) -> str:
        """Useful, account-scoped guidance when a remote free model is unavailable."""
        prompt = message.lower()
        if any(word in prompt for word in ("sign-in", "signin", "login", "approve", "code", "otp")):
            next_action = "Do not approve the request or share a code. Open the relevant service yourself, review its signed-in devices, and change the password if you do not recognise the attempt."
        elif any(word in prompt for word in ("message", "link", "email", "phish", "scam", "sms")):
            next_action = "Do not open the link or reply from the message. Verify the claim through the organisation's official app or website, and report or delete the message if it cannot be verified."
        elif any(word in prompt for word in ("lost", "stolen", "missing", "device")):
            next_action = "Mark the device as at risk, use the provider's official find-device service if available, revoke active sessions, and tell a trusted contact where appropriate."
        elif any(word in prompt for word in ("location", "boundary", "geofence")):
            next_action = "Confirm that location permission is active, check the saved boundary radius, and treat an unexpected boundary exit as a prompt to verify the device rather than proof of a breach."
        else:
            next_action = "Review unresolved items in Threat detection, verify unfamiliar activity through the original service, and avoid sharing credentials or recovery codes under pressure."

        score_context = "strong" if score >= 80 else "needs attention" if score >= 50 else "needs prompt review"
        return (
            f"Your current security score is {score}/100, which {score_context}. "
            f"{next_action} This response is generated from SentinelAI's local security rules while a remote free AI model is unavailable."
        )
