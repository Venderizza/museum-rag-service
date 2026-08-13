import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_add_document_use_case,
    get_delete_use_case,
    get_reindex_use_case,
    get_status_use_case,
)
from app.domain.enums import DocumentStatus
from app.domain.errors import DocumentAlreadyExistsError, DocumentDeletedError, DocumentNotFoundError
from app.main import app


class AddDocumentUseCaseStub:
    def __init__(self, result=DocumentStatus.QUEUED, error=None):
        self.result = result
        self.error = error
        self.calls = []

    async def execute(self, *, document_id, title, body, metadata):
        self.calls.append((document_id, title, body, metadata))
        if self.error:
            raise self.error
        return self.result


class StatusUseCaseStub:
    async def execute(self, document_id):
        if document_id == 404:
            raise DocumentNotFoundError()
        return type(
            'DocumentStatusResult',
            (),
            {
                'document_id': document_id,
                'status': DocumentStatus.INDEXED,
                'chunks_count': 2,
                'error': None,
            },
        )()


class MutationUseCaseStub:
    def __init__(self, result=DocumentStatus.DELETED, error=None):
        self.result = result
        self.error = error
        self.calls = []

    async def execute(self, document_id):
        self.calls.append(document_id)
        if self.error:
            raise self.error
        return self.result


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_post_document_returns_accepted_and_enqueues():
    stub = AddDocumentUseCaseStub()
    app.dependency_overrides[get_add_document_use_case] = lambda: stub
    client = TestClient(app)

    response = client.post(
        '/api/v1/documents/123',
        json={'title': 'Экспонат', 'body': 'Описание', 'metadata': {'a': 1}},
    )

    assert response.status_code == 202
    assert response.json() == {'document_id': 123, 'status': 'queued'}
    assert stub.calls == [(123, 'Экспонат', 'Описание', {'a': 1})]


def test_post_document_duplicate_returns_409():
    app.dependency_overrides[get_add_document_use_case] = lambda: AddDocumentUseCaseStub(
        error=DocumentAlreadyExistsError()
    )
    client = TestClient(app)

    response = client.post('/api/v1/documents/123', json={'title': 'A', 'body': 'B'})

    assert response.status_code == 409
    assert response.json()['error'] == 'document_already_exists'


def test_post_document_validation_error_for_empty_title():
    client = TestClient(app)

    response = client.post('/api/v1/documents/123', json={'title': '', 'body': 'B'})

    assert response.status_code == 422


def test_get_document_status_returns_status():
    app.dependency_overrides[get_status_use_case] = lambda: StatusUseCaseStub()
    client = TestClient(app)

    response = client.get('/api/v1/documents/123/status')

    assert response.status_code == 200
    assert response.json() == {
        'document_id': 123,
        'status': 'indexed',
        'chunks_count': 2,
        'error': None,
    }


def test_get_document_status_missing_returns_404():
    app.dependency_overrides[get_status_use_case] = lambda: StatusUseCaseStub()
    client = TestClient(app)

    response = client.get('/api/v1/documents/404/status')

    assert response.status_code == 404
    assert response.json()['error'] == 'document_not_found'


def test_delete_document_returns_deleted():
    stub = MutationUseCaseStub(result=DocumentStatus.DELETED)
    app.dependency_overrides[get_delete_use_case] = lambda: stub
    client = TestClient(app)

    response = client.delete('/api/v1/documents/123')

    assert response.status_code == 200
    assert response.json() == {'document_id': 123, 'status': 'deleted'}
    assert stub.calls == [123]


def test_reindex_deleted_document_returns_409():
    app.dependency_overrides[get_reindex_use_case] = lambda: MutationUseCaseStub(
        result=DocumentStatus.QUEUED,
        error=DocumentDeletedError(),
    )
    client = TestClient(app)

    response = client.post('/api/v1/documents/123/reindex')

    assert response.status_code == 409
    assert response.json()['error'] == 'document_deleted'
