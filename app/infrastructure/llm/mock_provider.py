from app.domain.ports.llm_provider import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 1000) -> LLMResponse:
        text = 'Это тестовый ответ mock LLM на основе найденного контекста. Подключите реальный LLM_PROVIDER для production-ответов.'
        return LLMResponse(text=text, raw_response={'mock': True}, model_name='mock-llm', provider_name='mock')
