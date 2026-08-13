from __future__ import annotations

import httpx

from app.domain.errors import LLMProviderError
from app.domain.ports.llm_provider import LLMProvider, LLMResponse
from app.infrastructure.gigachat.auth import GigaChatAuthClient


class GigaChatLLMProvider(LLMProvider):
    def __init__(
        self,
        api_url: str,
        auth_client: GigaChatAuthClient,
        model: str,
        verify_ssl: bool = True,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_url = api_url.rstrip('/')
        self.auth_client = auth_client
        self.model = model
        self.verify_ssl = verify_ssl
        self.http_client = http_client

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        token = await self.auth_client.get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': temperature,
            'max_tokens': max_tokens,
        }

        try:
            if self.http_client is not None:
                response = await self.http_client.post(f'{self.api_url}/chat/completions', headers=headers, json=payload)
            else:
                async with httpx.AsyncClient(timeout=90, verify=self.verify_ssl) as client:
                    response = await client.post(f'{self.api_url}/chat/completions', headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            text = data['choices'][0]['message']['content']
            return LLMResponse(text=text, raw_response=data, model_name=self.model, provider_name='gigachat')
        except Exception as exc:
            raise LLMProviderError(f'GigaChat chat completion request failed: {exc}') from exc
