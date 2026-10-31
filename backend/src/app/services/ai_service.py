from typing import Any
import httpx
from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("ai_service")


async def generate_chat_reply(
    messages: list[dict[str, str]],
    system_prompt: str | None = None,
    temperature: float = 0.7,
) -> dict[str, Any]:
    """Call Azure OpenAI gpt-4.1-mini to generate an assistant reply."""
    endpoint = settings.azure_openai_endpoint.rstrip("/")
    deployment = settings.deployment_name
    api_version = settings.azure_openai_api_version
    api_key = settings.azure_openai_api_key

    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

    formatted_messages = []
    if system_prompt:
        formatted_messages.append({"role": "system", "content": system_prompt})
    else:
        formatted_messages.append({
            "role": "system",
            "content": "You are a helpful, brilliant, concise AI assistant deployed on Cloudflare Workers and D1 Serverless SQL."
        })

    # Include recent conversation turns for context (up to last 12 messages)
    for m in messages[-12:]:
        formatted_messages.append({"role": m["role"], "content": m["content"]})

    payload = {
        "messages": formatted_messages,
        "temperature": temperature,
        "max_tokens": 1500,
    }

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        log.error("azure_openai_error", status_code=response.status_code, body=response.text)
        raise RuntimeError(f"Azure OpenAI Error ({response.status_code}): {response.text}")

    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    tokens_used = usage.get("total_tokens", 0)

    return {
        "reply": reply,
        "tokens_used": tokens_used,
        "model": data.get("model", deployment),
    }

