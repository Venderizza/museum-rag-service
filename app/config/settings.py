from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_env: str = 'local'
    app_host: str = '0.0.0.0'
    app_port: int = 8001
    log_level: str = 'INFO'

    database_url: str = 'postgresql+asyncpg://museum:museum@localhost:5432/museum_rag'

    qdrant_host: str = 'localhost'
    qdrant_port: int = 6333
    qdrant_collection: str = 'museum_chunks_gigachat'

    redis_url: str = 'redis://localhost:6379/0'

    llm_provider: str = 'mock'
    embedding_provider: str = 'mock'

    gigachat_api_url: str = 'https://gigachat.devices.sberbank.ru/api/v1'
    gigachat_auth_url: str = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
    gigachat_authorization_key: str | None = None
    gigachat_client_id: str | None = None
    gigachat_client_secret: str | None = None
    gigachat_scope: str = 'GIGACHAT_API_PERS'
    gigachat_model: str = 'GigaChat'
    gigachat_embedding_model: str = 'Embeddings'
    gigachat_verify_ssl: bool = True

    openai_compatible_api_url: str | None = None
    openai_compatible_api_key: str | None = None
    openai_compatible_model: str = 'deepseek-chat'

    embedding_model_name: str = 'mock-embedding'
    embedding_dimension: int = 384
    embedding_version: str = 'v1'

    chunk_size_tokens: int = 700
    chunk_overlap_tokens: int = 100

    retrieval_top_k: int = Field(default=10, ge=1, le=50)
    retrieval_min_score: float = 0.35
    answer_confidence_threshold: float = 0.45

    store_llm_prompts: bool = True
    store_llm_raw_responses: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
