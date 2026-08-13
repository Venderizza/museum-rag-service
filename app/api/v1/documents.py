from fastapi import APIRouter, Depends, status
from app.api.dependencies import get_add_document_use_case, get_delete_use_case, get_reindex_use_case, get_status_use_case
from app.api.v1.schemas.documents import AddDocumentRequest, DocumentMutationResponse, DocumentStatusResponse
from app.application.use_cases.add_document import AddDocumentUseCase
from app.application.use_cases.delete_document import DeleteDocumentUseCase
from app.application.use_cases.get_document_status import GetDocumentStatusUseCase
from app.application.use_cases.reindex_document import ReindexDocumentUseCase

router = APIRouter(prefix='/documents', tags=['documents'])


@router.post('/{document_id}', response_model=DocumentMutationResponse, status_code=status.HTTP_202_ACCEPTED)
async def add_document(
    document_id: int,
    request: AddDocumentRequest,
    use_case: AddDocumentUseCase = Depends(get_add_document_use_case),
) -> DocumentMutationResponse:
    result = await use_case.execute(document_id=document_id, title=request.title, body=request.body, metadata=request.metadata)
    return DocumentMutationResponse(document_id=document_id, status=result)


@router.get('/{document_id}/status', response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: int,
    use_case: GetDocumentStatusUseCase = Depends(get_status_use_case),
) -> DocumentStatusResponse:
    result = await use_case.execute(document_id)
    return DocumentStatusResponse(document_id=result.document_id, status=result.status, chunks_count=result.chunks_count, error=result.error)


@router.delete('/{document_id}', response_model=DocumentMutationResponse)
async def delete_document(
    document_id: int,
    use_case: DeleteDocumentUseCase = Depends(get_delete_use_case),
) -> DocumentMutationResponse:
    result = await use_case.execute(document_id)
    return DocumentMutationResponse(document_id=document_id, status=result)


@router.post('/{document_id}/reindex', response_model=DocumentMutationResponse, status_code=status.HTTP_202_ACCEPTED)
async def reindex_document(
    document_id: int,
    use_case: ReindexDocumentUseCase = Depends(get_reindex_use_case),
) -> DocumentMutationResponse:
    result = await use_case.execute(document_id)
    return DocumentMutationResponse(document_id=document_id, status=result)
