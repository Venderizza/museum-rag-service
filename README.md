# Museum RAG Service

Самостоятельный RAG-сервис для поиска и генерации ответов по текстовым описаниям музейных экспонатов.

## Стек

- Python 3.11
- FastAPI
- PostgreSQL
- Qdrant
- Redis
- Dramatiq
- SQLAlchemy async
- Alembic
- GigaChat/OpenAI-compatible provider abstraction

## Быстрый запуск на mock-провайдерах

```bash
cp .env.example .env
docker compose up --build
```

В отдельном терминале применить миграции:

```bash
docker compose exec app alembic upgrade head
```

Проверка:

```bash
curl http://localhost:8000/api/v1/health
```

## Тесты

```bash
uv pip install -e .
uv run pytest
```

Текущий быстрый набор: 36 тестов.

## Провайдеры

По умолчанию включены mock-провайдеры:

```env
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=mock
EMBEDDING_DIMENSION=384
```

### GigaChat

Поддержаны реальные провайдеры:

```env
LLM_PROVIDER=gigachat
EMBEDDING_PROVIDER=gigachat
```

Для авторизации можно использовать готовый authorization key из личного кабинета:

```env
GIGACHAT_AUTHORIZATION_KEY=<base64_authorization_key_without_or_with_Basic_prefix>
GIGACHAT_SCOPE=GIGACHAT_API_PERS
```

Или пару client id / client secret:

```env
GIGACHAT_CLIENT_ID=<client_id>
GIGACHAT_CLIENT_SECRET=<client_secret>
GIGACHAT_SCOPE=GIGACHAT_API_PERS
```

Модели:

```env
GIGACHAT_MODEL=GigaChat
GIGACHAT_EMBEDDING_MODEL=Embeddings
```

Важно: размерность embedding-модели должна совпадать с `EMBEDDING_DIMENSION`, иначе Qdrant collection будет создана с неверным размером вектора или провайдер вернёт ошибку dimension mismatch.

Примеры:

```env
# mock
EMBEDDING_DIMENSION=384

# GigaChat Embeddings / Embeddings-2: укажите фактическую размерность вашей модели
EMBEDDING_DIMENSION=1024

# EmbeddingsGigaR
GIGACHAT_EMBEDDING_MODEL=EmbeddingsGigaR
EMBEDDING_DIMENSION=2560
```

Если при локальном запуске есть проблемы с TLS-сертификатами, можно временно отключить проверку SSL:

```env
GIGACHAT_VERIFY_SSL=false
```

Для production это не рекомендуется.

### OpenAI-compatible LLM

Для DeepSeek или другого OpenAI-compatible API:

```env
LLM_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_API_URL=https://api.deepseek.com/v1
OPENAI_COMPATIBLE_API_KEY=<key>
OPENAI_COMPATIBLE_MODEL=deepseek-chat
```

Embeddings при этом можно оставить mock или включить GigaChat/local provider.

## API

### Добавить документ

```bash
curl -X POST http://localhost:8000/api/v1/documents/123 \
  -H 'Content-Type: application/json' \
  -d '{"title":"Шлем князя Ярослава","body":"Описание экспоната...","metadata":{}}'
```

### Статус

```bash
curl http://localhost:8000/api/v1/documents/123/status
```

### Search

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"шлем князя Ярослава","top_k":10}'
```

### Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Расскажи про шлем князя Ярослава"}],"top_k":10}'
```

### Delete

```bash
curl -X DELETE http://localhost:8000/api/v1/documents/123
```

### Reindex

```bash
curl -X POST http://localhost:8000/api/v1/documents/123/reindex
```

## Важные ограничения текущей версии

- Hybrid search, reranker, streaming и auth не входят в первую итерацию.
- Qdrant используется как производный индекс; PostgreSQL остаётся source of truth.
- При смене embedding-модели нужно использовать новый `EMBEDDING_VERSION` или reindex.
- Настройку confidence thresholds нужно проводить на реальных данных и реальных embeddings.
