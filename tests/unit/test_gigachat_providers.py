import base64

import httpx
import pytest

from app.infrastructure.embeddings.gigachat_provider import GigaChatEmbeddingProvider
from app.infrastructure.gigachat.auth import GigaChatAuthClient
from app.infrastructure.llm.gigachat_provider import GigaChatLLMProvider


@pytest.mark.asyncio
async def test_gigachat_auth_client_gets_and_caches_token():
    calls = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.headers['authorization'] == 'Basic ready-key'
        assert request.headers.get('rquid')
        assert request.content == b'scope=GIGACHAT_API_PERS'
        return httpx.Response(200, json={'access_token': 'token-1', 'expires_at': 9999999999999})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        auth = GigaChatAuthClient(
            auth_url='https://auth.test/oauth',
            scope='GIGACHAT_API_PERS',
            authorization_key='ready-key',
            http_client=client,
        )
        assert await auth.get_access_token() == 'token-1'
        assert await auth.get_access_token() == 'token-1'

    assert len(calls) == 1


def test_gigachat_auth_client_builds_basic_key_from_client_credentials():
    expected = base64.b64encode(b'id:secret').decode('ascii')
    auth = GigaChatAuthClient(
        auth_url='https://auth.test/oauth',
        scope='GIGACHAT_API_PERS',
        client_id='id',
        client_secret='secret',
    )

    assert auth.authorization == f'Basic {expected}'


@pytest.mark.asyncio
async def test_gigachat_embedding_provider_returns_vectors():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith('/oauth'):
            return httpx.Response(200, json={'access_token': 'token-1', 'expires_at': 9999999999999})
        assert request.url.path == '/api/v1/embeddings'
        assert request.headers['authorization'] == 'Bearer token-1'
        payload = __import__('json').loads(request.content)
        assert payload == {'model': 'Embeddings', 'input': ['a', 'b']}
        return httpx.Response(
            200,
            json={
                'object': 'list',
                'data': [
                    {'object': 'embedding', 'embedding': [0.1, 0.2, 0.3], 'index': 0},
                    {'object': 'embedding', 'embedding': [0.4, 0.5, 0.6], 'index': 1},
                ],
                'model': 'Embeddings',
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        auth = GigaChatAuthClient(
            auth_url='https://auth.test/oauth',
            scope='GIGACHAT_API_PERS',
            authorization_key='ready-key',
            http_client=client,
        )
        provider = GigaChatEmbeddingProvider(
            api_url='https://gigachat.test/api/v1',
            auth_client=auth,
            model='Embeddings',
            dimension=3,
            version='v1',
            http_client=client,
        )
        assert await provider.embed_batch(['a', 'b']) == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


@pytest.mark.asyncio
async def test_gigachat_llm_provider_returns_answer():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith('/oauth'):
            return httpx.Response(200, json={'access_token': 'token-1', 'expires_at': 9999999999999})
        assert request.url.path == '/api/v1/chat/completions'
        payload = __import__('json').loads(request.content)
        assert payload['model'] == 'GigaChat'
        assert payload['messages'][0]['role'] == 'system'
        return httpx.Response(
            200,
            json={'choices': [{'message': {'content': 'Ответ из GigaChat'}}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        auth = GigaChatAuthClient(
            auth_url='https://auth.test/oauth',
            scope='GIGACHAT_API_PERS',
            authorization_key='ready-key',
            http_client=client,
        )
        provider = GigaChatLLMProvider(
            api_url='https://gigachat.test/api/v1',
            auth_client=auth,
            model='GigaChat',
            http_client=client,
        )
        response = await provider.generate('system', 'user')

    assert response.text == 'Ответ из GigaChat'
    assert response.provider_name == 'gigachat'
