import httpx
from app.domain.errors import ConfigurationError, LLMProviderError
from app.domain.ports.llm_provider import LLMProvider, LLMResponse


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self, api_url: str | None, api_key: str | None, model: str):
        if not api_url or not api_key:
            raise ConfigurationError('OpenAI-compatible API URL and API key are required')
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model = model

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 1000) -> LLMResponse:
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': temperature,
            'max_tokens': max_tokens,
        }
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f'{self.api_url}/chat/completions', json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                text = data['choices'][0]['message']['content']
                return LLMResponse(text=text, raw_response=data, model_name=self.model, provider_name='openai_compatible')
        except Exception as exc:
            raise LLMProviderError(str(exc)) from exc
