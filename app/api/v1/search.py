from fastapi import APIRouter, Depends
from app.api.dependencies import get_search_use_case
from app.api.v1.schemas.search import SearchRequest, SearchResponse
from app.api.v1.schemas.query import SourceDTO
from app.application.use_cases.search_documents import SearchDocumentsUseCase

router = APIRouter(tags=['search'])


@router.post('/search', response_model=SearchResponse)
async def search_documents(request: SearchRequest, use_case: SearchDocumentsUseCase = Depends(get_search_use_case)) -> SearchResponse:
    results = await use_case.execute(request.query, request.top_k)
    return SearchResponse(results=[SourceDTO(document_id=s.document_id, title=s.title, score=s.score, text=s.text) for s in results])
