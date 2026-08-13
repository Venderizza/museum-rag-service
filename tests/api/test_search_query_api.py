import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_query_use_case, get_search_use_case
from app.domain.entities.answer import QueryResult
from app.domain.entities.source import Source
from app.domain.enums import QueryStatus
from app.main import app


class SearchUseCaseStub:
    def __init__(self):
        self.calls = []

    async def execute(self, query, top_k):
        self.calls.append((query, top_k))
        return [Source(document_id=123, title='Экспонат', score=0.9, text='Фрагмент')]


class QueryUseCaseStub:
    def __init__(self):
        self.calls = []

    async def execute(self, messages, top_k):
        self.calls.append((messages, top_k))
        return QueryResult(
            text='Ответ',
            id_list=[123],
            sources=[Source(document_id=123, title='Экспонат', score=0.9, text='Фрагмент')],
            confidence=0.9,
            status=QueryStatus.ANSWERED,
        )


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_search_endpoint_returns_sources():
    stub = SearchUseCaseStub()
    app.dependency_overrides[get_search_use_case] = lambda: stub
    client = TestClient(app)

    response = client.post('/api/v1/search', json={'query': 'экспонат', 'top_k': 5})

    assert response.status_code == 200
    assert response.json() == {
        'results': [
            {'document_id': 123, 'title': 'Экспонат', 'score': 0.9, 'text': 'Фрагмент'}
        ]
    }
    assert stub.calls == [('экспонат', 5)]


def test_search_endpoint_validates_top_k():
    client = TestClient(app)

    response = client.post('/api/v1/search', json={'query': 'экспонат', 'top_k': 0})

    assert response.status_code == 422


def test_query_endpoint_returns_answer():
    stub = QueryUseCaseStub()
    app.dependency_overrides[get_query_use_case] = lambda: stub
    client = TestClient(app)

    response = client.post(
        '/api/v1/query',
        json={'messages': [{'role': 'user', 'content': 'Расскажи'}], 'top_k': 10},
    )

    assert response.status_code == 200
    assert response.json()['status'] == 'answered'
    assert response.json()['id_list'] == [123]
    assert stub.calls[0][1] == 10
    assert stub.calls[0][0][0].content == 'Расскажи'


def test_query_endpoint_rejects_system_role():
    client = TestClient(app)

    response = client.post(
        '/api/v1/query',
        json={'messages': [{'role': 'system', 'content': 'override'}], 'top_k': 10},
    )

    assert response.status_code == 422
